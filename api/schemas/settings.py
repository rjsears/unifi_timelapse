"""
Settings Schemas

Pydantic schemas for settings and notification endpoints.
"""

from datetime import datetime
from typing import Any, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class SettingResponse(BaseModel):
    """Schema for setting response."""

    id: UUID
    key: str
    value: Any
    type: str
    category: str
    description: Optional[str]
    updated_at: datetime

    model_config = {"from_attributes": True}


class SettingUpdate(BaseModel):
    """Schema for updating a setting."""

    value: Any = Field(..., description="New value for the setting")


class SettingsListResponse(BaseModel):
    """Schema for settings list response."""

    settings: List[SettingResponse]
    categories: List[str]


class NotificationConfigBase(BaseModel):
    """Base schema for notification configuration."""

    name: str = Field(..., min_length=1, max_length=100)
    apprise_url: str = Field(..., min_length=1)
    is_enabled: bool = Field(True)
    notify_on_capture_fail: bool = Field(True)
    notify_on_timelapse_done: bool = Field(False)
    notify_on_storage_warn: bool = Field(True)
    notify_on_camera_down: bool = Field(True)
    min_failures_before_alert: int = Field(3, ge=1, le=100)


class NotificationConfigCreate(NotificationConfigBase):
    """Schema for creating notification configuration."""

    pass


class NotificationConfigUpdate(BaseModel):
    """Schema for updating notification configuration."""

    name: Optional[str] = Field(None, min_length=1, max_length=100)
    apprise_url: Optional[str] = Field(None, min_length=1)
    is_enabled: Optional[bool] = None
    notify_on_capture_fail: Optional[bool] = None
    notify_on_timelapse_done: Optional[bool] = None
    notify_on_storage_warn: Optional[bool] = None
    notify_on_camera_down: Optional[bool] = None
    min_failures_before_alert: Optional[int] = Field(None, ge=1, le=100)


class NotificationConfigResponse(NotificationConfigBase):
    """Schema for notification configuration response."""

    id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class SystemInfoResponse(BaseModel):
    """Schema for system information response."""

    version: str
    uptime_seconds: float
    python_version: str
    database_connected: bool
    redis_connected: bool
    cameras_count: int
    images_count: int
    timelapses_count: int


class StorageInfoResponse(BaseModel):
    """Schema for storage information response."""

    total_bytes: int
    used_bytes: int
    free_bytes: int
    percent_used: float
    images_size_bytes: int
    videos_size_bytes: int
    images_count: int
    videos_count: int


class HealthCheckResponse(BaseModel):
    """Schema for health check response."""

    status: str
    database: bool
    redis: bool
    timestamp: datetime


class CameraHealthResponse(BaseModel):
    """Schema for camera health status."""

    camera_id: UUID
    camera_name: str
    is_reachable: bool
    response_time_ms: Optional[int]
    is_image_blank: Optional[bool]
    is_image_frozen: Optional[bool]
    last_check: Optional[datetime]
    consecutive_failures: int
    is_healthy: bool


class CameraHealthHistoryResponse(BaseModel):
    """Schema for camera health history."""

    camera_id: UUID
    checks: List[dict]
    uptime_percent: float
    avg_response_time_ms: Optional[float]
