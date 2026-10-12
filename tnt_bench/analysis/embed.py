"""Embeddings for trace metrics.

The default embedder is a deterministic hashed character-n-gram bag: no
dependencies, no network, stable across processes (md5, not `hash()`).
It captures lexical similarity — sufficient for recurrence and repetition
metrics. For semantic novelty in the paper, pass an API embedder with the
same signature.
"""

from __future__ import annotations

import hashlib
import math
from typing import Callable

# texts -> one vector per text
Embedder = Callable[[list[str]], list[list[float]]]


def ngram_embedder(n: int = 3, dim: int = 512) -> Embedder:
    def embed(texts: list[str]) -> list[list[float]]:
        vectors = []
        for text in texts:
            vec = [0.0] * dim
            cleaned = " ".join(text.lower().split())
            for i in range(max(0, len(cleaned) - n + 1)):
                gram = cleaned[i : i + n]
                digest = hashlib.md5(gram.encode()).digest()
                vec[int.from_bytes(digest[:4], "big") % dim] += 1.0
            norm = math.sqrt(sum(x * x for x in vec))
            if norm > 0:
                vec = [x / norm for x in vec]
            vectors.append(vec)
        return vectors

    return embed


def cosine(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(x * x for x in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)
