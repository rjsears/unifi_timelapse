"""
Tests for notification service.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy.ext.asyncio import AsyncSession

from api.services.notification import NotificationService
from api.models.notification_config import NotificationConfig


class TestNotificationService:
    """Tests for NotificationService."""

    @pytest.fixture
    def mock_db(self):
        """Create mock database session."""
        return AsyncMock(spec=AsyncSession)

    @pytest.fixture
    def notification_service(self, mock_db):
        """Create notification service with mocked settings."""
        with patch("api.services.notification.get_settings") as mock_settings:
            mock_settings.return_value = MagicMock(
                apprise_enabled=True,
                apprise_url="http://apprise:8000",
            )
            service = NotificationService(mock_db)
            yield service

    @pytest.fixture
    def notification_service_disabled(self, mock_db):
        """Create notification service with notifications disabled."""
        with patch("api.services.notification.get_settings") as mock_settings:
            mock_settings.return_value = MagicMock(
                apprise_enabled=False,
            )
            service = NotificationService(mock_db)
            yield service

    @pytest.mark.asyncio
    async def test_send_notification_success(self, notification_service):
        """Test sending a notification successfully."""
        with patch("httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.raise_for_status = MagicMock()
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                return_value=mock_response
            )

            result = await notification_service.send_notification(
                title="Test Title",
                body="Test Body",
                notification_type="info",
            )

            assert result is True

    @pytest.mark.asyncio
    async def test_send_notification_disabled(self, notification_service_disabled):
        """Test sending notification when disabled."""
        result = await notification_service_disabled.send_notification(
            title="Test Title",
            body="Test Body",
        )

        assert result is False

    @pytest.mark.asyncio
    async def test_send_notification_failure(self, notification_service):
        """Test sending notification when HTTP fails."""
        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                side_effect=Exception("Connection error")
            )

            result = await notification_service.send_notification(
                title="Test Title",
                body="Test Body",
            )

            assert result is False

    @pytest.mark.asyncio
    async def test_notify_capture_failure_no_db(self):
        """Test capture failure notification without db."""
        with patch("api.services.notification.get_settings") as mock_settings:
            mock_settings.return_value = MagicMock(apprise_enabled=True)
            service = NotificationService(db=None)

            result = await service.notify_capture_failure(
                camera_name="Test Camera",
                error="Connection failed",
                consecutive_failures=5,
            )

            assert result is False

    @pytest.mark.asyncio
    async def test_notify_timelapse_complete_no_db(self):
        """Test timelapse complete notification without db."""
        with patch("api.services.notification.get_settings") as mock_settings:
            mock_settings.return_value = MagicMock(apprise_enabled=True)
            service = NotificationService(db=None)

            result = await service.notify_timelapse_complete(
                camera_name="Test Camera",
                timelapse_type="daily",
                date_range="2026-02-18",
                frame_count=2880,
            )

            assert result is False

    @pytest.mark.asyncio
    async def test_notify_camera_down_no_db(self):
        """Test camera down notification without db."""
        with patch("api.services.notification.get_settings") as mock_settings:
            mock_settings.return_value = MagicMock(apprise_enabled=True)
            service = NotificationService(db=None)

            result = await service.notify_camera_down(
                camera_name="Test Camera",
                last_seen="2026-02-19 10:00:00",
            )

            assert result is False

    @pytest.mark.asyncio
    async def test_notify_storage_warning_no_db(self):
        """Test storage warning notification without db."""
        with patch("api.services.notification.get_settings") as mock_settings:
            mock_settings.return_value = MagicMock(apprise_enabled=True)
            service = NotificationService(db=None)

            result = await service.notify_storage_warning(
                percent_used=90.5,
                free_bytes=10 * 1024**3,
            )

            assert result is False
