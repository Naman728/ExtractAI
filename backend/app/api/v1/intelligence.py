"""Website Intelligence API routes."""

from uuid import UUID

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import GuestKey, OptionalUser, get_db_session
from app.core.constants import GUEST_HEADER
from app.models.guest_session import GuestSession
from app.services.intelligence_service import IntelligenceService
from app.website_intelligence.profile import AnalyzeRequest, AnalyzeResponse

router = APIRouter(prefix="/intelligence", tags=["intelligence"])


def get_intelligence_service(session: AsyncSession = Depends(get_db_session)) -> IntelligenceService:
    return IntelligenceService(session)


@router.post("/analyze", response_model=AnalyzeResponse, status_code=status.HTTP_201_CREATED)
async def analyze_website(
    body: AnalyzeRequest,
    response: Response,
    user: OptionalUser,
    guest_key: GuestKey,
    service: IntelligenceService = Depends(get_intelligence_service),
) -> AnalyzeResponse:
    """
    Analyze a URL and return a WebsiteProfile + IntelligenceReport.

    Does not extract page content entities (products, emails, tables).
    """
    result, guest = await service.analyze(str(body.url), user=user, guest_key=guest_key)
    if isinstance(guest, GuestSession):
        response.headers[GUEST_HEADER] = guest.guest_key
    return result


@router.get("/{profile_id}", response_model=AnalyzeResponse)
async def get_intelligence_profile(
    profile_id: UUID,
    service: IntelligenceService = Depends(get_intelligence_service),
) -> AnalyzeResponse:
    return await service.get_analysis(profile_id)
