"""Generation-time leak guards (spec §5).

A narration may never carry mechanical information — the disclosure line is
the only information channel, printed identically in every cell. Guards run
when a pack is generated, so every published pack is clean by construction
and auditable by eye afterwards.
"""

from __future__ import annotations

import re

MIN_CHARS = 30
MAX_CHARS = 700

# Digits in any form leak magnitudes; number-words that commonly carry
# quantity ("twenty barrels of") are left to the audit pass — cheap guards
# catch the sharp leaks, the pack is human-reviewable for the rest.
_DIGIT = re.compile(r"\d")
_PRICE_WORDS = re.compile(
    r"\b(price[sd]?|discount|percent|multiplier|margin)\b", re.IGNORECASE
)
_ADVICE_WORDS = re.compile(
    r"\b(you should|consider (buying|selling|stocking)|be sure to|make sure (to|you)|"
    r"it would be wise|strategy|stock up)\b",
    re.IGNORECASE,
)


def guard_narration(text: str) -> list[str]:
    """Return a list of problems; empty means the text passes."""
    problems = []
    stripped = text.strip()
    if len(stripped) < MIN_CHARS:
        problems.append(f"too short (<{MIN_CHARS} chars)")
    if len(stripped) > MAX_CHARS:
        problems.append(f"too long (>{MAX_CHARS} chars)")
    if _DIGIT.search(stripped):
        problems.append("contains digits")
    if _PRICE_WORDS.search(stripped):
        problems.append("mentions prices/percentages")
    if _ADVICE_WORDS.search(stripped):
        problems.append("gives strategic advice")
    return problems
