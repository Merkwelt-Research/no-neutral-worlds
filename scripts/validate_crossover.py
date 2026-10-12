"""API-free pre-launch validation for docs/osf/FRAME_DOCTRINE_CROSSOVER.md."""

from __future__ import annotations

import hashlib
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from tnt_bench.harness import Condition, expand_specs
from tnt_bench.themes import load_theme


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


def main() -> None:
    specs = expand_specs(
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
    assert len(specs) == len({spec.run_id for spec in specs}) == 240

    expected_cells = {cell.cell_id for cell in CELLS}
    blocks = [specs[i:i + 6] for i in range(0, len(specs), 6)]
    assert len(blocks) == 40
    for block in blocks:
        assert len({(s.model, s.schedule_seed, s.replicate) for s in block}) == 1
        assert {s.condition.cell_id for s in block} == expected_cells

    print("frame x doctrine crossover: VALID")
    print(f"runs: {len(specs)} ({len(blocks)} randomized complete blocks x 6 cells)")
    print(f"model counts: {dict(Counter(s.model for s in specs))}")
    print(f"cell counts: {dict(Counter(s.condition.cell_id for s in specs))}")
    print("rendered prompt SHA-256 (horizon 90, disclosed):")
    for theme_name in THEMES:
        theme = load_theme(theme_name)
        prompt = theme.render_system_prompt(90, disclosed=True)
        digest = hashlib.sha256(prompt.encode("utf-8")).hexdigest()
        assert not theme.discloses_storage
        assert "Storage is free" not in prompt
        print(f"  {theme_name:<25} {digest}")


if __name__ == "__main__":
    main()
