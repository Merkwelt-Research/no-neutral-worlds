"""Agent layer (spec §6): tool definitions, the multi-turn day loop, and
scripted baseline policies.

The LLM interface is a plain callable (messages, tools) -> ChatResponse so
the loop is testable without a provider; the OpenAI-compatible adapter
lives in agent.llm and is imported lazily.
"""

from .tools import build_tools, dispatch_tool, MIN_REFLECTION_CHARS, MAX_REFLECTION_CHARS
from .day_loop import (
    ChatResponse,
    ChatToolCall,
    DayResult,
    run_agent_day,
    MAX_TOOL_CALLS_PER_DAY,
    MAX_CONSECUTIVE_NUDGES,
    FORCED_REFLECTION,
)
from .baselines import heuristic_policy, random_policy, oracle_policy

__all__ = [
    "build_tools",
    "dispatch_tool",
    "MIN_REFLECTION_CHARS",
    "MAX_REFLECTION_CHARS",
    "ChatResponse",
    "ChatToolCall",
    "DayResult",
    "run_agent_day",
    "MAX_TOOL_CALLS_PER_DAY",
    "MAX_CONSECUTIVE_NUDGES",
    "FORCED_REFLECTION",
    "heuristic_policy",
    "random_policy",
    "oracle_policy",
]
