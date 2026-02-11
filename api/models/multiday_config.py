"""
Multi-Day Configuration Model

Configuration for multi-day timelapse generation.
Supports two modes:
- Historical: Build timelapse from existing images
- Prospective: Collect images over time, then generate
"""

import uuid
from datetime import date, datetime, time
from typing import TYPE_CHECKING, Optional

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    ForeignKey,
    Index,
    Integer,
    String,
    Time,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from api.database import Base

if TYPE_CHECKING:
    from api.models.camera import Camera


class MultidayConfig(Base):
    """Multi-day timelapse configuration model."""

    __tablename__ = "multiday_configs"

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

    # Configuration
    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="Configuration name (e.g., 'Weekly Summary')",
    )
    is_enabled: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        comment="Whether this configuration is enabled",
    )

    # Mode: historical (build from existing) or prospective (collect forward)
    mode: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="historical",
        comment="Mode: 'historical' or 'prospective'",
    )

    # Status for tracking collection progress
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="idle",
        comment="Status: 'idle', 'collecting', 'ready', 'completed', 'failed'",
    )

    # Prospective collection tracking
    collection_start_date: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True,
        comment="When prospective collection started",
    )
    collection_end_date: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True,
        comment="When prospective collection ends",
    )
    collection_progress_days: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        comment="Days collected so far for prospective mode",
    )
    last_generation_at: Mapped[Optional[datetime]] = mapped_column(
        nullable=True,
        comment="Last time timelapse was generated",
    )
    auto_generate: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        comment="Auto-generate when collection completes (prospective mode)",
    )

    # Image selection
    images_per_hour: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=2,
        comment="Number of images to select per hour",
    )
    days_to_include: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=7,
        comment="Number of days to include",
    )

    # Schedule
    generation_day: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
        default="sunday",
        comment="Day to generate (monday-sunday, or day of month 1-31)",
    )
    generation_time: Mapped[time] = mapped_column(
        Time,
        nullable=False,
        default=time(2, 0, 0),
        comment="Time to generate timelapse",
    )

    # Video settings
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

    # Relationships
    camera: Mapped["Camera"] = relationship(
        "Camera",
        back_populates="multiday_configs",
    )

    # Constraints and indexes
    __table_args__ = (
        CheckConstraint(
            "images_per_hour >= 1 AND images_per_hour <= 60",
            name="ck_multiday_images_per_hour",
        ),
        CheckConstraint(
            "days_to_include >= 1 AND days_to_include <= 365",
            name="ck_multiday_days_to_include",
        ),
        CheckConstraint(
            "crf >= 0 AND crf <= 51",
            name="ck_multiday_crf",
        ),
        CheckConstraint(
            "frame_rate >= 1 AND frame_rate <= 120",
            name="ck_multiday_frame_rate",
        ),
        CheckConstraint(
            "mode IN ('historical', 'prospective')",
            name="ck_multiday_mode",
        ),
        CheckConstraint(
            "status IN ('idle', 'collecting', 'ready', 'completed', 'failed')",
            name="ck_multiday_status",
        ),
        Index("ix_multiday_configs_status", "status"),
        Index(
            "idx_multiday_configs_collection_dates",
            "collection_start_date",
            "collection_end_date",
        ),
    )

    @property
    def expected_frame_count(self) -> int:
        """Calculate expected number of frames."""
        return self.images_per_hour * 24 * self.days_to_include

    @property
    def expected_duration_seconds(self) -> float:
        """Calculate expected video duration in seconds."""
        return self.expected_frame_count / self.frame_rate

    @property
    def is_collecting(self) -> bool:
        """Check if this config is actively collecting images."""
        return self.mode == "prospective" and self.status == "collecting"

    @property
    def collection_progress_percent(self) -> float:
        """Get collection progress as percentage."""
        if self.days_to_include <= 0:
            return 0.0
        return min(100.0, (self.collection_progress_days / self.days_to_include) * 100)

    def __repr__(self) -> str:
        return f"<MultidayConfig(name='{self.name}', mode='{self.mode}', status='{self.status}')>"
