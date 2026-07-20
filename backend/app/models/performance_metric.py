"""Job-level performance metrics."""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING, Any

from sqlalchemy import BigInteger, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.job import Job


class PerformanceMetric(Base):
    __tablename__ = "performance_metrics"

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
    ttfb_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    dom_content_loaded_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    load_event_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    total_requests: Mapped[int | None] = mapped_column(Integer, nullable=True)
    total_transfer_bytes: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    extras: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)

    job: Mapped[Job] = relationship("Job", back_populates="performance_metrics")
