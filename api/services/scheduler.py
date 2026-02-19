"""
Scheduler Service

Service for managing and triggering scheduled tasks via API.
"""

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List

from api.config import get_settings

logger = logging.getLogger(__name__)


class SchedulerService:
    """Service for managing scheduled tasks."""

    def __init__(self):
        self.settings = get_settings()
        # Track manually triggered jobs
        self._running_jobs: Dict[str, datetime] = {}

    def get_schedule_info(self) -> List[Dict[str, Any]]:
        """
        Get information about scheduled tasks.

        Returns:
            List of scheduled task information
        """
        daily_hour, daily_minute = self._parse_time(self.settings.daily_timelapse_time)
        multiday_hour, multiday_minute = self._parse_time(self.settings.multiday_generation_time)
        cleanup_hour, cleanup_minute = self._parse_time(self.settings.cleanup_time)

        return [
            {
                "id": "capture_cycle",
                "name": "Camera Capture Cycle",
                "type": "interval",
                "interval_seconds": self.settings.default_capture_interval,
                "description": f"Captures images every {self.settings.default_capture_interval}s",
            },
            {
                "id": "daily_timelapse",
                "name": "Daily Timelapse Generation",
                "type": "cron",
                "schedule": f"{daily_hour:02d}:{daily_minute:02d}",
                "description": "Generates daily timelapse videos for all cameras",
            },
            {
                "id": "multiday_timelapse",
                "name": "Multi-day Timelapse Generation",
                "type": "cron",
                "schedule": f"{self.settings.multiday_generation_day} {multiday_hour:02d}:{multiday_minute:02d}",
                "description": "Generates multi-day summary timelapses",
            },
            {
                "id": "cleanup",
                "name": "File Cleanup",
                "type": "cron",
                "schedule": f"{cleanup_hour:02d}:{cleanup_minute:02d}",
                "description": "Cleans up old images and videos",
            },
            {
                "id": "health_check",
                "name": "Camera Health Check",
                "type": "interval",
                "interval_seconds": self.settings.health_check_interval,
                "description": "Checks camera connectivity",
            },
        ]

    def _parse_time(self, time_str: str) -> tuple[int, int]:
        """Parse HH:MM time string to hour, minute tuple."""
        parts = time_str.split(":")
        return int(parts[0]), int(parts[1])

    def is_job_running(self, job_id: str) -> bool:
        """
        Check if a job is currently running.

        Args:
            job_id: Job identifier

        Returns:
            True if job is running
        """
        return job_id in self._running_jobs

    def mark_job_started(self, job_id: str) -> None:
        """
        Mark a job as started.

        Args:
            job_id: Job identifier
        """
        self._running_jobs[job_id] = datetime.now(timezone.utc)
        logger.info(f"Job {job_id} started")

    def mark_job_completed(self, job_id: str) -> None:
        """
        Mark a job as completed.

        Args:
            job_id: Job identifier
        """
        if job_id in self._running_jobs:
            del self._running_jobs[job_id]
            logger.info(f"Job {job_id} completed")

    def get_running_jobs(self) -> Dict[str, datetime]:
        """
        Get all currently running jobs.

        Returns:
            Dictionary of job_id -> start_time
        """
        return self._running_jobs.copy()

    def get_retention_settings(self) -> Dict[str, int]:
        """
        Get retention period settings.

        Returns:
            Dictionary of retention settings
        """
        return {
            "images_days": self.settings.retention_days_images,
            "videos_days": self.settings.retention_days_videos,
            "cleanup_after_timelapse": self.settings.cleanup_after_timelapse,
        }

    def get_capture_settings(self) -> Dict[str, Any]:
        """
        Get capture-related settings.

        Returns:
            Dictionary of capture settings
        """
        return {
            "default_interval": self.settings.default_capture_interval,
            "max_concurrent": self.settings.max_concurrent_captures,
            "timeout": self.settings.capture_timeout,
            "retries": self.settings.capture_retries,
        }

    def get_timelapse_settings(self) -> Dict[str, Any]:
        """
        Get timelapse-related settings.

        Returns:
            Dictionary of timelapse settings
        """
        return {
            "default_frame_rate": self.settings.default_frame_rate,
            "default_crf": self.settings.default_crf,
            "default_pixel_format": self.settings.default_pixel_format,
            "ffmpeg_timeout": self.settings.ffmpeg_timeout,
            "daily_time": self.settings.daily_timelapse_time,
            "multiday_day": self.settings.multiday_generation_day,
            "multiday_time": self.settings.multiday_generation_time,
            "multiday_images_per_hour": self.settings.multiday_images_per_hour,
            "multiday_days_to_include": self.settings.multiday_days_to_include,
        }
