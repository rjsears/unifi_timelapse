"""
Application Configuration

Pydantic settings management for the UniFi Timelapse System.
All configuration is loaded from environment variables.
"""

from functools import lru_cache

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Database
    database_url: str = Field(
        default="postgresql+asyncpg://timelapse:timelapse@localhost:5432/timelapse",
        description="PostgreSQL connection URL",
    )

    # Redis
    redis_host: str = Field(default="redis", description="Redis host")
    redis_port: int = Field(default=6379, description="Redis port")

    # Security
    secret_key: str = Field(
        default="change-me-in-production",
        description="Secret key for JWT signing",
    )
    admin_username: str = Field(default="admin", description="Admin username")
    admin_password: str = Field(default="changeme", description="Admin password")
    jwt_expiration_hours: int = Field(default=24, description="JWT token expiration in hours")

    # Application
    debug: bool = Field(default=False, description="Debug mode")
    log_level: str = Field(default="INFO", description="Logging level")
    tz: str = Field(default="America/Los_Angeles", description="Timezone")

    # Storage paths
    output_base_path: str = Field(default="/output", description="Base path for output files")
    images_subpath: str = Field(default="unifi/images", description="Subdirectory for images")
    videos_subpath: str = Field(default="unifi/videos", description="Subdirectory for videos")

    # Capture defaults
    default_capture_interval: int = Field(
        default=30, ge=10, le=3600, description="Default capture interval in seconds"
    )
    max_concurrent_captures: int = Field(
        default=50, ge=1, le=200, description="Maximum concurrent camera captures"
    )
    capture_timeout: int = Field(default=30, ge=5, le=120, description="Capture timeout in seconds")
    capture_retries: int = Field(default=3, ge=0, le=10, description="Number of capture retries")

    # Timelapse defaults
    default_frame_rate: int = Field(
        default=30, ge=1, le=120, description="Default video frame rate"
    )
    default_crf: int = Field(default=20, ge=0, le=51, description="Default CRF (quality)")
    default_pixel_format: str = Field(default="yuv444p", description="Default pixel format")
    ffmpeg_timeout: int = Field(default=14400, ge=60, description="FFMPEG timeout in seconds")
    daily_timelapse_time: str = Field(
        default="01:00", description="Time to generate daily timelapse (HH:MM)"
    )

    # Multi-day timelapse defaults
    multiday_images_per_hour: int = Field(
        default=2, ge=1, le=60, description="Images per hour for multi-day timelapse"
    )
    multiday_days_to_include: int = Field(
        default=7, ge=1, le=365, description="Days to include in multi-day timelapse"
    )
    multiday_generation_day: str = Field(
        default="sunday", description="Day to generate multi-day timelapse"
    )
    multiday_generation_time: str = Field(
        default="02:00", description="Time to generate multi-day timelapse (HH:MM)"
    )

    # Cleanup
    cleanup_after_timelapse: bool = Field(
        default=False,
        description="Delete images after timelapse creation (deprecated - use retention instead)",
    )
    retention_days_images: int = Field(default=7, ge=1, description="Days to retain images")
    retention_days_videos: int = Field(default=365, ge=1, description="Days to retain videos")
    cleanup_time: str = Field(default="03:00", description="Time to run cleanup (HH:MM)")

    # Health monitor
    health_check_interval: int = Field(
        default=60, ge=10, description="Camera health check interval in seconds"
    )
    blank_check_interval: int = Field(
        default=300, ge=60, description="Blank image check interval in seconds"
    )
    frozen_check_interval: int = Field(
        default=300, ge=60, description="Frozen image check interval in seconds"
    )
    blank_threshold: float = Field(
        default=0.02, ge=0.0, le=1.0, description="Blank image detection threshold"
    )

    # Notifications
    apprise_enabled: bool = Field(default=False, description="Enable Apprise notifications")
    apprise_url: str = Field(default="http://apprise:8000", description="Apprise API URL")
    min_failures_before_alert: int = Field(
        default=3, ge=1, description="Consecutive failures before alerting"
    )
    alert_cooldown_minutes: int = Field(
        default=30, ge=1, description="Minutes between repeated alerts"
    )

    @field_validator("default_pixel_format")
    @classmethod
    def validate_pixel_format(cls, v: str) -> str:
        """Validate pixel format."""
        allowed = ["yuv420p", "yuv444p", "rgb24"]
        if v not in allowed:
            raise ValueError(f"pixel_format must be one of {allowed}")
        return v

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Validate log level."""
        allowed = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        v = v.upper()
        if v not in allowed:
            raise ValueError(f"log_level must be one of {allowed}")
        return v

    @property
    def images_path(self) -> str:
        """Full path to images directory."""
        return f"{self.output_base_path}/{self.images_subpath}"

    @property
    def videos_path(self) -> str:
        """Full path to videos directory."""
        return f"{self.output_base_path}/{self.videos_subpath}"

    @property
    def redis_url(self) -> str:
        """Redis connection URL."""
        return f"redis://{self.redis_host}:{self.redis_port}"


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
