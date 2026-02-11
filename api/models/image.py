"""
Image Model

Represents a captured image from a camera.
"""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import BigInteger, Boolean, ForeignKey, Index, Integer, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from api.database import Base

if TYPE_CHECKING:
    from api.models.camera import Camera
    from api.models.multiday_config import MultidayConfig
    from api.models.timelapse import Timelapse


class Image(Base):
    """Image model for captured camera snapshots."""

    __tablename__ = "images"

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

    # Image metadata
    captured_at: Mapped[datetime] = mapped_column(
        nullable=False,
        index=True,
        comment="When the image was captured",
    )
    file_path: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
        comment="Relative path from output root",
    )
    file_size: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
        comment="File size in bytes",
    )
    width: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        comment="Image width in pixels",
    )
    height: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        comment="Image height in pixels",
    )

    # Protection (for multi-day timelapses)
    is_protected: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        index=True,
        comment="Protected from cleanup",
    )
    protection_reason: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        comment="Reason for protection (multiday_timelapse, manual, etc.)",
    )

    # Timelapse association
    included_in_timelapse_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("timelapses.id", ondelete="SET NULL"),
        nullable=True,
        comment="Timelapse this image was used in",
    )

    # Prospective collection protection
    protected_by_config_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("multiday_configs.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="Multiday config that protected this image for prospective collection",
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        nullable=False,
        server_default=func.now(),
    )

    # Relationships
    camera: Mapped["Camera"] = relationship(
        "Camera",
        back_populates="images",
    )
    timelapse: Mapped[Optional["Timelapse"]] = relationship(
        "Timelapse",
        back_populates="images",
        foreign_keys=[included_in_timelapse_id],
    )
    protected_by_config: Mapped[Optional["MultidayConfig"]] = relationship(
        "MultidayConfig",
        foreign_keys=[protected_by_config_id],
    )

    # Indexes for common queries
    __table_args__ = (
        Index("idx_images_camera_captured", "camera_id", "captured_at"),
        Index(
            "idx_images_camera_date",
            "camera_id",
            func.date(captured_at),
        ),
        Index("idx_images_protected", "is_protected"),
    )

    @property
    def date(self) -> str:
        """Get the date portion as YYYYMMDD string."""
        return self.captured_at.strftime("%Y%m%d")

    @property
    def filename(self) -> str:
        """Get just the filename from the path."""
        return self.file_path.split("/")[-1]

    def __repr__(self) -> str:
        return f"<Image(camera_id={self.camera_id}, captured_at='{self.captured_at}')>"
