"""
Health Alerter

Send alerts for camera health issues with cooldown support.
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import Dict, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from api.config import get_settings
from api.models.camera import Camera
from api.services.notification import NotificationService

logger = logging.getLogger(__name__)


class HealthAlerter:
    """Send health alerts with cooldown to prevent spam."""

    def __init__(self):
        self.settings = get_settings()
        # Track last alert time per camera per alert type
        self._last_alerts: Dict[str, datetime] = {}
        self._notification_service: Optional[NotificationService] = None

    async def initialize(self) -> None:
        """Initialize the alerter."""
        logger.info("Health alerter initialized")

    def _get_alert_key(self, camera_id: str, alert_type: str) -> str:
        """Get unique key for alert tracking."""
        return f"{camera_id}:{alert_type}"

    def _can_alert(self, camera_id: str, alert_type: str) -> bool:
        """Check if we can send an alert (cooldown check)."""
        key = self._get_alert_key(camera_id, alert_type)
        last_alert = self._last_alerts.get(key)

        if last_alert is None:
            return True

        cooldown = timedelta(minutes=self.settings.alert_cooldown_minutes)
        return datetime.now(timezone.utc) - last_alert > cooldown

    def _record_alert(self, camera_id: str, alert_type: str) -> None:
        """Record that an alert was sent."""
        key = self._get_alert_key(camera_id, alert_type)
        self._last_alerts[key] = datetime.now(timezone.utc)

    async def alert_camera_down(
        self,
        db: AsyncSession,
        camera: Camera,
    ) -> bool:
        """
        Send alert for camera being unreachable.

        Args:
            db: Database session
            camera: Camera that is down

        Returns:
            True if alert was sent
        """
        if not self._can_alert(str(camera.id), "camera_down"):
            logger.debug(f"Alert cooldown active for {camera.name} camera_down")
            return False

        notification_service = NotificationService(db)

        last_seen = None
        if camera.last_capture_at:
            last_seen = camera.last_capture_at.strftime("%Y-%m-%d %H:%M:%S UTC")

        sent = await notification_service.notify_camera_down(
            camera_name=camera.name,
            last_seen=last_seen,
        )

        if sent:
            self._record_alert(str(camera.id), "camera_down")
            logger.info(f"Sent camera down alert for {camera.name}")

        return sent

    async def alert_blank_image(
        self,
        db: AsyncSession,
        camera: Camera,
    ) -> bool:
        """
        Send alert for camera producing blank images.

        Args:
            db: Database session
            camera: Camera producing blank images

        Returns:
            True if alert was sent
        """
        if not self._can_alert(str(camera.id), "blank_image"):
            logger.debug(f"Alert cooldown active for {camera.name} blank_image")
            return False

        notification_service = NotificationService(db)

        sent = await notification_service.send_notification(
            title=f"Blank Image Detected: {camera.name}",
            body=(
                f"Camera '{camera.name}' is producing blank/dark images.\n\n"
                "This may indicate a camera issue, lens obstruction, or lighting problem."
            ),
            notification_type="warning",
        )

        if sent:
            self._record_alert(str(camera.id), "blank_image")
            logger.info(f"Sent blank image alert for {camera.name}")

        return sent

    async def alert_frozen_image(
        self,
        db: AsyncSession,
        camera: Camera,
    ) -> bool:
        """
        Send alert for camera producing frozen/identical images.

        Args:
            db: Database session
            camera: Camera producing frozen images

        Returns:
            True if alert was sent
        """
        if not self._can_alert(str(camera.id), "frozen_image"):
            logger.debug(f"Alert cooldown active for {camera.name} frozen_image")
            return False

        notification_service = NotificationService(db)

        sent = await notification_service.send_notification(
            title=f"Frozen Image Detected: {camera.name}",
            body=(
                f"Camera '{camera.name}' is producing identical images.\n\n"
                "This may indicate the camera feed is frozen or stuck."
            ),
            notification_type="warning",
        )

        if sent:
            self._record_alert(str(camera.id), "frozen_image")
            logger.info(f"Sent frozen image alert for {camera.name}")

        return sent

    async def alert_capture_failure(
        self,
        db: AsyncSession,
        camera: Camera,
        error: str,
        consecutive_failures: int,
    ) -> bool:
        """
        Send alert for consecutive capture failures.

        Args:
            db: Database session
            camera: Camera with failures
            error: Error message
            consecutive_failures: Number of consecutive failures

        Returns:
            True if alert was sent
        """
        if consecutive_failures < self.settings.min_failures_before_alert:
            return False

        if not self._can_alert(str(camera.id), "capture_failure"):
            logger.debug(f"Alert cooldown active for {camera.name} capture_failure")
            return False

        notification_service = NotificationService(db)

        sent = await notification_service.notify_capture_failure(
            camera_name=camera.name,
            error=error,
            consecutive_failures=consecutive_failures,
        )

        if sent:
            self._record_alert(str(camera.id), "capture_failure")
            logger.info(f"Sent capture failure alert for {camera.name}")

        return sent

    def clear_cooldown(self, camera_id: str, alert_type: Optional[str] = None) -> None:
        """
        Clear cooldown for a camera's alerts.

        Args:
            camera_id: Camera UUID
            alert_type: Specific alert type or None for all
        """
        if alert_type:
            key = self._get_alert_key(camera_id, alert_type)
            self._last_alerts.pop(key, None)
        else:
            # Clear all alerts for this camera
            keys_to_remove = [
                k for k in self._last_alerts.keys()
                if k.startswith(f"{camera_id}:")
            ]
            for key in keys_to_remove:
                del self._last_alerts[key]
