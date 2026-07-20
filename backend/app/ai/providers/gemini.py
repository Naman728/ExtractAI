"""Google Gemini provider via Generative Language API."""

from __future__ import annotations

import time
from typing import Any

import httpx

from app.ai.providers.base import LLMMessage, LLMProvider, LLMResponse

_COST_TABLE: dict[str, tuple[float, float]] = {
    "gemini-2.0-flash": (0.10, 0.40),
    "gemini-1.5-flash": (0.075, 0.30),
    "gemini-1.5-pro": (1.25, 5.00),
}


def _estimate_cost(model: str, prompt_tokens: int, completion_tokens: int) -> float:
    inp, out = _COST_TABLE.get(model, (0.10, 0.40))
    return (prompt_tokens * inp + completion_tokens * out) / 1_000_000


class GeminiProvider(LLMProvider):
    name = "gemini"

    def __init__(
        self,
        api_key: str,
        model: str = "gemini-2.0-flash",
        *,
        base_url: str = "https://generativelanguage.googleapis.com/v1beta",
        timeout_seconds: float = 60.0,
    ) -> None:
        if not api_key:
            raise ValueError("GEMINI_API_KEY is required for GeminiProvider")
        self._api_key = api_key
        self._model = model
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout_seconds

    def complete(
        self,
        messages: list[LLMMessage],
        *,
        temperature: float = 0.2,
        max_tokens: int = 4096,
        response_format_json: bool = True,
    ) -> LLMResponse:
        system_parts = [m.content for m in messages if m.role == "system"]
        user_parts = [m.content for m in messages if m.role != "system"]
        contents = [
            {"role": "user", "parts": [{"text": "\n\n".join(user_parts)}]},
        ]
        payload: dict[str, Any] = {
            "contents": contents,
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": max_tokens,
            },
        }
        if system_parts:
            payload["systemInstruction"] = {"parts": [{"text": "\n\n".join(system_parts)}]}
        if response_format_json:
            payload["generationConfig"]["responseMimeType"] = "application/json"

        url = f"{self._base_url}/models/{self._model}:generateContent"
        started = time.perf_counter()
        with httpx.Client(timeout=self._timeout) as client:
            resp = client.post(url, params={"key": self._api_key}, json=payload)
            resp.raise_for_status()
            data = resp.json()
        latency_ms = int((time.perf_counter() - started) * 1000)

        candidates = data.get("candidates") or []
        text = ""
        if candidates:
            parts = ((candidates[0].get("content") or {}).get("parts")) or []
            text = "".join(p.get("text", "") for p in parts)

        usage = data.get("usageMetadata") or {}
        prompt_tokens = int(usage.get("promptTokenCount") or 0)
        completion_tokens = int(usage.get("candidatesTokenCount") or 0)
        total_tokens = int(usage.get("totalTokenCount") or (prompt_tokens + completion_tokens))

        return LLMResponse(
            text=text,
            model=self._model,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
            latency_ms=latency_ms,
            raw=data,
            estimated_cost_usd=_estimate_cost(self._model, prompt_tokens, completion_tokens),
        )
