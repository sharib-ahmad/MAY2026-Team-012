import logging
import os
from datetime import UTC, datetime
from zoneinfo import ZoneInfo

from celery import Celery
from sqlalchemy import select

from app.core.config import get_settings
from app.db import registry as _model_registry  # noqa: F401
from app.db.session import make_engine, make_session_factory

logger = logging.getLogger("celery_tasks")

settings = get_settings()

# Configure Celery with Redis broker and backend
broker_url = os.getenv("CELERY_BROKER_URL", settings.CELERY_BROKER_URL)
result_backend = os.getenv("CELERY_RESULT_BACKEND", settings.CELERY_RESULT_BACKEND)

celery_app = Celery(
    "verdeza_tasks",
    broker=broker_url,
    backend=result_backend,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone=settings.PILOT_TIMEZONE,
    enable_utc=True,
)

# Celery beat schedule setup
celery_app.conf.beat_schedule = {
    "generate-daily-pickup-schedules": {
        "task": "app.core.celery_app.generate_daily_schedules",
        # For manual testing: runs every 5 minutes (300 seconds)
        "schedule": 300.0,
        # To set for 1 day or daily (production), use crontab instead:
        # "schedule": crontab(hour=0, minute=0),
    }
}


@celery_app.task(name="app.core.celery_app.generate_daily_schedules")
def generate_daily_schedules():
    """Celery task to generate daily pickup schedules for all active collectors."""
    logger.info("Celery: Starting daily pickup schedule generation task...")

    engine = make_engine(settings.DATABASE_URL)
    session_factory = make_session_factory(engine)

    # Use midnight of today in pilot local timezone converted to UTC
    pilot_tz = ZoneInfo(settings.PILOT_TIMEZONE)
    local_now = datetime.now(pilot_tz)
    local_midnight = local_now.replace(hour=0, minute=0, second=0, microsecond=0)
    today_start = local_midnight.astimezone(UTC)

    with session_factory() as db:
        try:
            from app.features.collection_ops.models import DailyPickupSchedule
            from app.features.collection_ops.router import _materialize_assigned_bulk_stops
            from app.features.users.models import User
            from app.models.enums import Role, UserStatus

            # Query active collectors who are assigned to a ward (zone_id is not null)
            collectors = db.scalars(
                select(User).where(
                    User.role == Role.COLLECTION_WORKER,
                    User.status == UserStatus.ACTIVE,
                    User.deleted_at.is_(None),
                    User.zone_id.is_not(None),
                )
            ).all()

            logger.info(f"Celery: Found {len(collectors)} active collectors with assigned wards.")

            from datetime import timedelta

            from app.features.bulk_pickups.models import BulkPickupRequest
            from app.features.notifications.models import Notification
            from app.models.enums import BulkRequestStatus

            today_end = today_start + timedelta(days=1)

            for collector in collectors:
                # We no longer delete or reset assignments here to prevent changing stop UUIDs
                # and breaking active routes/UI for collectors when the task runs periodically.
                pass

                # 1. Automatically assign any PENDING bulk pickup requests for today
                # in this collector's ward to them
                pending_requests = db.scalars(
                    select(BulkPickupRequest).where(
                        BulkPickupRequest.zone_id == collector.zone_id,
                        BulkPickupRequest.status == BulkRequestStatus.PENDING,
                        BulkPickupRequest.requested_date >= today_start,
                        BulkPickupRequest.requested_date < today_end,
                    )
                ).all()

                for req in pending_requests:
                    req.assigned_collector_id = collector.id
                    req.status = BulkRequestStatus.ASSIGNED
                    req.decided_at = datetime.now(UTC)

                    db.add_all(
                        [
                            Notification(
                                user_id=req.requester_id,
                                title="Bulk pickup assigned",
                                body=f"{req.ref_code} has been assigned to {collector.name}.",
                            ),
                            Notification(
                                user_id=collector.id,
                                title="New bulk pickup assignment",
                                body=f"You were assigned {req.ref_code} in your ward.",
                            ),
                        ]
                    )
                    logger.info(
                        f"Celery: Automatically assigned pending request {req.ref_code} "
                        f"in ward {collector.zone_id} to collector {collector.name}"
                    )

                # Flush assignments so that materialization finds them
                db.flush()

                # 2. Ensure schedule exists for today_start
                schedule = db.scalar(
                    select(DailyPickupSchedule).where(
                        DailyPickupSchedule.collector_id == collector.id,
                        DailyPickupSchedule.zone_id == collector.zone_id,
                        DailyPickupSchedule.schedule_date == today_start,
                        DailyPickupSchedule.is_active.is_(True),
                    )
                )
                if not schedule:
                    schedule = DailyPickupSchedule(
                        collector_id=collector.id,
                        zone_id=collector.zone_id,
                        schedule_date=today_start,
                        total_stops=0,
                        completed_stops=0,
                        is_active=True,
                    )
                    db.add(schedule)
                    db.flush()
                    logger.info(
                        f"Celery: Created new DailyPickupSchedule for collector {collector.name} "
                        f"(ward ID: {collector.zone_id}) for date {today_start}"
                    )

                # 3. Materialize any bulk requests assigned to this collector
                materialized = _materialize_assigned_bulk_stops(db, collector)
                if materialized:
                    logger.info(
                        f"Celery: Materialized assigned bulk stops for collector {collector.name}"
                    )

            db.commit()
            logger.info("Celery: Daily pickup schedule generation task completed successfully.")
        except Exception as e:
            db.rollback()
            logger.exception(f"Celery: Error during daily pickup schedule generation: {e}")
            raise e
        finally:
            engine.dispose()
