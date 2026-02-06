"""
Database Models Package

All SQLAlchemy models for the UniFi Timelapse System.
"""

from api.database import Base

from api.models.camera import Camera
from api.models.image import Image
from api.models.timelapse import Timelapse
from api.models.multiday_config import MultidayConfig
from api.models.user import User
from api.models.settings import SystemSettings
from api.models.camera_health import CameraHealth
from api.models.notification_config import NotificationConfig
from api.models.cleanup_log import CleanupLog

__all__ = [
    "Base",
    "Camera",
    "Image",
    "Timelapse",
    "MultidayConfig",
    "User",
    "SystemSettings",
    "CameraHealth",
    "NotificationConfig",
    "CleanupLog",
]
