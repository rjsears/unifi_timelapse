"""
Cleanup Log Model

Logs of cleanup operations.
"""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import BigInteger, ForeignKey, Integer, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from api.database import Base

if TYPE_CHECKING:
    from api.models.camera import Camera


class CleanupLog(Base):
    """Cleanup operation log."""

    __tablename__ = "cleanup_logs"

    # Primary key
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    # Cleanup type
    type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="Cleanup type: images, videos, orphans",
    )

    # Optional camera association
    camera_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("cameras.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # Statistics
    files_deleted: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        comment="Number of files deleted",
    )
    bytes_freed: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
        default=0,
        comment="Bytes freed by cleanup",
    )
    protected_skipped: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        comment="Protected files skipped",
    )

    # Execution time
    executed_at: Mapped[datetime] = mapped_column(
        nullable=False,
        comment="When cleanup was executed",
    )

    # Record timestamp
    created_at: Mapped[datetime] = mapped_column(
        nullable=False,
        server_default=func.now(),
    )

    # Relationships
    camera: Mapped[Optional["Camera"]] = relationship("Camera")

    @property
    def bytes_freed_mb(self) -> float:
        """Get bytes freed in megabytes."""
        return self.bytes_freed / (1024 * 1024)

    def __repr__(self) -> str:
        return f"<CleanupLog(type='{self.type}', files_deleted={self.files_deleted})>"
