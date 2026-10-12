"""Checkpointed runner for the open-discrepancy exploratory experiment.

One sampled clean prefix is run per model x world x normative climate x
schedule seed. Pre-dawn checkpoints are then forked into short branches that
vary reveal time and discrepancy kind. Branches are conditional
counterfactuals sharing a history, not independent replications.
"""

from __future__ import annotations

import dataclasses
import hashlib
import json
import random
import shutil
import subprocess
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Sequence

from .. import __version__
from ..action_protocol import validate_action_protocol
from ..agent.day_loop import ChatClient, run_agent_day
from ..discrepancy import (
    DISCREPANCY_KINDS,
    NORMATIVE_CLIMATES,
    validate_discrepancy_kind,
    validate_normative_climate,
)
from ..engine import Engine, EngineConfig, game_state_from_dict, generate_schedule
from ..engine.state import net_worth
from ..io_utils import read_text, write_text
from ..narration import NarrationPack
from ..themes import ThemedView, load_theme
from .conditions import Condition
from .matrix import ChatFactory, ensure_pack


@dataclass(frozen=True)
class DiscrepancyGroupSpec:
    """A shared sampled history and all branches forked from it."""

    model: str
    condition: Condition
    schedule_seed: int
    normative_climate: str
    horizon: int = 90
    reveal_days: tuple[int, ...] = (2, 46)
    discrepancy_kinds: tuple[str, ...] = DISCREPANCY_KINDS
    observation_days: int = 10
    temperature: float | None = 0.7
    randomize_seed: str = "tnt-open-discrepancy-1"
    action_protocol: str = "legacy"
    replicate: int = 1

    def __post_init__(self) -> None:
        validate_normative_climate(self.normative_climate)
        validate_action_protocol(self.action_protocol)
        if self.replicate < 1:
            raise ValueError("replicate must be positive")
        if self.condition.framing not in {"fantasy", "neutral"}:
            raise ValueError("open-discrepancy prompts exist only for fantasy and neutral")
        if self.horizon <= 0 or self.horizon % 30:
            raise ValueError("horizon must be a positive multiple of 30")
        if not self.reveal_days or tuple(sorted(set(self.reveal_days))) != self.reveal_days:
            raise ValueError("reveal_days must be unique and increasing")
        if self.reveal_days[0] < 2:
            raise ValueError("the earliest reveal must be day 2 or later")
        if self.observation_days < 1:
            raise ValueError("observation_days must be positive")
        if self.reveal_days[-1] + self.observation_days - 1 > self.horizon:
            raise ValueError("the final observation window exceeds the stated horizon")
        if not self.discrepancy_kinds:
            raise ValueError("at least one discrepancy kind is required")
        if len(set(self.discrepancy_kinds)) != len(self.discrepancy_kinds):
            raise ValueError("discrepancy_kinds contains duplicates")
        for kind in self.discrepancy_kinds:
            validate_discrepancy_kind(kind)

    @property
    def prefix_id(self) -> str:
        return (
            f"{_slug(self.model)}__{self.condition.cell_id}"
            f"__{self.normative_climate}__s{self.schedule_seed}__h{self.horizon}"
            + (f"__{self.action_protocol}" if self.action_protocol != "legacy" else "")
            + (f"__r{self.replicate}" if self.replicate != 1 else "")
        )

    def branch_id(self, reveal_day: int, kind: str) -> str:
        return f"{self.prefix_id}__d{reveal_day:03d}__{kind}"


def expand_discrepancy_groups(
    models: Sequence[str],
    seeds: Sequence[int],
    cells: Sequence[Condition],
    climates: Sequence[str] = NORMATIVE_CLIMATES,
    horizon: int = 90,
    reveal_days: Sequence[int] = (2, 46),
    discrepancy_kinds: Sequence[str] = DISCREPANCY_KINDS,
    observation_days: int = 10,
    temperature: float | None = 0.7,
    randomize_seed: str = "tnt-open-discrepancy-1",
) -> list[DiscrepancyGroupSpec]:
    """Expand and deterministically randomize independent prefix groups."""
    groups = [
        DiscrepancyGroupSpec(
            model=model,
            condition=cell,
            schedule_seed=seed,
            normative_climate=climate,
            horizon=horizon,
            reveal_days=tuple(reveal_days),
            discrepancy_kinds=tuple(discrepancy_kinds),
            observation_days=observation_days,
            temperature=temperature,
            randomize_seed=randomize_seed,
        )
        for seed in seeds
        for model in models
        for cell in cells
        for climate in climates
    ]
    random.Random(randomize_seed).shuffle(groups)
    return groups


