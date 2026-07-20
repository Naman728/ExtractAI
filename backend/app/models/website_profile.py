"""Persisted Website Intelligence profile (standalone or job-linked)."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin

if TYPE_CHECKING:
    from app.models.guest_session import GuestSession
    from app.models.job import Job
    from app.models.user import User


class WebsiteProfileRecord(Base, TimestampMixin):
    """
    ORM row for intelligence profiles.

    Table name remains `website_profiles` for continuity with Phase 2 schema.
    `job_id` is optional so standalone /analyze runs can persist without a job.
    """

    __tablename__ = "website_profiles"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    job_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("jobs.id", ondelete="CASCADE"),
        unique=True,
        nullable=True,
        index=True,
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

    profile: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    report: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    discovery: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)

    profile_version: Mapped[str] = mapped_column(String(32), nullable=False)
    discovery_version: Mapped[str | None] = mapped_column(String(32), nullable=True)
    schema_version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    overall_confidence: Mapped[float | None] = mapped_column(Float, nullable=True)

    probed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    job: Mapped[Job | None] = relationship("Job", back_populates="website_profile")
    user: Mapped[User | None] = relationship("User")
    guest_session: Mapped[GuestSession | None] = relationship("GuestSession")


# Backwards-compatible alias used by older imports
WebsiteProfile = WebsiteProfileRecord
