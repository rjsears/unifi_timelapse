"""
Tests for connectivity checker.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import httpx

from health.checks.connectivity import ConnectivityChecker


class TestConnectivityChecker:
    """Tests for ConnectivityChecker."""

    @pytest.fixture
    def checker(self):
        """Create connectivity checker."""
        with patch("health.checks.connectivity.get_settings"):
            yield ConnectivityChecker(timeout=10)

    @pytest.fixture
    def mock_camera(self):
        """Create mock camera."""
        camera = MagicMock()
        camera.name = "Test Camera"
        camera.url = "http://192.168.1.100/snap.jpeg"
        camera.ip_address = "192.168.1.100"
        camera.hostname = None
        return camera

    @pytest.mark.asyncio
    async def test_check_reachable(self, checker, mock_camera):
        """Test checking reachable camera."""
        with patch("httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=mock_response
            )

            is_reachable, response_time = await checker.check(mock_camera)

            assert is_reachable is True
            assert response_time is not None

    @pytest.mark.asyncio
    async def test_check_unreachable_status(self, checker, mock_camera):
        """Test checking camera with error status."""
        with patch("httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 500
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=mock_response
            )

            is_reachable, response_time = await checker.check(mock_camera)

            assert is_reachable is False
            assert response_time is None

    @pytest.mark.asyncio
    async def test_check_timeout(self, checker, mock_camera):
        """Test checking camera that times out."""
        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                side_effect=httpx.TimeoutException("Timeout")
            )

            is_reachable, response_time = await checker.check(mock_camera)

            assert is_reachable is False
            assert response_time is None

    @pytest.mark.asyncio
    async def test_check_connection_error(self, checker, mock_camera):
        """Test checking camera with connection error."""
        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                side_effect=httpx.ConnectError("Connection refused")
            )

            is_reachable, response_time = await checker.check(mock_camera)

            assert is_reachable is False
            assert response_time is None

    @pytest.mark.asyncio
    async def test_check_generic_error(self, checker, mock_camera):
        """Test checking camera with generic error."""
        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                side_effect=Exception("Unknown error")
            )

            is_reachable, response_time = await checker.check(mock_camera)

            assert is_reachable is False
            assert response_time is None

    @pytest.mark.asyncio
    async def test_check_with_image_success(self, checker, mock_camera):
        """Test checking camera and fetching image."""
        with patch("httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.headers = {"content-type": "image/jpeg"}
            mock_response.content = b"fake image data"
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=mock_response
            )

            is_reachable, image_data = await checker.check_with_image(mock_camera)

            assert is_reachable is True
            assert image_data == b"fake image data"

    @pytest.mark.asyncio
    async def test_check_with_image_not_image(self, checker, mock_camera):
        """Test checking camera returns non-image content."""
        with patch("httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.headers = {"content-type": "text/html"}
            mock_response.content = b"<html>Not an image</html>"
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=mock_response
            )

            is_reachable, image_data = await checker.check_with_image(mock_camera)

            assert is_reachable is True
            assert image_data is None

    @pytest.mark.asyncio
    async def test_check_with_image_error_status(self, checker, mock_camera):
        """Test checking camera with error status returns no image."""
        with patch("httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 404
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=mock_response
            )

            is_reachable, image_data = await checker.check_with_image(mock_camera)

            assert is_reachable is False
            assert image_data is None

    @pytest.mark.asyncio
    async def test_check_with_image_exception(self, checker, mock_camera):
        """Test checking camera with image fetch error."""
        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                side_effect=Exception("Connection error")
            )

            is_reachable, image_data = await checker.check_with_image(mock_camera)

            assert is_reachable is False
            assert image_data is None

    @pytest.mark.asyncio
    async def test_ping_host_success(self, checker, mock_camera):
        """Test ping host succeeds."""
        with patch("asyncio.open_connection") as mock_conn:
            mock_writer = MagicMock()
            mock_writer.close = MagicMock()
            mock_writer.wait_closed = AsyncMock()
            mock_conn.return_value = (MagicMock(), mock_writer)

            result = await checker.ping_host(mock_camera)

            assert result is True

    @pytest.mark.asyncio
    async def test_ping_host_timeout(self, checker, mock_camera):
        """Test ping host with timeout."""
        with patch("asyncio.open_connection", side_effect=TimeoutError):
            result = await checker.ping_host(mock_camera)

            assert result is False

    @pytest.mark.asyncio
    async def test_ping_host_oserror(self, checker, mock_camera):
        """Test ping host with OS error."""
        with patch("asyncio.open_connection", side_effect=OSError):
            result = await checker.ping_host(mock_camera)

            assert result is False
