"""Agent day loop: dispatch, nudge policy, forced end, tool cap (spec §6)."""

import json

import pytest

from tnt_bench.agent import (
    FORCED_REFLECTION,
    ChatResponse,
    ChatToolCall,
    build_tools,
    dispatch_tool,
    run_agent_day,
)
from tnt_bench.engine import Engine, EngineConfig, Schedule
from tnt_bench.themes import ThemedView, load_theme

FANTASY = load_theme("fantasy")
NEUTRAL = load_theme("neutral")

VALID_REFLECTION = (
    "A steady first day: set prices across the shelf, placed a restock order, and "
    "watched the early trade. Tomorrow: check the delivery and mind the balance."
)


def make_view(theme=FANTASY):
    config = EngineConfig()
    return ThemedView(Engine(config, Schedule(seed=0, horizon=30, events=())), theme)


def call(name, args, id_="tc_1"):
    return ChatToolCall(id=id_, name=name, arguments=args)


class ScriptedChat:
    """Returns queued responses; repeats the last one if the queue empties."""

    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = 0

    def __call__(self, messages, tools):
        self.calls += 1
        if len(self.responses) > 1:
            return self.responses.pop(0)
        return self.responses[0]


# ----------------------------------------------------------------- dispatch


def test_dispatch_tools_end_to_end():
    view = make_view()
    view.dawn()
    assert dispatch_tool(view, "check_shop", {})["balance"] == 500
    assert dispatch_tool(view, "set_price", {"item_id": "health_potion", "price": 20})["ok"]
    assert dispatch_tool(view, "place_order", {"item_id": "antidote", "qty": 10})["ok"]
    ledger = dispatch_tool(view, "check_ledger", {"last_n": 5})
    assert ledger["transactions"][0]["type"] == "purchase"
    assert not dispatch_tool(view, "frobnicate", {})["ok"]
    assert not dispatch_tool(view, "check_ledger", {"last_n": -1})["ok"]


def test_end_day_rejects_bad_reflections_without_ending_day():
    view = make_view()
    view.dawn()
    result = dispatch_tool(view, "end_day", {"reflection": "too short"})
    assert not result["ok"] and "too short" in result["error"]
    result = dispatch_tool(view, "end_day", {"reflection": "x" * 3000})
    assert not result["ok"] and "too long" in result["error"]
    # Day is still open: a valid end_day now succeeds.
    result = dispatch_tool(view, "end_day", {"reflection": VALID_REFLECTION})
    assert result["ok"] and result["day_complete"] == 1


def test_tool_schemas_identical_across_themes_except_content():
    fantasy_tools = build_tools(make_view(FANTASY))
    neutral_tools = build_tools(make_view(NEUTRAL))
    assert [t["function"]["name"] for t in fantasy_tools] == [
        t["function"]["name"] for t in neutral_tools
    ]
    f_slugs = fantasy_tools[2]["function"]["parameters"]["properties"]["item_id"]["enum"]
    n_slugs = neutral_tools[2]["function"]["parameters"]["properties"]["item_id"]["enum"]
    assert f_slugs[0] == "health_potion" and n_slugs[0] == "sku_1"


# ----------------------------------------------------------------- day loop


def test_normal_day_flow():
    view = make_view()
    view.dawn()
    chat = ScriptedChat([
        ChatResponse(content="Checking the shop first.",
                     tool_calls=[call("check_shop", {})],
                     usage={"prompt_tokens": 100, "completion_tokens": 20}),
        ChatResponse(content="Pricing.",
                     tool_calls=[call("set_price", {"item_id": "health_potion", "price": 20}, "tc_2")],
                     usage={"prompt_tokens": 120, "completion_tokens": 15}),
        ChatResponse(tool_calls=[call("end_day", {"reflection": VALID_REFLECTION}, "tc_3")],
                     usage={"prompt_tokens": 140, "completion_tokens": 60}),
    ])
    result = run_agent_day(view, chat, briefing="=== DAY 1 ===")
    assert not result.forced and result.nudges == 0
    assert [tc["tool"] for tc in result.tool_calls] == ["check_shop", "set_price", "end_day"]
    assert result.reflection == VALID_REFLECTION
    assert result.usage == {"prompt_tokens": 360, "completion_tokens": 95}
    # Conversation shape: system, briefing, then assistant/tool alternation.
    assert result.messages[0]["role"] == "system"
    assert result.messages[1]["content"] == "=== DAY 1 ==="
    assert view.engine.state.reflections[0].text == VALID_REFLECTION


def test_nudges_then_forced_end():
    view = make_view()
    view.dawn()
    chat = ScriptedChat([ChatResponse(content="Hmm, let me think about this...")])
    result = run_agent_day(view, chat, briefing="=== DAY 1 ===")
    assert result.forced and result.nudges == 3
    assert result.reflection == FORCED_REFLECTION
    reflection = view.engine.state.reflections[0]
    assert reflection.forced and reflection.text == FORCED_REFLECTION
    # Two nudge messages sent (third strike breaks without nudging).
    nudge_messages = [m for m in result.messages if m["role"] == "user"][1:]
    assert len(nudge_messages) == 2


def test_nudge_streak_resets_on_tool_use():
    view = make_view()
    view.dawn()
    chat = ScriptedChat([
        ChatResponse(content="thinking..."),
        ChatResponse(content="still thinking..."),
        ChatResponse(tool_calls=[call("check_shop", {})]),
        ChatResponse(content="thinking again..."),
        ChatResponse(content="more thinking..."),
        ChatResponse(tool_calls=[call("end_day", {"reflection": VALID_REFLECTION}, "tc_9")]),
    ])
    result = run_agent_day(view, chat, briefing="b")
    assert not result.forced
    assert result.nudges == 4  # two streaks of two, neither reaching three


