"""
Background cleanup service for old sessions and files.

This module provides scheduled cleanup tasks to remove old sessions
and their associated files from the system.
"""
import logging
from datetime import datetime

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from app.core.config import get_settings
from app.db.database import get_session_factory
from app.services.session_manager import SessionManager

# Configure logging
logger = logging.getLogger(__name__)

# Global scheduler instance
_scheduler: AsyncIOScheduler | None = None


async def cleanup_old_sessions() -> None:
    """
    Cleanup task to remove old sessions and files.

    This runs periodically to clean up sessions that haven't been
    accessed within the configured time period.
    """
    settings = get_settings()
    session_factory = get_session_factory()

    try:
        logger.info(
            f"Starting cleanup task: removing sessions older than "
            f"{settings.session_cleanup_hours} hours"
        )

        async with session_factory() as db:
            session_manager = SessionManager(settings)
            sessions_deleted, files_deleted = await session_manager.cleanup_old_sessions(
                db=db,
                hours=settings.session_cleanup_hours,
            )

        if sessions_deleted > 0 or files_deleted > 0:
            logger.info(
                f"Cleanup completed: deleted {sessions_deleted} sessions "
                f"and {files_deleted} files"
            )
        else:
            logger.debug("Cleanup completed: no old sessions to remove")

    except Exception as e:
        logger.error(f"Error during cleanup task: {e}", exc_info=True)


def start_cleanup_scheduler() -> None:
    """
    Start the background cleanup scheduler.

    This should be called during application startup.
    """
    global _scheduler
    settings = get_settings()

    if _scheduler is not None:
        logger.warning("Cleanup scheduler already running")
        return

    # Create scheduler
    _scheduler = AsyncIOScheduler()

    # Add cleanup job
    interval_hours = settings.session_cleanup_interval_hours
    _scheduler.add_job(
        cleanup_old_sessions,
        trigger=IntervalTrigger(hours=interval_hours),
        id="cleanup_old_sessions",
        name="Cleanup old sessions and files",
        replace_existing=True,
    )

    # Start scheduler
    _scheduler.start()
    logger.info(
        f"Cleanup scheduler started: running every {interval_hours} hours, "
        f"removing sessions older than {settings.session_cleanup_hours} hours"
    )


def stop_cleanup_scheduler() -> None:
    """
    Stop the background cleanup scheduler.

    This should be called during application shutdown.
    """
    global _scheduler

    if _scheduler is not None:
        _scheduler.shutdown(wait=False)
        _scheduler = None
        logger.info("Cleanup scheduler stopped")


def get_scheduler() -> AsyncIOScheduler | None:
    """Get the current scheduler instance."""
    return _scheduler
