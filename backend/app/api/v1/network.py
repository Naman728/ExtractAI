"""Network Intelligence API routes."""

from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db_session
from app.network.types import NetworkAnalyzeRequest, NetworkAnalyzeResponse
from app.services.network_service import NetworkService

router = APIRouter(prefix="/network", tags=["network"])


def get_network_service(session: AsyncSession = Depends(get_db_session)) -> NetworkService:
    return NetworkService(session)


@router.post("/analyze", response_model=NetworkAnalyzeResponse, status_code=status.HTTP_201_CREATED)
async def analyze_network(
    body: NetworkAnalyzeRequest,
    service: NetworkService = Depends(get_network_service),
) -> NetworkAnalyzeResponse:
    """
    Discover public APIs / JSON feeds / GraphQL endpoints for a WebsiteProfile.

    Does not extract content via APIs — discovery, classification, and ranking only.
    """
    return await service.analyze(
        body.website_profile_id,
        strategy_analysis_id=body.strategy_analysis_id,
    )


@router.get("/{network_profile_id}", response_model=NetworkAnalyzeResponse)
async def get_network_profile(
    network_profile_id: UUID,
    service: NetworkService = Depends(get_network_service),
) -> NetworkAnalyzeResponse:
    return await service.get_analysis(network_profile_id)