def test_tool_call_cap_forces_end():
    view = make_view()
    view.dawn()
    chat = ScriptedChat([ChatResponse(tool_calls=[call("check_shop", {})])])
    result = run_agent_day(view, chat, briefing="b")
    assert result.forced
    assert len(result.tool_calls) == 20
    assert view.engine.state.reflections[0].forced


def test_chat_retries_absorb_transient_failures(monkeypatch):
    monkeypatch.setattr("tnt_bench.agent.day_loop.time.sleep", lambda s: None)
    view = make_view()
    view.dawn()
    state = {"calls": 0}

    def flaky_chat(messages, tools):
        state["calls"] += 1
        if state["calls"] == 1:
            raise RuntimeError("provider returned no choices")
        return ChatResponse(
            tool_calls=[call("end_day", {"reflection": VALID_REFLECTION})]
        )

    result = run_agent_day(view, flaky_chat, briefing="b")
    assert not result.forced and result.reflection == VALID_REFLECTION


def test_persistent_chat_failure_raises(monkeypatch):
    monkeypatch.setattr("tnt_bench.agent.day_loop.time.sleep", lambda s: None)
    view = make_view()
    view.dawn()

    def dead_chat(messages, tools):
        raise RuntimeError("provider is gone")

    with pytest.raises(RuntimeError, match="provider is gone"):
        run_agent_day(view, dead_chat, briefing="b")


def test_malformed_arguments_get_error_result_not_crash():
    """Observed live: Gemma 4 emitting concatenated JSON objects in one
    arguments string. The call must be answered with an error tool result
    (which the model sees and can correct), never crash the run."""
    view = make_view()
    view.dawn()
    raw = '{"item_id": "health_potion", "price": 25}{"item_id": "antidote", "price": 25}'
    bad = ChatToolCall(
        id="tc_bad", name="set_price", arguments={},
        raw_arguments=raw, parse_error="Extra data at char 41",
    )
    chat = ScriptedChat([
        ChatResponse(tool_calls=[bad]),
        ChatResponse(tool_calls=[call("end_day", {"reflection": VALID_REFLECTION}, "tc_2")]),
    ])
    result = run_agent_day(view, chat, briefing="b")
    assert not result.forced and result.reflection == VALID_REFLECTION
    logged = result.tool_calls[0]
    assert logged["tool"] == "set_price"
    assert not logged["result"]["ok"]
    assert "invalid tool arguments" in logged["result"]["error"]
    # No price actually changed (item_1 starts unpriced).
    assert view.engine.state.inventory["item_1"].list_price is None
    # The raw string reaches the model via the error result...
    assert raw[:80] in logged["result"]["error"]
    # ...while the transcript echo stays valid JSON (strict providers 400
    # the whole request otherwise), wrapping the raw string in an envelope.
    assistant = next(m for m in result.messages if m.get("tool_calls"))
    echoed = json.loads(assistant["tool_calls"][0]["function"]["arguments"])
    assert echoed == {"unparseable_arguments": raw}


def test_adapter_param_fallbacks():
    from tnt_bench.agent.llm import _should_drop_strict_routing, _should_drop_temperature

    routing_404 = RuntimeError(
        "Error code: 404 - No endpoints found that can handle the requested parameters."
    )
    state = {"extra_body": {"provider": {"require_parameters": True}}, "temperature": 0.7}
    assert _should_drop_strict_routing(routing_404, state)
    # Once dropped, the same error is no longer ours to absorb.
    assert not _should_drop_strict_routing(routing_404, {"extra_body": None})

    class BadRequestError(Exception):
        pass

    temp_400 = BadRequestError("temperature is not supported by this model")
    assert _should_drop_temperature(temp_400, state)
    assert not _should_drop_temperature(temp_400, {"temperature": None})
    assert not _should_drop_temperature(RuntimeError("temperature"), state)


def test_deterministic_client_errors_fail_fast(monkeypatch):
    sleeps = []
    monkeypatch.setattr("tnt_bench.agent.day_loop.time.sleep", sleeps.append)
    view = make_view()
    view.dawn()

    class NotFoundError(Exception):
        pass

    def dead_chat(messages, tools):
        raise NotFoundError("Error code: 404 - no such model")

    with pytest.raises(NotFoundError):
        run_agent_day(view, dead_chat, briefing="b")
    assert sleeps == []  # no retry backoff on a deterministic 404


def test_adapter_argument_parsing_is_lenient():
    from tnt_bench.agent.llm import _tool_call

    ok = _tool_call("tc_1", "set_price", '{"item_id": "sku_1", "price": 20}')
    assert ok.parse_error is None and ok.arguments["price"] == 20

    concat = _tool_call(
        "tc_2", "set_price", '{"item_id": "sku_1", "price": 20}{"item_id": "sku_2"}'
    )
    assert concat.parse_error and concat.arguments == {}
    assert concat.raw_arguments.startswith('{"item_id"')

    not_object = _tool_call("tc_3", "set_price", '["sku_1", 20]')
    assert not_object.parse_error == "arguments must be a JSON object"

    empty = _tool_call("tc_4", "check_shop", None)
    assert empty.parse_error is None and empty.arguments == {}


def test_retry_after_rejected_reflection():
    view = make_view()
    view.dawn()
    chat = ScriptedChat([
        ChatResponse(tool_calls=[call("end_day", {"reflection": "too short"})]),
        ChatResponse(tool_calls=[call("end_day", {"reflection": VALID_REFLECTION}, "tc_2")]),
    ])
    result = run_agent_day(view, chat, briefing="b")
    assert not result.forced
    assert result.reflection == VALID_REFLECTION
    assert len(result.tool_calls) == 2  # the rejected attempt is logged too
