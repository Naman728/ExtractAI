"""Factory for configuration-driven LLM provider selection."""

from __future__ import annotations

from app.ai.providers.anthropic import AnthropicProvider
from app.ai.providers.base import LLMProvider
from app.ai.providers.gemini import GeminiProvider
from app.ai.providers.heuristic import HeuristicProvider
from app.ai.providers.ollama import OllamaProvider
from app.ai.providers.openai import OpenAIProvider
from app.core.config import Settings, get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)


def create_llm_provider(settings: Settings | None = None) -> LLMProvider:
    """Create an LLM provider from Settings / environment.

    Switch via ``LLM_PROVIDER`` — no code changes required.
    Falls back to HeuristicProvider when keys are missing or provider is none.
    """
    cfg = settings or get_settings()
    provider = (cfg.llm_provider or "none").strip().lower()
    model = cfg.llm_model
    timeout = float(cfg.llm_timeout_seconds)

    try:
        if provider in {"none", "off", "disabled", "heuristic"}:
            return HeuristicProvider()

        if provider == "openai":
            key = cfg.openai_api_key or cfg.llm_api_key
            if not key:
                logger.warning("ai.provider.fallback", reason="missing_openai_key")
                return HeuristicProvider()
            return OpenAIProvider(
                api_key=key,
                model=model or "gpt-4o-mini",
                base_url=cfg.openai_base_url,
                timeout_seconds=timeout,
            )

        if provider == "gemini":
            key = cfg.gemini_api_key or cfg.llm_api_key
            if not key:
                logger.warning("ai.provider.fallback", reason="missing_gemini_key")
                return HeuristicProvider()
            return GeminiProvider(
                api_key=key,
                model=model or "gemini-2.0-flash",
                timeout_seconds=timeout,
            )

        if provider == "anthropic":
            key = cfg.anthropic_api_key or cfg.llm_api_key
            if not key:
                logger.warning("ai.provider.fallback", reason="missing_anthropic_key")
                return HeuristicProvider()
            return AnthropicProvider(
                api_key=key,
                model=model or "claude-3-5-haiku-latest",
                timeout_seconds=timeout,
            )

        if provider == "ollama":
            return OllamaProvider(
                model=model or "llama3.2",
                base_url=cfg.ollama_base_url,
                timeout_seconds=timeout,
            )

        logger.warning("ai.provider.unknown", provider=provider)
        return HeuristicProvider()
    except Exception as exc:
        logger.warning("ai.provider.error", error=str(exc))
        return HeuristicProvider()
