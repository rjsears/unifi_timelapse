"""
Camera Model

Represents a camera that can be captured for timelapse.
"""

import uuid
from datetime import datetime, time
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import Boolean, CheckConstraint, Integer, String, Time, func
from sqlalchemy.dialects.postgresql import INET, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from api.database import Base

if TYPE_CHECKING:
    from api.models.image import Image
    from api.models.timelapse import Timelapse
    from api.models.multiday_config import MultidayConfig
    from api.models.camera_health import CameraHealth


class Camera(Base):
    """Camera model for timelapse capture."""

    __tablename__ = "cameras"

    # Primary key
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    # Camera identification
    name: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False,
        index=True,
        comment="Unique camera name (used in filenames)",
    )
    hostname: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        comment="Camera hostname",
    )
    ip_address: Mapped[Optional[str]] = mapped_column(
        INET,
        nullable=True,
        comment="Camera IP address",
    )

    # Capture settings
    capture_interval: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=30,
        comment="Seconds between captures",
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        comment="Whether capture is enabled",
    )

    # Blackout period (no captures during this time)
    blackout_start: Mapped[Optional[time]] = mapped_column(
        Time,
        nullable=True,
        comment="Start of blackout period",
    )
    blackout_end: Mapped[Optional[time]] = mapped_column(
        Time,
        nullable=True,
        comment="End of blackout period",
    )

    # Timelapse settings
    timelapse_enabled: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        comment="Whether to create timelapses",
    )
    timelapse_time: Mapped[time] = mapped_column(
        Time,
        nullable=False,
        default=time(1, 0, 0),
        comment="Time to generate daily timelapse",
    )

    # Status tracking
    last_capture_at: Mapped[Optional[datetime]] = mapped_column(
        nullable=True,
        comment="Last successful capture time",
    )
    last_capture_status: Mapped[Optional[str]] = mapped_column(
        String(20),
        nullable=True,
        comment="Last capture status (success/failed)",
    )
    consecutive_errors: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        comment="Count of consecutive capture failures",
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
    images: Mapped[List["Image"]] = relationship(
        "Image",
        back_populates="camera",
        cascade="all, delete-orphan",
    )
    timelapses: Mapped[List["Timelapse"]] = relationship(
        "Timelapse",
        back_populates="camera",
        cascade="all, delete-orphan",
    )
    multiday_configs: Mapped[List["MultidayConfig"]] = relationship(
        "MultidayConfig",
        back_populates="camera",
        cascade="all, delete-orphan",
    )
    health_records: Mapped[List["CameraHealth"]] = relationship(
        "CameraHealth",
        back_populates="camera",
        cascade="all, delete-orphan",
    )

    # Constraints
    __table_args__ = (
        CheckConstraint(
            "(hostname IS NOT NULL) OR (ip_address IS NOT NULL)",
            name="ck_camera_hostname_or_ip",
        ),
        CheckConstraint(
            "(capture_interval >= 10) AND (capture_interval <= 3600)",
            name="ck_camera_capture_interval",
        ),
    )

    @property
    def url(self) -> str:
        """Get the camera snapshot URL."""
        host = self.hostname or str(self.ip_address)
        return f"http://{host}/snap.jpeg"

    def is_in_blackout(self, check_time: Optional[time] = None) -> bool:
        """Check if the given time is within the blackout period."""
        if not self.blackout_start or not self.blackout_end:
            return False

        if check_time is None:
            check_time = datetime.now().time()

        # Handle overnight blackout (e.g., 22:00 to 06:00)
        if self.blackout_start > self.blackout_end:
            return check_time >= self.blackout_start or check_time <= self.blackout_end
        else:
            return self.blackout_start <= check_time <= self.blackout_end

    def __repr__(self) -> str:
        return f"<Camera(name='{self.name}', active={self.is_active})>"
