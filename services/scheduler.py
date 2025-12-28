from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.date import DateTrigger
from datetime import datetime, timedelta
from typing import Optional
import logging

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()


async def schedule_reminder(booking_id: int, booking_datetime: datetime, callback):
    """Schedule a reminder 24 hours before booking"""
    reminder_time = booking_datetime - timedelta(hours=24)
    
    if reminder_time > datetime.now():
        job_id = f"reminder_{booking_id}"
        scheduler.add_job(
            callback,
            trigger=DateTrigger(run_date=reminder_time),
            args=[booking_id],
            id=job_id,
            replace_existing=True
        )
        logger.info(f"Scheduled reminder for booking {booking_id} at {reminder_time}")


async def schedule_feedback_request(
    booking_id: int,
    booking_datetime: datetime,
    duration_minutes: int,
    callback
):
    """Schedule feedback request after booking completion"""
    feedback_time = booking_datetime + timedelta(minutes=duration_minutes)
    
    if feedback_time > datetime.now():
        job_id = f"feedback_{booking_id}"
        scheduler.add_job(
            callback,
            trigger=DateTrigger(run_date=feedback_time),
            args=[booking_id],
            id=job_id,
            replace_existing=True
        )
        logger.info(f"Scheduled feedback request for booking {booking_id} at {feedback_time}")


async def cancel_scheduled_tasks(booking_id: int):
    """Cancel all scheduled tasks for a booking"""
    reminder_job_id = f"reminder_{booking_id}"
    feedback_job_id = f"feedback_{booking_id}"
    
    for job_id in [reminder_job_id, feedback_job_id]:
        try:
            scheduler.remove_job(job_id)
            logger.info(f"Cancelled scheduled task {job_id}")
        except Exception as e:
            logger.debug(f"Job {job_id} not found or already executed: {e}")


def start_scheduler():
    """Start the scheduler"""
    if not scheduler.running:
        scheduler.start()
        logger.info("Scheduler started")


def stop_scheduler():
    """Stop the scheduler"""
    if scheduler.running:
        scheduler.shutdown()
        logger.info("Scheduler stopped")
