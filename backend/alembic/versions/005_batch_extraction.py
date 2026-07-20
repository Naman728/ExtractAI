"""Batch extraction migration.

Revision ID: 005_batches
Revises: 004_network
Create Date: 2026-07-16
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "005_batches"
down_revision: Union[str, None] = "004_network"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "extraction_batches",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "guest_session_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("guest_sessions.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("url", sa.Text(), nullable=False),
        sa.Column("workflow", sa.String(64), nullable=True),
        sa.Column("status", sa.String(32), nullable=False, server_default="pending"),
        sa.Column("total_items", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("completed_items", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("failed_items", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "meta",
            postgresql.JSONB(),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
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
    )
    op.create_index("ix_extraction_batches_user_id", "extraction_batches", ["user_id"])
    op.create_index(
        "ix_extraction_batches_guest_session_id", "extraction_batches", ["guest_session_id"]
    )
    op.create_index("ix_extraction_batches_status", "extraction_batches", ["status"])

    op.create_table(
        "extraction_batch_items",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "batch_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("extraction_batches.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("position", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("address", sa.Text(), nullable=False),
        sa.Column(
            "job_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("jobs.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("status", sa.String(32), nullable=False, server_default="pending"),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column(
            "result_summary",
            postgresql.JSONB(),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
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
    )
    op.create_index("ix_extraction_batch_items_batch_id", "extraction_batch_items", ["batch_id"])
    op.create_index("ix_extraction_batch_items_job_id", "extraction_batch_items", ["job_id"])
    op.create_index("ix_extraction_batch_items_status", "extraction_batch_items", ["status"])


def downgrade() -> None:
    op.drop_index("ix_extraction_batch_items_status", table_name="extraction_batch_items")
    op.drop_index("ix_extraction_batch_items_job_id", table_name="extraction_batch_items")
    op.drop_index("ix_extraction_batch_items_batch_id", table_name="extraction_batch_items")
    op.drop_table("extraction_batch_items")
    op.drop_index("ix_extraction_batches_status", table_name="extraction_batches")
    op.drop_index("ix_extraction_batches_guest_session_id", table_name="extraction_batches")
    op.drop_index("ix_extraction_batches_user_id", table_name="extraction_batches")
    op.drop_table("extraction_batches")
