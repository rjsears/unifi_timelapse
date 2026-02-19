"""
Camera Health Model

Health check records for cameras.
"""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Boolean, ForeignKey, Index, Integer, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from api.database import Base

if TYPE_CHECKING:
    from api.models.camera import Camera


class CameraHealth(Base):
    """Camera health check record."""

    __tablename__ = "camera_health"

    # Primary key
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    # Foreign keys
    camera_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("cameras.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Check timestamp
    checked_at: Mapped[datetime] = mapped_column(
        nullable=False,
        index=True,
        comment="When the check was performed",
    )

    # Connectivity
    is_reachable: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        comment="Whether camera responded to HTTP request",
    )
    response_time_ms: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        comment="Response time in milliseconds",
    )

    # Image quality
    is_image_blank: Mapped[Optional[bool]] = mapped_column(
        Boolean,
        nullable=True,
        comment="Whether captured image appears blank",
    )
    is_image_frozen: Mapped[Optional[bool]] = mapped_column(
        Boolean,
        nullable=True,
        comment="Whether image is same as previous (frozen)",
    )

    # Error tracking
    error_message: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Error message if check failed",
    )

    # Record timestamp
    created_at: Mapped[datetime] = mapped_column(
        nullable=False,
        server_default=func.now(),
    )

    # Relationships
    camera: Mapped["Camera"] = relationship(
        "Camera",
        back_populates="health_records",
    )

    # Indexes
    __table_args__ = (Index("idx_camera_health_camera_checked", "camera_id", "checked_at"),)

    @property
    def is_healthy(self) -> bool:
        """Check if the camera is considered healthy."""
        if not self.is_reachable:
            return False
        if self.is_image_blank:
            return False
        if self.is_image_frozen:
            return False
        return True

    def __repr__(self) -> str:
        return f"<CameraHealth(camera_id={self.camera_id}, healthy={self.is_healthy})>"
