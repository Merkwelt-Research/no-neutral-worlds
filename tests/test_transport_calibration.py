"""Spending, audit and simulation checks without network requests."""
import json

import pytest

from scripts import calibrate_transport as calibration
from tnt_bench.agent.day_loop import ChatResponse, ChatToolCall
from tnt_bench.harness.conditions import Condition
from tnt_bench.harness.run import RunSpec


def test_low_plan_freezes_supported_settings_and_reduces_only_full_queue(tmp_path, monkeypatch):
    def public(url):
        if url.endswith("/models"):
            return {"data": [{"id": model, "reasoning": {
                "mandatory": False, "supported_efforts": [] if "k2.6" in model else ["high", "low"]}}
                for model in calibration.MODEL_ENDPOINTS]}
        model = url.split("/models/")[1].removesuffix("/endpoints")
        return {"data": {"endpoints": [{
            "tag": calibration.MODEL_ENDPOINTS[model], "status": 0,
            "supported_parameters": ["tools", "tool_choice", "max_tokens", "reasoning"],
            "provider_name": "Test", "pricing": {"prompt": "0.000001", "completion": "0.000002"},
            "max_completion_tokens": 32768}]}}
    monkeypatch.setattr(calibration, "get_public", public)
    calibration.prepare(tmp_path)
    plan = calibration.validate(tmp_path)
    assert len(calibration.stage_queue(plan, "smoke")) == 18
    assert len(calibration.stage_queue(plan, "full")) == 6
    assert {entry["case"] for entry in plan["full_queue"]} == {"ordinary"}
    for profile in plan["profiles"]:
        expected = {"enabled": False} if "k2.6" in profile["model"] else {"effort": "low"}
        assert profile["reasoning"] == expected
        assert profile["provider"]["allow_fallbacks"] is False


@pytest.mark.parametrize("model,metadata", [
    ("deepseek/deepseek-v4.1-flash", {"supported_efforts": ["high"]}),
    ("moonshotai/kimi-k2.6", {"mandatory": True}),
    ("moonshotai/kimi-k2.6", {}),
])
def test_unsupported_reasoning_refused(model, metadata):
    with pytest.raises(calibration.CalibrationStop):
        calibration.calibration_reasoning(model, metadata)


def test_previous_runner_guard_preserves_live_and_stale_locks(tmp_path, monkeypatch):
    monkeypatch.setattr(calibration, "ROOT", tmp_path)
    previous = tmp_path / "previous"
    previous.mkdir()
    lock = previous / "running.lock"
    lock.write_text("12345")
    plan = {"exclusive_with_batches": ["previous"]}
    monkeypatch.setattr(calibration, "process_alive", lambda pid: True)
    with pytest.raises(calibration.CalibrationStop, match="still active"):
        calibration.check_previous_runners(plan)
    monkeypatch.setattr(calibration, "process_alive", lambda pid: False)
    calibration.check_previous_runners(plan)
    assert lock.read_text() == "12345"


def test_process_check_recognizes_current_process():
    assert calibration.process_alive(calibration.os.getpid())


def test_budget_reservations_survive_restart_and_unknown_cost(tmp_path):
    budget = calibration.Budget(tmp_path, 1)
    request = budget.reserve(.6, "test")
    assert not budget.settle(request, None)
    recovered = calibration.Budget(tmp_path, 1)
    with pytest.raises(calibration.CalibrationStop):
        recovered.reserve(.5, "would exceed budget")
    recovered.settle(request, .1)
    assert calibration.Budget(tmp_path, 1).spent == .1
    recovered.reserve(.5, "now affordable")
    assert calibration.Budget(tmp_path, 1).spent == .6


def test_no_optional_ceiling_still_records_cost(tmp_path):
    budget = calibration.Budget(tmp_path, None)
    request = budget.reserve(.6, "fixed-count probe")
    budget.settle(request, .1)
    assert calibration.Budget(tmp_path, None).spent == .1


@pytest.mark.parametrize("kind,passes", [("valid_cap", True), ("error_cap", False), ("no_action", False)])
def test_forced_day_distinguishes_task_budget_from_compatibility(tmp_path, kind, passes):
    calls = [{"tool": "place_order", "result": {"ok": True}} for _ in range(20)]
    if kind == "error_cap":
        calls[-1]["result"] = {"ok": False, "error": "invalid tool arguments"}
    if kind == "no_action":
        calls = []
    calibration.append(tmp_path / "days.jsonl", {"day": 1, "forced": True,
                       "nudges": 0 if calls else 3, "tool_calls": calls})
    checks = calibration.gate(tmp_path, 1)
    assert checks["pass"] is passes
    assert checks["forced"] == 1
    assert checks["forced_budget_days"] == int(kind == "valid_cap")


def test_review_preserves_original_gate_and_detects_trace_changes(tmp_path):
    calibration.write(tmp_path / "complete.json", {"technical_gate": {"pass": False}})
    calibration.append(tmp_path / "days.jsonl", {"day": 1})
    assert not calibration.completed_pass(tmp_path)
    calibration.write(tmp_path / "gate_review.json", {
        "checks": {"pass": True}, "days_sha256": calibration.digest(tmp_path / "days.jsonl")})
    assert calibration.completed_pass(tmp_path)
    assert not calibration.read(tmp_path / "complete.json")["technical_gate"]["pass"]
    calibration.append(tmp_path / "days.jsonl", {"day": 2})
    with pytest.raises(calibration.CalibrationStop):
        calibration.completed_pass(tmp_path)