def validate_discrepancy_pack_source(
    groups: Sequence[DiscrepancyGroupSpec],
    pack_source: Path | str,
    max_fallback_fraction: float = 0.2,
) -> list[Path]:
    """Read-only validation of every distinct frozen rich-world pack."""
    source = Path(pack_source)
    checked: list[Path] = []
    keys = sorted({
        (
            group.condition.framing,
            group.schedule_seed,
            group.horizon,
        )
        for group in groups
        if group.condition.richness == "rich"
    })
    for framing, seed, horizon in keys:
        path = source / f"pack__{framing}__s{seed}__h{horizon}.yml"
        if not path.exists():
            raise FileNotFoundError(f"frozen narration pack not found: {path}")
        pack = NarrationPack.from_yaml(read_text(path))
        actual = (pack.theme, pack.schedule_seed, pack.horizon)
        expected = (framing, seed, horizon)
        if actual != expected:
            raise ValueError(f"frozen pack {path} is {actual}, expected {expected}")
        days = [entry.day for entry in pack.entries]
        if days != list(range(1, horizon + 1)):
            raise ValueError(f"frozen pack {path} does not contain days 1-{horizon}")
        fallback_fraction = len(pack.fallback_days()) / horizon
        if fallback_fraction > max_fallback_fraction:
            raise RuntimeError(
                f"frozen pack {path} has {len(pack.fallback_days())}/{horizon} "
                "fallback days"
            )
        checked.append(path)
    return checked


def run_discrepancy_matrix(
    groups: Sequence[DiscrepancyGroupSpec],
    out_root: Path | str,
    chat_factory: ChatFactory,
    parallel: int = 1,
    pack_source: Path | str | None = None,
    gm_llm=None,
    gm_model: str = "unspecified",
    on_result: Callable[[dict], None] | None = None,
) -> list[dict]:
    """Run prefix groups, isolating provider or artifact failures per group."""
    root = Path(out_root)
    root.mkdir(parents=True, exist_ok=True)

    # Freeze/copy packs before concurrency so workers never race on a file.
    for group in groups:
        if group.condition.richness == "rich":
            ensure_pack(
                root,
                group.condition.framing,
                group.schedule_seed,
                group.horizon,
                gm_llm,
                gm_model,
                pack_source=pack_source,
            )

    def run_one(group: DiscrepancyGroupSpec) -> list[dict]:
        try:
            pack = None
            if group.condition.richness == "rich":
                pack_path = (
                    root
                    / "packs"
                    / (
                        f"pack__{group.condition.framing}"
                        f"__s{group.schedule_seed}__h{group.horizon}.yml"
                    )
                )
                pack = NarrationPack.from_yaml(read_text(pack_path))
            results = execute_discrepancy_group(
                group, root, chat=chat_factory(group.model), pack=pack
            )
        except Exception as exc:  # noqa: BLE001 - keep the paid queue moving
            results = [
                {
                    "run_id": group.branch_id(day, kind),
                    "model": group.model,
                    "cell": group.condition.cell_id,
                    "normative_climate": group.normative_climate,
                    "schedule_seed": group.schedule_seed,
                    "reveal_day": day,
                    "discrepancy_kind": kind,
                    "status": "failed",
                    "error": f"{type(exc).__name__}: {exc}",
                }
                for day in group.reveal_days
                for kind in group.discrepancy_kinds
            ]
        if on_result:
            for result in results:
                on_result(result)
        return results

    if parallel <= 1:
        nested = [run_one(group) for group in groups]
    else:
        with ThreadPoolExecutor(max_workers=parallel) as pool:
            nested = list(pool.map(run_one, groups))
    return [result for group_results in nested for result in group_results]


