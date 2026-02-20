"""
Tests for uptime tracker.
"""

import pytest
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from health.checks.uptime import UptimeTracker
from api.models.camera_health import CameraHealth


class TestUptimeTracker:
    """Tests for UptimeTracker."""

    @pytest.fixture
    def tracker(self):
        """Create uptime tracker."""
        return UptimeTracker()

    @pytest.fixture
    def mock_camera(self):
        """Create mock camera."""
        camera = MagicMock()
        camera.id = uuid4()
        camera.name = "Test Camera"
        return camera

    @pytest.fixture
    def mock_db(self):
        """Create mock database session."""
        session = AsyncMock()
        session.add = MagicMock()
        session.commit = AsyncMock()
        session.refresh = AsyncMock()
        return session

    @pytest.mark.asyncio
    async def test_record_check(self, tracker, mock_db, mock_camera):
        """Test recording a health check."""
        result = await tracker.record_check(
            db=mock_db,
            camera=mock_camera,
            is_reachable=True,
            response_time_ms=50,
        )

        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once()

    @pytest.mark.asyncio
    async def test_record_check_with_error(self, tracker, mock_db, mock_camera):
        """Test recording a failed health check."""
        result = await tracker.record_check(
            db=mock_db,
            camera=mock_camera,
            is_reachable=False,
            error_message="Connection refused",
        )

        mock_db.add.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_uptime_percentage_no_data(self, tracker, mock_db, mock_camera):
        """Test uptime when no health data."""
        mock_result = MagicMock()
        mock_result.scalar.return_value = 0
        mock_db.execute.return_value = mock_result

        uptime = await tracker.get_uptime_percentage(mock_db, mock_camera)

        assert uptime == 100.0

    @pytest.mark.asyncio
    async def test_get_uptime_percentage_all_online(self, tracker, mock_db, mock_camera):
        """Test uptime when always online."""
        mock_result = MagicMock()
        # First call returns total, second returns online
        mock_result.scalar.side_effect = [10, 10]
        mock_db.execute.return_value = mock_result

        uptime = await tracker.get_uptime_percentage(mock_db, mock_camera)

        assert uptime == 100.0

    @pytest.mark.asyncio
    async def test_get_uptime_percentage_partial(self, tracker, mock_db, mock_camera):
        """Test uptime when partially online."""
        # Need to mock two separate execute calls
        mock_total_result = MagicMock()
        mock_total_result.scalar.return_value = 10

        mock_online_result = MagicMock()
        mock_online_result.scalar.return_value = 8

        mock_db.execute.side_effect = [mock_total_result, mock_online_result]

        uptime = await tracker.get_uptime_percentage(mock_db, mock_camera)

        assert uptime == 80.0

    @pytest.mark.asyncio
    async def test_get_average_response_time(self, tracker, mock_db, mock_camera):
        """Test getting average response time."""
        mock_result = MagicMock()
        mock_result.scalar.return_value = 45.5
        mock_db.execute.return_value = mock_result

        avg = await tracker.get_average_response_time(mock_db, mock_camera)

        assert avg == 45.5

    @pytest.mark.asyncio
    async def test_get_average_response_time_no_data(self, tracker, mock_db, mock_camera):
        """Test average response time when no data."""
        mock_result = MagicMock()
        mock_result.scalar.return_value = None
        mock_db.execute.return_value = mock_result

        avg = await tracker.get_average_response_time(mock_db, mock_camera)

        assert avg is None

    @pytest.mark.asyncio
    async def test_get_health_history(self, tracker, mock_db, mock_camera):
        """Test getting health history."""
        mock_records = [MagicMock(), MagicMock(), MagicMock()]
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = mock_records
        mock_db.execute.return_value = mock_result

        history = await tracker.get_health_history(mock_db, mock_camera)

        assert len(history) == 3

    @pytest.mark.asyncio
    async def test_get_health_history_empty(self, tracker, mock_db, mock_camera):
        """Test getting empty health history."""
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db.execute.return_value = mock_result

        history = await tracker.get_health_history(mock_db, mock_camera)

        assert len(history) == 0

    @pytest.mark.asyncio
    async def test_get_downtime_periods_no_history(self, tracker, mock_db, mock_camera):
        """Test downtime periods with no history."""
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db.execute.return_value = mock_result

        periods = await tracker.get_downtime_periods(mock_db, mock_camera)

        assert periods == []

    @pytest.mark.asyncio
    async def test_cleanup_old_records(self, tracker, mock_db):
        """Test cleaning up old health records."""
        mock_result = MagicMock()
        mock_result.rowcount = 5
        mock_db.execute.return_value = mock_result

        deleted = await tracker.cleanup_old_records(mock_db, days=30)

        assert deleted == 5
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_cleanup_old_records_none(self, tracker, mock_db):
        """Test cleanup when no old records."""
        mock_result = MagicMock()
        mock_result.rowcount = 0
        mock_db.execute.return_value = mock_result

        deleted = await tracker.cleanup_old_records(mock_db, days=30)

        assert deleted == 0
