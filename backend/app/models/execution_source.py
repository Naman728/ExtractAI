"""Execution source recommendations linked to network / strategy analyses."""

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
    from app.models.strategy_analysis import StrategyAnalysis


class ExecutionSource(Base):
    __tablename__ = "execution_sources"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    network_profile_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("network_profiles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    strategy_analysis_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("strategy_analyses.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    preferred_data_source: Mapped[str] = mapped_column(String(32), nullable=False, default="html")
    fallback_sources: Mapped[list[Any]] = mapped_column(JSONB, nullable=False, default=list)
    estimated_speed: Mapped[str] = mapped_column(String(16), nullable=False, default="medium")
    estimated_reliability: Mapped[float] = mapped_column(Float, nullable=False, default=0.7)
    reasoning: Mapped[list[Any]] = mapped_column(JSONB, nullable=False, default=list)
    top_endpoints: Mapped[list[Any]] = mapped_column(JSONB, nullable=False, default=list)
    is_applied_to_plan: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    rank: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    network_profile: Mapped[NetworkProfileRecord] = relationship(
        "NetworkProfileRecord", back_populates="execution_sources"
    )
