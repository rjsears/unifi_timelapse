"""
Worker Main Entry Point

APScheduler-based worker for scheduled tasks:
- Camera image capture
- Daily timelapse generation
- Multi-day timelapse generation
- Cleanup of old files
"""

import asyncio
import logging
import signal
import sys
import time
from typing import Optional

import redis.asyncio as redis
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

from api.config import get_settings
from api.database import close_db, init_db
from worker.tasks.capture import run_capture_cycle
from worker.tasks.timelapse import run_daily_timelapse_generation
from worker.tasks.multiday import run_multiday_timelapse_generation
from worker.tasks.cleanup import run_cleanup

# Configure logging
settings = get_settings()
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)


async def update_heartbeat() -> None:
    """Update worker heartbeat in Redis."""
    settings = get_settings()
    try:
        r = redis.from_url(settings.redis_url)
        await r.set("worker:heartbeat", str(time.time()), ex=300)  # Expires in 5 minutes
        await r.close()
    except Exception as e:
        logger.warning(f"Failed to update heartbeat: {e}")


class WorkerManager:
    """Manages the worker scheduler and tasks."""

    def __init__(self):
        self.settings = get_settings()
        self.scheduler: Optional[AsyncIOScheduler] = None
        self._shutdown_event = asyncio.Event()

    def _parse_time(self, time_str: str) -> tuple[int, int]:
        """Parse HH:MM time string to hour, minute tuple."""
        parts = time_str.split(":")
        return int(parts[0]), int(parts[1])

    def _get_multiday_day(self) -> str:
        """Convert day name to cron day of week."""
        day_map = {
            "monday": "mon",
            "tuesday": "tue",
            "wednesday": "wed",
            "thursday": "thu",
            "friday": "fri",
            "saturday": "sat",
            "sunday": "sun",
        }
        return day_map.get(self.settings.multiday_generation_day.lower(), "sun")

    async def setup_scheduler(self) -> None:
        """Initialize and configure the scheduler."""
        self.scheduler = AsyncIOScheduler(
            timezone=self.settings.tz,
            job_defaults={
                "coalesce": True,
                "max_instances": 1,
                "misfire_grace_time": 60,
            },
        )

        # Add capture job - runs at capture interval
        self.scheduler.add_job(
            run_capture_cycle,
            trigger=IntervalTrigger(seconds=self.settings.default_capture_interval),
            id="capture_cycle",
            name="Camera Capture Cycle",
            replace_existing=True,
        )
        logger.info(
            f"Scheduled capture cycle every {self.settings.default_capture_interval}s"
        )

        # Add daily timelapse job
        daily_hour, daily_minute = self._parse_time(self.settings.daily_timelapse_time)
        self.scheduler.add_job(
            run_daily_timelapse_generation,
            trigger=CronTrigger(hour=daily_hour, minute=daily_minute),
            id="daily_timelapse",
            name="Daily Timelapse Generation",
            replace_existing=True,
        )
        logger.info(
            f"Scheduled daily timelapse at {self.settings.daily_timelapse_time}"
        )

        # Add multi-day timelapse job
        multiday_hour, multiday_minute = self._parse_time(
            self.settings.multiday_generation_time
        )
        self.scheduler.add_job(
            run_multiday_timelapse_generation,
            trigger=CronTrigger(
                day_of_week=self._get_multiday_day(),
                hour=multiday_hour,
                minute=multiday_minute,
            ),
            id="multiday_timelapse",
            name="Multi-day Timelapse Generation",
            replace_existing=True,
        )
        logger.info(
            f"Scheduled multiday timelapse on {self.settings.multiday_generation_day} "
            f"at {self.settings.multiday_generation_time}"
        )

        # Add cleanup job
        cleanup_hour, cleanup_minute = self._parse_time(self.settings.cleanup_time)
        self.scheduler.add_job(
            run_cleanup,
            trigger=CronTrigger(hour=cleanup_hour, minute=cleanup_minute),
            id="cleanup",
            name="File Cleanup",
            replace_existing=True,
        )
        logger.info(f"Scheduled cleanup at {self.settings.cleanup_time}")

        # Add heartbeat job - runs every 30 seconds
        self.scheduler.add_job(
            update_heartbeat,
            trigger=IntervalTrigger(seconds=30),
            id="heartbeat",
            name="Worker Heartbeat",
            replace_existing=True,
        )
        logger.info("Scheduled heartbeat every 30s")

    async def start(self) -> None:
        """Start the worker."""
        logger.info("Starting UniFi Timelapse Worker...")

        # Initialize database
        await init_db()
        logger.info("Database initialized")

        # Setup and start scheduler
        await self.setup_scheduler()
        self.scheduler.start()
        logger.info("Scheduler started")

        # Send initial heartbeat
        await update_heartbeat()

        # Run initial capture cycle
        logger.info("Running initial capture cycle...")
        try:
            await run_capture_cycle()
        except Exception as e:
            logger.error(f"Initial capture cycle failed: {e}")

        # Wait for shutdown signal
        await self._shutdown_event.wait()

    async def shutdown(self) -> None:
        """Shutdown the worker gracefully."""
        logger.info("Shutting down worker...")

        if self.scheduler:
            self.scheduler.shutdown(wait=True)
            logger.info("Scheduler stopped")

        await close_db()
        logger.info("Database closed")

        self._shutdown_event.set()

    def handle_signal(self, signum: int) -> None:
        """Handle shutdown signals."""
        logger.info(f"Received signal {signum}")
        asyncio.create_task(self.shutdown())


async def main() -> None:
    """Main entry point."""
    manager = WorkerManager()

    # Setup signal handlers
    loop = asyncio.get_event_loop()
    for sig in (signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(sig, lambda s=sig: manager.handle_signal(s))

    try:
        await manager.start()
    except Exception as e:
        logger.exception(f"Worker failed: {e}")
        await manager.shutdown()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
