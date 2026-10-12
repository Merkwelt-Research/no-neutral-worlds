"""Frontier (Opus 5.5, direct Anthropic API) transport: offline tests only.

A fake client stands in for the SDK; no network access or API key is used.
"""
import json
from pathlib import Path

import pytest

from scripts import frontier_anthropic as fa
from scripts import run_frontier_transport as fr
from tnt_bench.agent.day_loop import ChatResponse, ChatToolCall, run_agent_day
from tnt_bench.engine import Engine, EngineConfig, generate_schedule
from tnt_bench.harness.conditions import Condition
from tnt_bench.harness.run import RunSpec, execute_run
from tnt_bench.themes import ThemedView, load_theme

ENTRY = ("The daily record is complete. I have checked the information available and will keep "
         "the stock and balance in mind when choosing the next actions.")


def message(blocks, stop="tool_use", usage=None):
    return {"id": "msg", "type": "message", "role": "assistant", "model": fa.MODEL, "content": blocks,
            "stop_reason": stop, "usage": usage or {"input_tokens": 100, "cache_creation_input_tokens": 50,
                                                     "cache_read_input_tokens": 1000, "output_tokens": 40}}


THINK = {"type": "thinking", "thinking": "summary", "signature": "sig-1"}


class FakeClient:
    """Records request bodies and returns scripted responses."""

    def __init__(self, responses):
        self.responses, self.bodies = list(responses), []
        self.beta = self
        self.messages = self

    def create(self, **body):
        self.bodies.append(json.loads(json.dumps(body)))
        return self.responses.pop(0)


def test_matrix_swaps_only_the_model_and_keeps_the_registered_cells():
    jobs = fr.frontier_jobs()
    exploit = [j for j in jobs if j["arm"] == "exploit"]
    groups = [j for j in jobs if j["arm"] == "discrepancy"]
    assert len(exploit) == 80 and len(groups) == 20
    assert {j["spec"]["model"] for j in jobs} == {fa.MODEL}
    assert {j["spec"]["temperature"] for j in jobs} == {None}
    assert {j["spec"]["schedule_seed"] for j in jobs} == set(range(13, 23))
    assert {j["spec"]["exploit_condition"] for j in exploit} == {"ambiguous", "ambiguous_wit", "explicit", "explicit_wit"}
    assert all(j["observe_days"] == 20 for j in exploit)
    assert {j["spec"]["replicate"] for j in groups} == {1}
    assert {j["spec"]["normative_climate"] for j in groups} == {"baseline"}
    assert all(len(j["branches"]) == 4 and all(fa.MODEL in b for b in j["branches"]) for j in groups)
    assert len({j["job_id"] for j in jobs}) == len(jobs)


def test_translation_merges_tool_results_and_nudges_after_verbatim_assistant_blocks():
    raw_blocks = [THINK, {"type": "tool_use", "id": "t1", "name": "check_shop", "input": {}},
                  {"type": "tool_use", "id": "t2", "name": "view_ledger", "input": {}}]
    messages = [
        {"role": "system", "content": "SYSTEM"},
        {"role": "user", "content": "=== DAY 1 ==="},
        {"role": "assistant", "content": None, "anthropic_content": raw_blocks, "tool_calls": []},
        {"role": "tool", "tool_call_id": "t1", "name": "check_shop", "content": "{\"ok\": true}"},
        {"role": "tool", "tool_call_id": "t2", "name": "view_ledger", "content": "{\"ok\": true}"},
        {"role": "user", "content": "There is no time left for further actions today."},
    ]
    system, out = fa.to_request(messages)
    assert system == [{"type": "text", "text": "SYSTEM", "cache_control": {"type": "ephemeral"}}]
    assert [m["role"] for m in out] == ["user", "assistant", "user"]
    assert out[1]["content"][0] == THINK  # thinking replayed unchanged, signature included
    assert [b["type"] for b in out[2]["content"]] == ["tool_result", "tool_result", "text"]
    assert out[2]["content"][0]["tool_use_id"] == "t1"


def test_assistant_turn_without_raw_blocks_is_refused():
    with pytest.raises(fa.ReviewStop):
        fa.to_request([{"role": "system", "content": "S"}, {"role": "user", "content": "U"},
                       {"role": "assistant", "content": "hi"}])


