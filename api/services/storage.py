"""
Storage Service

File storage operations for images and videos.
"""

import os
from datetime import datetime
from pathlib import Path
from typing import Optional

from api.config import get_settings


class StorageService:
    """Service for managing file storage."""

    def __init__(self):
        self.settings = get_settings()

    def get_image_dir(self, camera_name: str, date: datetime) -> Path:
        """
        Get the directory path for storing images.

        Creates the directory if it doesn't exist.

        Args:
            camera_name: Name of the camera
            date: Date for the images

        Returns:
            Path to the image directory
        """
        date_str = date.strftime("%Y%m%d")
        dir_path = Path(self.settings.images_path) / camera_name / date_str

        dir_path.mkdir(parents=True, exist_ok=True)
        return dir_path

    def get_video_dir(self, camera_name: str, video_type: str = "daily") -> Path:
        """
        Get the directory path for storing videos.

        Creates the directory if it doesn't exist.

        Args:
            camera_name: Name of the camera
            video_type: Type of video (daily or summary)

        Returns:
            Path to the video directory
        """
        dir_path = Path(self.settings.videos_path) / camera_name / video_type

        dir_path.mkdir(parents=True, exist_ok=True)
        return dir_path

    def get_image_filename(self, camera_name: str, timestamp: datetime) -> str:
        """
        Generate image filename.

        Args:
            camera_name: Name of the camera
            timestamp: Capture timestamp

        Returns:
            Image filename
        """
        timestamp_str = timestamp.strftime("%Y%m%d%H%M%S")
        return f"{timestamp_str}_{camera_name}.jpeg"

    def get_image_path(self, camera_name: str, timestamp: datetime) -> Path:
        """
        Get full path for an image file.

        Args:
            camera_name: Name of the camera
            timestamp: Capture timestamp

        Returns:
            Full path to the image file
        """
        dir_path = self.get_image_dir(camera_name, timestamp)
        filename = self.get_image_filename(camera_name, timestamp)
        return dir_path / filename

    def get_relative_image_path(self, camera_name: str, timestamp: datetime) -> str:
        """
        Get relative path for database storage.

        Args:
            camera_name: Name of the camera
            timestamp: Capture timestamp

        Returns:
            Relative path from output root
        """
        date_str = timestamp.strftime("%Y%m%d")
        filename = self.get_image_filename(camera_name, timestamp)
        return f"{self.settings.images_subpath}/{camera_name}/{date_str}/{filename}"

    def get_daily_video_filename(self, date: datetime) -> str:
        """
        Generate daily timelapse video filename.

        Args:
            date: Date of the timelapse

        Returns:
            Video filename
        """
        date_str = date.strftime("%Y%m%d")
        return f"{date_str}.mp4"

    def get_summary_video_filename(
        self, start_date: datetime, end_date: datetime
    ) -> str:
        """
        Generate summary timelapse video filename.

        Args:
            start_date: Start date of the timelapse
            end_date: End date of the timelapse

        Returns:
            Video filename
        """
        start_str = start_date.strftime("%Y%m%d")
        end_str = end_date.strftime("%Y%m%d")
        return f"{start_str}-{end_str}_summary.mp4"

    def get_relative_video_path(
        self,
        camera_name: str,
        video_type: str,
        filename: str,
    ) -> str:
        """
        Get relative video path for database storage.

        Args:
            camera_name: Name of the camera
            video_type: Type of video (daily or summary)
            filename: Video filename

        Returns:
            Relative path from output root
        """
        return f"{self.settings.videos_subpath}/{camera_name}/{video_type}/{filename}"

    def save_image(
        self,
        camera_name: str,
        timestamp: datetime,
        image_data: bytes,
    ) -> tuple[Path, int]:
        """
        Save an image to disk.

        Args:
            camera_name: Name of the camera
            timestamp: Capture timestamp
            image_data: Image bytes

        Returns:
            Tuple of (file path, file size)
        """
        file_path = self.get_image_path(camera_name, timestamp)

        # Write atomically using temp file
        temp_path = file_path.with_suffix(".tmp")
        try:
            temp_path.write_bytes(image_data)
            temp_path.rename(file_path)
        except Exception:
            if temp_path.exists():
                temp_path.unlink()
            raise

        return file_path, len(image_data)

    def delete_file(self, file_path: str) -> bool:
        """
        Delete a file.

        Args:
            file_path: Path to the file (relative or absolute)

        Returns:
            True if deleted, False if not found
        """
        # Handle relative paths
        if not file_path.startswith("/"):
            file_path = f"{self.settings.output_base_path}/{file_path}"

        path = Path(file_path)
        if path.exists():
            path.unlink()
            return True
        return False

    def get_disk_usage(self) -> dict:
        """
        Get disk usage statistics.

        Returns:
            Dictionary with total, used, free bytes and percent used
        """
        try:
            stat = os.statvfs(self.settings.output_base_path)
            total = stat.f_blocks * stat.f_frsize
            free = stat.f_bavail * stat.f_frsize
            used = total - free
            percent = (used / total) * 100 if total > 0 else 0

            return {
                "total_bytes": total,
                "used_bytes": used,
                "free_bytes": free,
                "percent_used": percent,
            }
        except Exception:
            return {
                "total_bytes": 0,
                "used_bytes": 0,
                "free_bytes": 0,
                "percent_used": 0,
            }

    def list_images_for_date(
        self, camera_name: str, date: datetime
    ) -> list[Path]:
        """
        List all images for a camera on a specific date.

        Args:
            camera_name: Name of the camera
            date: Date to list images for

        Returns:
            List of image file paths, sorted by name
        """
        dir_path = self.get_image_dir(camera_name, date)
        if not dir_path.exists():
            return []

        images = list(dir_path.glob("*.jpeg"))
        return sorted(images)
