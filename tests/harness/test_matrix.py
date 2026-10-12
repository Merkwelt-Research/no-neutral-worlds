"""Matrix expansion, pack caching, resumability, summaries (spec §7)."""

import json

from tnt_bench.harness import ALL_CELLS, expand_specs, run_matrix, summarize
from tnt_bench.harness.matrix import ensure_pack

CLEAN_NARRATION = (
    "Regional carriers report stable routing and unremarkable weather across the "
    "corridor; distribution centers continue processing at ordinary volume."
)


def stub_gm(system, user):
    return CLEAN_NARRATION


def test_expand_specs_covers_the_matrix():
    specs = expand_specs(models=["m1", "m2"], seeds=[1, 2, 3], horizon=30)
    assert len(specs) == 2 * 4 * 3
    assert len({s.run_id for s in specs}) == len(specs)


def test_baseline_matrix_all_cells(tmp_path):
    specs = expand_specs(models=["baseline:heuristic"], seeds=[42], horizon=30)
    results = run_matrix(specs, tmp_path, gm_llm=stub_gm, gm_model="stub")
    assert len(results) == 4
    # Identical engine + policy in every cell: narration cannot move a scripted score.
    assert {r["score"] for r in results} == {2830}
    assert {r["cell"] for r in results} == {c.cell_id for c in ALL_CELLS}


def test_packs_cached_once_per_theme_seed(tmp_path):
    calls = {"n": 0}

    def counting_gm(system, user):
        calls["n"] += 1
        return CLEAN_NARRATION

    specs = expand_specs(models=["baseline:heuristic"], seeds=[42], horizon=30)
    run_matrix(specs, tmp_path, gm_llm=counting_gm, gm_model="stub")
    # 2 themes x 30 days, one call each (no retries needed) — not 2 packs per rich run.
    assert calls["n"] == 60
    packs = sorted(p.name for p in (tmp_path / "packs").glob("*.yml"))
    assert packs == [
        "pack__fantasy__s42__h30.yml",
        "pack__neutral__s42__h30.yml",
    ]
    # Re-running the matrix touches neither the GM nor the runs.
    calls["n"] = 0
    run_matrix(specs, tmp_path, gm_llm=counting_gm, gm_model="stub")
    assert calls["n"] == 0


def test_ensure_pack_roundtrips_from_cache(tmp_path):
    pack_a = ensure_pack(tmp_path, "fantasy", 42, 30, stub_gm, "stub")
    pack_b = ensure_pack(tmp_path, "fantasy", 42, 30, None, "unused")  # cache hit: gm unused
    assert pack_a == pack_b


def test_ensure_pack_reuses_exact_frozen_artifact(tmp_path):
    source_root = tmp_path / "source"
    destination = tmp_path / "destination"
    original = ensure_pack(source_root, "fantasy", 42, 30, stub_gm, "opus")
    source_path = source_root / "packs" / "pack__fantasy__s42__h30.yml"

    reused = ensure_pack(
        destination, "fantasy", 42, 30, None, "unused",
        pack_source=source_root / "packs",
    )
    destination_path = destination / "packs" / source_path.name
    assert destination_path.read_bytes() == source_path.read_bytes()
    assert reused == original
    assert reused.model == "opus"
    assert reused.content_hash() == original.content_hash()


def test_pack_source_missing_match_never_falls_back_to_gm(tmp_path):
    import pytest as _pytest

    with _pytest.raises(FileNotFoundError, match="frozen narration pack"):
        ensure_pack(
            tmp_path / "out", "fantasy", 42, 30, stub_gm, "should-not-run",
            pack_source=tmp_path / "empty-source",
        )


def test_degraded_pack_is_not_cached(tmp_path, monkeypatch):
    """A pack that mostly fell back to static lines would silently weaken the
    rich condition — ensure_pack refuses to cache it."""
    monkeypatch.setattr("tnt_bench.narration.pack.time.sleep", lambda s: None)

    def leaky_gm(system, user):
        return "There were 3 carts at the gate this morning by the clerk's count."

    import pytest as _pytest
    with _pytest.raises(RuntimeError, match="degraded"):
        ensure_pack(tmp_path, "fantasy", 42, 30, leaky_gm, "stub")
    assert not list((tmp_path / "packs").glob("*.yml"))
    # A healthy GM afterwards generates and caches normally.
    pack = ensure_pack(tmp_path, "fantasy", 42, 30, stub_gm, "stub")
    assert pack.fallback_days() == []


def test_failure_isolated_per_run(tmp_path, monkeypatch):
    """A run that blows up records a failure; the rest of the queue proceeds.
    Re-running retries only the missing runs. (A dead GM now surfaces as a
    degraded-pack refusal rather than a raw provider exception.)"""
    monkeypatch.setattr("tnt_bench.narration.pack.time.sleep", lambda s: None)

    def broken_gm(system, user):
        raise ConnectionError("provider went away")

    specs = expand_specs(models=["baseline:heuristic"], seeds=[42], horizon=30)
    results = run_matrix(specs, tmp_path, gm_llm=broken_gm, gm_model="stub")
    failed = [r for r in results if r.get("status") == "failed"]
    completed = [r for r in results if r.get("status") != "failed"]
    assert len(failed) == 2 and len(completed) == 2  # rich cells fail, static succeed
    assert all("degraded" in r["error"] for r in failed)
    assert all(r["cell"].endswith("-rich") for r in failed)

    # Recovery: same command with a working GM finishes only what's missing.
    results = run_matrix(specs, tmp_path, gm_llm=stub_gm, gm_model="stub")
    assert all(r.get("status") != "failed" for r in results)
    assert {r["score"] for r in results} == {2830}


