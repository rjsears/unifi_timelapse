"""
Tests for storage service.
"""

import os
import pytest
import tempfile
from datetime import datetime
from pathlib import Path
from unittest.mock import patch, MagicMock

from api.services.storage import StorageService


class TestStorageService:
    """Tests for StorageService."""

    @pytest.fixture
    def storage_service(self):
        """Create storage service with mocked settings."""
        with patch("api.services.storage.get_settings") as mock_settings:
            mock_settings.return_value = MagicMock(
                images_path="/tmp/test_images",
                videos_path="/tmp/test_videos",
                output_base_path="/tmp/test_output",
                images_subpath="images",
                videos_subpath="videos",
            )
            yield StorageService()

    def test_normalize_camera_name(self, storage_service):
        """Test camera name normalization."""
        assert storage_service._normalize_camera_name("Front Door") == "front_door"
        assert storage_service._normalize_camera_name("BACK YARD") == "back_yard"
        assert storage_service._normalize_camera_name("garage") == "garage"

    def test_get_image_dir(self, storage_service):
        """Test getting image directory path."""
        timestamp = datetime(2026, 2, 19, 10, 30, 0)
        dir_path = storage_service.get_image_dir("Front Door", timestamp)

        assert isinstance(dir_path, Path)
        assert "front_door" in str(dir_path)
        assert "20260219" in str(dir_path)

    def test_get_video_dir(self, storage_service):
        """Test getting video directory path."""
        dir_path = storage_service.get_video_dir("Front Door", "daily")

        assert isinstance(dir_path, Path)
        assert "front_door" in str(dir_path)
        assert "daily" in str(dir_path)

    def test_get_image_filename(self, storage_service):
        """Test generating image filename."""
        timestamp = datetime(2026, 2, 19, 10, 30, 45)
        filename = storage_service.get_image_filename("Test Camera", timestamp)

        assert "20260219103045" in filename
        assert "test_camera" in filename
        assert filename.endswith(".jpeg")

    def test_get_daily_video_filename(self, storage_service):
        """Test generating daily video filename."""
        date = datetime(2026, 2, 19)
        filename = storage_service.get_daily_video_filename(date)

        assert filename == "20260219.mp4"

    def test_get_summary_video_filename(self, storage_service):
        """Test generating summary video filename."""
        start = datetime(2026, 2, 12)
        end = datetime(2026, 2, 19)
        filename = storage_service.get_summary_video_filename(start, end)

        assert filename == "20260212-20260219_summary.mp4"

    def test_get_relative_image_path(self, storage_service):
        """Test getting relative image path."""
        timestamp = datetime(2026, 2, 19, 10, 30, 0)
        path = storage_service.get_relative_image_path("Test Camera", timestamp)

        assert "images" in path
        assert "test_camera" in path
        assert "20260219" in path

    def test_get_relative_video_path(self, storage_service):
        """Test getting relative video path."""
        path = storage_service.get_relative_video_path("Test Camera", "daily", "test.mp4")

        assert "videos" in path
        assert "test_camera" in path
        assert "daily" in path
        assert "test.mp4" in path

    def test_save_image(self, storage_service):
        """Test saving an image to disk."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch.object(storage_service, "get_image_path") as mock_path:
                file_path = Path(tmpdir) / "test.jpeg"
                mock_path.return_value = file_path

                image_data = b"fake image data"
                result_path, result_size = storage_service.save_image(
                    "Test Camera",
                    datetime.now(),
                    image_data,
                )

                assert result_path == file_path
                assert result_size == len(image_data)
                assert file_path.exists()

    def test_delete_file_exists(self, storage_service):
        """Test deleting an existing file."""
        with tempfile.NamedTemporaryFile(delete=False) as f:
            temp_path = f.name
            f.write(b"test")

        try:
            result = storage_service.delete_file(temp_path)
            assert result is True
            assert not os.path.exists(temp_path)
        except Exception:
            if os.path.exists(temp_path):
                os.unlink(temp_path)
            raise

    def test_delete_file_not_exists(self, storage_service):
        """Test deleting a non-existent file."""
        result = storage_service.delete_file("/tmp/nonexistent_file_12345.txt")
        assert result is False

    def test_get_disk_usage(self, storage_service):
        """Test getting disk usage statistics."""
        with patch("os.statvfs") as mock_statvfs:
            mock_stat = MagicMock()
            mock_stat.f_blocks = 1000000
            mock_stat.f_frsize = 4096
            mock_stat.f_bavail = 500000
            mock_statvfs.return_value = mock_stat

            usage = storage_service.get_disk_usage()

            assert "total_bytes" in usage
            assert "used_bytes" in usage
            assert "free_bytes" in usage
            assert "percent_used" in usage

    def test_get_disk_usage_error(self, storage_service):
        """Test disk usage when statvfs fails."""
        with patch("os.statvfs", side_effect=OSError("Disk error")):
            usage = storage_service.get_disk_usage()

            assert usage["total_bytes"] == 0
            assert usage["percent_used"] == 0

    def test_list_images_for_date_empty(self, storage_service):
        """Test listing images when directory doesn't exist."""
        with patch.object(storage_service, "get_image_dir") as mock_dir:
            mock_dir.return_value = Path("/nonexistent/path")

            images = storage_service.list_images_for_date("Test Camera", datetime.now())
            assert images == []
