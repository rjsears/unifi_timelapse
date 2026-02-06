"""
Pydantic Schemas Package

Request/response validation schemas for the API.
"""

from api.schemas.camera import (
    CameraCreate,
    CameraUpdate,
    CameraResponse,
    CameraListResponse,
    CameraTestResponse,
)
from api.schemas.image import (
    ImageResponse,
    ImageListResponse,
    ImageProtectRequest,
)
from api.schemas.timelapse import (
    TimelapseResponse,
    TimelapseListResponse,
    TimelapseCreateRequest,
    MultidayConfigCreate,
    MultidayConfigUpdate,
    MultidayConfigResponse,
)
from api.schemas.auth import (
    LoginRequest,
    LoginResponse,
    UserResponse,
    PasswordChangeRequest,
)
from api.schemas.settings import (
    SettingResponse,
    SettingUpdate,
    NotificationConfigCreate,
    NotificationConfigUpdate,
    NotificationConfigResponse,
)

__all__ = [
    # Camera
    "CameraCreate",
    "CameraUpdate",
    "CameraResponse",
    "CameraListResponse",
    "CameraTestResponse",
    # Image
    "ImageResponse",
    "ImageListResponse",
    "ImageProtectRequest",
    # Timelapse
    "TimelapseResponse",
    "TimelapseListResponse",
    "TimelapseCreateRequest",
    "MultidayConfigCreate",
    "MultidayConfigUpdate",
    "MultidayConfigResponse",
    # Auth
    "LoginRequest",
    "LoginResponse",
    "UserResponse",
    "PasswordChangeRequest",
    # Settings
    "SettingResponse",
    "SettingUpdate",
    "NotificationConfigCreate",
    "NotificationConfigUpdate",
    "NotificationConfigResponse",
]
