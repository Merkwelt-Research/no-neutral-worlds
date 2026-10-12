"""Run execution and artifacts (spec §7)."""

import json

import pytest

from tnt_bench.agent import ChatResponse, ChatToolCall
from tnt_bench.engine import generate_schedule
from tnt_bench.harness import Condition, RunSpec, execute_run
from tnt_bench.narration import generate_pack
from tnt_bench.themes import load_theme

VALID_REFLECTION = (
    "Held prices steady and watched the customers come and go; the balance is thinner "
    "than I'd like, so tomorrow I must decide whether to restock or hold cash."
)

CLEAN_NARRATION = (
    "The morning carriers filed through the gates in good order, and the market "
    "settled into its usual rhythm of small bargains and smaller complaints."
)


class EndDayChat:
    """An agent that only ever ends the day with a valid reflection."""

    def __call__(self, messages, tools):
        return ChatResponse(
            tool_calls=[ChatToolCall(id="tc", name="end_day",
                                     arguments={"reflection": VALID_REFLECTION})],
            usage={"prompt_tokens": 500, "completion_tokens": 50},
            provider="StubHost",
        )


class ExplodingChat:
    def __call__(self, messages, tools):
        raise AssertionError("chat client must not be called for a completed run")


def spec_for(model="baseline:heuristic", framing="fantasy", richness="static"):
    return RunSpec(
        model=model,
        condition=Condition(framing=framing, richness=richness),
        schedule_seed=42,
        horizon=30,
    )


def make_pack(framing="fantasy"):
    schedule = generate_schedule(42, 30)
    return generate_pack(schedule, load_theme(framing), lambda s, u: CLEAN_NARRATION, model="stub")


# ---------------------------------------------------------------- baselines


def test_baseline_run_writes_full_artifact_set(tmp_path):
    result = execute_run(spec_for(), tmp_path)
    assert result["score"] == 2830 and result["end_reason"] == "completed"

    run_dir = tmp_path / result["run_id"]
    assert (run_dir / "manifest.json").exists()
    assert (run_dir / "schedule.yml").exists()
    assert (run_dir / "result.json").exists()

    days = [json.loads(line) for line in (run_dir / "days.jsonl").read_text().splitlines()]
    assert len(days) == 30
    assert days[0]["day"] == 1 and days[-1]["day"] == 30
    assert all(d["reflection"] for d in days)
    assert all(d["disclosure"].startswith("EFFECT:") for d in days)

    manifest = json.loads((run_dir / "manifest.json").read_text())
    assert manifest["cell"] == "fantasy-static"
    assert manifest["config_hash"]
    assert manifest["narration_pack_hash"] is None


def test_llm_run_records_transcript_and_bankruptcy(tmp_path):
    """The end-day-only agent never prices anything -> sleeper -> bankrupt.
    (Proportional windfalls no longer buy the old extra day: bankrupt day 15.)"""
    spec = spec_for(model="stub-model")
    result = execute_run(spec, tmp_path, chat=EndDayChat())
    assert result["end_reason"] == "bankrupt"
    assert result["days_survived"] == 15
    assert result["totals"]["tool_calls"] == 15
    assert result["totals"]["prompt_tokens"] == 15 * 500
    assert result["providers"] == ["StubHost"]  # resolved upstream hosts

    run_dir = tmp_path / result["run_id"]
    transcript = [json.loads(l) for l in (run_dir / "transcript.jsonl").read_text().splitlines()]
    assert {m["day"] for m in transcript} == set(range(1, 16))
    roles = [m["role"] for m in transcript if m["day"] == 1]
    assert roles == ["system", "user", "assistant", "tool"]
    days = [json.loads(l) for l in (run_dir / "days.jsonl").read_text().splitlines()]
    assert all(d["providers"] == ["StubHost"] for d in days)


def test_replicate_and_temperature_provenance(tmp_path):
    """Replication protocol (2026-07-10 review): realization >= 2 gets its
    own run id so realizations coexist; the manifest records the requested
    temperature and the replicate number."""
    base = spec_for(model="stub-model")
    r2 = RunSpec(
        model=base.model, condition=base.condition,
        schedule_seed=base.schedule_seed, horizon=base.horizon,
        replicate=2, temperature=0.7,
    )
    assert base.run_id + "__r2" == r2.run_id

    result = execute_run(r2, tmp_path, chat=EndDayChat())
    manifest = json.loads((tmp_path / result["run_id"] / "manifest.json").read_text())
    assert manifest["replicate"] == 2
    assert manifest["temperature"] == 0.7
    # Realization 1 keeps the historical id and defaults.
    result1 = execute_run(base, tmp_path, chat=EndDayChat())
    manifest1 = json.loads((tmp_path / result1["run_id"] / "manifest.json").read_text())
    assert manifest1["replicate"] == 1 and manifest1["temperature"] is None


def test_rich_condition_uses_pack_and_stamps_hash(tmp_path):
    pack = make_pack()
    result = execute_run(spec_for(richness="rich"), tmp_path, pack=pack)
    run_dir = tmp_path / result["run_id"]

    days = [json.loads(line) for line in (run_dir / "days.jsonl").read_text().splitlines()]
    assert all(d["narration"] == CLEAN_NARRATION for d in days)
    manifest = json.loads((run_dir / "manifest.json").read_text())
    assert manifest["narration_pack_hash"] == pack.content_hash()
    assert (run_dir / "narration_pack.yml").exists()
    # Same schedule, same policy: rich vs static narration cannot move the score.
    assert result["score"] == 2830


def test_static_condition_uses_theme_lines(tmp_path):
    result = execute_run(spec_for(framing="neutral"), tmp_path)
    run_dir = tmp_path / result["run_id"]
    days = [json.loads(line) for line in (run_dir / "days.jsonl").read_text().splitlines()]
    neutral = load_theme("neutral")
    assert all(d["narration"] in neutral.static_events.values() for d in days)


# -------------------------------------------------------------------- guards


def test_rich_condition_requires_matching_pack(tmp_path):
    with pytest.raises(ValueError, match="requires a narration pack"):
        execute_run(spec_for(richness="rich"), tmp_path)
    wrong_pack = generate_pack(
        generate_schedule(7, 30), load_theme("fantasy"), lambda s, u: CLEAN_NARRATION, model="stub"
    )
    with pytest.raises(ValueError, match="does not match"):
        execute_run(spec_for(richness="rich"), tmp_path, pack=wrong_pack)


def test_llm_model_requires_chat_client(tmp_path):
    with pytest.raises(ValueError, match="needs a chat client"):
        execute_run(spec_for(model="some/model"), tmp_path)


def test_completed_run_is_never_reexecuted(tmp_path):
    spec = spec_for(model="stub-model")
    first = execute_run(spec, tmp_path, chat=EndDayChat())
    second = execute_run(spec, tmp_path, chat=ExplodingChat())
    assert second == first


def test_companion_theme_cells_are_valid_conditions():
    """The CLI failed on creed cells because Condition was pinned to the
    2x2; framings now follow the theme registry."""
    from tnt_bench.harness.conditions import Condition

    for framing in ("fantasy_creed_full", "fantasy_creed_lean", "fantasy_dark"):
        assert Condition(framing=framing, richness="static").cell_id == f"{framing}-static"
