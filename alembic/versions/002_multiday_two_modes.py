"""Add two-mode multiday timelapse support

Revision ID: 002
Revises: 001
Create Date: 2026-02-10 00:00:00.000000

Adds support for historical and prospective multiday timelapse modes.
- Historical: Generate timelapse from existing images
- Prospective: Collect images over time, then generate

Changes:
- multiday_configs: Add mode, status, collection dates, progress fields
- images: Add protected_by_config_id for prospective protection tracking
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add new columns to multiday_configs
    op.add_column(
        "multiday_configs",
        sa.Column(
            "mode",
            sa.String(20),
            nullable=False,
            server_default="historical",
            comment="Mode: 'historical' (build from existing) or 'prospective' (collect forward)",
        ),
    )
    op.add_column(
        "multiday_configs",
        sa.Column(
            "status",
            sa.String(20),
            nullable=False,
            server_default="idle",
            comment="Status: 'idle', 'collecting', 'ready', 'completed', 'failed'",
        ),
    )
    op.add_column(
        "multiday_configs",
        sa.Column(
            "collection_start_date",
            sa.Date(),
            nullable=True,
            comment="When prospective collection started",
        ),
    )
    op.add_column(
        "multiday_configs",
        sa.Column(
            "collection_end_date",
            sa.Date(),
            nullable=True,
            comment="When prospective collection ends",
        ),
    )
    op.add_column(
        "multiday_configs",
        sa.Column(
            "collection_progress_days",
            sa.Integer(),
            nullable=False,
            server_default="0",
            comment="Days collected so far for prospective mode",
        ),
    )
    op.add_column(
        "multiday_configs",
        sa.Column(
            "last_generation_at",
            sa.DateTime(timezone=True),
            nullable=True,
            comment="Last time timelapse was generated",
        ),
    )
    op.add_column(
        "multiday_configs",
        sa.Column(
            "auto_generate",
            sa.Boolean(),
            nullable=False,
            server_default="true",
            comment="Auto-generate when collection completes (prospective mode)",
        ),
    )

    # Add constraint for mode values
    op.create_check_constraint(
        "ck_multiday_mode",
        "multiday_configs",
        "mode IN ('historical', 'prospective')",
    )

    # Add constraint for status values
    op.create_check_constraint(
        "ck_multiday_status",
        "multiday_configs",
        "status IN ('idle', 'collecting', 'ready', 'completed', 'failed')",
    )

    # Add index on status for finding active collections
    op.create_index(
        "ix_multiday_configs_status",
        "multiday_configs",
        ["status"],
    )

    # Add index on collection dates for finding configs in collection period
    op.create_index(
        "idx_multiday_configs_collection_dates",
        "multiday_configs",
        ["collection_start_date", "collection_end_date"],
    )

    # Add protected_by_config_id to images table
    op.add_column(
        "images",
        sa.Column(
            "protected_by_config_id",
            postgresql.UUID(as_uuid=True),
            nullable=True,
            comment="Multiday config that protected this image for prospective collection",
        ),
    )

    # Add protection_reason column if not exists (was in model but not in 001 migration)
    # Check if column exists first
    conn = op.get_bind()
    result = conn.execute(
        sa.text(
            "SELECT column_name FROM information_schema.columns "
            "WHERE table_name='images' AND column_name='protection_reason'"
        )
    )
    if not result.fetchone():
        op.add_column(
            "images",
            sa.Column(
                "protection_reason",
                sa.String(50),
                nullable=True,
                comment="Reason for protection (multiday_timelapse, manual, prospective, etc.)",
            ),
        )

    # Add foreign key from images to multiday_configs
    op.create_foreign_key(
        "fk_images_protected_config",
        "images",
        "multiday_configs",
        ["protected_by_config_id"],
        ["id"],
        ondelete="SET NULL",
    )

    # Add index on protected_by_config_id for finding protected images
    op.create_index(
        "ix_images_protected_by_config",
        "images",
        ["protected_by_config_id"],
    )


def downgrade() -> None:
    # Remove index on images
    op.drop_index("ix_images_protected_by_config", table_name="images")

    # Remove foreign key from images
    op.drop_constraint("fk_images_protected_config", "images", type_="foreignkey")

    # Remove protected_by_config_id from images
    op.drop_column("images", "protected_by_config_id")

    # Remove indexes from multiday_configs
    op.drop_index("idx_multiday_configs_collection_dates", table_name="multiday_configs")
    op.drop_index("ix_multiday_configs_status", table_name="multiday_configs")

    # Remove constraints from multiday_configs
    op.drop_constraint("ck_multiday_status", "multiday_configs", type_="check")
    op.drop_constraint("ck_multiday_mode", "multiday_configs", type_="check")

    # Remove new columns from multiday_configs
    op.drop_column("multiday_configs", "auto_generate")
    op.drop_column("multiday_configs", "last_generation_at")
    op.drop_column("multiday_configs", "collection_progress_days")
    op.drop_column("multiday_configs", "collection_end_date")
    op.drop_column("multiday_configs", "collection_start_date")
    op.drop_column("multiday_configs", "status")
    op.drop_column("multiday_configs", "mode")
