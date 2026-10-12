"""OpenAI-compatible chat adapter for the agent loop.

Lazy import keeps openai out of the core dependency set. Default endpoint
is OpenRouter, as elsewhere in the project.
"""

from __future__ import annotations

import json
from typing import Callable

from .day_loop import ChatClient, ChatResponse, ChatToolCall


def _tool_call(call_id: str, name: str, raw: str | None) -> ChatToolCall:
    """Parse an arguments string defensively. Some models (observed:
    Gemma 4) occasionally emit concatenated JSON objects or trailing junk
    in a single call's arguments; that is the model's error to see and
    correct, not a reason to kill a 90-day run — flag it so the day loop
    answers with an error tool result instead of dispatching."""
    raw = raw or "{}"
    try:
        arguments = json.loads(raw)
    except json.JSONDecodeError as e:
        return ChatToolCall(
            id=call_id, name=name, arguments={},
            raw_arguments=raw, parse_error=f"{e.msg} at char {e.pos}",
        )
    if not isinstance(arguments, dict):
        return ChatToolCall(
            id=call_id, name=name, arguments={},
            raw_arguments=raw, parse_error="arguments must be a JSON object",
        )
    return ChatToolCall(id=call_id, name=name, arguments=arguments)


def _should_drop_strict_routing(e: Exception, state: dict) -> bool:
    """OpenRouter 404 'No endpoints found that can handle the requested
    parameters' — the strict flag excluded every host for this model."""
    return (
        state.get("extra_body") is not None
        and "no endpoints found" in str(e).lower()
    )


def _should_drop_temperature(e: Exception, state: dict) -> bool:
    """Some models (Sonnet 5, Opus 4.7+) reject sampling parameters."""
    return (
        state.get("temperature") is not None
        and type(e).__name__ == "BadRequestError"
        and "temperature" in str(e).lower()
    )


def openai_chat_client(
    api_key: str,
    model: str,
    base_url: str = "https://openrouter.ai/api/v1",
    temperature: float | None = 0.7,
    max_retries: int = 5,
    *,
    provider: dict | None = None,
    reasoning: dict | None = None,
    max_tokens: int | None = None,
    strict: bool = False,
    before_request: Callable[[dict], None] | None = None,
    on_response: Callable[[dict], None] | None = None,
) -> ChatClient:
    import openai  # lazy: optional dependency

    client = openai.OpenAI(api_key=api_key, base_url=base_url, max_retries=max_retries)

    # OpenRouter load-balances each model across upstream hosts of varying
    # quality; require_parameters restricts routing to hosts that actually
    # support every request parameter (tools, tool_choice) instead of ones
    # that mangle tool-call JSON or reject the request outright. But it is
    # strict: models whose sole endpoint rejects a sampling param (e.g.
    # Sonnet 5 takes no temperature) route to *nothing* — so degrade
    # per-client when the router says no endpoint fits, and drop
    # temperature if the endpoint itself rejects it. (Without the strict
    # flag OpenRouter silently drops unsupported params, so this matches
    # what those models effectively ran with all along.)
    state = {
        "extra_body": (
            {"provider": {"require_parameters": True}}
            if "openrouter" in base_url
            else None
        ),
        "temperature": temperature,
    }
    if provider is not None or reasoning is not None:
        state["extra_body"] = dict(state["extra_body"] or {})
        if provider is not None:
            state["extra_body"]["provider"] = provider
        if reasoning is not None:
            state["extra_body"]["reasoning"] = reasoning

    def chat(messages: list[dict], tools: list[dict]) -> ChatResponse:
        while True:
            kwargs: dict = {}
            if state["temperature"] is not None:
                kwargs["temperature"] = state["temperature"]
            if state["extra_body"]:
                kwargs["extra_body"] = state["extra_body"]
            if max_tokens is not None:
                kwargs["max_tokens"] = max_tokens
            if before_request is not None:
                before_request(dict(model=model, messages=messages, tools=tools,
                                    tool_choice="auto", **kwargs))
            try:
                response = client.chat.completions.create(
                    model=model,
                    messages=messages,
                    tools=tools,
                    tool_choice="auto",
                    **kwargs,
                )
            except Exception as e:
                if not strict and _should_drop_strict_routing(e, state):
                    state["extra_body"] = None
                    continue
                if not strict and _should_drop_temperature(e, state):
                    state["temperature"] = None
                    continue
                raise
            break
        if on_response is not None:
            on_response(response.model_dump(mode="json"))
        # OpenRouter can return HTTP 200 with choices=null and an error
        # payload; the SDK neither raises nor retries that. Surface it.
        if not response.choices:
            from ..narration.llm import _provider_error

            raise RuntimeError(f"provider returned no choices: {_provider_error(response)}")
        choice = response.choices[0].message
        tool_calls = [
            _tool_call(tc.id, tc.function.name, tc.function.arguments)
            for tc in (choice.tool_calls or [])
        ]
        for parsed, raw in zip(tool_calls, choice.tool_calls or []):
            extra = getattr(raw, "extra_content", None)
            if extra is not None:
                parsed.provider_fields["extra_content"] = extra
        usage = {
            "prompt_tokens": getattr(response.usage, "prompt_tokens", 0) or 0,
            "completion_tokens": getattr(response.usage, "completion_tokens", 0) or 0,
        }
        return ChatResponse(
            content=choice.content, tool_calls=tool_calls, usage=usage,
            # OpenRouter names the upstream host that actually served the
            # request; the SDK keeps the extra field. Recorded per day in
            # days.jsonl and aggregated in result.json (provenance for the
            # provider-drift analyses; 2026-07-10 external review).
            provider=getattr(response, "provider", None),
            provider_fields={
                key: getattr(choice, key)
                for key in ("reasoning", "reasoning_details", "reasoning_content")
                if getattr(choice, key, None) is not None
            },
        )

    return chat
