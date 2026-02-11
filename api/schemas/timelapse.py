"""
Timelapse Schemas

Pydantic schemas for timelapse API endpoints.
"""

from datetime import date, datetime, time
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class TimelapseResponse(BaseModel):
    """Schema for timelapse response."""

    id: UUID
    camera_id: UUID
    type: str
    date_start: date
    date_end: date
    file_path: Optional[str]
    file_size: Optional[int]
    frame_count: Optional[int]
    frame_rate: int
    crf: int
    pixel_format: str
    duration_seconds: Optional[float]
    status: str
    error_message: Optional[str]
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    created_at: datetime
    days_covered: int
    filename: str

    model_config = {"from_attributes": True}


class TimelapseListResponse(BaseModel):
    """Schema for timelapse list response."""

    timelapses: List[TimelapseResponse]
    total: int
    page: int = 1
    per_page: int = 50


class TimelapseCreateRequest(BaseModel):
    """Schema for triggering timelapse creation."""

    date_start: Optional[date] = Field(
        None,
        description="Start date (defaults to yesterday)",
    )
    date_end: Optional[date] = Field(
        None,
        description="End date (defaults to start date)",
    )
    frame_rate: Optional[int] = Field(None, ge=1, le=120)
    crf: Optional[int] = Field(None, ge=0, le=51)
    pixel_format: Optional[str] = Field(None)


class MultidayConfigBase(BaseModel):
    """Base schema for multi-day configuration."""

    name: str = Field(..., min_length=1, max_length=100)
    is_enabled: bool = Field(True)
    images_per_hour: int = Field(2, ge=1, le=60)
    days_to_include: int = Field(7, ge=1, le=365)
    generation_day: str = Field("sunday")
    generation_time: time = Field(default=time(2, 0, 0))
    frame_rate: int = Field(30, ge=1, le=120)
    crf: int = Field(20, ge=0, le=51)
    pixel_format: str = Field("yuv444p")
    mode: str = Field("historical", pattern="^(historical|prospective)$")
    auto_generate: bool = Field(True)


class MultidayConfigCreate(MultidayConfigBase):
    """Schema for creating multi-day configuration."""

    camera_id: UUID


class MultidayConfigUpdate(BaseModel):
    """Schema for updating multi-day configuration."""

    name: Optional[str] = Field(None, min_length=1, max_length=100)
    is_enabled: Optional[bool] = None
    images_per_hour: Optional[int] = Field(None, ge=1, le=60)
    days_to_include: Optional[int] = Field(None, ge=1, le=365)
    generation_day: Optional[str] = None
    generation_time: Optional[time] = None
    frame_rate: Optional[int] = Field(None, ge=1, le=120)
    crf: Optional[int] = Field(None, ge=0, le=51)
    pixel_format: Optional[str] = None
    mode: Optional[str] = Field(None, pattern="^(historical|prospective)$")
    auto_generate: Optional[bool] = None


class MultidayConfigResponse(MultidayConfigBase):
    """Schema for multi-day configuration response."""

    id: UUID
    camera_id: UUID
    created_at: datetime
    updated_at: datetime
    expected_frame_count: int
    expected_duration_seconds: float
    status: str
    collection_start_date: Optional[date] = None
    collection_end_date: Optional[date] = None
    collection_progress_days: int = 0
    collection_progress_percent: float = 0.0
    last_generation_at: Optional[datetime] = None
    is_collecting: bool = False

    model_config = {"from_attributes": True}


# ============ Available Dates Schemas ============


class DateImageCount(BaseModel):
    """Schema for date with image count."""

    date: date
    image_count: int
    protected_count: int


class AvailableDatesResponse(BaseModel):
    """Schema for available dates response."""

    dates: List[DateImageCount]
    oldest_date: Optional[date] = None
    newest_date: Optional[date] = None
    total_images: int


# ============ Historical Generation Schemas ============


class HistoricalGenerateRequest(BaseModel):
    """Schema for generating historical timelapse from existing images."""

    camera_id: UUID
    start_date: date
    end_date: date
    images_per_hour: int = Field(2, ge=1, le=60)
    frame_rate: int = Field(30, ge=1, le=120)
    crf: int = Field(20, ge=0, le=51)
    pixel_format: str = Field("yuv444p")


class HistoricalGenerateResponse(BaseModel):
    """Schema for historical generation response."""

    timelapse_id: UUID
    message: str
    estimated_frames: int


# ============ Prospective Collection Schemas ============


class StartCollectionRequest(BaseModel):
    """Schema for starting prospective collection."""

    days_to_collect: int = Field(..., ge=1, le=365)


class CollectionProgressResponse(BaseModel):
    """Schema for collection progress response."""

    config_id: UUID
    status: str
    mode: str
    days_to_collect: int
    days_collected: int
    progress_percent: float
    collection_start_date: Optional[date] = None
    collection_end_date: Optional[date] = None
    protected_images_count: int
    auto_generate: bool


class CancelCollectionRequest(BaseModel):
    """Schema for cancelling prospective collection."""

    unprotect_images: bool = Field(
        False,
        description="Whether to remove protection from collected images",
    )
