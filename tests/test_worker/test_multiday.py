"""
Tests for multiday timelapse task.
"""

import pytest
from datetime import date, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from worker.tasks.multiday import select_images_for_multiday


class TestMultidayTask:
    """Tests for multiday timelapse task functions."""

    @pytest.fixture
    def mock_db(self):
        """Create mock database session."""
        session = AsyncMock()
        session.execute = AsyncMock()
        session.commit = AsyncMock()
        return session

    @pytest.mark.asyncio
    async def test_select_images_for_multiday_empty(self, mock_db):
        """Test image selection when no images exist."""
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db.execute.return_value = mock_result

        camera_id = uuid4()
        start_date = date.today() - timedelta(days=7)
        end_date = date.today() - timedelta(days=1)

        result = await select_images_for_multiday(
            db=mock_db,
            camera_id=camera_id,
            start_date=start_date,
            end_date=end_date,
            images_per_hour=2,
        )

        assert result == []

    @pytest.mark.asyncio
    async def test_select_images_for_multiday_basic(self, mock_db):
        """Test basic image selection."""
        # Create mock images across different hours
        base_time = datetime.now() - timedelta(days=1)
        mock_images = []
        for hour in range(3):  # 3 hours
            for i in range(4):  # 4 images per hour
                img = MagicMock()
                img.captured_at = base_time.replace(hour=hour, minute=i * 15)
                mock_images.append(img)

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = mock_images
        mock_db.execute.return_value = mock_result

        camera_id = uuid4()
        start_date = date.today() - timedelta(days=2)
        end_date = date.today()

        result = await select_images_for_multiday(
            db=mock_db,
            camera_id=camera_id,
            start_date=start_date,
            end_date=end_date,
            images_per_hour=2,
        )

        # Should select 2 images per hour, 3 hours = 6 images
        assert len(result) == 6

    @pytest.mark.asyncio
    async def test_select_images_for_multiday_less_than_requested(self, mock_db):
        """Test image selection when fewer images than requested per hour."""
        base_time = datetime.now() - timedelta(days=1)
        # Only 1 image per hour
        mock_images = []
        for hour in range(3):
            img = MagicMock()
            img.captured_at = base_time.replace(hour=hour, minute=0)
            mock_images.append(img)

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = mock_images
        mock_db.execute.return_value = mock_result

        camera_id = uuid4()
        result = await select_images_for_multiday(
            db=mock_db,
            camera_id=camera_id,
            start_date=date.today() - timedelta(days=2),
            end_date=date.today(),
            images_per_hour=5,  # Request more than available
        )

        # Should select all available (1 per hour = 3 total)
        assert len(result) == 3
