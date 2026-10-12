"""Novelty decay (spec §8.2).

novelty_t = 1 - max cosine(r_t, r_{<t}): how far today's reflection sits
from everything already written. A healthy trajectory keeps finding new
things to say; a collapsing one converges on its own prior text.
"""

from __future__ import annotations

from .embed import Embedder, cosine, ngram_embedder


def novelty_series(texts: list[str], embedder: Embedder | None = None) -> list[float]:
    """Novelty per text vs all its predecessors. First entry is 1.0 by
    convention (nothing to repeat yet)."""
    if not texts:
        return []
    embedder = embedder or ngram_embedder()
    vectors = embedder(texts)
    series = [1.0]
    for t in range(1, len(vectors)):
        max_sim = max(cosine(vectors[t], vectors[s]) for s in range(t))
        series.append(1.0 - max_sim)
    return series


def slope(values: list[float]) -> float | None:
    """Ordinary least-squares slope over index 1..n. None below 3 points."""
    n = len(values)
    if n < 3:
        return None
    xs = range(1, n + 1)
    mean_x = (n + 1) / 2
    mean_y = sum(values) / n
    ss_xy = sum((x - mean_x) * (y - mean_y) for x, y in zip(xs, values))
    ss_xx = sum((x - mean_x) ** 2 for x in xs)
    return ss_xy / ss_xx


def time_to_floor(series: list[float], floor: float = 0.1) -> int | None:
    """First (1-indexed) position where novelty drops below `floor`; None if
    it never does."""
    for i, value in enumerate(series, start=1):
        if value < floor:
            return i
    return None
