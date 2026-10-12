"""OpenAI-compatible chat adapter for pack generation.

Kept out of the core import path so the engine and themes never require the
openai package. Default endpoint is OpenRouter, as in the legacy project.
"""

from __future__ import annotations

from .pack import LLMFn


def openai_chat_llm(
    api_key: str,
    model: str,
    base_url: str = "https://openrouter.ai/api/v1",
    temperature: float = 0.8,
    max_retries: int = 5,
) -> LLMFn:
    import openai  # lazy: optional dependency

    client = openai.OpenAI(api_key=api_key, base_url=base_url, max_retries=max_retries)

    def call(system: str, user: str) -> str:
        response = client.chat.completions.create(
            model=model,
            temperature=temperature,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        )
        # OpenRouter can return HTTP 200 with choices=null and an error
        # payload; the SDK neither raises nor retries that. Surface it.
        if not response.choices:
            raise RuntimeError(f"provider returned no choices: {_provider_error(response)}")
        return response.choices[0].message.content or ""

    return call


def _provider_error(response) -> str:
    error = getattr(response, "error", None)
    if error is None and getattr(response, "model_extra", None):
        error = response.model_extra.get("error")
    return repr(error)
