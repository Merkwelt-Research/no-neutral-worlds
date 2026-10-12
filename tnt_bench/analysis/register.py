"""Register adoption and frame-break instruments (pre-registration v1.1).

The uptake metric (`narration_engagement`) measures *referential* uptake —
world content-words reappearing in the journal. But inhabitation has a
second, dissociable dimension: *register adoption* — writing like the
persona rather than about its world. Qwen's bard-Berrin cites the town
almost never yet writes "let the gold sing"; one number cannot carry both.

`register_density` is a transparent lexical instrument: poetic/affective/
archaic marker hits per 100 words. Deliberately crude, fully inspectable,
and pre-registered before the main-run data existed. `frame_break_days`
counts days whose entry steps outside the fiction to discuss the
game/score/harness — the container's leak detector.
"""

from __future__ import annotations

import re

# Poetic/affective/archaic register markers. Curated from probe journals
# BEFORE the main run; frozen thereafter. Mechanics vocabulary is
# deliberately absent — required shop-talk cannot score.
POETIC_MARKERS = frozenset("""
dawn dusk twilight morn eve whisper whispers sing sings song hum hums
heart soul spirit honor honour fortune fate fates gods blessed bless
quiet stillness silence breath breathe tide tides harvest gleam glow
shadow shadows mist song weary wander wanders dignity grace stride
bones blood ink candle bell bells door doors threshold hearth ember
embers coin coins purse ledger's rest sleeps dream dreams pride humble
storm winds winter spring summer autumn season's farewell dear old
""".split())

_WORD = re.compile(r"[a-z']+")

_FRAME_BREAK = re.compile(
    r"\bthe (game|run|benchmark|simulation|eval)\b|\bfinal score\b|"
    r"\bgame end(s|ed)?\b|\brest of (the )?game\b|\bforce[- ]end\w*\b|"
    r"\brun complete\b|\bas an ai\b|\blanguage model\b",
    re.IGNORECASE,
)


def register_density(texts: list[str]) -> float | None:
    """Mean poetic-marker hits per 100 words across texts."""
    densities = []
    for text in texts:
        words = _WORD.findall(text.lower())
        if len(words) < 20:
            continue
        hits = sum(1 for w in words if w in POETIC_MARKERS)
        densities.append(100.0 * hits / len(words))
    return sum(densities) / len(densities) if densities else None


def frame_break_days(day_records: list[dict]) -> int:
    """Days whose reflection steps outside the fiction (game/score/harness
    vocabulary). The container-leak detector for P6."""
    return sum(
        1
        for r in day_records
        if not r.get("forced") and _FRAME_BREAK.search(r.get("reflection", ""))
    )
