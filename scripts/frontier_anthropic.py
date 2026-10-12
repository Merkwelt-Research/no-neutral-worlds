"""Direct Anthropic Messages API adapter for the frontier transport.

The day loop speaks OpenAI-style chat messages (system / user / assistant with
tool_calls / tool). This module translates at the boundary and nowhere else:

- the static system prompt becomes a cached top-level system block;
- each assistant turn is replayed from the raw content blocks the API returned
  (thinking, text and tool_use, verbatim), so thinking stays bound to its
  conversation within the day;
- consecutive tool results and any following user text (nudges, the
  action-budget notice) merge into one user turn, tool results first.

The day loop rebuilds the tool list every turn and legitimately changes it
(the exploit fault's report tool disappears after a report; only end_day
remains once the action allowance is spent). A changed tool set invalidates
earlier thinking blocks, so requests opt into the documented drop_block
behaviour and every drop is logged from the response's input_transformations.

Kept outside tnt_bench/ so the frozen GLM/Muse batch's source hashes stay
valid. The SDK lives in tmp/frontier-deps for the same reason.
"""
from __future__ import annotations

import json
from pathlib import Path
import sys
from typing import Callable

ROOT = Path(__file__).resolve().parents[1]
DEPS = ROOT / "tmp/frontier-deps"
if DEPS.exists() and str(DEPS) not in sys.path:
    sys.path.append(str(DEPS))  # appended: the project environment keeps precedence

from tnt_bench.agent.day_loop import ChatClient, ChatResponse, ChatToolCall

MODEL = "claude-opus-5-5"
THINKING_BINDING_BETA = "thinking-binding-controls-2026-08-01"
# USD per million tokens (Claude API first-party list prices, cached 2026-06-24;
# re-checked against the live price page when the plan is frozen).
PRICES = {"input": 4.00, "output": 20.00, "cache_write_5m": 5.00, "cache_read": 0.20}


class ReviewStop(RuntimeError):
    """A response that must not be absorbed silently (refusal, truncation)."""
    no_retry = True


def to_tools(tools: list[dict]) -> list[dict]:
    """OpenAI function schemas -> Anthropic tool definitions, order preserved."""
    return [{"name": t["function"]["name"],
             "description": t["function"].get("description", ""),
             "input_schema": t["function"].get("parameters") or {"type": "object", "properties": {}}}
            for t in tools]


def _input_block(block: dict) -> dict:
    """Echo a returned content block in its documented input shape."""
    kind = block["type"]
    if kind == "thinking":
        return {"type": "thinking", "thinking": block.get("thinking", ""), "signature": block["signature"]}
    if kind == "redacted_thinking":
        return {"type": "redacted_thinking", "data": block["data"]}
    if kind == "text":
        return {"type": "text", "text": block["text"]}
    if kind == "tool_use":
        return {"type": "tool_use", "id": block["id"], "name": block["name"], "input": block["input"]}
    raise ReviewStop(f"unexpected content block type in history: {kind}")


def to_request(messages: list[dict]) -> tuple[list[dict], list[dict]]:
    """Split the day loop's messages into (system blocks, Anthropic messages)."""
    if not messages or messages[0]["role"] != "system":
        raise ValueError("the day loop always opens with the static system prompt")
    system = [{"type": "text", "text": messages[0]["content"], "cache_control": {"type": "ephemeral"}}]
    out: list[dict] = []
    pending: list[dict] = []  # user-side blocks awaiting the next assistant turn

    def flush():
        nonlocal pending
        if pending:
            out.append({"role": "user", "content": pending})
            pending = []

    for m in messages[1:]:
        role = m["role"]
        if role == "assistant":
            flush()
            raw = m.get("anthropic_content")
            if raw is None:
                raise ReviewStop("assistant turn without its raw Anthropic content; cannot replay faithfully")
            out.append({"role": "assistant", "content": [_input_block(b) for b in raw]})
        elif role == "tool":
            pending.append({"type": "tool_result", "tool_use_id": m["tool_call_id"], "content": m["content"]})
        elif role == "user":
            pending.append({"type": "text", "text": m["content"]})
        else:
            raise ValueError(f"unexpected message role: {role}")
    flush()
    return system, out