def test_refusal_and_truncation_stop_for_review():
    with pytest.raises(fa.ReviewStop):
        fa.parse_response({**message([]), "stop_reason": "refusal", "stop_details": {"category": "cyber"}})
    with pytest.raises(fa.ReviewStop):
        fa.parse_response({**message([]), "stop_reason": "max_tokens"})


def test_usage_and_cost_count_cached_and_uncached_input():
    parsed = fa.parse_response(message([{"type": "text", "text": "ok"}], stop="end_turn"))
    assert parsed.usage == {"prompt_tokens": 1150, "completion_tokens": 40}
    expected = (100 * 4 + 50 * 5 + 1000 * 0.2 + 40 * 20) / 1e6
    assert fa.response_cost(message([])) == pytest.approx(expected)


def test_request_uses_low_effort_adaptive_thinking_auto_tools_caching_and_no_temperature():
    body = fa.request_body(fa.MODEL, [{"role": "system", "content": "S"}, {"role": "user", "content": "U"}],
                           [{"type": "function", "function": {"name": "end_day", "description": "d",
                                                              "parameters": {"type": "object", "properties": {}}}}],
                           effort="low", max_tokens=16384)
    assert body["output_config"] == {"effort": "low"}
    assert body["thinking"]["type"] == "adaptive"
    assert body["thinking"]["block_binding"] == {"prefix_mismatch_behavior": "drop_block"}
    assert body["tool_choice"] == {"type": "auto"}
    assert body["cache_control"] == {"type": "ephemeral"}
    assert "temperature" not in body
    assert body["tools"][0]["input_schema"] == {"type": "object", "properties": {}}


def test_one_agent_day_round_trips_through_the_fake_api():
    fake = FakeClient([
        message([THINK, {"type": "tool_use", "id": "t1", "name": "check_shop", "input": {}}]),
        message([{"type": "tool_use", "id": "t2", "name": "end_day", "input": {"reflection": ENTRY}}]),
    ])
    chat = fa.anthropic_chat_client(None, client=fake)
    view = ThemedView(Engine(EngineConfig(horizon=90), generate_schedule(900001, 90)), load_theme("neutral"),
                      action_protocol="disclosed_journal_v1")
    dawn = view.dawn()
    result = run_agent_day(view, chat, view.briefing(dawn, view.static_narration(dawn)))
    assert not result.forced and result.reflection == ENTRY
    second = fake.bodies[1]["messages"]
    assert second[1]["content"][0] == THINK
    assert second[2]["content"][0]["type"] == "tool_result" and second[2]["content"][0]["tool_use_id"] == "t1"


def test_observation_window_stops_a_run_after_the_stated_days(tmp_path):
    def chat(messages, tools):
        return ChatResponse(tool_calls=[ChatToolCall(id="e", name="end_day", arguments={"reflection": ENTRY})])
    spec = RunSpec("test-model", Condition("neutral", "static"), 900001, horizon=90,
                   action_protocol="disclosed_journal_v1")
    with fr.observation_window(3):
        execute_run(spec, tmp_path, chat)
    days = (tmp_path / spec.run_id / "days.jsonl").read_text(encoding="utf-8").splitlines()
    assert len(days) == 3
    from tnt_bench.harness import run as run_module
    assert run_module.ThemedView is ThemedView  # restored after the window


def test_replay_returns_saved_decisions_without_a_live_call():
    raw = message([{"type": "tool_use", "id": "t2", "name": "end_day", "input": {"reflection": ENTRY}}])
    request = {"messages": [{"role": "system", "content": "S"}], "tools": []}
    def live(messages, tools):
        raise AssertionError("no live call expected")
    chat = fr.ReplayingChat([(request, raw)], None, live)
    out = chat(request["messages"], request["tools"])
    assert out.tool_calls[0].name == "end_day" and chat.index == 1
    with pytest.raises(fr.Stop):
        fr.ReplayingChat([(request, raw)], None, live)([{"role": "system", "content": "changed"}], [])


def test_spending_cap_refuses_a_request_that_would_exceed_it(tmp_path):
    guard = fr.SpendGuard(tmp_path, cap=1.0)
    guard.reserve("a", 0.6)
    with pytest.raises(fr.Stop):
        guard.reserve("b", 0.5)
    guard.settle("a", 0.2)
    guard.reserve("b", 0.5)


def test_valid_response_requires_the_registered_model_and_a_normal_stop():
    assert fr.valid_response(message([]))
    assert not fr.valid_response({**message([]), "model": "claude-opus-5"})
    assert not fr.valid_response({**message([]), "stop_reason": "max_tokens"})
