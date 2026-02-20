"""
Tests for cleanup service.
"""

import pytest
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from api.services.cleanup import CleanupService
from api.models.image import Image
from api.models.timelapse import Timelapse


class TestCleanupService:
    """Tests for CleanupService."""

    @pytest.fixture
    def mock_db(self):
        """Create mock database session."""
        session = AsyncMock()
        session.execute = AsyncMock()
        session.commit = AsyncMock()
        session.delete = AsyncMock()
        session.add = MagicMock()
        return session

    @pytest.fixture
    def cleanup_service(self, mock_db):
        """Create cleanup service with mocked settings."""
        with patch("api.services.cleanup.get_settings") as mock_settings:
            mock_settings.return_value = MagicMock(
                retention_days_images=30,
                retention_days_videos=90,
            )
            with patch("api.services.cleanup.StorageService"):
                service = CleanupService(mock_db)
                service.storage = MagicMock()
                yield service

    @pytest.mark.asyncio
    async def test_cleanup_old_images_no_images(self, cleanup_service, mock_db):
        """Test cleanup when no old images exist."""
        # Mock empty result
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_result.scalar.return_value = 0
        mock_db.execute.return_value = mock_result

        log = await cleanup_service.cleanup_old_images()

        assert log.files_deleted == 0
        assert log.bytes_freed == 0
        assert log.type == "images"

    @pytest.mark.asyncio
    async def test_cleanup_old_images_with_retention_days(self, cleanup_service, mock_db):
        """Test cleanup with custom retention days."""
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_result.scalar.return_value = 0
        mock_db.execute.return_value = mock_result

        log = await cleanup_service.cleanup_old_images(retention_days=7)

        assert log.type == "images"

    @pytest.mark.asyncio
    async def test_cleanup_old_images_with_camera_id(self, cleanup_service, mock_db):
        """Test cleanup for specific camera."""
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_result.scalar.return_value = 0
        mock_db.execute.return_value = mock_result

        camera_id = str(uuid4())
        log = await cleanup_service.cleanup_old_images(camera_id=camera_id)

        assert log.camera_id == camera_id

    @pytest.mark.asyncio
    async def test_cleanup_old_videos_no_videos(self, cleanup_service, mock_db):
        """Test video cleanup when no old videos exist."""
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db.execute.return_value = mock_result

        log = await cleanup_service.cleanup_old_videos()

        assert log.files_deleted == 0
        assert log.type == "videos"

    @pytest.mark.asyncio
    async def test_cleanup_old_videos_with_camera_id(self, cleanup_service, mock_db):
        """Test video cleanup for specific camera."""
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db.execute.return_value = mock_result

        camera_id = str(uuid4())
        log = await cleanup_service.cleanup_old_videos(camera_id=camera_id)

        assert log.camera_id == camera_id

    @pytest.mark.asyncio
    async def test_cleanup_after_timelapse_not_completed(self, cleanup_service):
        """Test cleanup fails for non-completed timelapse."""
        timelapse = MagicMock()
        timelapse.status = "pending"

        with pytest.raises(ValueError, match="Can only cleanup after completed timelapse"):
            await cleanup_service.cleanup_after_timelapse(timelapse)

    @pytest.mark.asyncio
    async def test_cleanup_after_timelapse_success(self, cleanup_service, mock_db):
        """Test cleanup after successful timelapse."""
        timelapse = MagicMock()
        timelapse.id = uuid4()
        timelapse.camera_id = uuid4()
        timelapse.status = "completed"

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_result.scalar.return_value = 0
        mock_db.execute.return_value = mock_result

        log = await cleanup_service.cleanup_after_timelapse(timelapse)

        assert log.type == "timelapse_cleanup"
        assert log.camera_id == timelapse.camera_id
