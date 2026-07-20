"""Extraction job and job event models."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.constants import JobStatus
from app.core.database import Base
from app.models.base import TimestampMixin

if TYPE_CHECKING:
    from app.models.extracted_data import ExtractedData
    from app.models.export import Export
    from app.models.guest_session import GuestSession
    from app.models.network_request import NetworkRequest
    from app.models.performance_metric import PerformanceMetric
    from app.models.pipeline_log import PipelineLog
    from app.models.snapshot import Snapshot
    from app.models.strategy_decision import StrategyDecision
    from app.models.user import User
    from app.models.website_profile import WebsiteProfileRecord


class Job(Base, TimestampMixin):
    __tablename__ = "jobs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    guest_session_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("guest_sessions.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    url: Mapped[str] = mapped_column(Text, nullable=False)
    normalized_url: Mapped[str] = mapped_column(Text, nullable=False, index=True)
    status: Mapped[str] = mapped_column(
        String(32), nullable=False, default=JobStatus.PENDING.value, index=True
    )

    strategy_used: Mapped[str | None] = mapped_column(String(64), nullable=True)
    extractor_type: Mapped[str] = mapped_column(String(32), nullable=False, default="basic")
    selected_strategy: Mapped[str | None] = mapped_column(String(64), nullable=True)

    progress_pct: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    current_stage: Mapped[str | None] = mapped_column(String(64), nullable=True)

    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    duration_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)

    error_code: Mapped[str | None] = mapped_column(String(64), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    retry_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    max_retries: Mapped[int] = mapped_column(Integer, nullable=False, default=3)
    output_size_bytes: Mapped[int | None] = mapped_column(Integer, nullable=True)

    pipeline_version: Mapped[str] = mapped_column(String(32), nullable=False)
    strategy_version: Mapped[str] = mapped_column(String(32), nullable=False)
    plugin_set_version: Mapped[str] = mapped_column(String(64), nullable=False)
    schema_version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    profile_version: Mapped[str | None] = mapped_column(String(32), nullable=True)
    discovery_version: Mapped[str | None] = mapped_column(String(32), nullable=True)

    overall_confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    partial: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    meta: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    user: Mapped[User | None] = relationship("User", back_populates="jobs")
    guest_session: Mapped[GuestSession | None] = relationship(
        "GuestSession", back_populates="jobs"
    )
    website_profile: Mapped[WebsiteProfileRecord | None] = relationship(
        "WebsiteProfileRecord",
        back_populates="job",
        uselist=False,
    )
    extracted_data: Mapped[ExtractedData | None] = relationship(
        "ExtractedData", back_populates="job", uselist=False, cascade="all, delete-orphan"
    )
    events: Mapped[list[JobEvent]] = relationship(
        "JobEvent", back_populates="job", cascade="all, delete-orphan"
    )
    strategy_decisions: Mapped[list[StrategyDecision]] = relationship(
        "StrategyDecision", back_populates="job", cascade="all, delete-orphan"
    )
    pipeline_logs: Mapped[list[PipelineLog]] = relationship(
        "PipelineLog", back_populates="job", cascade="all, delete-orphan"
    )
    network_requests: Mapped[list[NetworkRequest]] = relationship(
        "NetworkRequest", back_populates="job", cascade="all, delete-orphan"
    )
    snapshots: Mapped[list[Snapshot]] = relationship(
        "Snapshot", back_populates="job", cascade="all, delete-orphan"
    )
    performance_metrics: Mapped[PerformanceMetric | None] = relationship(
        "PerformanceMetric", back_populates="job", uselist=False, cascade="all, delete-orphan"
    )
    exports: Mapped[list[Export]] = relationship("Export", back_populates="job")


class JobEvent(Base):
    __tablename__ = "job_events"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    job_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False, index=True
    )
    stage: Mapped[str] = mapped_column(String(64), nullable=False)
    level: Mapped[str] = mapped_column(String(16), nullable=False, default="info")
    message: Mapped[str] = mapped_column(Text, nullable=False)
    details: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    job: Mapped[Job] = relationship("Job", back_populates="events")
