"""Experiment harness (spec §7): conditions, run execution, artifacts, matrix.

A run = (model, condition, schedule_seed, horizon). Every run writes a
self-describing directory; a run whose result.json exists is never
re-executed. The analysis layer consumes these artifacts only.
"""

from .conditions import Condition, ALL_CELLS
from .run import RunSpec, execute_run, load_result
from .matrix import expand_specs, run_matrix, ensure_pack, summarize
from ..exploit import EXPLOIT_CONDITIONS
from .discrepancy import (
    DiscrepancyGroupSpec,
    execute_discrepancy_group,
    expand_discrepancy_groups,
    run_discrepancy_matrix,
    validate_discrepancy_pack_source,
)

__all__ = [
    "Condition",
    "ALL_CELLS",
    "RunSpec",
    "execute_run",
    "load_result",
    "expand_specs",
    "run_matrix",
    "ensure_pack",
    "summarize",
    "EXPLOIT_CONDITIONS",
    "DiscrepancyGroupSpec",
    "execute_discrepancy_group",
    "expand_discrepancy_groups",
    "run_discrepancy_matrix",
    "validate_discrepancy_pack_source",
]
