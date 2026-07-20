"""Strategy decision / analysis repositories."""

from __future__ import annotations

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.strategy_analysis import StrategyAnalysis
from app.models.strategy_decision import StrategyDecision


class StrategyAnalysisRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, row: StrategyAnalysis) -> StrategyAnalysis:
        self._session.add(row)
        await self._session.flush()
        await self._session.refresh(row)
        return row

    async def get_by_id(self, analysis_id: uuid.UUID) -> StrategyAnalysis | None:
        return await self._session.get(StrategyAnalysis, analysis_id)


class StrategyDecisionRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create_many(self, rows: list[StrategyDecision]) -> None:
        self._session.add_all(rows)
        await self._session.flush()
