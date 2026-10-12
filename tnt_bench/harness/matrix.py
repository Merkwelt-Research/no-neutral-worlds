"""Run-set expansion and execution (spec §7).

A run-set = models x cells x seeds at one horizon, sharing one schedule per
seed and one narration pack per (seed, theme). Packs are generated once and
cached under <out_root>/packs/. Completed runs are skipped, so a run-set
can be re-invoked after crashes, new seeds, or new models.
"""

from __future__ import annotations

import json
import shutil
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Callable, Sequence

from ..agent.day_loop import ChatClient
from ..engine import generate_schedule
from ..exploit import validate_exploit_condition
from ..narration import NarrationPack, generate_pack
from ..narration.pack import LLMFn
from ..io_utils import read_text, write_text
from ..themes import load_theme
from .conditions import ALL_CELLS, Condition
from .run import BASELINE_PREFIX, RunSpec, execute_run

# model name -> ChatClient (None allowed for baseline-only matrices)
ChatFactory = Callable[[str], ChatClient]


def expand_specs(
    models: Sequence[str],
    seeds: Sequence[int],
    horizon: int = 30,
    cells: Sequence[Condition] = ALL_CELLS,
    disclose_horizon: bool = True,
    carrying_cost: float = 0.0,
    interleave_seed: str | None = None,
    block_seed: str | None = None,
    temperature: float | None = None,
    replicate: int | Sequence[int] = 1,
    exploit_condition: str | Sequence[str] | None = None,
) -> list[RunSpec]:
    """Expand the matrix. Default order is model -> cell -> seed, which
    executes conditions in fixed blocks — a treatment-by-time confound
    when providers drift (2026-07-10 external review). Two opt-in
    remedies, mutually exclusive (run ids and artifacts are
    order-independent either way; historical commands replay
    byte-identically without them):

    - `interleave_seed`: shuffle the whole queue deterministically.
    - `block_seed`: randomized complete blocks (the replication arm's
      protocol, stronger against provider drift). One block per
      (seed, model, replicate), seed-major with realizations
      innermost, so a seed's blocks — both models', both
      realizations' — sit adjacent in wall-clock time (independent
      realizations collected in the same window keep the sampling-
      variance estimate free of drift). Within a block the cells run
      in a frozen-seed random order whose lead condition rotates
      through the cell list across successive blocks, so every
      condition leads (near-)equally often. With --parallel equal to
      the cell count, each block's cells share one wall-clock window.

    `replicate` may be a single realization number or a sequence
    (e.g. (1, 2)) to expand every cell once per realization.

    `exploit_condition` may likewise be one condition or a sequence. A
    sequence crosses every world cell with every exploit treatment inside
    the same randomized complete block; this is required for the exploit
    factorial so normative condition is not confounded with collection time.
    """
    if interleave_seed is not None and block_seed is not None:
        raise ValueError("interleave_seed and block_seed are mutually exclusive")
    replicates = (replicate,) if isinstance(replicate, int) else tuple(replicate)
    if exploit_condition is None:
        exploit_conditions: tuple[str | None, ...] = (None,)
    elif isinstance(exploit_condition, str):
        exploit_conditions = (exploit_condition,)
    else:
        exploit_conditions = tuple(exploit_condition)
        if not exploit_conditions:
            raise ValueError("exploit_condition sequence cannot be empty")
    if len(set(exploit_conditions)) != len(exploit_conditions):
        raise ValueError("exploit_condition sequence contains duplicates")
    for condition in exploit_conditions:
        validate_exploit_condition(condition)

    treatments = tuple(
        (cell, condition)
        for cell in cells
        for condition in exploit_conditions
    )

    def spec(
        model: str,
        cell: Condition,
        seed: int,
        rep: int,
        condition: str | None,
    ) -> RunSpec:
        return RunSpec(
            model=model, condition=cell, schedule_seed=seed,
            horizon=horizon, disclose_horizon=disclose_horizon,
            carrying_cost=carrying_cost, replicate=rep,
            temperature=(
                None if model.startswith(BASELINE_PREFIX) else temperature
            ),
            exploit_condition=condition,
        )

    if block_seed is not None:
        import random

        specs = []
        blocks = [
            (seed, model, rep)
            for seed in seeds
            for model in models
            for rep in replicates
        ]
        for i, (seed, model, rep) in enumerate(blocks):
            block_treatments = list(treatments)
            random.Random(f"{block_seed}|{model}|s{seed}|r{rep}").shuffle(
                block_treatments
            )
            lead = treatments[i % len(treatments)]
            j = block_treatments.index(lead)
            block_treatments = block_treatments[j:] + block_treatments[:j]
            specs.extend(
                spec(model, cell, seed, rep, condition)
                for cell, condition in block_treatments
            )
        return specs

    specs = [
        spec(model, cell, seed, rep, condition)
        for rep in replicates
        for model in models
        for cell, condition in treatments
        for seed in seeds
    ]
    if interleave_seed is not None:
        import random

        random.Random(interleave_seed).shuffle(specs)
    return specs


def _pack_filename(theme_name: str, schedule_seed: int, horizon: int) -> str:
    return f"pack__{theme_name}__s{schedule_seed}__h{horizon}.yml"


