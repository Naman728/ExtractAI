"""Strategy Engine API routes."""

from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db_session
from app.services.strategy_service import StrategyService
from app.strategy.types import StrategyAnalyzeRequest, StrategyAnalyzeResponse

router = APIRouter(prefix="/strategy", tags=["strategy"])


def get_strategy_service(session: AsyncSession = Depends(get_db_session)) -> StrategyService:
    return StrategyService(session)


@router.post("/analyze", response_model=StrategyAnalyzeResponse, status_code=status.HTTP_201_CREATED)
async def analyze_strategy(
    body: StrategyAnalyzeRequest,
    service: StrategyService = Depends(get_strategy_service),
) -> StrategyAnalyzeResponse:
    """
    Score strategies for a persisted WebsiteProfile and return an ExecutionPlan.

    Does not fetch pages or extract content.
    """
    return await service.analyze(body.website_profile_id)


@router.get("/{analysis_id}", response_model=StrategyAnalyzeResponse)
async def get_strategy_analysis(
    analysis_id: UUID,
    service: StrategyService = Depends(get_strategy_service),
) -> StrategyAnalyzeResponse:
    return await service.get_analysis(analysis_id)
