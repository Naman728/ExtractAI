"""Fetch engine factory / registry — keyed by ExecutionPlan.fetch_engine."""

from __future__ import annotations

from app.core.config import Settings, get_settings
from app.scrapers.fetch.base import FetchEngine
from app.scrapers.fetch.browser_agent import BrowserAgentFetchEngine
from app.scrapers.fetch.dynamic import DynamicFetchEngine
from app.scrapers.fetch.static import StaticFetchEngine


class FetchEngineRegistry:
    def __init__(self, settings: Settings | None = None) -> None:
        self._settings = settings or get_settings()
        self._engines: dict[str, FetchEngine] = {
            "requests_http": StaticFetchEngine(self._settings),
            "playwright": DynamicFetchEngine(self._settings),
            "browser_agent": BrowserAgentFetchEngine(self._settings),
        }

    def get(self, engine_id: str) -> FetchEngine:
        engine = self._engines.get(engine_id)
        if engine is None:
            # Unknown engines fall back to static — never if/else chains of strategy
            return self._engines["requests_http"]
        return engine

    def register(self, engine: FetchEngine) -> None:
        self._engines[engine.id()] = engine


def create_fetch_registry(settings: Settings | None = None) -> FetchEngineRegistry:
    return FetchEngineRegistry(settings)
