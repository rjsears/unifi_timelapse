"""
Camera Schemas

Pydantic schemas for camera API endpoints.
"""

from datetime import datetime, time
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator, model_validator


class CameraBase(BaseModel):
    """Base camera schema with shared fields."""

    name: str = Field(..., min_length=1, max_length=100, description="Unique camera name")
    hostname: Optional[str] = Field(None, max_length=255, description="Camera hostname")
    ip_address: Optional[str] = Field(None, description="Camera IP address")
    capture_interval: int = Field(30, ge=10, le=3600, description="Capture interval in seconds")
    is_active: bool = Field(True, description="Whether capture is enabled")
    blackout_start: Optional[time] = Field(None, description="Blackout period start")
    blackout_end: Optional[time] = Field(None, description="Blackout period end")
    timelapse_enabled: bool = Field(True, description="Whether to create timelapses")
    timelapse_time: time = Field(default=time(1, 0, 0), description="Daily timelapse time")

    @model_validator(mode="after")
    def validate_hostname_or_ip(self) -> "CameraBase":
        """Ensure at least hostname or IP is provided."""
        if not self.hostname and not self.ip_address:
            raise ValueError("Either hostname or ip_address must be provided")
        return self

    @field_validator("ip_address")
    @classmethod
    def validate_ip_address(cls, v: Optional[str]) -> Optional[str]:
        """Validate IP address format."""
        if v is None:
            return v
        import ipaddress

        try:
            ipaddress.ip_address(v)
        except ValueError:
            raise ValueError("Invalid IP address format")
        return v


class CameraCreate(CameraBase):
    """Schema for creating a camera."""

    pass


class CameraUpdate(BaseModel):
    """Schema for updating a camera."""

    name: Optional[str] = Field(None, min_length=1, max_length=100)
    hostname: Optional[str] = Field(None, max_length=255)
    ip_address: Optional[str] = Field(None)
    capture_interval: Optional[int] = Field(None, ge=10, le=3600)
    is_active: Optional[bool] = None
    blackout_start: Optional[time] = None
    blackout_end: Optional[time] = None
    timelapse_enabled: Optional[bool] = None
    timelapse_time: Optional[time] = None

    @field_validator("ip_address")
    @classmethod
    def validate_ip_address(cls, v: Optional[str]) -> Optional[str]:
        """Validate IP address format."""
        if v is None:
            return v
        import ipaddress

        try:
            ipaddress.ip_address(v)
        except ValueError:
            raise ValueError("Invalid IP address format")
        return v


class CameraResponse(BaseModel):
    """Schema for camera response."""

    id: UUID
    name: str
    hostname: Optional[str]
    ip_address: Optional[str]
    capture_interval: int
    is_active: bool
    blackout_start: Optional[time]
    blackout_end: Optional[time]
    timelapse_enabled: bool
    timelapse_time: time
    last_capture_at: Optional[datetime]
    last_capture_status: Optional[str]
    consecutive_errors: int
    created_at: datetime
    updated_at: datetime
    url: str
    image_count: int = 0
    timelapse_count: int = 0

    model_config = {"from_attributes": True}


class CameraListResponse(BaseModel):
    """Schema for camera list response."""

    cameras: List[CameraResponse]
    total: int


class CameraTestResponse(BaseModel):
    """Schema for camera connectivity test response."""

    success: bool
    response_time_ms: Optional[int] = None
    error: Optional[str] = None
    image_size: Optional[int] = None
    image_dimensions: Optional[str] = None