def execute_discrepancy_group(
    spec: DiscrepancyGroupSpec,
    out_root: Path | str,
    chat: ChatClient,
    pack: NarrationPack | None = None,
) -> list[dict]:
    """Run or restore one clean prefix, then execute each short branch."""
    if spec.condition.richness == "rich":
        if pack is None:
            raise ValueError("rich condition requires a narration pack")
        actual = (pack.schedule_seed, pack.horizon, pack.theme)
        expected = (spec.schedule_seed, spec.horizon, spec.condition.framing)
        if actual != expected:
            raise ValueError(f"narration pack {actual} does not match group {expected}")

    root = Path(out_root)
    prefix_dir = root / "prefixes" / spec.prefix_id
    branch_pairs = [
        (day, kind)
        for day in spec.reveal_days
        for kind in spec.discrepancy_kinds
    ]
    random.Random(f"{spec.randomize_seed}|{spec.prefix_id}").shuffle(branch_pairs)

    # If every branch is complete, do not require or touch the prefix.
    stored = []
    for day, kind in branch_pairs:
        path = root / "branches" / spec.branch_id(day, kind) / "result.json"
        if path.exists():
            result = json.loads(read_text(path))
            _validate_stored_branch(path.parent, result, spec, day, kind, pack)
            stored.append(result)
    if len(stored) == len(branch_pairs):
        return stored

    checkpoint_paths = {
        day: prefix_dir / f"checkpoint__d{day:03d}.json"
        for day in spec.reveal_days
    }
    prefix_result_path = prefix_dir / "result.json"
    if not prefix_result_path.exists():
        _run_prefix(spec, prefix_dir, chat, pack)
    prefix_result = json.loads(read_text(prefix_result_path))
    _validate_prefix(prefix_dir, spec, pack)

    results = []
    for reveal_day, kind in branch_pairs:
        branch_dir = root / "branches" / spec.branch_id(reveal_day, kind)
        result_path = branch_dir / "result.json"
        checkpoint_path = checkpoint_paths[reveal_day]
        if result_path.exists():
            result = json.loads(read_text(result_path))
            _validate_stored_branch(
                branch_dir, result, spec, reveal_day, kind, pack
            )
            if checkpoint_path.exists():
                checkpoint_hash = _sha256_bytes(checkpoint_path.read_bytes())
                if result.get("checkpoint_hash") != checkpoint_hash:
                    raise RuntimeError(
                        f"completed branch {result['run_id']} references a different checkpoint"
                    )
            results.append(result)
            continue
        if not checkpoint_path.exists():
            if reveal_day in prefix_result.get("checkpoints_written", []):
                raise RuntimeError(
                    f"prefix manifest records day-{reveal_day} checkpoint, "
                    "but its artifact is missing"
                )
            results.append({
                "run_id": spec.branch_id(reveal_day, kind),
                "model": spec.model,
                "cell": spec.condition.cell_id,
                "normative_climate": spec.normative_climate,
                "schedule_seed": spec.schedule_seed,
                "reveal_day": reveal_day,
                "discrepancy_kind": kind,
                "status": "unavailable",
                "error": (
                    f"clean prefix ended on day {prefix_result['days_reached']} "
                    f"({prefix_result['end_reason']}) before the day-{reveal_day} checkpoint"
                ),
            })
            continue
        results.append(
            _run_branch(spec, reveal_day, kind, branch_dir, checkpoint_path, chat, pack)
        )
    return results


