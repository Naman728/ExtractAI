"""Strategy Engine application service."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.core.constants import StrategyDecisionOutcome
from app.core.exceptions import NotFoundError, ValidationAppError
from app.core.logging import get_logger
from app.models.strategy_analysis import StrategyAnalysis
from app.models.strategy_decision import StrategyDecision
from app.observability import metrics
from app.repositories.strategy_repository import (
    StrategyAnalysisRepository,
    StrategyDecisionRepository,
)
from app.repositories.website_profile_repository import WebsiteProfileRepository
from app.strategy.engine import StrategyEngine
from app.strategy.types import StrategyAnalyzeResponse
from app.website_intelligence.profile import WebsiteProfile

logger = get_logger(__name__)


class StrategyService:
    def __init__(self, session: AsyncSession, settings: Settings | None = None) -> None:
        self._session = session
        self._settings = settings or get_settings()
        self._profiles = WebsiteProfileRepository(session)
        self._analyses = StrategyAnalysisRepository(session)
        self._decisions = StrategyDecisionRepository(session)
        self._engine = StrategyEngine(settings=self._settings)

    async def analyze(self, website_profile_id: str) -> StrategyAnalyzeResponse:
        try:
            profile_uuid = uuid.UUID(website_profile_id)
        except ValueError as exc:
            raise ValidationAppError("Invalid website_profile_id") from exc

        record = await self._profiles.get_by_id(profile_uuid)
        if not record:
            raise NotFoundError("Website profile not found")

        profile = WebsiteProfile.model_validate(record.profile)
        plan, ranking, reasoning = self._engine.decide(profile)

        warnings = list(plan.warnings)
        for score in ranking.scores:
            warnings.extend(score.warnings)
        # de-dupe preserve order
        warnings = list(dict.fromkeys(warnings))

        analysis = StrategyAnalysis(
            website_profile_id=record.id,
            chosen_strategy=plan.strategy,
            chosen_strategy_id=plan.strategy_id,
            confidence=plan.confidence,
            decision_time_ms=ranking.decision_time_ms,
            execution_plan=plan.model_dump(mode="json"),
            ranking=ranking.model_dump(mode="json"),
            candidates=[s.model_dump(mode="json") for s in ranking.scores],
            reasoning=reasoning,
            warnings=warnings,
            pipeline_version=plan.pipeline_version,
            strategy_version=self._settings.strategy_version,
        )
        analysis = await self._analyses.create(analysis)

        decision_rows: list[StrategyDecision] = []
        for order, score in enumerate(ranking.scores):
            is_chosen = score.strategy_id == ranking.chosen_strategy_id
            decision_rows.append(
                StrategyDecision(
                    job_id=None,
                    strategy_analysis_id=analysis.id,
                    website_profile_id=record.id,
                    strategy_name=score.strategy_id,
                    strategy_version=self._settings.strategy_version,
                    score=score.suitability_score,
                    score_breakdown=score.score_breakdown,
                    decision="selected" if is_chosen else ("skipped" if not score.can_handle else "ranked"),
                    reject_reason=score.reject_reason,
                    attempt_order=order,
                    duration_ms=int(ranking.decision_time_ms),
                    outcome=(
                        StrategyDecisionOutcome.SELECTED.value
                        if is_chosen
                        else (
                            StrategyDecisionOutcome.SKIPPED.value
                            if not score.can_handle
                            else StrategyDecisionOutcome.SUCCEEDED.value
                        )
                    ),
                    execution_plan=plan.model_dump(mode="json") if is_chosen else None,
                    created_at=datetime.now(UTC),
                )
            )
        await self._decisions.create_many(decision_rows)
        await self._session.commit()
        await self._session.refresh(analysis)

        metrics.incr("strategy.analyses_persisted")
        logger.info(
            "strategy.analysis_saved",
            analysis_id=str(analysis.id),
            profile_id=str(record.id),
            chosen=plan.strategy_id,
        )

        return StrategyAnalyzeResponse(
            id=str(analysis.id),
            website_profile_id=str(record.id),
            execution_plan=plan,
            ranking=ranking,
            reasoning=reasoning,
            warnings=warnings,
            confidence=plan.confidence,
            pipeline_version=plan.pipeline_version,
            strategy_version=self._settings.strategy_version,
        )

    async def get_analysis(self, analysis_id: uuid.UUID) -> StrategyAnalyzeResponse:
        row = await self._analyses.get_by_id(analysis_id)
        if not row:
            raise NotFoundError("Strategy analysis not found")
        from app.strategy.types import ExecutionPlan, StrategyRanking

        return StrategyAnalyzeResponse(
            id=str(row.id),
            website_profile_id=str(row.website_profile_id),
            execution_plan=ExecutionPlan.model_validate(row.execution_plan),
            ranking=StrategyRanking.model_validate(row.ranking),
            reasoning=list(row.reasoning or []),
            warnings=list(row.warnings or []),
            confidence=row.confidence,
            pipeline_version=row.pipeline_version,
            strategy_version=row.strategy_version,
        )
