"""Classifier-censoring amendment: offline tests with synthetic logs only."""
import json

import pytest

from scripts import resume_frontier_reviewed as rv
from scripts import run_frontier_transport as fr

REFUSAL = {"model": "claude-opus-5-5", "stop_reason": "refusal", "content": [],
           "stop_details": {"type": "refusal", "category": "cyber", "explanation": "blocked"},
           "usage": {"input_tokens": 2, "output_tokens": 0}}
JOB = {"arm": "exploit", "job_id": "claude-opus-5-5__test", "kind": "full", "run_id": "claude-opus-5-5__test"}


def log_pair(path, day, response):
    fr.append(path, {"kind": "request", "request_id": "r1", "day": day, "request": {"messages": [], "tools": []}})
    fr.append(path, {"kind": "response", "request_id": "r1", "cost": 0, "cache": {}, "thinking_dropped": [],
                     "response": response})


def test_refusal_becomes_censoring_with_day_and_category(tmp_path, monkeypatch):
    path = tmp_path / "api_calls.jsonl"
    def frozen(path_, key, stop, guard):
        def chat(messages, tools):
            log_pair(path_, 7, REFUSAL)
            raise fr.Stop("Unexpected model, refusal or truncated output; response preserved for review.")
        return chat
    monkeypatch.setattr(rv, "FROZEN_MEASURED_CHAT", frozen)
    chat = rv.measured_chat(path, None, None, None)
    with pytest.raises(rv.Censored) as caught:
        chat([], [])
    assert caught.value.info["day"] == 7 and caught.value.info["category"] == "cyber"
    assert caught.value.info["pre_output"] is True


def test_other_stops_are_not_censored(tmp_path, monkeypatch):
    path = tmp_path / "api_calls.jsonl"
    def frozen(path_, key, stop, guard):
        def chat(messages, tools):
            log_pair(path_, 3, {**REFUSAL, "stop_reason": "max_tokens"})
            raise fr.Stop("truncated")
        return chat
    monkeypatch.setattr(rv, "FROZEN_MEASURED_CHAT", frozen)
    with pytest.raises(fr.Stop) as caught:
        rv.measured_chat(path, None, None, None)([], [])
    assert not isinstance(caught.value, rv.Censored)


def test_censored_job_is_closed_and_counts_observed_days(tmp_path, monkeypatch):
    monkeypatch.setattr(fr.ext, "job_directory", lambda root, job: tmp_path / "job")
    def frozen(root, plan, job, key, stop, guard, resume=False, chat_factory=None):
        attempt = tmp_path / "job" / "attempt-1"
        (attempt / "data" / "run").mkdir(parents=True)
        (attempt / "data" / "run" / "days.jsonl").write_text('{"day": 1}\n{"day": 2}\n', encoding="utf-8")
        raise rv.Censored({"day": 3, "category": "cyber"})
    monkeypatch.setattr(rv, "FROZEN_EXECUTE_JOB", frozen)
    assert rv.execute_job(tmp_path, {}, JOB, None, None, None) == JOB["job_id"]
    result = json.loads((tmp_path / "job" / "attempt-1" / "complete.json").read_text(encoding="utf-8"))["result"]
    assert result["censored"] is True and result["day"] == 3 and result["observed_days"] == 2


def test_earlier_refusal_stop_is_closed_without_new_inference(tmp_path, monkeypatch):
    monkeypatch.setattr(fr.ext, "job_directory", lambda root, job: tmp_path / "job")
    attempt = tmp_path / "job" / "attempt-1"
    attempt.mkdir(parents=True)
    log_pair(attempt / "api_calls.jsonl", 1, REFUSAL)
    closed = rv.close_prior_refusals(tmp_path, {"jobs": [JOB]})
    assert closed == [JOB["job_id"]]
    assert json.loads((attempt / "complete.json").read_text(encoding="utf-8"))["result"]["censored"] is True


def test_interrupted_but_not_refused_attempts_are_left_for_replay(tmp_path, monkeypatch):
    monkeypatch.setattr(fr.ext, "job_directory", lambda root, job: tmp_path / "job")
    attempt = tmp_path / "job" / "attempt-1"
    attempt.mkdir(parents=True)
    log_pair(attempt / "api_calls.jsonl", 1, {**REFUSAL, "stop_reason": "tool_use", "content": [{"type": "text", "text": "x"}]})
    assert rv.close_prior_refusals(tmp_path, {"jobs": [JOB]}) == []
    assert not (attempt / "complete.json").exists()