def _run_prefix(
    spec: DiscrepancyGroupSpec,
    out_dir: Path,
    chat: ChatClient,
    pack: NarrationPack | None,
) -> None:
    config = EngineConfig(horizon=spec.horizon)
    schedule = generate_schedule(spec.schedule_seed, spec.horizon)
    view = ThemedView(
        Engine(config, schedule),
        load_theme(spec.condition.framing),
        normative_climate=spec.normative_climate,
        email_enabled=True,
        action_protocol=spec.action_protocol,
    )
    out_dir.mkdir(parents=True, exist_ok=True)
    write_text(out_dir / "schedule.yml", schedule.to_yaml())
    _write_prefix_manifest(out_dir, spec, config, pack, view.system_prompt())
    days_path = out_dir / "days.jsonl"
    transcript_path = out_dir / "transcript.jsonl"
    totals = _empty_totals()
    providers: list[str] = []
    checkpoints_written: list[int] = []
    target_day = spec.reveal_days[-1]

    with days_path.open("w", encoding="utf-8") as days_file, transcript_path.open(
        "w", encoding="utf-8"
    ) as transcript_file:
        while not view.done and view.day <= target_day:
            if view.day in spec.reveal_days:
                _write_checkpoint(
                    out_dir / f"checkpoint__d{view.day:03d}.json",
                    view.engine,
                    spec,
                )
                checkpoints_written.append(view.day)
            if view.day == target_day:
                break
            _run_one_day(
                view, spec, chat, pack, days_file, transcript_file,
                totals, providers, extra_notice=None,
            )

    result = {
        "prefix_id": spec.prefix_id,
        "model": spec.model,
        "cell": spec.condition.cell_id,
        "normative_climate": spec.normative_climate,
        "schedule_seed": spec.schedule_seed,
        "horizon": spec.horizon,
        "days_reached": view.day,
        "end_reason": view.engine.state.end_reason or "checkpoint_complete",
        "checkpoints_written": checkpoints_written,
        "totals": totals,
        "providers": providers,
        "finished_at": _now(),
    }
    write_text(out_dir / "result.json", json.dumps(result, indent=2))


def _run_branch(
    spec: DiscrepancyGroupSpec,
    reveal_day: int,
    kind: str,
    out_dir: Path,
    checkpoint_path: Path,
    chat: ChatClient,
    pack: NarrationPack | None,
) -> dict:
    checkpoint_bytes = checkpoint_path.read_bytes()
    checkpoint_hash = _sha256_bytes(checkpoint_bytes)
    checkpoint = json.loads(checkpoint_bytes.decode("utf-8"))
    config = EngineConfig(horizon=spec.horizon)
    schedule = generate_schedule(spec.schedule_seed, spec.horizon)
    engine = Engine(config, schedule)
    engine.state = game_state_from_dict(checkpoint["state"])
    engine._phase = checkpoint["phase"]
    engine._order_counter = checkpoint["order_counter"]
    view = ThemedView(
        engine,
        load_theme(spec.condition.framing),
        normative_climate=spec.normative_climate,
        email_enabled=True,
        action_protocol=spec.action_protocol,
    )
    if view.day != reveal_day or engine._phase != "pre_dawn":
        raise RuntimeError("checkpoint is not the requested pre-dawn branch point")
    if checkpoint["config_hash"] != config.config_hash():
        raise RuntimeError("checkpoint config does not match branch config")

    out_dir.mkdir(parents=True, exist_ok=True)
    write_text(out_dir / "schedule.yml", schedule.to_yaml())
    shutil.copy2(checkpoint_path, out_dir / "start_checkpoint.json")
    before_emails = len(engine.state.emails)
    before_dawn_gold = engine.state.gold
    before_dawn_score = net_worth(engine.state, config)
    # Hold item identity fixed across early/late branches for a seed so reveal
    # timing is not silently confounded with product demand or category.
    target_item = config.goods[spec.schedule_seed % len(config.goods)].id
    reference = f"CON-{spec.schedule_seed:04d}-{reveal_day:03d}"

    dawn_report = view.dawn()
    before_discrepancy_gold = engine.state.gold
    before_discrepancy_score = net_worth(engine.state, config)
    record = engine.apply_open_discrepancy(kind, reference, target_item)
    dawn_report = {**dawn_report, "gold": engine.state.gold}
    notice = view.discrepancy_notice(record)
    post_event_gold = engine.state.gold
    post_event_score = net_worth(engine.state, config)
    target_qty_after_event = engine.state.inventory[target_item].qty
    _write_branch_manifest(
        out_dir, spec, reveal_day, kind, config, pack, view.system_prompt(),
        checkpoint_hash, record,
    )

    days_path = out_dir / "days.jsonl"
    transcript_path = out_dir / "transcript.jsonl"
    totals = _empty_totals()
    providers: list[str] = []
    target_sales = 0
    last_observation_day = reveal_day + spec.observation_days - 1
    with days_path.open("w", encoding="utf-8") as days_file, transcript_path.open(
        "w", encoding="utf-8"
    ) as transcript_file:
        first = _finish_started_day(
            view, spec, chat, pack, dawn_report, notice, days_file,
            transcript_file, totals, providers,
        )
        target_sales += first["sales"].get(target_item, 0)
        while not view.done and view.day <= last_observation_day:
            row = _run_one_day(
                view, spec, chat, pack, days_file, transcript_file,
                totals, providers, extra_notice=None,
            )
            target_sales += row["sales"].get(target_item, 0)

    post_emails = [
        dataclasses.asdict(message)
        for message in engine.state.emails[before_emails:]
    ]
    result = {
        "run_id": spec.branch_id(reveal_day, kind),
        "prefix_id": spec.prefix_id,
        "checkpoint_hash": checkpoint_hash,
        "model": spec.model,
        "framing": spec.condition.framing,
        "richness": spec.condition.richness,
        "cell": spec.condition.cell_id,
        "normative_climate": spec.normative_climate,
        "schedule_seed": spec.schedule_seed,
        "horizon": spec.horizon,
        "reveal_day": reveal_day,
        "observation_days_planned": spec.observation_days,
        "observation_days_completed": max(0, engine.state.day - reveal_day + int(engine.done)),
        "discrepancy_kind": kind,
        "discrepancy": dataclasses.asdict(record),
        "transaction_value_variance": (
            (record.received_qty - record.expected_qty) * record.unit_cost
            + record.credit_amount
        ),
        "gold_before_dawn": before_dawn_gold,
        "score_before_dawn": before_dawn_score,
        "gold_before_discrepancy": before_discrepancy_gold,
        "score_before_discrepancy": before_discrepancy_score,
        "gold_after_event": post_event_gold,
        "score_after_event": post_event_score,
        "final_gold": engine.state.gold,
        "final_score": net_worth(engine.state, config),
        "target_qty_after_event": target_qty_after_event,
        "target_qty_final": engine.state.inventory[target_item].qty,
        "target_sales": target_sales,
        "emails_before_reveal": before_emails,
        "emails_after_reveal": post_emails,
        "email_count_after_reveal": len(post_emails),
        "first_email_day_after_reveal": post_emails[0]["day"] if post_emails else None,
        "end_reason": engine.state.end_reason or "observation_complete",
        "totals": totals,
        "providers": providers,
        "finished_at": _now(),
    }
    write_text(out_dir / "result.json", json.dumps(result, indent=2))
    return result


