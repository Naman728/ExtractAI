"""Batch extraction routes."""

from uuid import UUID

from fastapi import APIRouter, Response, status

from app.api.deps import GuestKey, OptionalUser, QuotaServiceDep
from app.core.constants import GUEST_HEADER
from app.schemas import BatchCreateRequest, BatchResponse, BatchResultsResponse
from app.services.batch_service import BatchService
from app.api.deps import DbSession

router = APIRouter(prefix="/batches", tags=["batches"])


@router.post("", status_code=status.HTTP_201_CREATED, response_model=BatchResponse)
async def create_batch(
    body: BatchCreateRequest,
    response: Response,
    session: DbSession,
    quota: QuotaServiceDep,
    user: OptionalUser,
    guest_key: GuestKey,
) -> BatchResponse:
    service = BatchService(session)
    batch, guest = await service.create_batch(
        str(body.url),
        body.addresses,
        workflow=body.workflow,
        extra_inputs=body.inputs,
        user=user,
        guest_key=guest_key,
    )
    if guest is not None:
        response.headers[GUEST_HEADER] = guest.guest_key
        response.headers["X-Guest-Jobs-Remaining"] = str(
            max(0, guest.jobs_limit - guest.jobs_used)
        )
    return batch


@router.get("/{batch_id}", response_model=BatchResponse)
async def get_batch(
    batch_id: UUID,
    session: DbSession,
    user: OptionalUser,
    guest_key: GuestKey,
) -> BatchResponse:
    return await BatchService(session).get_batch(
        batch_id, user=user, guest_key=guest_key
    )


@router.get("/{batch_id}/results", response_model=BatchResultsResponse)
async def get_batch_results(
    batch_id: UUID,
    session: DbSession,
    user: OptionalUser,
    guest_key: GuestKey,
) -> BatchResultsResponse:
    return await BatchService(session).get_results(
        batch_id, user=user, guest_key=guest_key
    )
