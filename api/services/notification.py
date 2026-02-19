"""
Notification Service

Send notifications via Apprise.
"""

import logging
from typing import Optional

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.config import get_settings
from api.models.notification_config import NotificationConfig

logger = logging.getLogger(__name__)


class NotificationService:
    """Service for sending notifications via Apprise."""

    def __init__(self, db: Optional[AsyncSession] = None):
        self.db = db
        self.settings = get_settings()

    async def send_notification(
        self,
        title: str,
        body: str,
        notification_type: str = "info",
        apprise_url: Optional[str] = None,
    ) -> bool:
        """
        Send a notification via Apprise.

        Args:
            title: Notification title
            body: Notification body
            notification_type: Type (info, success, warning, failure)
            apprise_url: Optional specific Apprise URL to use

        Returns:
            True if sent successfully
        """
        if not self.settings.apprise_enabled:
            logger.debug("Notifications disabled, skipping")
            return False

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.settings.apprise_url}/notify",
                    json={
                        "urls": apprise_url or "",
                        "title": title,
                        "body": body,
                        "type": notification_type,
                    },
                    timeout=30,
                )
                response.raise_for_status()
                logger.info(f"Notification sent: {title}")
                return True

        except Exception as e:
            logger.warning(f"Failed to send notification: {e}")
            return False

    async def notify_capture_failure(
        self,
        camera_name: str,
        error: str,
        consecutive_failures: int,
    ) -> bool:
        """
        Send notification about capture failure.

        Only sends if consecutive failures exceed threshold.

        Args:
            camera_name: Name of the camera
            error: Error message
            consecutive_failures: Number of consecutive failures

        Returns:
            True if notification sent
        """
        if self.db is None:
            return False

        # Check if we should notify
        result = await self.db.execute(
            select(NotificationConfig).where(
                NotificationConfig.is_enabled == True,
                NotificationConfig.notify_on_capture_fail == True,
            )
        )
        configs = result.scalars().all()

        for config in configs:
            if consecutive_failures >= config.min_failures_before_alert:
                await self.send_notification(
                    title=f"Camera Capture Failed: {camera_name}",
                    body=f"Camera '{camera_name}' has failed {consecutive_failures} times.\n\nError: {error}",
                    notification_type="failure",
                    apprise_url=config.apprise_url,
                )
                return True

        return False

    async def notify_timelapse_complete(
        self,
        camera_name: str,
        timelapse_type: str,
        date_range: str,
        frame_count: int,
    ) -> bool:
        """
        Send notification about timelapse completion.

        Args:
            camera_name: Name of the camera
            timelapse_type: Type of timelapse (daily or multiday)
            date_range: Date range string
            frame_count: Number of frames in timelapse

        Returns:
            True if notification sent
        """
        if self.db is None:
            return False

        result = await self.db.execute(
            select(NotificationConfig).where(
                NotificationConfig.is_enabled == True,
                NotificationConfig.notify_on_timelapse_done == True,
            )
        )
        configs = result.scalars().all()

        for config in configs:
            await self.send_notification(
                title=f"Timelapse Complete: {camera_name}",
                body=f"{timelapse_type.capitalize()} timelapse for '{camera_name}' has been generated.\n\nDate: {date_range}\nFrames: {frame_count}",
                notification_type="success",
                apprise_url=config.apprise_url,
            )

        return len(configs) > 0

    async def notify_camera_down(
        self,
        camera_name: str,
        last_seen: Optional[str] = None,
    ) -> bool:
        """
        Send notification about camera being unreachable.

        Args:
            camera_name: Name of the camera
            last_seen: Last seen timestamp

        Returns:
            True if notification sent
        """
        if self.db is None:
            return False

        result = await self.db.execute(
            select(NotificationConfig).where(
                NotificationConfig.is_enabled == True,
                NotificationConfig.notify_on_camera_down == True,
            )
        )
        configs = result.scalars().all()

        body = f"Camera '{camera_name}' is unreachable."
        if last_seen:
            body += f"\n\nLast seen: {last_seen}"

        for config in configs:
            await self.send_notification(
                title=f"Camera Down: {camera_name}",
                body=body,
                notification_type="failure",
                apprise_url=config.apprise_url,
            )

        return len(configs) > 0

    async def notify_storage_warning(
        self,
        percent_used: float,
        free_bytes: int,
    ) -> bool:
        """
        Send notification about low storage.

        Args:
            percent_used: Percentage of storage used
            free_bytes: Free bytes remaining

        Returns:
            True if notification sent
        """
        if self.db is None:
            return False

        result = await self.db.execute(
            select(NotificationConfig).where(
                NotificationConfig.is_enabled == True,
                NotificationConfig.notify_on_storage_warn == True,
            )
        )
        configs = result.scalars().all()

        free_gb = free_bytes / (1024**3)

        for config in configs:
            await self.send_notification(
                title="Storage Warning",
                body=f"Storage is {percent_used:.1f}% full.\n\nFree space: {free_gb:.2f} GB",
                notification_type="warning",
                apprise_url=config.apprise_url,
            )

        return len(configs) > 0