def parse_response(raw: dict) -> ChatResponse:
    """Decode a saved or live response identically (replay depends on this)."""
    if raw.get("stop_reason") == "refusal":
        details = raw.get("stop_details") or {}
        raise ReviewStop(f"refusal ({details.get('category')}): {details.get('explanation')}")
    if raw.get("stop_reason") == "max_tokens":
        raise ReviewStop("response truncated at max_tokens")
    blocks = raw.get("content") or []
    text = "\n".join(b["text"] for b in blocks if b["type"] == "text") or None
    calls = [ChatToolCall(id=b["id"], name=b["name"],
                          arguments=b["input"] if isinstance(b.get("input"), dict) else {},
                          parse_error=None if isinstance(b.get("input"), dict) else "tool input was not an object")
             for b in blocks if b["type"] == "tool_use"]
    usage = raw.get("usage") or {}
    prompt = sum(usage.get(k) or 0 for k in ("input_tokens", "cache_read_input_tokens", "cache_creation_input_tokens"))
    return ChatResponse(
        content=text, tool_calls=calls,
        usage={"prompt_tokens": prompt, "completion_tokens": usage.get("output_tokens") or 0},
        provider="anthropic",
        provider_fields={"anthropic_content": blocks},
    )


def response_cost(raw: dict) -> float:
    u = raw.get("usage") or {}
    return ((u.get("input_tokens") or 0) * PRICES["input"]
            + (u.get("cache_creation_input_tokens") or 0) * PRICES["cache_write_5m"]
            + (u.get("cache_read_input_tokens") or 0) * PRICES["cache_read"]
            + (u.get("output_tokens") or 0) * PRICES["output"]) / 1_000_000


def request_body(model: str, messages: list[dict], tools: list[dict], *, effort: str, max_tokens: int) -> dict:
    system, converted = to_request(messages)
    return dict(
        model=model, max_tokens=max_tokens, system=system, messages=converted, tools=to_tools(tools),
        tool_choice={"type": "auto"},
        thinking={"type": "adaptive", "display": "summarized",
                  "block_binding": {"prefix_mismatch_behavior": "drop_block"}},
        output_config={"effort": effort},
        cache_control={"type": "ephemeral"},  # moving breakpoint: caches the day's conversation so far
        betas=[THINKING_BINDING_BETA],
    )


def anthropic_chat_client(
    api_key: str | None,
    model: str = MODEL,
    *,
    effort: str = "low",
    max_tokens: int = 16384,
    max_retries: int = 0,
    before_request: Callable[[dict], None] | None = None,
    on_response: Callable[[dict], None] | None = None,
    client=None,
) -> ChatClient:
    """ChatClient for the day loop. `client` may be injected (tests)."""
    if client is None:
        import anthropic
        client = anthropic.Anthropic(api_key=api_key, max_retries=max_retries)

    def chat(messages: list[dict], tools: list[dict]) -> ChatResponse:
        body = request_body(model, messages, tools, effort=effort, max_tokens=max_tokens)
        if before_request is not None:
            # The day loop's own messages/tools are what recovery replay compares;
            # the translated body is what was actually sent.
            before_request({"messages": messages, "tools": tools, "body": body})
        response = client.beta.messages.create(**body)
        raw = response.model_dump(mode="json") if hasattr(response, "model_dump") else response
        if on_response is not None:
            on_response(raw)
        return parse_response(raw)

    return chat


def cache_summary(raw: dict) -> dict:
    u = raw.get("usage") or {}
    return {k: u.get(k) or 0 for k in ("input_tokens", "cache_creation_input_tokens",
                                       "cache_read_input_tokens", "output_tokens")}


def dropped_thinking(raw: dict) -> list[dict]:
    return [t for t in raw.get("input_transformations") or [] if t.get("type") == "thinking_dropped"]


if __name__ == "__main__":
    print(json.dumps(PRICES))
