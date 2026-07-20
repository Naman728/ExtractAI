"""Persisted Network Intelligence profile."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.api_endpoint import ApiEndpoint
    from app.models.execution_source import ExecutionSource
    from app.models.network_request import NetworkRequest
    from app.models.strategy_analysis import StrategyAnalysis
    from app.models.website_profile import WebsiteProfileRecord


class NetworkProfileRecord(Base):
    __tablename__ = "network_profiles"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    website_profile_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("website_profiles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    strategy_analysis_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("strategy_analyses.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    final_url: Mapped[str] = mapped_column(Text, nullable=False)
    discovery_version: Mapped[str] = mapped_column(String(32), nullable=False)
    profile: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    recommendation: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    timings: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    diagnostics: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    endpoints_found: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    useful_endpoints: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    rejected_endpoints: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    websocket_detected: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    sse_detected: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    discovery_time_ms: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    classification_time_ms: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    endpoints: Mapped[list[ApiEndpoint]] = relationship(
        "ApiEndpoint", back_populates="network_profile", cascade="all, delete-orphan"
    )
    requests: Mapped[list[NetworkRequest]] = relationship(
        "NetworkRequest", back_populates="network_profile"
    )
    execution_sources: Mapped[list[ExecutionSource]] = relationship(
        "ExecutionSource", back_populates="network_profile", cascade="all, delete-orphan"
    )


# Public alias
NetworkProfile = NetworkProfileRecord
