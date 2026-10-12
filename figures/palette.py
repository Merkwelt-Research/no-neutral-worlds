"""The house palette: four fixed temperament colors, two surfaces.

This file and the two .mplstyle files in figures/styles/ ARE the visual
identity (docs/FIGURES.md). Every data figure imports from here; nothing
downstream hardcodes a color.

Rules (from the signature-style note, docs/FIGURES.md):
- Model order is FIXED everywhere: Gemma, Qwen, Sonnet, Gemini. Colors
  follow the entity, never a rank or a cycle position.
- Sigils mark models in legends/titles so identity is never color-alone
  (mask = Gemma, quill = Qwen, ledger = Sonnet, storm = Gemini). The
  glyphs below are typographic stand-ins that render in DejaVu; final
  sigil art is an Inkscape job.
- Monospace is reserved for agent-written text (quoted journal lines);
  labels and captions stay in the sans ink.

Validation record (dataviz skill, scripts/validate_palette.js, 2026-07-08):
  dark  "#bc861c,#9678e4,#1ea482,#dc5844" --mode dark  --surface "#0a0a0f"
        -> ALL CHECKS PASS (band L 0.48-0.67, chroma, CVD worst adj 21.0
           protan with normal 97.7, contrast >= 3:1)
  print "#9a6c10,#6a4cbc,#0f9078,#b84030" --mode light --surface "#f4f1ea"
        -> ALL CHECKS PASS
Re-run the validator before changing any hex below.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

STYLES_DIR = Path(__file__).parent / "styles"

SURFACE = {"dark": "#0a0a0f", "print": "#f4f1ea"}

INK = {
    "dark": {"primary": "#e8e2d0", "secondary": "#b8aed4", "muted": "#6a6480"},
    "print": {"primary": "#1a1a1a", "secondary": "#4a4640", "muted": "#8a857a"},
}


@dataclass(frozen=True)
class Temperament:
    key: str        # short key used in scripts and metrics matching
    label: str      # display name
    sigil: str      # stand-in glyph (see module docstring)
    sigil_name: str
    dark: str       # hex on SURFACE['dark']
    print: str      # hex on SURFACE['print']

    def color(self, mode: str) -> str:
        return {"dark": self.dark, "print": self.print}[mode]

    @property
    def tag(self) -> str:
        return f"{self.sigil} {self.label}"


# Fixed order — never reordered, never cycled.
TEMPERAMENTS = (
    Temperament("gemma", "Gemma", "◐", "mask", "#bc861c", "#9a6c10"),
    Temperament("qwen", "Qwen", "✎", "quill", "#9678e4", "#6a4cbc"),
    Temperament("sonnet", "Sonnet", "▤", "ledger", "#1ea482", "#0f9078"),
    Temperament("gemini", "Gemini", "ϟ", "storm", "#dc5844", "#b84030"),
)

MODEL_ORDER = tuple(t.key for t in TEMPERAMENTS)
BY_KEY = {t.key: t for t in TEMPERAMENTS}


def temperament_of(model_id: str) -> Temperament | None:
    """Match a metrics.csv model string (e.g. 'google/gemma-4-31b-it')."""
    for t in TEMPERAMENTS:
        if t.key in model_id.lower():
            return t
    return None


def style_path(mode: str) -> Path:
    name = {"dark": "latentarchives.mplstyle", "print": "print.mplstyle"}[mode]
    return STYLES_DIR / name


def use(mode: str) -> None:
    """Apply a house style. Determinism: fixed svg hashsalt so re-running
    the pipeline on unchanged data produces byte-identical SVGs."""
    import matplotlib.pyplot as plt

    plt.style.use(str(style_path(mode)))
    plt.rcParams["svg.hashsalt"] = "token-and-trinket"