def _load_matching_pack(
    path: Path,
    theme_name: str,
    schedule_seed: int,
    horizon: int,
) -> NarrationPack:
    pack = NarrationPack.from_yaml(read_text(path))
    expected = (schedule_seed, horizon, theme_name)
    actual = (pack.schedule_seed, pack.horizon, pack.theme)
    if actual != expected:
        raise ValueError(
            f"narration pack {path} has seed/horizon/theme {actual}, "
            f"expected {expected}"
        )
    days = [entry.day for entry in pack.entries]
    if days != list(range(1, horizon + 1)):
        raise ValueError(
            f"narration pack {path} is incomplete or out of order: "
            f"expected days 1-{horizon}"
        )
    return pack


def ensure_pack(
    out_root: Path | str,
    theme_name: str,
    schedule_seed: int,
    horizon: int,
    gm_llm: LLMFn | None,
    gm_model: str,
    max_fallback_fraction: float = 0.2,
    pack_source: Path | str | None = None,
) -> NarrationPack:
    """Load the cached narration pack for (theme, seed, horizon), generating
    it once if absent. If `pack_source` names a directory containing frozen
    packs, the exact source artifact is copied into this run set instead of
    calling a GM. A generation where too many days fell back to static lines
    is NOT cached — a degraded pack would silently weaken the rich condition
    for every run that shares it."""
    packs_dir = Path(out_root) / "packs"
    packs_dir.mkdir(parents=True, exist_ok=True)
    filename = _pack_filename(theme_name, schedule_seed, horizon)
    path = packs_dir / filename
    if path.exists():
        return _load_matching_pack(path, theme_name, schedule_seed, horizon)
    if pack_source is not None:
        source_path = Path(pack_source) / filename
        if not source_path.exists():
            raise FileNotFoundError(f"frozen narration pack not found: {source_path}")
        source_pack = _load_matching_pack(
            source_path, theme_name, schedule_seed, horizon
        )
        fallback_fraction = len(source_pack.fallback_days()) / horizon
        if fallback_fraction > max_fallback_fraction:
            raise RuntimeError(
                f"frozen pack {source_path} degraded: "
                f"{len(source_pack.fallback_days())}/{horizon} fallback days"
            )
        shutil.copy2(source_path, path)
        return _load_matching_pack(path, theme_name, schedule_seed, horizon)
    if gm_llm is None:
        raise ValueError(
            f"rich cell needs gm_llm, a cached pack at {path}, or "
            f"--pack-source containing {filename}"
        )
    schedule = generate_schedule(schedule_seed, horizon)
    pack = generate_pack(schedule, load_theme(theme_name), gm_llm, model=gm_model)
    fallback_fraction = len(pack.fallback_days()) / horizon
    if fallback_fraction > max_fallback_fraction:
        raise RuntimeError(
            f"pack for {theme_name}/s{schedule_seed} degraded: "
            f"{len(pack.fallback_days())}/{horizon} days fell back to static lines "
            "(provider trouble or persistent guard failures) — not caching; retry"
        )
    write_text(path, pack.to_yaml())
    return pack


def run_matrix(
    specs: Sequence[RunSpec],
    out_root: Path | str,
    chat_factory: ChatFactory | None = None,
    gm_llm: LLMFn | None = None,
    gm_model: str = "unspecified",
    on_result: Callable[[dict], None] | None = None,
    parallel: int = 1,
    pack_source: Path | str | None = None,
) -> list[dict]:
    """Execute every spec, skipping completed runs. Baseline models need no
    chat client; rich cells need gm_llm, pre-cached packs, or a frozen
    `pack_source` directory.

    Failures are isolated per spec: an exception (provider outage, bad pack
    generation) records a {"status": "failed"} entry and the matrix moves on.
    Re-invoking the same matrix retries only the failed/missing runs.

    `parallel` > 1 runs that many specs concurrently. Runs are independent
    (separate directories, per-spec chat clients); packs are generated
    sequentially up front so concurrent runs never race the GM. Results
    return in spec order regardless of completion order."""

    def run_one(spec: RunSpec) -> dict:
        try:
            pack = None
            if spec.condition.richness == "rich":
                pack = ensure_pack(
                    out_root, spec.condition.framing, spec.schedule_seed,
                    spec.horizon, gm_llm, gm_model,
                    pack_source=pack_source,
                )

            chat = None
            if not spec.model.startswith(BASELINE_PREFIX):
                if chat_factory is None:
                    raise ValueError(f"model {spec.model!r} needs a chat_factory")
                chat = chat_factory(spec.model)

            result = execute_run(spec, out_root, chat=chat, pack=pack)
        except Exception as e:  # noqa: BLE001 — isolate the queue from any one run
            result = {
                "run_id": spec.run_id,
                "model": spec.model,
                "cell": spec.condition.cell_id,
                "schedule_seed": spec.schedule_seed,
                "horizon": spec.horizon,
                "status": "failed",
                "error": f"{type(e).__name__}: {e}",
            }
        if on_result:
            on_result(result)
        return result

    if parallel <= 1:
        return [run_one(spec) for spec in specs]

    # Pre-generate all needed packs sequentially before fanning out.
    if gm_llm is not None or pack_source is not None:
        for spec in specs:
            if spec.condition.richness == "rich":
                ensure_pack(
                    out_root, spec.condition.framing, spec.schedule_seed,
                    spec.horizon, gm_llm, gm_model,
                    pack_source=pack_source,
                )
    with ThreadPoolExecutor(max_workers=parallel) as pool:
        return list(pool.map(run_one, specs))


def summarize(out_root: Path | str) -> list[dict]:
    """Collect all completed results under out_root, best score first."""
    results = []
    root = Path(out_root)
    if root.exists():
        for result_path in sorted(root.glob("*/result.json")):
            results.append(json.loads(read_text(result_path)))
    return sorted(results, key=lambda r: r["score"], reverse=True)
