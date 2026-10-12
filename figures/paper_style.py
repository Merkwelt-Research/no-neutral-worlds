"""Visual system for the No Neutral Worlds manuscript figures.

Colours follow the manuscript's paper and ink (paper/style.typ). The frame
pair is the one categorical encoding shared across every figure: fantasy is
warm, corporate is cool. Everything else is ink, shape and fill.

Validation record (dataviz skill, scripts/validate_palette.js, 2026-09-26):
  "#b0512a,#1b69a8" --mode light --surface "#fbfaf6" -> ALL CHECKS PASS
Re-run the validator before changing FANTASY or CORPORATE.
"""

from __future__ import annotations

from contextlib import contextmanager

import matplotlib.pyplot as plt

PAPER = "#fbfaf6"
FIELD = "#f0eee7"
INK = "#18212b"
SECONDARY = "#5d6670"
MUTED = "#9aa0a6"
RULE = "#c7c3b8"
RUST = "#9b4f32"
MOSS = "#49664f"

FANTASY = "#b0512a"
CORPORATE = "#1b69a8"
FANTASY_TINT = "#f4e6df"
CORPORATE_TINT = "#e2ebf3"

SANS = ["Segoe UI", "DejaVu Sans"]
SEMIBOLD = "Segoe UI Semibold"

RC = {
    "font.family": "sans-serif",
    "font.sans-serif": SANS,
    "font.size": 8.6,
    "axes.labelsize": 8.6,
    "axes.labelcolor": SECONDARY,
    "axes.edgecolor": RULE,
    "axes.linewidth": 0.7,
    "axes.facecolor": PAPER,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.spines.left": False,
    "axes.titlesize": 9,
    "axes.titleweight": "normal",
    "xtick.color": SECONDARY,
    "ytick.color": SECONDARY,
    "xtick.labelsize": 7.8,
    "ytick.labelsize": 7.8,
    "xtick.major.size": 0,
    "ytick.major.size": 0,
    "xtick.major.pad": 5,
    "grid.color": RULE,
    "grid.linewidth": 0.5,
    "grid.alpha": 0.7,
    "figure.facecolor": PAPER,
    "savefig.facecolor": PAPER,
    "savefig.dpi": 240,
    "svg.fonttype": "path",
    "legend.frameon": False,
}


@contextmanager
def context():
    with plt.rc_context(RC):
        yield


def sign_colour(value: float) -> str:
    """Colour a fantasy-minus-corporate contrast by the frame it favours."""
    return FANTASY if value > 0 else CORPORATE if value < 0 else MUTED
