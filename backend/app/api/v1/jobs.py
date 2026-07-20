"""Job routes."""

from uuid import UUID

from fastapi import APIRouter, Query, Response, status

from app.api.deps import CurrentUser, DbSession, GuestKey, JobServiceDep, OptionalUser, QuotaServiceDep
from app.core.constants import GUEST_HEADER
from app.schemas import (
    BatchResponse,
    JobCreateRequest,
    JobEventsResponse,
    JobListResponse,
    JobResponse,
)
from app.services.batch_service import BatchService, normalize_addresses

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_job(
    body: JobCreateRequest,
    response: Response,
    session: DbSession,
    jobs: JobServiceDep,
    quota: QuotaServiceDep,
    user: OptionalUser,
    guest_key: GuestKey,
) -> JobResponse | BatchResponse:
    addresses = normalize_addresses(list(body.addresses or []))
    single_address = (body.inputs or {}).get("address")
    if single_address and single_address.strip():
        # Prefer explicit inputs.address for single-job path unless many addresses sent
        if len(addresses) <= 1:
            addresses = []

    # Multi-address → batch
    if len(addresses) >= 2:
        batch, guest = await BatchService(session).create_batch(
            str(body.url),
            addresses,
            workflow=body.workflow,
            extra_inputs={k: v for k, v in (body.inputs or {}).items() if k != "address"},
            user=user,
            guest_key=guest_key,
        )
        if guest is not None:
            response.headers[GUEST_HEADER] = guest.guest_key
            response.headers["X-Guest-Jobs-Remaining"] = str(
                max(0, guest.jobs_limit - guest.jobs_used)
            )
        response.headers["X-Batch-Id"] = str(batch.id)
        return batch

    # Single address from addresses[] convenience
    inputs = dict(body.inputs or {})
    if len(addresses) == 1:
        inputs["address"] = addresses[0]

    job, guest = await jobs.create_job(
        str(body.url),
        user=user,
        guest_key=guest_key,
        inputs=inputs,
        workflow=body.workflow,
        follow_pagination=body.follow_pagination,
        max_pages=body.max_pages,
    )
    if guest is not None:
        response.headers[GUEST_HEADER] = guest.guest_key
        response.headers["X-Guest-Jobs-Remaining"] = str(
            max(0, guest.jobs_limit - guest.jobs_used)
        )
    return job


@router.get("", response_model=JobListResponse)
async def list_jobs(
    user: CurrentUser,
    jobs: JobServiceDep,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
) -> JobListResponse:
    return await jobs.list_jobs(user, page=page, page_size=page_size)


@router.get("/{job_id}", response_model=JobResponse)
async def get_job(
    job_id: UUID,
    jobs: JobServiceDep,
    user: OptionalUser,
    guest_key: GuestKey,
) -> JobResponse:
    return await jobs.get_job(job_id, user=user, guest_key=guest_key)


@router.get("/{job_id}/events", response_model=JobEventsResponse)
async def get_job_events(
    job_id: UUID,
    jobs: JobServiceDep,
    user: OptionalUser,
    guest_key: GuestKey,
    limit: int = Query(40, ge=1, le=200),
) -> JobEventsResponse:
    return await jobs.get_job_events(job_id, user=user, guest_key=guest_key, limit=limit)


@router.delete("/{job_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_job(job_id: UUID, user: CurrentUser, jobs: JobServiceDep) -> Response:
    await jobs.delete_job(job_id, user=user)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/{job_id}/retry", response_model=JobResponse)
async def retry_job(job_id: UUID, user: CurrentUser, jobs: JobServiceDep) -> JobResponse:
    return await jobs.retry_job(job_id, user=user)
