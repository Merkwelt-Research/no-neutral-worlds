"""Deterministic simulation engine.

Pure Python, no I/O, no LLM calls. Given the same (EngineConfig, Schedule)
and the same sequence of agent actions, two runs produce identical
trajectories. The engine speaks only abstract identifiers (item_1..item_6,
"funds"); every agent-facing string is mapped by the theme layer (M2).
"""

from .config import EngineConfig, Good, DEFAULT_GOODS
from .schedule import Schedule, ScheduledEvent, generate_schedule
from .state import (
    ActiveEffect,
    DiscrepancyRecord,
    EmailMessage,
    GameState,
    InventoryEntry,
    LedgerEntry,
    PendingOrder,
    game_state_from_dict,
)
from .engine import Engine, EnginePhaseError

__all__ = [
    "EngineConfig",
    "Good",
    "DEFAULT_GOODS",
    "Schedule",
    "ScheduledEvent",
    "generate_schedule",
    "GameState",
    "InventoryEntry",
    "PendingOrder",
    "ActiveEffect",
    "LedgerEntry",
    "EmailMessage",
    "DiscrepancyRecord",
    "game_state_from_dict",
    "Engine",
    "EnginePhaseError",
]