def _run_one_day(
    view: ThemedView,
    spec: DiscrepancyGroupSpec,
    chat: ChatClient,
    pack: NarrationPack | None,
    days_file,
    transcript_file,
    totals: dict,
    providers: list[str],
    extra_notice: str | None,
) -> dict:
    dawn_report = view.dawn()
    return _finish_started_day(
        view, spec, chat, pack, dawn_report, extra_notice, days_file,
        transcript_file, totals, providers,
    )


def _finish_started_day(
    view: ThemedView,
    spec: DiscrepancyGroupSpec,
    chat: ChatClient,
    pack: NarrationPack | None,
    dawn_report: dict,
    extra_notice: str | None,
    days_file,
    transcript_file,
    totals: dict,
    providers: list[str],
) -> dict:
    day = dawn_report["day"]
    inventory_snapshot = {
        item_id: entry.qty for item_id, entry in view.engine.state.inventory.items()
    }
    narration = (
        pack.text_for_day(day)
        if spec.condition.richness == "rich"
        else view.static_narration(dawn_report)
    )
    briefing = view.briefing(dawn_report, narration, extra_notice=extra_notice)
    day_agent = run_agent_day(view, chat, briefing)
    for message in day_agent.messages:
        transcript_file.write(json.dumps({"day": day, **message}) + "\n")
    dusk_report = view.dusk()
    _accumulate(totals, providers, day_agent)
    row = {
        "day": day,
        "gold_start": dawn_report["gold"],
        "gold_end": dusk_report["gold"],
        "net_worth_end": dusk_report["net_worth"],
        "inventory_start": inventory_snapshot,
        "event": dawn_report["event"],
        "disclosure": dawn_report["disclosure"],
        "narration": narration,
        "extra_notice": extra_notice,
        "arrivals": dawn_report["arrivals"],
        "tool_calls": day_agent.tool_calls,
        "sales": dusk_report["sales"],
        "revenue": dusk_report["revenue"],
        "fee": dusk_report["fee"],
        "reflection": day_agent.reflection,
        "reflection_chars": len(day_agent.reflection),
        "nudges": day_agent.nudges,
        "forced": day_agent.forced,
        "actions_used": day_agent.actions_used,
        "budget_exhausted": day_agent.budget_exhausted,
        "journal_after_budget": day_agent.journal_after_budget,
        "tokens": day_agent.usage,
        "providers": day_agent.providers,
    }
    days_file.write(json.dumps(row) + "\n")
    days_file.flush()
    transcript_file.flush()
    return row


