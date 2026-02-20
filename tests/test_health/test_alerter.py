"""
Tests for health alerter.
"""

import pytest
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from health.alerter import HealthAlerter


class TestHealthAlerter:
    """Tests for HealthAlerter."""

    @pytest.fixture
    def alerter(self):
        """Create alerter with mocked settings."""
        with patch("health.alerter.get_settings") as mock_settings:
            mock_settings.return_value = MagicMock(
                alert_cooldown_minutes=30,
                min_failures_before_alert=3,
            )
            yield HealthAlerter()

    @pytest.fixture
    def mock_camera(self):
        """Create mock camera."""
        camera = MagicMock()
        camera.id = uuid4()
        camera.name = "Test Camera"
        camera.last_capture_at = datetime.now(timezone.utc)
        return camera

    @pytest.fixture
    def mock_db(self):
        """Create mock database session."""
        return AsyncMock()

    def test_get_alert_key(self, alerter):
        """Test alert key generation."""
        key = alerter._get_alert_key("camera-123", "camera_down")
        assert key == "camera-123:camera_down"

    def test_can_alert_no_previous(self, alerter):
        """Test can alert when no previous alert."""
        assert alerter._can_alert("camera-123", "camera_down") is True

    def test_can_alert_within_cooldown(self, alerter):
        """Test cannot alert within cooldown period."""
        alerter._record_alert("camera-123", "camera_down")
        assert alerter._can_alert("camera-123", "camera_down") is False

    def test_can_alert_after_cooldown(self, alerter):
        """Test can alert after cooldown expires."""
        alerter._last_alerts["camera-123:camera_down"] = datetime.now(timezone.utc) - timedelta(
            minutes=60
        )
        assert alerter._can_alert("camera-123", "camera_down") is True

    def test_record_alert(self, alerter):
        """Test recording an alert."""
        alerter._record_alert("camera-123", "camera_down")
        assert "camera-123:camera_down" in alerter._last_alerts

    @pytest.mark.asyncio
    async def test_initialize(self, alerter):
        """Test alerter initialization."""
        await alerter.initialize()
        # Should not raise any errors

    @pytest.mark.asyncio
    async def test_alert_camera_down_cooldown(self, alerter, mock_db, mock_camera):
        """Test camera down alert respects cooldown."""
        alerter._record_alert(str(mock_camera.id), "camera_down")

        result = await alerter.alert_camera_down(mock_db, mock_camera)

        assert result is False

    @pytest.mark.asyncio
    async def test_alert_camera_down_sends(self, alerter, mock_db, mock_camera):
        """Test camera down alert sends notification."""
        with patch("health.alerter.NotificationService") as mock_service:
            mock_instance = MagicMock()
            mock_instance.notify_camera_down = AsyncMock(return_value=True)
            mock_service.return_value = mock_instance

            result = await alerter.alert_camera_down(mock_db, mock_camera)

            assert result is True
            mock_instance.notify_camera_down.assert_called_once()

    @pytest.mark.asyncio
    async def test_alert_blank_image_cooldown(self, alerter, mock_db, mock_camera):
        """Test blank image alert respects cooldown."""
        alerter._record_alert(str(mock_camera.id), "blank_image")

        result = await alerter.alert_blank_image(mock_db, mock_camera)

        assert result is False

    @pytest.mark.asyncio
    async def test_alert_blank_image_sends(self, alerter, mock_db, mock_camera):
        """Test blank image alert sends notification."""
        with patch("health.alerter.NotificationService") as mock_service:
            mock_instance = MagicMock()
            mock_instance.send_notification = AsyncMock(return_value=True)
            mock_service.return_value = mock_instance

            result = await alerter.alert_blank_image(mock_db, mock_camera)

            assert result is True

    @pytest.mark.asyncio
    async def test_alert_frozen_image_sends(self, alerter, mock_db, mock_camera):
        """Test frozen image alert sends notification."""
        with patch("health.alerter.NotificationService") as mock_service:
            mock_instance = MagicMock()
            mock_instance.send_notification = AsyncMock(return_value=True)
            mock_service.return_value = mock_instance

            result = await alerter.alert_frozen_image(mock_db, mock_camera)

            assert result is True

    @pytest.mark.asyncio
    async def test_alert_capture_failure_below_threshold(self, alerter, mock_db, mock_camera):
        """Test capture failure alert below threshold doesn't send."""
        result = await alerter.alert_capture_failure(
            mock_db, mock_camera, "Error", consecutive_failures=1
        )

        assert result is False

    @pytest.mark.asyncio
    async def test_alert_capture_failure_sends(self, alerter, mock_db, mock_camera):
        """Test capture failure alert sends when above threshold."""
        with patch("health.alerter.NotificationService") as mock_service:
            mock_instance = MagicMock()
            mock_instance.notify_capture_failure = AsyncMock(return_value=True)
            mock_service.return_value = mock_instance

            result = await alerter.alert_capture_failure(
                mock_db, mock_camera, "Error", consecutive_failures=5
            )

            assert result is True

    def test_clear_cooldown_specific(self, alerter):
        """Test clearing cooldown for specific alert type."""
        alerter._record_alert("camera-123", "camera_down")
        alerter._record_alert("camera-123", "blank_image")

        alerter.clear_cooldown("camera-123", "camera_down")

        assert "camera-123:camera_down" not in alerter._last_alerts
        assert "camera-123:blank_image" in alerter._last_alerts

    def test_clear_cooldown_all(self, alerter):
        """Test clearing all cooldowns for a camera."""
        alerter._record_alert("camera-123", "camera_down")
        alerter._record_alert("camera-123", "blank_image")
        alerter._record_alert("camera-456", "camera_down")

        alerter.clear_cooldown("camera-123")

        assert "camera-123:camera_down" not in alerter._last_alerts
        assert "camera-123:blank_image" not in alerter._last_alerts
        assert "camera-456:camera_down" in alerter._last_alerts
