"""
Notification Configuration Model

Configuration for Apprise notifications.
"""

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from api.database import Base


class NotificationConfig(Base):
    """Notification configuration model."""

    __tablename__ = "notification_configs"

    # Primary key
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    # Configuration
    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="Configuration name",
    )
    apprise_url: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="Apprise notification URL",
    )

    # Status
    is_enabled: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        comment="Whether notifications are enabled",
    )

    # Notification types
    notify_on_capture_fail: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        comment="Alert on capture failures",
    )
    notify_on_timelapse_done: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        comment="Alert when timelapse is complete",
    )
    notify_on_storage_warn: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        comment="Alert on low storage",
    )
    notify_on_camera_down: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        comment="Alert when camera is unreachable",
    )

    # Alert thresholds
    min_failures_before_alert: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=3,
        comment="Consecutive failures before alerting",
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        nullable=False,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    def __repr__(self) -> str:
        return f"<NotificationConfig(name='{self.name}', enabled={self.is_enabled})>"
