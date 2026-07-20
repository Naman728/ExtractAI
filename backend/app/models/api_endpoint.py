"""Discovered API endpoint rows."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.network_profile import NetworkProfileRecord


class ApiEndpoint(Base):
    __tablename__ = "api_endpoints"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    network_profile_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("network_profiles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    url: Mapped[str] = mapped_column(Text, nullable=False)
    method: Mapped[str] = mapped_column(String(16), nullable=False, default="GET")
    endpoint_type: Mapped[str] = mapped_column(String(32), nullable=False, default="unknown")
    content_type: Mapped[str | None] = mapped_column(String(255), nullable=True)
    status_code: Mapped[int | None] = mapped_column(Integer, nullable=True)
    authentication_required: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    returns_json: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    returns_html: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    returns_xml: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    pagination_support: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    estimated_value: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    confidence: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    framework_hint: Mapped[str | None] = mapped_column(String(64), nullable=True)
    source: Mapped[str] = mapped_column(String(32), nullable=False, default="discovery")
    parameters: Mapped[list[Any]] = mapped_column(JSONB, nullable=False, default=list)
    rate_limit_indicators: Mapped[list[Any]] = mapped_column(JSONB, nullable=False, default=list)
    classification_evidence: Mapped[list[Any]] = mapped_column(JSONB, nullable=False, default=list)
    profile_json: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    network_profile: Mapped[NetworkProfileRecord] = relationship(
        "NetworkProfileRecord", back_populates="endpoints"
    )
