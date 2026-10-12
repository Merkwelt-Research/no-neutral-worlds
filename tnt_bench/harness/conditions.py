"""The condition matrix (spec §5, design doc).

The main run's 2x2 is FRAMINGS x RICHNESS; companion arms add themes
(fantasy_dark, the creed pair), so a framing is valid iff a theme of
that name exists on disk.
"""

from __future__ import annotations

from dataclasses import dataclass

from ..themes import available_themes

FRAMINGS = ("fantasy", "neutral")  # the main run's F+ / F-
RICHNESS = ("rich", "static")  # R+ / R-


@dataclass(frozen=True)
class Condition:
    framing: str  # theme name
    richness: str

    def __post_init__(self):
        if self.framing not in available_themes():
            raise ValueError(
                f"framing must name a theme, one of {available_themes()}"
            )
        if self.richness not in RICHNESS:
            raise ValueError(f"richness must be one of {RICHNESS}")

    @property
    def cell_id(self) -> str:
        return f"{self.framing}-{self.richness}"

    @property
    def short(self) -> str:
        f = "F+" if self.framing == "fantasy" else "F-"
        r = "R+" if self.richness == "rich" else "R-"
        return f + r


ALL_CELLS = tuple(
    Condition(framing=f, richness=r) for f in FRAMINGS for r in RICHNESS
)
