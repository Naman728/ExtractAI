"""Results routes."""

from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import GuestKey, OptionalUser, get_db_session
from app.services.results_service import ResultsService

router = APIRouter(prefix="/results", tags=["results"])


def get_results_service(session: AsyncSession = Depends(get_db_session)) -> ResultsService:
    return ResultsService(session)


@router.get("/{job_id}")
async def get_results(
    job_id: UUID,
    user: OptionalUser,
    guest_key: GuestKey,
    service: ResultsService = Depends(get_results_service),
) -> dict:
    return await service.get_results(job_id, user=user, guest_key=guest_key)
