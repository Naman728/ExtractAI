"""Results and export APIs."""

from __future__ import annotations

import csv
import io
import json
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID

from openpyxl import Workbook
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.consolidation import consolidate
from app.core.config import Settings, get_settings
from app.core.constants import ExportFormat, ExportStatus
from app.core.exceptions import ForbiddenError, NotFoundError, ValidationAppError
from app.models.export import Export
from app.models.extracted_data import ExtractedData
from app.models.job import Job
from app.models.user import User
from app.repositories.job_repository import JobRepository
from app.services.quota_service import QuotaService
from app.storage import StorageBackend, create_storage_backend


class ResultsService:
    def __init__(self, session: AsyncSession, settings: Settings | None = None) -> None:
        self._session = session
        self._settings = settings or get_settings()
        self._jobs = JobRepository(session)
        self._quota = QuotaService(session, self._settings)
        self._storage = create_storage_backend(self._settings)

    async def get_results(
        self,
        job_id: UUID,
        *,
        user: User | None = None,
        guest_key: str | None = None,
    ) -> dict[str, Any]:
        job = await self._require_job(job_id, user=user, guest_key=guest_key)
        result = await self._session.execute(
            select(ExtractedData).where(ExtractedData.job_id == job.id)
        )
        data = result.scalar_one_or_none()
        if not data:
            raise NotFoundError("Results not ready yet")
        ready = consolidate(
            data.normalized_payload,
            url=job.url,
            ai=data.ai_understanding if isinstance(data.ai_understanding, dict) else None,
        )
        return {
            "job_id": str(job.id),
            "url": job.url,
            "status": job.status,
            "strategy_used": job.strategy_used,
            "schema_version": data.schema_version,
            "summary": data.summary,
            "normalized": data.normalized_payload,
            "ready": ready,
            "validation_report": data.validation_report,
            "section_confidence": data.section_confidence,
            "raw": data.payload,
            "duration_ms": job.duration_ms,
            "overall_confidence": job.overall_confidence,
            "ai_status": data.ai_status,
            "ai_understanding": data.ai_understanding,
        }

    async def export(
        self,
        job_id: UUID,
        *,
        fmt: ExportFormat,
        user: User,
    ) -> Export:
        job = await self._jobs.get_by_id(job_id)
        if not job:
            raise NotFoundError("Job not found")
        if job.user_id != user.id:
            raise ForbiddenError("Exports require ownership — sign in and use your jobs")

        result = await self._session.execute(
            select(ExtractedData).where(ExtractedData.job_id == job.id)
        )
        data = result.scalar_one_or_none()
        if not data or not data.normalized_payload:
            raise ValidationAppError("No normalized data to export")

        payload = data.normalized_payload
        ready = consolidate(
            payload,
            url=job.url,
            ai=data.ai_understanding if isinstance(data.ai_understanding, dict) else None,
        )
        if fmt == ExportFormat.JSON:
            # Prefer ready-made entity dicts for direct project paste
            content = json.dumps(ready or payload, indent=2, ensure_ascii=False).encode("utf-8")
            content_type = "application/json"
            ext = "json"
        elif fmt == ExportFormat.CSV:
            content = self._to_csv(payload)
            content_type = "text/csv"
            ext = "csv"
        elif fmt == ExportFormat.EXCEL:
            content = self._to_excel(payload)
            content_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            ext = "xlsx"
        else:
            raise ValidationAppError("Unsupported export format")

        key = f"exports/{user.id}/{job.id}.{ext}"
        stored = self._storage.put_bytes(key, content, content_type=content_type)
        export = Export(
            job_id=job.id,
            user_id=user.id,
            format=fmt.value,
            status=ExportStatus.READY.value,
            storage_path=stored.path,
            size_bytes=stored.size_bytes,
            expires_at=datetime.now(UTC) + timedelta(days=7),
        )
        self._session.add(export)
        await self._session.commit()
        await self._session.refresh(export)
        return export

    async def download_export(self, export_id: UUID, *, user: User) -> tuple[bytes, str, str]:
        export = await self._session.get(Export, export_id)
        if not export or export.user_id != user.id:
            raise NotFoundError("Export not found")
        if not export.storage_path:
            raise NotFoundError("Export file missing")
        data = self._storage.get_bytes(export.storage_path)
        filename = f"extractai-{export.job_id}.{export.format}"
        return data, filename, export.format

    async def _require_job(
        self,
        job_id: UUID,
        *,
        user: User | None,
        guest_key: str | None,
    ) -> Job:
        job = await self._jobs.get_by_id(job_id)
        if not job:
            raise NotFoundError("Job not found")
        if user and job.user_id == user.id:
            return job
        if guest_key and job.guest_session_id:
            guest = await self._quota._guests.get_by_key(guest_key)
            if guest and guest.id == job.guest_session_id:
                return job
        raise ForbiddenError("You do not have access to this job")

    def _to_csv(self, payload: dict[str, Any]) -> bytes:
        buf = io.StringIO()
        writer = csv.writer(buf)
        writer.writerow(["section", "index", "value"])
        for section, value in payload.items():
            if isinstance(value, list):
                for i, item in enumerate(value):
                    writer.writerow([section, i, json.dumps(item, ensure_ascii=False)])
            elif isinstance(value, dict):
                writer.writerow([section, 0, json.dumps(value, ensure_ascii=False)])
            else:
                writer.writerow([section, 0, value])
        return buf.getvalue().encode("utf-8")

    def _to_excel(self, payload: dict[str, Any]) -> bytes:
        wb = Workbook()
        # summary sheet
        ws = wb.active
        ws.title = "summary"
        ws.append(["section", "count_or_value"])
        for section, value in payload.items():
            if isinstance(value, list):
                ws.append([section, len(value)])
            elif isinstance(value, dict):
                ws.append([section, len(value)])
            else:
                ws.append([section, value])
        # detail sheets for list sections
        for section, value in payload.items():
            if not isinstance(value, list) or not value:
                continue
            sheet = wb.create_sheet(title=section[:28])
            if isinstance(value[0], dict):
                keys = list(value[0].keys())
                sheet.append(keys)
                for row in value:
                    sheet.append([json.dumps(row.get(k), ensure_ascii=False) if isinstance(row.get(k), (dict, list)) else row.get(k) for k in keys])
            else:
                sheet.append(["value"])
                for item in value:
                    sheet.append([item])
        out = io.BytesIO()
        wb.save(out)
        return out.getvalue()
