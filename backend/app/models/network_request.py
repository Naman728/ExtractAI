"""Captured network requests from browser strategies / network intelligence."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.job import Job
    from app.models.network_profile import NetworkProfileRecord
    from app.models.strategy_decision import StrategyDecision


class NetworkRequest(Base):
    __tablename__ = "network_requests"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    job_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("jobs.id", ondelete="CASCADE"), nullable=True, index=True
    )
    network_profile_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("network_profiles.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    strategy_decision_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("strategy_decisions.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    request_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    method: Mapped[str] = mapped_column(String(16), nullable=False)
    url: Mapped[str] = mapped_column(Text, nullable=False)
    resource_type: Mapped[str | None] = mapped_column(String(32), nullable=True)
    status_code: Mapped[int | None] = mapped_column(Integer, nullable=True)
    request_headers: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    response_headers: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    content_type: Mapped[str | None] = mapped_column(String(255), nullable=True)
    body_storage_path: Mapped[str | None] = mapped_column(Text, nullable=True)
    body_sha256: Mapped[str | None] = mapped_column(String(64), nullable=True)
    is_graphql: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    graphql_operation: Mapped[str | None] = mapped_column(String(128), nullable=True)
    is_json: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_public_candidate: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    duration_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    transfer_size: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    job: Mapped[Job | None] = relationship("Job", back_populates="network_requests")
    network_profile: Mapped[NetworkProfileRecord | None] = relationship(
        "NetworkProfileRecord", back_populates="requests"
    )
    strategy_decision: Mapped[StrategyDecision | None] = relationship(
        "StrategyDecision", back_populates="network_requests"
    )