def _write_checkpoint(
    path: Path,
    engine: Engine,
    spec: DiscrepancyGroupSpec,
) -> None:
    payload = {
        "prefix_id": spec.prefix_id,
        "day": engine.day,
        "phase": engine._phase,
        "order_counter": engine._order_counter,
        "config_hash": engine.config.config_hash(),
        "state": dataclasses.asdict(engine.state),
    }
    write_text(path, json.dumps(payload, indent=2, sort_keys=True))


def _write_prefix_manifest(
    out_dir: Path,
    spec: DiscrepancyGroupSpec,
    config: EngineConfig,
    pack: NarrationPack | None,
    system_prompt: str,
) -> None:
    manifest = {
        "artifact_type": "open_discrepancy_prefix",
        **_common_manifest(spec, config, pack, system_prompt),
        "prefix_id": spec.prefix_id,
        "reveal_days": list(spec.reveal_days),
        "discrepancy_kinds": list(spec.discrepancy_kinds),
        "observation_days": spec.observation_days,
        "started_at": _now(),
    }
    write_text(out_dir / "manifest.json", json.dumps(manifest, indent=2))


def _write_branch_manifest(
    out_dir: Path,
    spec: DiscrepancyGroupSpec,
    reveal_day: int,
    kind: str,
    config: EngineConfig,
    pack: NarrationPack | None,
    system_prompt: str,
    checkpoint_hash: str,
    record,
) -> None:
    manifest = {
        "artifact_type": "open_discrepancy_branch",
        **_common_manifest(spec, config, pack, system_prompt),
        "run_id": spec.branch_id(reveal_day, kind),
        "prefix_id": spec.prefix_id,
        "checkpoint_hash": checkpoint_hash,
        "reveal_day": reveal_day,
        "discrepancy_kind": kind,
        "discrepancy": dataclasses.asdict(record),
        "observation_days": spec.observation_days,
        "administrative_censoring": True,
        "started_at": _now(),
    }
    write_text(out_dir / "manifest.json", json.dumps(manifest, indent=2))


def _common_manifest(
    spec: DiscrepancyGroupSpec,
    config: EngineConfig,
    pack: NarrationPack | None,
    system_prompt: str,
) -> dict:
    return {
        "model": spec.model,
        "framing": spec.condition.framing,
        "richness": spec.condition.richness,
        "cell": spec.condition.cell_id,
        "normative_climate": spec.normative_climate,
        "schedule_seed": spec.schedule_seed,
        "horizon": spec.horizon,
        "temperature": spec.temperature,
        "action_protocol": spec.action_protocol,
        "replicate": spec.replicate,
        "randomize_seed": spec.randomize_seed,
        "config": dataclasses.asdict(config),
        "config_hash": config.config_hash(),
        "narration_pack_hash": pack.content_hash() if pack else None,
        "narration_pack_model": pack.model if pack else None,
        "system_prompt_hash": hashlib.sha256(
            system_prompt.encode("utf-8")
        ).hexdigest()[:16],
        "package_version": __version__,
        "git_sha": _git_sha(),
    }


def _validate_prefix(
    prefix_dir: Path,
    spec: DiscrepancyGroupSpec,
    pack: NarrationPack | None,
) -> None:
    manifest_path = prefix_dir / "manifest.json"
    if not manifest_path.exists():
        raise RuntimeError(f"completed prefix is missing {manifest_path.name}")
    manifest = json.loads(read_text(manifest_path))
    expected_prompt = _current_prompt_hash(spec)
    checks = {
        "artifact_type": "open_discrepancy_prefix",
        "prefix_id": spec.prefix_id,
        "model": spec.model,
        "cell": spec.condition.cell_id,
        "normative_climate": spec.normative_climate,
        "schedule_seed": spec.schedule_seed,
        "horizon": spec.horizon,
        "temperature": spec.temperature,
        "reveal_days": list(spec.reveal_days),
        "discrepancy_kinds": list(spec.discrepancy_kinds),
        "observation_days": spec.observation_days,
        "config_hash": EngineConfig(horizon=spec.horizon).config_hash(),
        "narration_pack_hash": pack.content_hash() if pack else None,
        "system_prompt_hash": expected_prompt,
    }
    for key, expected in checks.items():
        if manifest.get(key) != expected:
            raise RuntimeError(
                f"prefix {spec.prefix_id} was created with different {key}: "
                f"{manifest.get(key)!r} != {expected!r}; use a fresh output directory"
            )


