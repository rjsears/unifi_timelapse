"""
Timelapse Model

Represents a generated timelapse video.
"""

import uuid
from datetime import date, datetime
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    Date,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from api.database import Base

if TYPE_CHECKING:
    from api.models.camera import Camera
    from api.models.image import Image


class Timelapse(Base):
    """Timelapse model for generated videos."""

    __tablename__ = "timelapses"

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

    # Timelapse type and date range
    type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="daily",
        comment="Timelapse type: daily or multiday",
    )
    date_start: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        comment="Start date of timelapse",
    )
    date_end: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        comment="End date of timelapse",
    )

    # Output file
    file_path: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
        comment="Output video path",
    )
    file_size: Mapped[Optional[int]] = mapped_column(
        BigInteger,
        nullable=True,
        comment="Video file size in bytes",
    )

    # Video metadata
    frame_count: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        comment="Number of frames used",
    )
    frame_rate: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=30,
        comment="Output frame rate",
    )
    crf: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=20,
        comment="CRF quality setting",
    )
    pixel_format: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="yuv444p",
        comment="Pixel format",
    )
    duration_seconds: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
        comment="Video duration in seconds",
    )

    # Status
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="pending",
        index=True,
        comment="Status: pending, processing, completed, failed",
    )
    error_message: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Error message if failed",
    )

    # Processing timestamps
    started_at: Mapped[Optional[datetime]] = mapped_column(
        nullable=True,
        comment="Processing start time",
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        nullable=True,
        comment="Processing completion time",
    )

    # Record timestamps
    created_at: Mapped[datetime] = mapped_column(
        nullable=False,
        server_default=func.now(),
    )

    # Relationships
    camera: Mapped["Camera"] = relationship(
        "Camera",
        back_populates="timelapses",
    )
    images: Mapped[List["Image"]] = relationship(
        "Image",
        back_populates="timelapse",
        foreign_keys="Image.included_in_timelapse_id",
    )

    # Constraints
    __table_args__ = (
        UniqueConstraint(
            "camera_id",
            "type",
            "date_start",
            "date_end",
            name="uq_timelapse_camera_type_dates",
        ),
        CheckConstraint(
            "type IN ('daily', 'multiday')",
            name="ck_timelapse_type",
        ),
        CheckConstraint(
            "crf >= 0 AND crf <= 51",
            name="ck_timelapse_crf",
        ),
        CheckConstraint(
            "frame_rate >= 1 AND frame_rate <= 120",
            name="ck_timelapse_frame_rate",
        ),
        CheckConstraint(
            "status IN ('pending', 'processing', 'completed', 'failed')",
            name="ck_timelapse_status",
        ),
        Index("idx_timelapse_camera_dates", "camera_id", "date_start", "date_end"),
    )

    @property
    def is_daily(self) -> bool:
        """Check if this is a daily timelapse."""
        return self.type == "daily"

    @property
    def is_multiday(self) -> bool:
        """Check if this is a multi-day timelapse."""
        return self.type == "multiday"

    @property
    def days_covered(self) -> int:
        """Calculate the number of days covered."""
        return (self.date_end - self.date_start).days + 1

    @property
    def filename(self) -> str:
        """Get just the filename from the path."""
        if self.file_path:
            return self.file_path.split("/")[-1]
        return ""

    def __repr__(self) -> str:
        return (
            f"<Timelapse(camera_id={self.camera_id}, type='{self.type}', status='{self.status}')>"
        )
