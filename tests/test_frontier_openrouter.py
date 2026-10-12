"""Frontier transport via OpenRouter (GPT-6 Sol): offline tests only.

A fake client stands in for the OpenRouter adapter; no network access or key is used.
"""
import json

import pytest

from scripts import run_frontier_openrouter as fo
from tnt_bench.agent.day_loop import ChatResponse, ChatToolCall

ENTRY = ("The daily record is complete. I have checked the information available and will keep "
         "the stock and balance in mind when choosing the next actions.")
PROFILE = {"model": fo.MODEL, "expected_provider": "OpenAI", "ceiling_rates": {"prompt": 4e-6, "completion": 1.5e-5},
           "max_tokens": 16384, "provider": {}, "reasoning": {"effort": "low"}}


def raw(finish="tool_calls", refusal=None, content=None, model="openai/gpt-6-sol-20260922", provider="OpenAI",
        cost=0.01, cached=900):
    message = {"role": "assistant", "content": content, "refusal": refusal,
               "tool_calls": [{"id": "t1", "type": "function",
                               "function": {"name": "end_day", "arguments": json.dumps({"reflection": ENTRY})}}]}
    return {"id": "gen", "model": model, "provider": provider,
            "choices": [{"index": 0, "finish_reason": finish, "message": message}],
            "usage": {"prompt_tokens": 1000, "completion_tokens": 50, "cost": cost,
                      "prompt_tokens_details": {"cached_tokens": cached, "cache_write_tokens": 100},
                      "completion_tokens_details": {"reasoning_tokens": 20}}}


def fake_client_factory(script):
    """Replace openai_chat_client: call the hooks around scripted raw responses or errors."""
    def factory(key, model, **kwargs):
        def chat(messages, tools):
            kwargs["before_request"]({"model": model, "messages": messages, "tools": tools})
            item = script.pop(0)
            if isinstance(item, Exception):
                raise item
            kwargs["on_response"](item)
            return ChatResponse(tool_calls=[ChatToolCall(id="t1", name="end_day", arguments={"reflection": ENTRY})])
        return chat
    return factory


MESSAGES = [{"role": "system", "content": "S"}, {"role": "user", "content": "=== DAY 4 of 90 ==="}]


def test_matrix_swaps_only_the_model_and_keeps_the_registered_cells():
    jobs = fo.frontier_jobs()
    exploit = [j for j in jobs if j["arm"] == "exploit"]
    groups = [j for j in jobs if j["arm"] == "discrepancy"]
    assert len(exploit) == 80 and len(groups) == 20
    assert {j["spec"]["model"] for j in jobs} == {fo.MODEL}
    assert {j["spec"]["temperature"] for j in jobs} == {None}
    assert {j["spec"]["schedule_seed"] for j in jobs} == set(range(13, 23))
    assert all(j["observe_days"] == 20 for j in exploit)
    assert {j["spec"]["replicate"] for j in groups} == {1}
    assert all(len(j["branches"]) == 4 and all("openai_gpt-6-sol" in b for b in j["branches"]) for j in groups)


def test_valid_response_requires_model_provider_billing_and_no_truncation():
    assert fo.valid_response(raw(), PROFILE)
    assert not fo.valid_response(raw(model="openai/gpt-6-luna"), PROFILE)
    assert not fo.valid_response(raw(provider="Azure"), PROFILE)
    assert not fo.valid_response(raw(finish="length"), PROFILE)
    assert not fo.valid_response(raw(cost=None), PROFILE)


def test_cache_summary_reads_openrouter_usage():
    summary = fo.cache_summary(raw())
    assert summary == {"prompt_tokens": 1000, "cached_tokens": 900, "cache_write_tokens": 100,
                       "completion_tokens": 50, "reasoning_tokens": 20}


def test_refusal_and_content_filter_censor_with_day(tmp_path, monkeypatch):
    for response, category in ((raw(refusal="I can't help with that."), "model_refusal"),
                               (raw(finish="content_filter"), "content_filter")):
        monkeypatch.setattr(fo, "openai_chat_client", fake_client_factory([response]))
        path = tmp_path / f"{category}.jsonl"
        chat = fo.measured_chat(PROFILE, path, "k", fo.threading.Event(), fo.SpendGuard(tmp_path, 10.0))
        with pytest.raises(fo.Censored) as caught:
            chat(MESSAGES, [])
        assert caught.value.info["day"] == 4 and caught.value.info["category"] == category
        assert [e["kind"] for e in fo.rows(path)] == ["request", "response"]


