"""
System Settings Model

Key-value storage for application settings.
"""

import uuid
from datetime import datetime
from typing import Any, Optional

from sqlalchemy import String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from api.database import Base


class SystemSettings(Base):
    """System settings key-value store."""

    __tablename__ = "settings"

    # Primary key
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    # Key-value
    key: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False,
        index=True,
        comment="Setting key",
    )
    value: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="Setting value (JSON for complex types)",
    )

    # Metadata
    type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="string",
        comment="Value type: string, integer, boolean, json",
    )
    category: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="general",
        comment="Setting category for grouping",
    )
    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Human-readable description",
    )

    # Timestamps
    updated_at: Mapped[datetime] = mapped_column(
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    def get_typed_value(self) -> Any:
        """Get the value with proper type conversion."""
        import json

        if self.type == "integer":
            return int(self.value)
        elif self.type == "boolean":
            return self.value.lower() in ("true", "1", "yes")
        elif self.type == "json":
            return json.loads(self.value)
        else:
            return self.value

    def set_typed_value(self, value: Any) -> None:
        """Set the value with proper type conversion."""
        import json

        if self.type == "integer":
            self.value = str(int(value))
        elif self.type == "boolean":
            self.value = "true" if value else "false"
        elif self.type == "json":
            self.value = json.dumps(value)
        else:
            self.value = str(value)

    def __repr__(self) -> str:
        return f"<SystemSettings(key='{self.key}', type='{self.type}')>"
