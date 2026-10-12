"""Lexical collapse measures (spec §8.2)."""

from __future__ import annotations

import gzip
import re

_WORD = re.compile(r"[a-z0-9]+")


def _words(text: str) -> list[str]:
    return _WORD.findall(text.lower())


def _ngrams(words: list[str], n: int = 3) -> list[tuple[str, ...]]:
    return [tuple(words[i : i + n]) for i in range(len(words) - n + 1)]


def compression_ratio(texts: list[str]) -> float | None:
    """gzip size / raw size of the concatenated corpus. Repetitive corpora
    compress harder (lower ratio)."""
    raw = "\n".join(texts).encode()
    if not raw:
        return None
    return len(gzip.compress(raw, compresslevel=9)) / len(raw)


def distinct_ngram_ratio(texts: list[str], n: int = 3) -> float | None:
    """Unique / total word n-grams over the whole corpus."""
    grams = _ngrams(_words(" ".join(texts)), n)
    if not grams:
        return None
    return len(set(grams)) / len(grams)


def consecutive_overlap(texts: list[str], n: int = 3) -> float | None:
    """Mean Jaccard overlap of word n-gram sets between consecutive texts —
    day-over-day self-repetition."""
    if len(texts) < 2:
        return None
    overlaps = []
    for a, b in zip(texts, texts[1:]):
        set_a, set_b = set(_ngrams(_words(a), n)), set(_ngrams(_words(b), n))
        union = set_a | set_b
        if union:
            overlaps.append(len(set_a & set_b) / len(union))
    return sum(overlaps) / len(overlaps) if overlaps else None
