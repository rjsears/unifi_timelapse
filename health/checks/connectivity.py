"""
Connectivity Checker

Check if cameras are reachable via HTTP.
"""

import logging
from typing import Optional

import httpx

from api.config import get_settings
from api.models.camera import Camera

logger = logging.getLogger(__name__)
settings = get_settings()


class ConnectivityChecker:
    """Check camera connectivity via HTTP."""

    def __init__(self, timeout: int = 10):
        """
        Initialize connectivity checker.

        Args:
            timeout: HTTP request timeout in seconds
        """
        self.timeout = timeout

    async def check(self, camera: Camera) -> tuple[bool, int | None]:
        """
        Check if a camera is reachable.

        Args:
            camera: Camera to check

        Returns:
            Tuple of (is_reachable, response_time_ms)
        """
        try:
            import time

            async with httpx.AsyncClient() as client:
                start = time.time()
                # Use GET instead of HEAD - some cameras don't support HEAD
                response = await client.get(
                    camera.url,
                    timeout=self.timeout,
                    follow_redirects=True,
                )
                elapsed_ms = int((time.time() - start) * 1000)

                # Consider 2xx and 3xx as success
                is_reachable = response.status_code < 400

                if is_reachable:
                    logger.debug(f"Camera {camera.name} is reachable ({elapsed_ms}ms)")
                else:
                    logger.warning(f"Camera {camera.name} returned status {response.status_code}")

                return is_reachable, elapsed_ms if is_reachable else None

        except httpx.TimeoutException:
            logger.warning(f"Camera {camera.name} connection timed out")
            return False, None

        except httpx.ConnectError:
            logger.warning(f"Camera {camera.name} connection refused")
            return False, None

        except Exception as e:
            logger.warning(f"Camera {camera.name} check failed: {e}")
            return False, None

    async def check_with_image(self, camera: Camera) -> tuple[bool, Optional[bytes]]:
        """
        Check camera connectivity and fetch image.

        Args:
            camera: Camera to check

        Returns:
            Tuple of (is_reachable, image_data or None)
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    camera.url,
                    timeout=self.timeout,
                    follow_redirects=True,
                )

                if response.status_code != 200:
                    return False, None

                # Verify it looks like an image
                content_type = response.headers.get("content-type", "")
                if not content_type.startswith("image/"):
                    logger.warning(f"Camera {camera.name} returned non-image: {content_type}")
                    return True, None  # Reachable but not returning image

                return True, response.content

        except Exception as e:
            logger.warning(f"Camera {camera.name} image fetch failed: {e}")
            return False, None

    async def ping_host(self, camera: Camera) -> bool:
        """
        Simple host reachability check using socket.

        This is a lightweight check that doesn't fetch the image.

        Args:
            camera: Camera to check

        Returns:
            True if host is reachable
        """
        import asyncio

        host = camera.hostname or str(camera.ip_address)
        port = 80  # HTTP port

        try:
            # Create socket connection
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(host, port),
                timeout=5,
            )
            writer.close()
            await writer.wait_closed()
            return True

        except (TimeoutError, OSError):
            return False
