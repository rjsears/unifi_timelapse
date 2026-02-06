"""Initial database schema

Revision ID: 001
Revises:
Create Date: 2024-01-01 00:00:00.000000

Creates all tables for the UniFi Timelapse System.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Users table
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("username", sa.String(50), nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("is_admin", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
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
        sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("username"),
    )
    op.create_index("ix_users_username", "users", ["username"])

    # Cameras table
    op.create_table(
        "cameras",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("hostname", sa.String(255), nullable=True),
        sa.Column("ip_address", postgresql.INET(), nullable=True),
        sa.Column("capture_interval", sa.Integer(), nullable=False, server_default="30"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("blackout_start", sa.Time(), nullable=True),
        sa.Column("blackout_end", sa.Time(), nullable=True),
        sa.Column("timelapse_enabled", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("timelapse_time", sa.Time(), nullable=False, server_default="01:00:00"),
        sa.Column("last_capture_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_capture_status", sa.String(20), nullable=True),
        sa.Column("consecutive_errors", sa.Integer(), nullable=False, server_default="0"),
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
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
        sa.CheckConstraint(
            "(hostname IS NOT NULL) OR (ip_address IS NOT NULL)",
            name="ck_camera_hostname_or_ip",
        ),
        sa.CheckConstraint(
            "(capture_interval >= 10) AND (capture_interval <= 3600)",
            name="ck_camera_capture_interval",
        ),
    )
    op.create_index("ix_cameras_name", "cameras", ["name"])

    # Images table
    op.create_table(
        "images",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("camera_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("captured_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("file_path", sa.String(500), nullable=False),
        sa.Column("file_size", sa.Integer(), nullable=True),
        sa.Column("width", sa.Integer(), nullable=True),
        sa.Column("height", sa.Integer(), nullable=True),
        sa.Column("is_protected", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("included_in_timelapse_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["camera_id"], ["cameras.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_images_camera_id", "images", ["camera_id"])
    op.create_index("ix_images_captured_at", "images", ["captured_at"])
    op.create_index(
        "idx_images_camera_captured",
        "images",
        ["camera_id", "captured_at"],
    )

    # Timelapses table
    op.create_table(
        "timelapses",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("camera_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("type", sa.String(20), nullable=False),
        sa.Column("date_start", sa.Date(), nullable=False),
        sa.Column("date_end", sa.Date(), nullable=False),
        sa.Column("frame_rate", sa.Integer(), nullable=False, server_default="30"),
        sa.Column("crf", sa.Integer(), nullable=False, server_default="20"),
        sa.Column("pixel_format", sa.String(20), nullable=False, server_default="yuv444p"),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("file_path", sa.String(500), nullable=True),
        sa.Column("file_size", sa.Integer(), nullable=True),
        sa.Column("frame_count", sa.Integer(), nullable=True),
        sa.Column("duration_seconds", sa.Float(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["camera_id"], ["cameras.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint(
            "type IN ('daily', 'multiday')",
            name="ck_timelapse_type",
        ),
        sa.CheckConstraint(
            "status IN ('pending', 'processing', 'completed', 'failed')",
            name="ck_timelapse_status",
        ),
    )
    op.create_index("ix_timelapses_camera_id", "timelapses", ["camera_id"])
    op.create_index("ix_timelapses_status", "timelapses", ["status"])
    op.create_index(
        "idx_timelapses_camera_dates",
        "timelapses",
        ["camera_id", "date_start", "date_end"],
    )

    # Add FK from images to timelapses (after timelapses table exists)
    op.create_foreign_key(
        "fk_images_timelapse",
        "images",
        "timelapses",
        ["included_in_timelapse_id"],
        ["id"],
        ondelete="SET NULL",
    )

    # Multiday configs table
    op.create_table(
        "multiday_configs",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("camera_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("is_enabled", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("images_per_hour", sa.Integer(), nullable=False, server_default="2"),
        sa.Column("days_to_include", sa.Integer(), nullable=False, server_default="7"),
        sa.Column("generation_day", sa.String(10), nullable=False, server_default="sunday"),
        sa.Column("generation_time", sa.Time(), nullable=False, server_default="02:00:00"),
        sa.Column("frame_rate", sa.Integer(), nullable=False, server_default="30"),
        sa.Column("crf", sa.Integer(), nullable=False, server_default="20"),
        sa.Column("pixel_format", sa.String(20), nullable=False, server_default="yuv444p"),
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
        sa.ForeignKeyConstraint(
            ["camera_id"], ["cameras.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint(
            "images_per_hour >= 1 AND images_per_hour <= 60",
            name="ck_multiday_images_per_hour",
        ),
        sa.CheckConstraint(
            "days_to_include >= 1 AND days_to_include <= 365",
            name="ck_multiday_days_to_include",
        ),
        sa.CheckConstraint(
            "crf >= 0 AND crf <= 51",
            name="ck_multiday_crf",
        ),
        sa.CheckConstraint(
            "frame_rate >= 1 AND frame_rate <= 120",
            name="ck_multiday_frame_rate",
        ),
    )
    op.create_index("ix_multiday_configs_camera_id", "multiday_configs", ["camera_id"])

    # Camera health table
    op.create_table(
        "camera_health",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("camera_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("checked_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("is_reachable", sa.Boolean(), nullable=False),
        sa.Column("response_time_ms", sa.Integer(), nullable=True),
        sa.Column("is_image_blank", sa.Boolean(), nullable=True),
        sa.Column("is_image_frozen", sa.Boolean(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["camera_id"], ["cameras.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_camera_health_camera_id", "camera_health", ["camera_id"])
    op.create_index("ix_camera_health_checked_at", "camera_health", ["checked_at"])
    op.create_index(
        "idx_camera_health_camera_checked",
        "camera_health",
        ["camera_id", "checked_at"],
    )

    # Notification configs table
    op.create_table(
        "notification_configs",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("apprise_url", sa.String(500), nullable=False),
        sa.Column("is_enabled", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("notify_on_capture_fail", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("notify_on_timelapse_done", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("notify_on_camera_down", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("notify_on_storage_warn", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("min_failures_before_alert", sa.Integer(), nullable=False, server_default="3"),
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
        sa.PrimaryKeyConstraint("id"),
    )

    # System settings table
    op.create_table(
        "system_settings",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("key", sa.String(100), nullable=False),
        sa.Column("value", sa.Text(), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
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
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("key"),
    )
    op.create_index("ix_system_settings_key", "system_settings", ["key"])

    # Cleanup logs table
    op.create_table(
        "cleanup_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("type", sa.String(50), nullable=False),
        sa.Column("camera_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("files_deleted", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("bytes_freed", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("protected_skipped", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("executed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["camera_id"], ["cameras.id"], ondelete="SET NULL"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_cleanup_logs_type", "cleanup_logs", ["type"])
    op.create_index("ix_cleanup_logs_executed_at", "cleanup_logs", ["executed_at"])


def downgrade() -> None:
    op.drop_table("cleanup_logs")
    op.drop_table("system_settings")
    op.drop_table("notification_configs")
    op.drop_table("camera_health")
    op.drop_table("multiday_configs")
    op.drop_constraint("fk_images_timelapse", "images", type_="foreignkey")
    op.drop_table("timelapses")
    op.drop_table("images")
    op.drop_table("cameras")
    op.drop_table("users")
