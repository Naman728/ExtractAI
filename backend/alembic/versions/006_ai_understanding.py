"""AI Understanding Engine migration.

Revision ID: 006_ai_understanding
Revises: 005_batches
Create Date: 2026-07-16
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "006_ai_understanding"
down_revision: Union[str, None] = "005_batches"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "extracted_data",
        sa.Column("ai_understanding", postgresql.JSONB(), nullable=True),
    )
    op.add_column(
        "extracted_data",
        sa.Column("ai_status", sa.String(length=32), nullable=True),
    )

    op.create_table(
        "ai_understanding_cache",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("content_hash", sa.String(64), nullable=False),
        sa.Column(
            "payload",
            postgresql.JSONB(),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column("hit_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("last_hit_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("notes", sa.Text(), nullable=True),
    )
    op.create_index(
        "ix_ai_understanding_cache_content_hash",
        "ai_understanding_cache",
        ["content_hash"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index("ix_ai_understanding_cache_content_hash", table_name="ai_understanding_cache")
    op.drop_table("ai_understanding_cache")
    op.drop_column("extracted_data", "ai_status")
    op.drop_column("extracted_data", "ai_understanding")
