"""Normalized + validated extraction payload for a job."""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING, Any

from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin

if TYPE_CHECKING:
    from app.models.job import Job


class ExtractedData(Base, TimestampMixin):
    __tablename__ = "extracted_data"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    job_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("jobs.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True,
    )
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    normalized_payload: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    summary: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    validation_report: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    section_confidence: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    ai_understanding: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    ai_status: Mapped[str | None] = mapped_column(String(32), nullable=True)  # pending|running|completed|failed|skipped
    storage_path: Mapped[str | None] = mapped_column(Text, nullable=True)
    content_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    schema_version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    job: Mapped[Job] = relationship("Job", back_populates="extracted_data")
