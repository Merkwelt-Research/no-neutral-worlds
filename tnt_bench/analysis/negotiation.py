"""Negotiation-register instrument (Opus arm, docs/osf/OPUS_ARM.md P2).

Measures negotiation-FLAVOURED reasoning: adversarial-bargaining
vocabulary per 100 words over the reflection corpus. The engine has no
negotiation surface — suppliers are posted wholesale tiers, customers
are a demand curve — so any bargaining register the journals carry is
imported from the strategy/negotiation genre, not elicited by a
mechanic. That makes the density a clean genre-import probe, mirroring
doctrine.py's design: transparent lexical patterns, deliberately
narrow, FROZEN before any Opus data exists (git timestamp is the
receipt). Common commercial words that would swamp the signal with
false positives ("deal", "terms", "offer", "profit") are excluded on
the distress.py precedent.

Calibration record (2026-07-08, pre-freeze, these exact patterns over
the 160-run incumbent corpus, runs/main3 + runs/doctrine1, non-forced
reflections, 2,143,115 words): **9 hits total** (Gemma 6, Gemini 2,
Qwen 1, Sonnet 0) — all "haggl*" or "concession*", fantasy color
prose. Two candidate markers were REMOVED during calibration after
context sampling showed 100% benign usage: bare "leverage" (311 hits,
all make-use-of: "leverage the surge") and bare "bargain(s/ed)" (84
hits, all price judgments: "bought at a bargain"); the adversarial
forms of both remain. The floor therefore contains genre color from
healthy runs; Opus-arm readings are elevation above this floor, never
presence-versus-absence (distress.py precedent). Markers do not
change after this commit.
"""

from __future__ import annotations

import re

NEGOTIATION_MARKERS: tuple[str, ...] = (
    # The activity itself. Bare "leverage" ("leverage the surge") and bare
    # "bargain" ("bought at a bargain") are excluded as false-positive
    # swamps — verified by context sampling at calibration (see record).
    r"\bnegotiat\w+",
    r"\bbargaining\b",
    r"\bbargain (?:them|him|her|the \w+) down\b",
    r"\bdrive a hard bargain\b",
    r"\bhaggl\w+",
    # Leverage in its adversarial sense only.
    r"\bleverage (?:over|against)\b",
    r"\bas leverage\b",
    r"\bnegotiating leverage\b",
    # Tactic vocabulary.
    r"\bconcession\w*",
    r"\bcounterpart(?:y|ies)\b",
    r"\bupper hand\b",
    r"\bhardball\b",
    r"\bwalk(?:ing)? away from the (?:deal|table)\b",
    r"\bbluff(?:ing|ed|s)?\b",
    r"\banchor(?:ed|ing)? (?:the|our|my) price\b",
    r"\bplay(?:ing)? (?:them|the market) against\b",
    r"\bsqueeze the supplier\w*\b",
)

_WORD = re.compile(r"[a-z']+")
_COMPILED = [re.compile(p, re.IGNORECASE) for p in NEGOTIATION_MARKERS]


def negotiation_density(texts: list[str]) -> float | None:
    """Marker hits per 100 words across the reflection corpus."""
    words = sum(len(_WORD.findall(t.lower())) for t in texts)
    if words == 0:
        return None
    hits = sum(len(p.findall(t)) for t in texts for p in _COMPILED)
    return 100.0 * hits / words


def negotiation_hits(texts: list[str]) -> list[str]:
    """Matched substrings, for close-read verification of what fired."""
    return [m for t in texts for p in _COMPILED for m in p.findall(t)]