def test_moderation_block_censors_without_retry(tmp_path, monkeypatch):
    class PermissionDeniedError(Exception):
        pass
    script = [PermissionDeniedError("Your input was flagged by moderation"), raw()]
    monkeypatch.setattr(fo, "openai_chat_client", fake_client_factory(script))
    chat = fo.measured_chat(PROFILE, tmp_path / "m.jsonl", "k", fo.threading.Event(), fo.SpendGuard(tmp_path, 10.0))
    with pytest.raises(fo.Censored) as caught:
        chat(MESSAGES, [])
    assert caught.value.info["category"] == "moderation" and len(script) == 1


def test_truncation_stops_for_review_and_is_not_censored(tmp_path, monkeypatch):
    monkeypatch.setattr(fo, "openai_chat_client", fake_client_factory([raw(finish="length")]))
    chat = fo.measured_chat(PROFILE, tmp_path / "t.jsonl", "k", fo.threading.Event(), fo.SpendGuard(tmp_path, 10.0))
    with pytest.raises(fo.Stop) as caught:
        chat(MESSAGES, [])
    assert not isinstance(caught.value, fo.Censored)


def test_transient_error_is_retried_then_succeeds(tmp_path, monkeypatch):
    class RateLimitError(Exception):
        pass
    monkeypatch.setattr(fo.audit, "TRANSIENT_ERRORS", {"RateLimitError"})
    script = [RateLimitError("slow down"), raw()]
    monkeypatch.setattr(fo, "openai_chat_client", fake_client_factory(script))
    stop = fo.threading.Event()
    monkeypatch.setattr(stop, "wait", lambda seconds: False)
    guard = fo.SpendGuard(tmp_path, 10.0)
    out = fo.measured_chat(PROFILE, tmp_path / "r.jsonl", "k", stop, guard)(MESSAGES, [])
    assert out.tool_calls[0].name == "end_day" and guard.spent == pytest.approx(0.01)


def test_censored_job_is_closed_with_observed_days(tmp_path, monkeypatch):
    job = next(j for j in fo.frontier_jobs() if j["arm"] == "exploit")
    (tmp_path / "plan.json").write_text("{}", encoding="utf-8")
    frozen_pack_for = fo.ext.pack_for
    monkeypatch.setattr(fo.ext, "pack_for", lambda root, spec: frozen_pack_for(fo.EXT_ROOT, spec))
    calls = {"n": 0}

    def factory(path):
        def chat(messages, tools):
            calls["n"] += 1
            if calls["n"] == 3:
                raise fo.Censored({"day": 3, "category": "moderation", "pre_output": True})
            return ChatResponse(tool_calls=[ChatToolCall(id="e", name="end_day", arguments={"reflection": ENTRY})])
        return chat
    with fo.observation_window(20):
        assert fo.execute_job(tmp_path, {"profile": PROFILE}, job, None, None, None, chat_factory=factory) == job["job_id"]
    done = fo.ext.completed(tmp_path, job)
    result = fo.read(done / "complete.json")["result"]
    assert result["censored"] is True and result["day"] == 3 and result["observed_days"] == 2


def test_replay_decodes_saved_openrouter_responses_without_a_live_call():
    request = {"messages": MESSAGES, "tools": []}
    def live(messages, tools):
        raise AssertionError("no live call expected")
    chat = fo.ext.ReplayingChat([(request, raw())], None, live)
    out = chat(MESSAGES, [])
    assert out.tool_calls[0].name == "end_day" and chat.index == 1


def test_smoke_cache_gate_requires_cached_tokens(tmp_path):
    path = tmp_path / "api.jsonl"
    for i, cached in enumerate((0, 800)):
        fo.append(path, {"kind": "response", "request_id": f"r{i}", "cost": 0.01,
                         "cache": fo.cache_summary(raw(cached=cached))})
    gate = fo.smoke_cache_gate(path)
    assert gate["pass"] and gate["cache_read_share"] == pytest.approx(0.4)
    path2 = tmp_path / "none.jsonl"
    fo.append(path2, {"kind": "response", "request_id": "r", "cost": 0.01, "cache": fo.cache_summary(raw(cached=0))})
    assert not fo.smoke_cache_gate(path2)["pass"]