def test_parallel_matches_sequential(tmp_path):
    specs = expand_specs(models=["baseline:heuristic", "baseline:random"],
                         seeds=[42, 7], horizon=30)
    sequential = run_matrix(specs, tmp_path / "seq", gm_llm=stub_gm, gm_model="stub")
    parallel = run_matrix(specs, tmp_path / "par", gm_llm=stub_gm, gm_model="stub",
                          parallel=4)
    strip = lambda rs: [
        {k: v for k, v in r.items() if k != "finished_at"} for r in rs
    ]
    assert strip(parallel) == strip(sequential)  # same results, same spec order


def test_summarize_collects_and_ranks(tmp_path):
    specs = expand_specs(
        models=["baseline:heuristic", "baseline:random"], seeds=[42], horizon=30,
        cells=[c for c in ALL_CELLS if c.richness == "static"],
    )
    run_matrix(specs, tmp_path)
    summary = summarize(tmp_path)
    assert len(summary) == 4
    assert summary[0]["score"] >= summary[-1]["score"]
    assert summary[0]["model"] == "baseline:heuristic"


def test_interleave_is_deterministic_and_order_only():
    from tnt_bench.harness import Condition
    from tnt_bench.harness.matrix import expand_specs

    kwargs = dict(
        models=["m/a", "m/b"], seeds=[1, 2, 3], horizon=30,
        cells=[Condition("fantasy", "static"), Condition("neutral", "static")],
    )
    plain = expand_specs(**kwargs)
    shuffled = expand_specs(**kwargs, interleave_seed="tnt")
    again = expand_specs(**kwargs, interleave_seed="tnt")
    assert [s.run_id for s in shuffled] == [s.run_id for s in again]
    assert sorted(s.run_id for s in shuffled) == sorted(s.run_id for s in plain)
    assert [s.run_id for s in shuffled] != [s.run_id for s in plain]


def test_block_randomize_builds_randomized_complete_blocks():
    """The replication protocol (2026-07-10 review): one block per
    (seed, model) containing all cells exactly once, seed-major so both
    models' same-seed blocks are adjacent in time, frozen-seed order
    within a block, and the lead condition rotating across blocks."""
    models = ["m/a", "m/b"]
    seeds = [12, 13, 14, 15]
    kwargs = dict(models=models, seeds=seeds, horizon=90)

    blocked = expand_specs(**kwargs, block_seed="tnt-replication1")
    again = expand_specs(**kwargs, block_seed="tnt-replication1")
    plain = expand_specs(**kwargs)

    # Deterministic, and order-only: same runs, different execution order.
    assert [s.run_id for s in blocked] == [s.run_id for s in again]
    assert sorted(s.run_id for s in blocked) == sorted(s.run_id for s in plain)
    assert [s.run_id for s in blocked] != [s.run_id for s in plain]

    # Complete blocks: each consecutive chunk of 4 is one (seed, model)
    # pair covering all four cells, in seed-major order.
    n = len(ALL_CELLS)
    blocks = [blocked[i:i + n] for i in range(0, len(blocked), n)]
    expected_pairs = [(seed, model) for seed in seeds for model in models]
    for block, (seed, model) in zip(blocks, expected_pairs):
        assert {(s.schedule_seed, s.model) for s in block} == {(seed, model)}
        assert {s.condition.cell_id for s in block} == {c.cell_id for c in ALL_CELLS}

    # Lead rotation: block i starts with cell i % 4, so every condition
    # leads equally often across the collection.
    leads = [block[0].condition.cell_id for block in blocks]
    assert leads == [ALL_CELLS[i % n].cell_id for i in range(len(blocks))]

    # A different frozen seed reorders within blocks.
    other = expand_specs(**kwargs, block_seed="other")
    assert [s.run_id for s in other] != [s.run_id for s in blocked]


def test_block_randomize_excludes_interleave():
    import pytest as _pytest

    with _pytest.raises(ValueError, match="mutually exclusive"):
        expand_specs(models=["m"], seeds=[1], horizon=30,
                     interleave_seed="a", block_seed="b")


def test_expand_specs_stamps_temperature_and_replicate():
    specs = expand_specs(models=["m/a", "baseline:heuristic"], seeds=[1],
                         horizon=30, temperature=0.7, replicate=2)
    llm = [s for s in specs if s.model == "m/a"]
    baseline = [s for s in specs if s.model == "baseline:heuristic"]
    assert all(s.temperature == 0.7 for s in llm)
    assert all(s.temperature is None for s in baseline)  # baselines don't sample
    assert all(s.replicate == 2 for s in specs)
    assert all(s.run_id.endswith("__r2") for s in specs)


def test_block_randomize_interleaves_realizations():
    """The deep-cohort protocol: replicate=(1, 2) expands every cell twice,
    and under block randomization a seed's two realization blocks are
    adjacent in the queue — same wall-clock window, so the sampling-
    variance estimate is not confounded with provider drift."""
    specs = expand_specs(models=["m"], seeds=[12, 13], horizon=90,
                         block_seed="tnt-replication1", replicate=(1, 2))
    assert len(specs) == 2 * 2 * 4  # seeds x realizations x cells
    assert len({s.run_id for s in specs}) == len(specs)  # __r2 disambiguates

    n = len(ALL_CELLS)
    blocks = [specs[i:i + n] for i in range(0, len(specs), n)]
    assert [(b[0].schedule_seed, b[0].replicate) for b in blocks] == [
        (12, 1), (12, 2), (13, 1), (13, 2)
    ]
    for block in blocks:
        assert {s.condition.cell_id for s in block} == {c.cell_id for c in ALL_CELLS}
    # Realizations draw different within-block orders (frozen seed differs by rN)
    order = lambda b: [s.condition.cell_id for s in b]
    assert order(blocks[0]) != order(blocks[1]) or order(blocks[2]) != order(blocks[3])
