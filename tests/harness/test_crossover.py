"""Frozen matrix checks for the frame x doctrine crossover."""

from collections import Counter

from tnt_bench.harness import Condition, expand_specs


MODELS = ("google/gemma-4-31b-it", "openai/gpt-5.6-luna")
SEEDS = tuple(range(27, 37))
REPLICATES = (1, 2)
THEMES = (
    "fantasy",
    "fantasy_crossover_full",
    "fantasy_crossover_lean",
    "neutral",
    "neutral_crossover_full",
    "neutral_crossover_lean",
)
CELLS = tuple(Condition(theme, "static") for theme in THEMES)


def crossover_specs():
    return expand_specs(
        models=MODELS,
        seeds=SEEDS,
        horizon=90,
        cells=CELLS,
        disclose_horizon=True,
        carrying_cost=0.0,
        block_seed="tnt-frame-doctrine-1",
        temperature=0.7,
        replicate=REPLICATES,
    )


def test_crossover_matrix_is_240_unique_runs():
    specs = crossover_specs()
    assert len(specs) == 240
    assert len({spec.run_id for spec in specs}) == 240
    assert Counter(spec.model for spec in specs) == {
        "google/gemma-4-31b-it": 120,
        "openai/gpt-5.6-luna": 120,
    }
    assert Counter(spec.condition.cell_id for spec in specs) == {
        f"{theme}-static": 40 for theme in THEMES
    }


def test_crossover_uses_complete_randomized_six_cell_blocks():
    specs = crossover_specs()
    expected_cells = {cell.cell_id for cell in CELLS}
    blocks = [specs[i:i + 6] for i in range(0, len(specs), 6)]
    assert len(blocks) == len(MODELS) * len(SEEDS) * len(REPLICATES)
    for block in blocks:
        assert len({(s.model, s.schedule_seed, s.replicate) for s in block}) == 1
        assert {s.condition.cell_id for s in block} == expected_cells
        assert all(s.condition.richness == "static" for s in block)
        assert all(s.horizon == 90 and s.disclose_horizon for s in block)
        assert all(s.carrying_cost == 0.0 and s.temperature == 0.7 for s in block)

    # The forced-lead rotation is balanced to within one block.
    lead_counts = Counter(block[0].condition.cell_id for block in blocks)
    assert max(lead_counts.values()) - min(lead_counts.values()) <= 1
