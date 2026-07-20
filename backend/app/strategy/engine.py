"""Strategy Engine — scores registered strategies and builds an ExecutionPlan."""

from __future__ import annotations

import time
from datetime import UTC, datetime

from app.core.config import Settings, get_settings
from app.core.logging import get_logger
from app.observability import metrics, span
from app.strategy.base import ExtractionStrategy
from app.strategy.data_sources import enrich_data_sources
from app.strategy.registry import StrategyRegistry, get_strategy_registry
from app.strategy.types import ExecutionPlan, StrategyRanking, StrategyScore
from app.website_intelligence.profile import WebsiteProfile

logger = get_logger(__name__)


class StrategyEngine:
    """
    Consumes WebsiteProfile → ranks strategies → returns ExecutionPlan.

    Selection is purely score-based (+ priority tie-break). No if/else trees.
    """

    def __init__(
        self,
        registry: StrategyRegistry | None = None,
        settings: Settings | None = None,
    ) -> None:
        self._registry = registry or get_strategy_registry()
        self._settings = settings or get_settings()

    def decide(
        self, profile: WebsiteProfile
    ) -> tuple[ExecutionPlan, StrategyRanking, list[str]]:
        with span("strategy.decide", url=profile.normalized_url):
            started = time.perf_counter()
            candidates = self._registry.enabled()
            scores: list[StrategyScore] = []
            reasoning: list[str] = []

            for strategy in candidates:
                evaluation = self._evaluate(strategy, profile)
                scores.append(evaluation)
                if evaluation.can_handle:
                    reasoning.append(
                        f"{evaluation.strategy_id}: score={evaluation.suitability_score} "
                        f"({evaluation.reason})"
                    )
                else:
                    reasoning.append(
                        f"{evaluation.strategy_id}: rejected ({evaluation.reject_reason})"
                    )
                    metrics.incr("strategy.rejected", strategy=evaluation.strategy_id)

            viable = [s for s in scores if s.can_handle]
            if not viable:
                # Absolute fallback: pick static_html plan from registry if present
                fallback = self._registry.get("static_html")
                if fallback is None:
                    raise RuntimeError("No strategies available to build an execution plan")
                plan = fallback.build_execution_plan(profile)
                plan.warnings.append("No viable strategies; forced static_html fallback")
                plan = enrich_data_sources(plan, profile)
                ranking = StrategyRanking(
                    scores=scores,
                    chosen_strategy_id=fallback.id(),
                    chosen_strategy_name=fallback.name(),
                    decision_time_ms=round((time.perf_counter() - started) * 1000, 2),
                    decided_at=datetime.now(UTC),
                )
                metrics.incr("strategy.forced_fallback")
                return plan, ranking, reasoning

            # Sort by suitability, then confidence, then strategy.priority()
            priority_map = {s.id(): s.priority() for s in candidates}

            def sort_key(item: StrategyScore) -> tuple[float, float, int]:
                return (
                    item.suitability_score,
                    item.confidence,
                    priority_map.get(item.strategy_id, 0),
                )

            viable_sorted = sorted(viable, key=sort_key, reverse=True)
            winner = viable_sorted[0]
            chosen = self._registry.get(winner.strategy_id)
            assert chosen is not None

            plan = chosen.build_execution_plan(profile)
            # Attach runner-up as fallback if not already set
            if len(viable_sorted) > 1 and not plan.fallback_strategy:
                plan.fallback_strategy = viable_sorted[1].strategy_id

            # Surface future disabled strategies as alternatives
            reserved = [
                s.id()
                for s in self._registry.all()
                if not s.is_enabled() and s.id() != plan.strategy_id
            ]
            plan.future_alternatives = list(
                dict.fromkeys([*(plan.future_alternatives or []), *reserved])
            )
            plan = enrich_data_sources(plan, profile)

            decision_ms = round((time.perf_counter() - started) * 1000, 2)
            ranking = StrategyRanking(
                scores=sorted(scores, key=lambda s: s.suitability_score, reverse=True),
                chosen_strategy_id=winner.strategy_id,
                chosen_strategy_name=winner.strategy_name,
                decision_time_ms=decision_ms,
                decided_at=datetime.now(UTC),
            )

            metrics.incr("strategy.chosen", strategy=winner.strategy_id)
            metrics.observe("strategy.decision_ms", decision_ms)
            logger.info(
                "strategy.decided",
                chosen=winner.strategy_id,
                score=winner.suitability_score,
                decision_ms=decision_ms,
            )
            return plan, ranking, reasoning

    def _evaluate(self, strategy: ExtractionStrategy, profile: WebsiteProfile) -> StrategyScore:
        with span("strategy.score", strategy=strategy.id()):
            if not strategy.can_handle(profile):
                return StrategyScore(
                    strategy_id=strategy.id(),
                    strategy_name=strategy.name(),
                    suitability_score=0.0,
                    confidence=0.0,
                    estimated_runtime_ms=0,
                    estimated_cost=0.0,
                    reason="Strategy cannot handle this profile",
                    can_handle=False,
                    reject_reason="can_handle_false",
                )
            return strategy.score(profile)
