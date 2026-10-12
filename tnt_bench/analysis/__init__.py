"""Analysis pipeline (spec §8): trace-health and behavioral metrics.

Consumes run artifacts only — never touches the engine. Stdlib-only; the
embedder is pluggable (default: deterministic hashed character-n-gram
vectors, adequate for lexical recurrence; swap in API embeddings for the
paper's semantic variants).
"""

from .embed import Embedder, ngram_embedder, cosine
from .novelty import novelty_series, slope
from .rqa import rqa_metrics
from .lexical import compression_ratio, distinct_ngram_ratio, consecutive_overlap
from .behavior import action_entropy, behavior_metrics
from .register import register_density, frame_break_days
from .distress import distress_density, distress_days, distress_hits
from .doctrine import doctrine_density
from .negotiation import negotiation_density, negotiation_hits
from .runs import RunMetrics, analyze_run, collect, to_csv, cell_summary
from .exploit import (
    ExploitRecord,
    collect_exploit,
    exploit_cell_summary,
    exploit_to_csv,
)
from .discrepancy import (
    collect_discrepancy,
    discrepancy_channel_summary,
    discrepancy_to_csv,
)

__all__ = [
    "Embedder",
    "ngram_embedder",
    "cosine",
    "novelty_series",
    "slope",
    "rqa_metrics",
    "compression_ratio",
    "distinct_ngram_ratio",
    "consecutive_overlap",
    "action_entropy",
    "behavior_metrics",
    "register_density",
    "frame_break_days",
    "distress_density",
    "distress_days",
    "distress_hits",
    "doctrine_density",
    "negotiation_density",
    "negotiation_hits",
    "RunMetrics",
    "analyze_run",
    "collect",
    "to_csv",
    "cell_summary",
    "ExploitRecord",
    "collect_exploit",
    "exploit_cell_summary",
    "exploit_to_csv",
    "collect_discrepancy",
    "discrepancy_channel_summary",
    "discrepancy_to_csv",
]
