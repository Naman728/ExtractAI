"""Guest quota info endpoint."""

from fastapi import APIRouter, Response

from app.api.deps import GuestKey, QuotaServiceDep
from app.core.constants import GUEST_HEADER
from app.schemas import GuestSessionResponse

router = APIRouter(prefix="/guest", tags=["guest"])


@router.post("/session", response_model=GuestSessionResponse)
async def create_or_get_guest_session(
    response: Response,
    quota: QuotaServiceDep,
    guest_key: GuestKey,
) -> GuestSessionResponse:
    guest = await quota.resolve_or_create_guest(guest_key)
    response.headers[GUEST_HEADER] = guest.guest_key
    return quota.to_response(guest)
