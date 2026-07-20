"""Network Intelligence persistence."""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.api_endpoint import ApiEndpoint
from app.models.execution_source import ExecutionSource
from app.models.network_profile import NetworkProfileRecord
from app.models.network_request import NetworkRequest


class NetworkProfileRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, record: NetworkProfileRecord) -> NetworkProfileRecord:
        self._session.add(record)
        await self._session.flush()
        await self._session.refresh(record)
        return record

    async def get_by_id(self, profile_id: uuid.UUID) -> NetworkProfileRecord | None:
        stmt = (
            select(NetworkProfileRecord)
            .where(NetworkProfileRecord.id == profile_id)
            .options(
                selectinload(NetworkProfileRecord.endpoints),
                selectinload(NetworkProfileRecord.execution_sources),
            )
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def add_endpoints(self, rows: list[ApiEndpoint]) -> None:
        self._session.add_all(rows)
        await self._session.flush()

    async def add_execution_source(self, row: ExecutionSource) -> ExecutionSource:
        self._session.add(row)
        await self._session.flush()
        await self._session.refresh(row)
        return row

    async def add_requests(self, rows: list[NetworkRequest]) -> None:
        self._session.add_all(rows)
        await self._session.flush()