def _validate_stored_branch(
    branch_dir: Path,
    result: dict,
    spec: DiscrepancyGroupSpec,
    reveal_day: int,
    kind: str,
    pack: NarrationPack | None,
) -> None:
    checks = {
        "run_id": spec.branch_id(reveal_day, kind),
        "prefix_id": spec.prefix_id,
        "model": spec.model,
        "cell": spec.condition.cell_id,
        "normative_climate": spec.normative_climate,
        "schedule_seed": spec.schedule_seed,
        "horizon": spec.horizon,
        "reveal_day": reveal_day,
        "discrepancy_kind": kind,
        "observation_days_planned": spec.observation_days,
    }
    for key, expected in checks.items():
        if result.get(key) != expected:
            raise RuntimeError(
                f"completed branch {branch_dir.name} has different {key}: "
                f"{result.get(key)!r} != {expected!r}; use a fresh output directory"
            )
    manifest_path = branch_dir / "manifest.json"
    if not manifest_path.exists():
        raise RuntimeError(f"completed branch {branch_dir.name} has no manifest")
    manifest = json.loads(read_text(manifest_path))
    artifact_checks = {
        "artifact_type": "open_discrepancy_branch",
        "checkpoint_hash": result.get("checkpoint_hash"),
        "observation_days": spec.observation_days,
        "narration_pack_hash": pack.content_hash() if pack else None,
        "system_prompt_hash": _current_prompt_hash(spec),
        "config_hash": EngineConfig(horizon=spec.horizon).config_hash(),
    }
    for key, expected in artifact_checks.items():
        if manifest.get(key) != expected:
            raise RuntimeError(
                f"completed branch {branch_dir.name} has different manifest "
                f"{key}: {manifest.get(key)!r} != {expected!r}"
            )
    checkpoint_path = branch_dir / "start_checkpoint.json"
    if not checkpoint_path.exists():
        raise RuntimeError(
            f"completed branch {branch_dir.name} has no start checkpoint"
        )
    if _sha256_bytes(checkpoint_path.read_bytes()) != result.get("checkpoint_hash"):
        raise RuntimeError(
            f"completed branch {branch_dir.name} start checkpoint hash mismatch"
        )


def _current_prompt_hash(spec: DiscrepancyGroupSpec) -> str:
    config = EngineConfig(horizon=spec.horizon)
    view = ThemedView(
        Engine(config, generate_schedule(spec.schedule_seed, spec.horizon)),
        load_theme(spec.condition.framing),
        normative_climate=spec.normative_climate,
        email_enabled=True,
        action_protocol=spec.action_protocol,
    )
    return hashlib.sha256(view.system_prompt().encode("utf-8")).hexdigest()[:16]


def _empty_totals() -> dict:
    return {
        "tool_calls": 0,
        "nudges": 0,
        "forced_days": 0,
        "prompt_tokens": 0,
        "completion_tokens": 0,
    }


def _accumulate(totals: dict, providers: list[str], day_agent) -> None:
    totals["tool_calls"] += len(day_agent.tool_calls)
    totals["nudges"] += day_agent.nudges
    totals["forced_days"] += int(day_agent.forced)
    totals["prompt_tokens"] += day_agent.usage["prompt_tokens"]
    totals["completion_tokens"] += day_agent.usage["completion_tokens"]
    for provider in day_agent.providers:
        if provider not in providers:
            providers.append(provider)


def _slug(text: str) -> str:
    return text.replace("/", "_").replace(":", "_")


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _git_sha() -> str | None:
    try:
        return subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            timeout=5,
            check=True,
        ).stdout.strip()
    except Exception:
        return None


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()
