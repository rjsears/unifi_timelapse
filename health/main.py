"""
Health Monitor Main Entry Point

Lightweight monitoring service for camera health checks.
"""

import asyncio
import logging
import signal
import sys

from sqlalchemy import select

from api.config import get_settings
from api.database import close_db, get_db_context, init_db
from api.models.camera import Camera
from health.alerter import HealthAlerter
from health.checks.connectivity import ConnectivityChecker
from health.checks.image_quality import ImageQualityChecker
from health.checks.uptime import UptimeTracker

# Configure logging
settings = get_settings()
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)


class HealthMonitor:
    """Camera health monitoring service."""

    def __init__(self):
        self.settings = get_settings()
        self._shutdown_event = asyncio.Event()
        self.connectivity_checker = ConnectivityChecker()
        self.image_checker = ImageQualityChecker()
        self.uptime_tracker = UptimeTracker()
        self.alerter = HealthAlerter()

    async def run_health_checks(self) -> None:
        """Run all health checks for all cameras."""
        async with get_db_context() as db:
            # Get all active cameras
            result = await db.execute(
                select(Camera).where(Camera.is_active == True)
            )
            cameras = result.scalars().all()

            if not cameras:
                logger.debug("No active cameras to check")
                return

            logger.debug(f"Running health checks on {len(cameras)} camera(s)")

            for camera in cameras:
                try:
                    # Run connectivity check
                    is_reachable = await self.connectivity_checker.check(camera)

                    if not is_reachable:
                        logger.warning(f"Camera {camera.name} is unreachable")
                        await self.alerter.alert_camera_down(
                            db=db,
                            camera=camera,
                        )
                        continue

                    # Update uptime
                    await self.uptime_tracker.record_check(
                        db=db,
                        camera=camera,
                        is_reachable=is_reachable,
                    )

                except Exception as e:
                    logger.error(f"Health check failed for {camera.name}: {e}")

    async def run_image_quality_checks(self) -> None:
        """Run image quality checks for all cameras."""
        async with get_db_context() as db:
            result = await db.execute(
                select(Camera).where(Camera.is_active == True)
            )
            cameras = result.scalars().all()

            for camera in cameras:
                try:
                    # Check for blank images
                    is_blank = await self.image_checker.check_blank(
                        db=db,
                        camera=camera,
                    )
                    if is_blank:
                        await self.alerter.alert_blank_image(db=db, camera=camera)

                    # Check for frozen images
                    is_frozen = await self.image_checker.check_frozen(
                        db=db,
                        camera=camera,
                    )
                    if is_frozen:
                        await self.alerter.alert_frozen_image(db=db, camera=camera)

                except Exception as e:
                    logger.error(f"Image quality check failed for {camera.name}: {e}")

    async def start(self) -> None:
        """Start the health monitor."""
        logger.info("Starting UniFi Timelapse Health Monitor...")

        # Initialize database
        await init_db()
        logger.info("Database initialized")

        # Initialize alerter
        await self.alerter.initialize()

        # Create tasks for different check intervals
        health_task = asyncio.create_task(self._health_check_loop())
        quality_task = asyncio.create_task(self._quality_check_loop())

        # Wait for shutdown
        await self._shutdown_event.wait()

        # Cancel tasks
        health_task.cancel()
        quality_task.cancel()

        try:
            await asyncio.gather(health_task, quality_task, return_exceptions=True)
        except asyncio.CancelledError:
            pass

    async def _health_check_loop(self) -> None:
        """Continuous health check loop."""
        while not self._shutdown_event.is_set():
            try:
                await self.run_health_checks()
            except Exception as e:
                logger.exception(f"Health check loop error: {e}")

            try:
                await asyncio.wait_for(
                    self._shutdown_event.wait(),
                    timeout=self.settings.health_check_interval,
                )
                break
            except TimeoutError:
                continue

    async def _quality_check_loop(self) -> None:
        """Continuous image quality check loop."""
        while not self._shutdown_event.is_set():
            try:
                await self.run_image_quality_checks()
            except Exception as e:
                logger.exception(f"Image quality check loop error: {e}")

            try:
                await asyncio.wait_for(
                    self._shutdown_event.wait(),
                    timeout=self.settings.blank_check_interval,
                )
                break
            except TimeoutError:
                continue

    async def shutdown(self) -> None:
        """Shutdown the health monitor gracefully."""
        logger.info("Shutting down health monitor...")
        self._shutdown_event.set()
        await close_db()
        logger.info("Health monitor stopped")

    def handle_signal(self, signum: int) -> None:
        """Handle shutdown signals."""
        logger.info(f"Received signal {signum}")
        asyncio.create_task(self.shutdown())


async def main() -> None:
    """Main entry point."""
    monitor = HealthMonitor()

    # Setup signal handlers
    loop = asyncio.get_event_loop()
    for sig in (signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(sig, lambda s=sig: monitor.handle_signal(s))

    try:
        await monitor.start()
    except Exception as e:
        logger.exception(f"Health monitor failed: {e}")
        await monitor.shutdown()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
