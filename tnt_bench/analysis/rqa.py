"""Recurrence quantification over reflection embeddings (spec §8.2).

The recurrence matrix marks pairs of days whose reflections are similar
above a per-run adaptive threshold (75th percentile of off-diagonal
similarities, >= so exact-duplicate corpora saturate visibly). With an
adaptive threshold the recurrence rate is pinned near 0.25 by construction
except in degenerate (highly repetitive) runs — so DET, LAM, and trapping
time carry most of the signal, and RR flags degeneracy.

- RR  (recurrence rate): density of recurrent pairs
- DET (determinism): fraction of recurrent points on diagonal lines >= 2 —
  repeated *sequences* of days
- LAM (laminarity): fraction on vertical lines >= 2 — days the trajectory
  gets stuck near one state
- TT  (trapping time): mean vertical line length — how long it stays stuck
"""

from __future__ import annotations

from .embed import Embedder, cosine, ngram_embedder


def rqa_metrics(
    texts: list[str],
    embedder: Embedder | None = None,
    l_min: int = 2,
) -> dict[str, float | None]:
    n = len(texts)
    if n < 4:
        return {"rr": None, "det": None, "lam": None, "tt": None, "threshold": None}
    embedder = embedder or ngram_embedder()
    vectors = embedder(texts)

    sims = [[cosine(vectors[i], vectors[j]) for j in range(n)] for i in range(n)]
    off_diagonal = sorted(sims[i][j] for i in range(n) for j in range(n) if i != j)
    threshold = off_diagonal[int(0.75 * (len(off_diagonal) - 1))]

    recurrent = [[i != j and sims[i][j] >= threshold for j in range(n)] for i in range(n)]
    total = sum(row.count(True) for row in recurrent)
    if total == 0:
        return {"rr": 0.0, "det": 0.0, "lam": 0.0, "tt": None, "threshold": threshold}

    rr = total / (n * (n - 1))

    # Diagonal lines (excluding the main diagonal).
    det_points = 0
    for offset in range(-(n - 1), n):
        if offset == 0:
            continue
        line = [
            recurrent[i][i + offset]
            for i in range(max(0, -offset), min(n, n - offset))
        ]
        det_points += _points_in_runs(line, l_min)

    # Vertical lines.
    lam_points = 0
    lengths: list[int] = []
    for j in range(n):
        column = [recurrent[i][j] for i in range(n)]
        lam_points += _points_in_runs(column, l_min)
        lengths.extend(_run_lengths(column, l_min))

    return {
        "rr": rr,
        "det": det_points / total,
        "lam": lam_points / total,
        "tt": sum(lengths) / len(lengths) if lengths else None,
        "threshold": threshold,
    }


def _run_lengths(line: list[bool], l_min: int) -> list[int]:
    lengths, current = [], 0
    for value in line + [False]:
        if value:
            current += 1
        else:
            if current >= l_min:
                lengths.append(current)
            current = 0
    return lengths


def _points_in_runs(line: list[bool], l_min: int) -> int:
    return sum(_run_lengths(line, l_min))
