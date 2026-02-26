"""
Tests for timelapse service.
"""

import pytest
from datetime import date, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from api.services.timelapse import TimelapseService
from api.models.timelapse import Timelapse
from api.models.image import Image


class TestTimelapseService:
    """Tests for TimelapseService."""

    @pytest.fixture
    def mock_db(self):
        """Create mock database session."""
        session = AsyncMock()
        session.execute = AsyncMock()
        session.commit = AsyncMock()
        session.refresh = AsyncMock()
        session.add = MagicMock()
        return session

    @pytest.fixture
    def mock_camera(self):
        """Create mock camera."""
        camera = MagicMock()
        camera.id = uuid4()
        camera.name = "Test Camera"
        return camera

    @pytest.fixture
    def timelapse_service(self, mock_db):
        """Create timelapse service with mocked settings."""
        with patch("api.services.timelapse.get_settings") as mock_settings:
            mock_settings.return_value = MagicMock(
                default_frame_rate=30,
                default_crf=20,
                default_pixel_format="yuv444p",
                output_base_path="/output",
                ffmpeg_timeout=3600,
            )
            with patch("api.services.timelapse.StorageService") as mock_storage:
                mock_storage_instance = MagicMock()
                mock_storage_instance.get_daily_video_filename.return_value = "timelapse.mp4"
                mock_storage_instance.get_relative_video_path.return_value = "videos/timelapse.mp4"
                mock_storage_instance.get_video_dir.return_value = MagicMock(__truediv__=lambda s, x: f"/output/videos/{x}")
                mock_storage.return_value = mock_storage_instance

                service = TimelapseService(mock_db)
                service.storage = mock_storage_instance
                yield service

    @pytest.mark.asyncio
    async def test_generate_daily_timelapse_no_images(self, timelapse_service, mock_db, mock_camera):
        """Test timelapse generation fails when no images found."""
        target_date = date.today() - timedelta(days=1)

        # First query returns no existing timelapse
        mock_timelapse_result = MagicMock()
        mock_timelapse_result.scalar_one_or_none.return_value = None

        # Second query returns no images
        mock_images_result = MagicMock()
        mock_images_result.scalars.return_value.all.return_value = []

        mock_db.execute.side_effect = [mock_timelapse_result, mock_images_result]

        result = await timelapse_service.generate_daily_timelapse(mock_camera, target_date)

        assert result.status == "failed"
        assert result.error_message == "No images found for this date"
        # Verify started_at was set (line 89)
        assert result.started_at is not None

    @pytest.mark.asyncio
    async def test_generate_daily_timelapse_sets_timestamps(self, timelapse_service, mock_db, mock_camera):
        """Test that timelapse generation sets started_at and completed_at timestamps."""
        target_date = date.today() - timedelta(days=1)

        # First query returns no existing timelapse
        mock_timelapse_result = MagicMock()
        mock_timelapse_result.scalar_one_or_none.return_value = None

        # Create mock images
        mock_images = [
            MagicMock(
                id=uuid4(),
                file_path=f"cameras/test/2026/02/25/image_{i:04d}.jpg",
                captured_at=datetime.now() - timedelta(hours=i),
            )
            for i in range(5)
        ]
        mock_images_result = MagicMock()
        mock_images_result.scalars.return_value.all.return_value = mock_images

        mock_db.execute.side_effect = [mock_timelapse_result, mock_images_result]

        # Mock _generate_video to return a path
        with patch.object(timelapse_service, "_generate_video") as mock_gen:
            mock_gen.return_value = "/output/videos/timelapse.mp4"

            # Mock os.path.getsize
            with patch("api.services.timelapse.os.path.getsize", return_value=1024000):
                result = await timelapse_service.generate_daily_timelapse(mock_camera, target_date)

        # Verify timestamps were set
        assert result.started_at is not None
        assert result.completed_at is not None
        assert result.status == "completed"
        # started_at should be set before completed_at
        assert result.started_at <= result.completed_at

    @pytest.mark.asyncio
    async def test_generate_daily_timelapse_existing_timelapse(self, timelapse_service, mock_db, mock_camera):
        """Test regenerating an existing timelapse updates it."""
        target_date = date.today() - timedelta(days=1)

        # Return existing timelapse
        existing_timelapse = MagicMock()
        existing_timelapse.id = uuid4()
        existing_timelapse.status = "pending"
        existing_timelapse.started_at = None
        existing_timelapse.completed_at = None

        mock_timelapse_result = MagicMock()
        mock_timelapse_result.scalar_one_or_none.return_value = existing_timelapse

        # No images
        mock_images_result = MagicMock()
        mock_images_result.scalars.return_value.all.return_value = []

        mock_db.execute.side_effect = [mock_timelapse_result, mock_images_result]

        result = await timelapse_service.generate_daily_timelapse(mock_camera, target_date)

        # Should have set started_at on the existing timelapse
        assert existing_timelapse.started_at is not None
        assert result.status == "failed"

    @pytest.mark.asyncio
    async def test_get_pending_timelapses(self, timelapse_service, mock_db):
        """Test getting pending timelapses."""
        mock_timelapses = [MagicMock(), MagicMock()]
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = mock_timelapses
        mock_db.execute.return_value = mock_result

        result = await timelapse_service.get_pending_timelapses()

        assert len(result) == 2
