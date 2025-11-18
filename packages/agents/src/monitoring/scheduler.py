"""Metric polling scheduler."""
import logging
from typing import Dict, Callable, Any
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

logger = logging.getLogger(__name__)


class MonitoringScheduler:
    """Schedules periodic metric polling jobs."""

    def __init__(self):
        """Initialize scheduler."""
        self.scheduler = AsyncIOScheduler()
        self.jobs: Dict[str, Any] = {}

    def start(self) -> None:
        """Start the scheduler."""
        self.scheduler.start()
        logger.info("Monitoring scheduler started")

    def stop(self) -> None:
        """Stop the scheduler."""
        self.scheduler.shutdown()
        logger.info("Monitoring scheduler stopped")

    def add_polling_job(
        self,
        job_id: str,
        func: Callable,
        interval_seconds: int,
        args: tuple = (),
    ) -> None:
        """
        Add periodic polling job.

        Args:
            job_id: Unique job identifier
            func: Function to call
            interval_seconds: Polling interval
            args: Function arguments
        """
        trigger = IntervalTrigger(seconds=interval_seconds)
        job = self.scheduler.add_job(
            func, trigger=trigger, id=job_id, args=args, replace_existing=True
        )
        self.jobs[job_id] = job
        logger.info(f"Added polling job: {job_id} (interval={interval_seconds}s)")

    def remove_job(self, job_id: str) -> None:
        """
        Remove polling job.

        Args:
            job_id: Job identifier
        """
        if job_id in self.jobs:
            self.scheduler.remove_job(job_id)
            del self.jobs[job_id]
            logger.info(f"Removed polling job: {job_id}")

    def get_job_status(self, job_id: str) -> Dict[str, Any]:
        """
        Get job status.

        Args:
            job_id: Job identifier

        Returns:
            Job status dictionary
        """
        if job_id not in self.jobs:
            return {"status": "not_found"}

        job = self.jobs[job_id]
        return {
            "status": "running" if job.next_run_time else "stopped",
            "next_run": str(job.next_run_time) if job.next_run_time else None,
        }

