"""
Image Schemas

Pydantic schemas for image API endpoints.
"""

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class ImageResponse(BaseModel):
    """Schema for image response."""

    id: UUID
    camera_id: UUID
    captured_at: datetime
    file_path: str
    file_size: int
    width: Optional[int]
    height: Optional[int]
    is_protected: bool
    protection_reason: Optional[str]
    included_in_timelapse_id: Optional[UUID]
    created_at: datetime
    filename: str
    date: str

    model_config = {"from_attributes": True}


class ImageListResponse(BaseModel):
    """Schema for image list response."""

    images: List[ImageResponse]
    total: int
    page: int = 1
    per_page: int = 50


class ImageProtectRequest(BaseModel):
    """Schema for protecting/unprotecting an image."""

    is_protected: bool = Field(..., description="Whether to protect the image")
    reason: Optional[str] = Field(
        None,
        max_length=50,
        description="Reason for protection",
    )


class ImageStats(BaseModel):
    """Schema for image statistics."""

    total_images: int
    total_size_bytes: int
    protected_count: int
    oldest_image: Optional[datetime]
    newest_image: Optional[datetime]
    images_today: int
    size_by_camera: dict[str, int]
