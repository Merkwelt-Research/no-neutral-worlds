"""Offline checks for provider pinning, reasoning continuity and billing hooks."""
from types import SimpleNamespace
import sys

import pytest

from tnt_bench.agent.day_loop import _assistant_message, _chat_with_retries
from tnt_bench.agent.llm import openai_chat_client


def install_fake(monkeypatch, create):
    monkeypatch.setitem(sys.modules, "openai", SimpleNamespace(
        OpenAI=lambda **kw: SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=create)))))


def test_strict_request_never_drops_provider_or_temperature(monkeypatch):
    calls = []
    def create(**kwargs):
        calls.append(kwargs)
        raise RuntimeError("No endpoints found that can handle the requested parameters")
    install_fake(monkeypatch, create)
    provider = {"only": ["chosen/fp8"], "allow_fallbacks": False, "require_parameters": True}
    chat = openai_chat_client("fake", "test/model", provider=provider,
                              reasoning={"effort": "high"}, max_tokens=16384, strict=True)
    with pytest.raises(RuntimeError):
        chat([], [])
    assert len(calls) == 1
    assert calls[0]["extra_body"]["provider"] == provider
    assert calls[0]["temperature"] == .7
    assert calls[0]["extra_body"]["reasoning"] == {"effort": "high"}
    assert calls[0]["max_tokens"] == 16384


def test_reasoning_and_tool_signatures_survive_tool_round_trip(monkeypatch):
    detail = [{"type": "reasoning.encrypted", "data": "opaque", "index": 0}]
    tc = SimpleNamespace(id="call1", function=SimpleNamespace(name="check_shop", arguments="{}"),
                         extra_content={"google": {"thought_signature": "signature"}})
    message = SimpleNamespace(content=None, tool_calls=[tc], reasoning="reasoning text", reasoning_details=detail)
    response = SimpleNamespace(choices=[SimpleNamespace(message=message)],
        usage=SimpleNamespace(prompt_tokens=10, completion_tokens=20), provider="Chosen",
        model_dump=lambda **kw: {"usage": {"cost": .001}, "id": "generation-1"})
    install_fake(monkeypatch, lambda **kwargs: response)
    recorded = []
    chat = openai_chat_client("fake", "test/model", on_response=recorded.append)
    restored = _assistant_message(chat([], []))
    assert restored["reasoning_details"] == detail
    assert restored["reasoning"] == "reasoning text"
    assert restored["tool_calls"][0]["extra_content"]["google"]["thought_signature"] == "signature"
    assert recorded == [{"usage": {"cost": .001}, "id": "generation-1"}]


def test_no_retry_stops_before_another_paid_attempt():
    from scripts.calibrate_transport import CalibrationStop
    calls = []
    def chat(*args):
        calls.append(1)
        raise CalibrationStop("budget exhausted")
    with pytest.raises(CalibrationStop):
        _chat_with_retries(chat, [], [])
    assert len(calls) == 1