@pytest.mark.parametrize("limit", [0, -1, float("nan"), float("inf")])
def test_invalid_budget_refused(tmp_path, limit):
    with pytest.raises(ValueError):
        calibration.Budget(tmp_path, limit)


@pytest.mark.parametrize("fault", ["truncated", "provider", "cost"])
def test_bad_response_is_logged_and_stops(tmp_path, monkeypatch, fault):
    def fake_factory(*args, **kwargs):
        def chat(messages, tools):
            kwargs["before_request"]({"messages": messages, "tools": tools})
            kwargs["on_response"]({"provider": "Other" if fault == "provider" else "Chosen",
                "usage": {"cost": None if fault == "cost" else .01},
                "choices": [{"finish_reason": "length" if fault == "truncated" else "stop"}]})
        return chat
    monkeypatch.setattr(calibration, "openai_chat_client", fake_factory)
    profile = {"model": "test", "temperature": .7, "provider": {}, "reasoning": {},
               "max_tokens": 16384, "expected_provider": "Chosen",
               "ceiling_rates": {"prompt": 1e-6, "completion": 1e-6}}
    path = tmp_path / "api_calls.jsonl"
    chat = calibration.measured_chat(profile, path, calibration.Budget(tmp_path, 1), "fake")
    with pytest.raises(calibration.CalibrationStop):
        chat([], [])
    assert [r["kind"] for r in calibration.rows(path)] == ["request", "response"]
    assert calibration.Budget(tmp_path, 1).spent > 0


def test_smoke_keeps_ninety_day_prompt_and_stops_after_three(tmp_path):
    prompts = []
    def chat(messages, tools):
        prompts.append(messages[0]["content"])
        return ChatResponse(tool_calls=[ChatToolCall("end", "end_day", {
            "reflection": "This is a technical calibration journal entry. I have reviewed the shop and will continue checking its inventory and cash balance tomorrow."
        })])
    spec = RunSpec("test", Condition("neutral", "static"), 900001, horizon=90)
    calibration.smoke(spec, tmp_path, chat, None, 3)
    assert len(prompts) == 3
    assert all("90" in p for p in prompts)
    assert calibration.read(tmp_path / "result.json")["days_survived"] == 3
    assert calibration.gate(tmp_path, 3)["pass"]


@pytest.mark.parametrize("failures", [1, 3])
def test_transport_retries_are_bounded_and_each_attempt_is_accounted(tmp_path, monkeypatch, failures):
    attempts = []
    APIConnectionError = type("APIConnectionError", (Exception,), {})
    def fake_factory(*args, **kwargs):
        def chat(messages, tools):
            attempts.append(1)
            kwargs["before_request"]({"messages": messages, "tools": tools})
            if len(attempts) <= failures:
                raise APIConnectionError("test connection failure")
            kwargs["on_response"]({"provider": "Chosen", "usage": {"cost": .01},
                                   "choices": [{"finish_reason": "stop"}]})
            return ChatResponse()
        return chat
    monkeypatch.setattr(calibration, "openai_chat_client", fake_factory)
    monkeypatch.setattr(calibration.time, "sleep", lambda seconds: None)
    profile = {"model": "test", "temperature": .7, "provider": {}, "reasoning": {},
               "max_tokens": 16384, "expected_provider": "Chosen",
               "ceiling_rates": {"prompt": 1e-6, "completion": 1e-6}}
    chat = calibration.measured_chat(profile, tmp_path/'api_calls.jsonl',
                                    calibration.Budget(tmp_path, None), "fake", initial_day=23)
    if failures == 3:
        with pytest.raises(calibration.CalibrationStop):
            chat([], [])
    else:
        chat([], [])
    assert len(attempts) == min(failures + 1, 3)
    events = calibration.rows(tmp_path/'api_calls.jsonl')
    assert all(e["day"] == 24 for e in events if e["kind"] == "request")
    reservations = [r for r in calibration.rows(tmp_path/'budget.jsonl') if r["kind"] == "reserve"]
    assert len(reservations) == len(attempts)
    assert calibration.Budget(tmp_path, None).spent > .01


def test_replay_checks_context_before_any_live_request():
    request = {"messages": [{"role": "user", "content": "original"}], "tools": []}
    event = {"request": request, "day": 24}
    response = {"choices": [{"message": {"content": "saved", "reasoning_details": [{"data": "opaque"}]}}],
                "usage": {"prompt_tokens": 3, "completion_tokens": 4}, "provider": "Chosen"}
    live_calls = []
    def live(messages, tools):
        live_calls.append(1)
        return ChatResponse(content="live")
    replay = calibration.ReplayChat([(event, response)], event, live)
    saved = replay(request["messages"], [])
    assert saved.content == "saved"
    assert saved.provider_fields["reasoning_details"] == [{"data": "opaque"}]
    assert live_calls == []
    with pytest.raises(calibration.CalibrationStop):
        replay([{"role": "user", "content": "changed"}], [])
    assert live_calls == []
    assert replay(request["messages"], []).content == "live"
    assert live_calls == [1]


def test_load_replay_refuses_changed_model_settings(tmp_path):
    calibration.write(tmp_path/'settings.json', {"profile": {"max_tokens": 16384}, "case": {}, "stage": "full"})
    with pytest.raises(calibration.CalibrationStop, match="original model settings"):
        calibration.load_replay(tmp_path, {"max_tokens": 32768}, {})
