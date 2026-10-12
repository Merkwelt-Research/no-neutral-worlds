"""Doctrine instrument: ordering-rationale registers (STAGE2_SPECIMENS §5a).

Frames import policy doctrines: the fantasy shopkeeper genre encodes
full-shelves-as-virtue, the corporate-operations genre encodes
lean-inventory-as-discipline (including mechanics that don't exist in
this engine, e.g. "holding costs"). This instrument measures which
doctrine a journal reasons from, per 100 words, mirroring register.py's
design: transparent lexical patterns, deliberately crude, frozen before
the doctrine×economy experiment's data exist.

Calibration record (2026-07-08, pre-freeze, Gemma main3 corpus, 80
cells, these exact patterns): shelf-pride fired 343× in fantasy vs 101×
in neutral; lean-ops 482× in neutral vs 192× in fantasy; phantom
carrying-cost mechanics ("holding cost", "storage cost", "tie up
capital") 60× in neutral vs 1× in fantasy — in an engine where holding
inventory is free. The
instrument separates the doctrines it was built to measure on the corpus
that motivated it; the doctrine×economy experiment tests whether
*injected* creeds move it. Markers do not change after this commit.
"""

from __future__ import annotations

import re

DOCTRINE_MARKERS: dict[str, tuple[str, ...]] = {
    # Full-shelves-as-virtue: stock as pride, duty, readiness.
    "shelf_pride": (
        r"well[- ]stocked",
        r"full(?:y stocked)? shel(?:f|ves)",
        r"shel(?:f|ves) (?:are|remain|stay|look(?:ing)?) (?:full|stocked|respectable|healthy)",
        r"keep the shel(?:f|ves)",
        r"shel(?:f|ves) (?:from going|going) bare",
        r"bare shel(?:f|ves)",
        r"stocked shelves",
        r"shelves groan",
        r"ready for (?:the|any|whatever)",
        r"be prepared\b",
        r"never (?:run|be) (?:dry|empty|out)",
    ),
    # Lean-inventory-as-discipline: stock as risk, capital drag, exposure.
    "lean_ops": (
        r"\bbuffer\b",
        r"avoid (?:a )?(?:stockout|overstock)",
        r"overstock(?:ing|ed)?\b",
        r"minimi[sz]e\b",
        r"lean (?:inventory|stock|operations?)",
        r"tie[sd]? up capital",
        r"capital (?:tied|locked) up",
        r"holding (?:cost|fee)s?",
        r"storage (?:cost|fee)s?",
        r"carrying costs?",
        r"dead (?:stock|weight)\b",
        r"excess inventory",
        r"inventory risk",
    ),
    # Phantom-mechanic subset (also counted in lean_ops): costs the engine
    # does not charge — confabulated world-physics. Track separately so
    # the carrying-cost economy (where these become REAL) can be compared.
    "phantom_carrying": (
        r"holding (?:cost|fee)s?",
        r"storage (?:cost|fee)s?",
        r"carrying costs?",
        r"tie[sd]? up capital",
    ),
}

_WORD = re.compile(r"[a-z']+")


def _compiled() -> dict[str, list[re.Pattern]]:
    return {
        cat: [re.compile(p, re.IGNORECASE) for p in patterns]
        for cat, patterns in DOCTRINE_MARKERS.items()
    }


_COMPILED = _compiled()


def doctrine_density(texts: list[str]) -> dict[str, float | None]:
    """Marker hits per 100 words per register, plus 'balance' =
    shelf_pride − lean_ops density (positive = full-shelf doctrine)."""
    words = sum(len(_WORD.findall(t.lower())) for t in texts)
    if words == 0:
        return dict.fromkeys((*DOCTRINE_MARKERS, "balance"))
    out = {}
    for cat, patterns in _COMPILED.items():
        hits = sum(len(p.findall(t)) for t in texts for p in patterns)
        out[cat] = 100.0 * hits / words
    out["balance"] = out["shelf_pride"] - out["lean_ops"]
    return out
