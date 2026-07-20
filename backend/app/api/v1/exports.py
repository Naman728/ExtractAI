"""Export routes — auth required."""

from uuid import UUID

from fastapi import APIRouter, Depends
from fastapi.responses import Response
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import CurrentUser, get_db_session
from app.core.constants import ExportFormat
from app.services.results_service import ResultsService

router = APIRouter(prefix="/exports", tags=["exports"])


class ExportRequest(BaseModel):
    job_id: UUID


def get_results_service(session: AsyncSession = Depends(get_db_session)) -> ResultsService:
    return ResultsService(session)


@router.post("/json")
async def export_json(
    body: ExportRequest,
    user: CurrentUser,
    service: ResultsService = Depends(get_results_service),
) -> dict:
    export = await service.export(body.job_id, fmt=ExportFormat.JSON, user=user)
    return {"id": str(export.id), "format": export.format, "status": export.status}


@router.post("/csv")
async def export_csv(
    body: ExportRequest,
    user: CurrentUser,
    service: ResultsService = Depends(get_results_service),
) -> dict:
    export = await service.export(body.job_id, fmt=ExportFormat.CSV, user=user)
    return {"id": str(export.id), "format": export.format, "status": export.status}


@router.post("/excel")
async def export_excel(
    body: ExportRequest,
    user: CurrentUser,
    service: ResultsService = Depends(get_results_service),
) -> dict:
    export = await service.export(body.job_id, fmt=ExportFormat.EXCEL, user=user)
    return {"id": str(export.id), "format": export.format, "status": export.status}


@router.get("/{export_id}/download")
async def download_export(
    export_id: UUID,
    user: CurrentUser,
    service: ResultsService = Depends(get_results_service),
) -> Response:
    data, filename, fmt = await service.download_export(export_id, user=user)
    media = {
        "json": "application/json",
        "csv": "text/csv",
        "excel": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    }.get(fmt, "application/octet-stream")
    return Response(
        content=data,
        media_type=media,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
