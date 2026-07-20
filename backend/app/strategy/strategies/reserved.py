"""Future / reserved strategies — interface-only, disabled."""

from __future__ import annotations

from app.strategy.base import ExtractionStrategy
from app.strategy.types import ExecutionPlan, StrategyScore
from app.website_intelligence.profile import WebsiteProfile


class _ReservedStrategy(ExtractionStrategy):
    """Base for strategies that are registered but not enabled yet."""

    _strategy_id: str
    _strategy_name: str
    _priority: int = 10

    def id(self) -> str:
        return self._strategy_id

    def name(self) -> str:
        return self._strategy_name

    def priority(self) -> int:
        return self._priority

    def version(self) -> str:
        return "0.0.0-reserved"

    def is_enabled(self) -> bool:
        return False

    def can_handle(self, profile: WebsiteProfile) -> bool:
        return False

    def score(self, profile: WebsiteProfile) -> StrategyScore:
        return StrategyScore(
            strategy_id=self.id(),
            strategy_name=self.name(),
            suitability_score=0.0,
            confidence=0.0,
            estimated_runtime_ms=0,
            estimated_cost=0.0,
            reason="Reserved for future implementation",
            can_handle=False,
            reject_reason="not_implemented",
        )

    def build_execution_plan(self, profile: WebsiteProfile) -> ExecutionPlan:
        raise NotImplementedError(f"{self.name()} is reserved and not implemented yet")


class RestApiStrategy(_ReservedStrategy):
    _strategy_id = "rest_api"
    _strategy_name = "Public REST API"
    _priority = 90


class GraphQLStrategy(_ReservedStrategy):
    _strategy_id = "graphql"
    _strategy_name = "GraphQL"
    _priority = 85


class LLMStrategy(_ReservedStrategy):
    _strategy_id = "llm"
    _strategy_name = "LLM Extraction"
    _priority = 20


class RemoteBrowserStrategy(_ReservedStrategy):
    _strategy_id = "remote_browser"
    _strategy_name = "Remote Browser"
    _priority = 25
