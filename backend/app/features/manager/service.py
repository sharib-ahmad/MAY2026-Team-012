"""Database-backed read model for the municipal manager dashboard."""

from collections import defaultdict
from datetime import UTC, datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from app.features.bulk_pickups.models import BulkPickupRequest
from app.features.collection_ops.models import (
    DailyPickupSchedule,
    DailyPickupStop,
    DelayLog,
    MixedWasteTag,
)
from app.features.complaints.models import Ticket
from app.features.notifications.models import Notification
from app.features.users.models import User
from app.models.enums import Availability, BulkRequestStatus, PickupStopStatus, Role, TicketStatus
from app.models.zone import Zone

OPEN_TICKET_STATUSES = {TicketStatus.OPEN, TicketStatus.IN_PROGRESS, TicketStatus.REOPENED}


def notify_zone_managers(db: Session, zone_id, title: str, body: str) -> None:
    """Notify the manager assigned to a ward, with a legacy zone-member fallback."""
    manager_ids = set(db.scalars(select(Zone.manager_id).where(Zone.id == zone_id)).all())
    manager_ids.discard(None)
    manager_ids.update(
        db.scalars(
            select(User.id).where(
                User.role == Role.MUNICIPAL_OFFICER,
                User.zone_id == zone_id,
                User.deleted_at.is_(None),
            )
        ).all()
    )
    db.add_all(
        Notification(user_id=manager_id, title=title, body=body) for manager_id in manager_ids
    )


def get_managed_zone_ids(db: Session, manager: User) -> list:
    """Return only wards explicitly assigned to this manager."""
    zone_ids = list(db.scalars(select(Zone.id).where(Zone.manager_id == manager.id)).all())
    if manager.zone_id and manager.zone_id not in zone_ids:
        zone_ids.append(manager.zone_id)
    return zone_ids


def _day_bounds(now: datetime) -> tuple[datetime, datetime]:
    start = now.astimezone(UTC).replace(hour=0, minute=0, second=0, microsecond=0)
    return start, start + timedelta(days=1)


def _ticket_severity(ticket: Ticket) -> str:
    """Tickets have no persisted severity yet; prioritise operationally urgent types."""
    if ticket.issue_type.value in {"MISSED_PICKUP", "OVERFLOW", "MIXED_WASTE"}:
        return "HIGH"
    return "MEDIUM"


def _schedule_status(schedule: DailyPickupSchedule) -> str:
    if schedule.completed_at or (
        schedule.total_stops and schedule.completed_stops >= schedule.total_stops
    ):
        return "COMPLETED"
    if schedule.completed_stops > 0:
        return "IN_PROGRESS"
    return "ASSIGNED"


def get_dashboard_data(db: Session, manager: User, now: datetime | None = None) -> dict:
    """Build a consistent manager view from persisted operational records.

    A manager sees only explicitly assigned wards. The legacy ``users.zone_id``
    assignment remains supported while the zone-manager relationship is rolled
    out.
    """
    now = now or datetime.now(UTC)
    today_start, tomorrow_start = _day_bounds(now)
    managed_ids = get_managed_zone_ids(db, manager)
    zones = db.scalars(
        select(Zone).where(Zone.id.in_(managed_ids) if managed_ids else False).order_by(Zone.code)
    ).all()
    zone_ids = [zone.id for zone in zones]
    all_zones = db.scalars(select(Zone).order_by(Zone.code)).all()
    all_zone_ids = [zone.id for zone in all_zones]

    tickets = (
        db.scalars(
            select(Ticket)
            .where(Ticket.zone_id.in_(zone_ids) if zone_ids else False)
            .options(
                joinedload(Ticket.zone),
                joinedload(Ticket.raised_by),
                joinedload(Ticket.resolved_by),
            )
            .order_by(Ticket.created_at.desc())
        )
        .unique()
        .all()
    )
    schedules = (
        db.scalars(
            select(DailyPickupSchedule)
            .where(
                DailyPickupSchedule.zone_id.in_(zone_ids) if zone_ids else False,
                DailyPickupSchedule.schedule_date >= today_start,
                DailyPickupSchedule.schedule_date < tomorrow_start,
            )
            .options(
                joinedload(DailyPickupSchedule.zone), joinedload(DailyPickupSchedule.collector)
            )
            .order_by(DailyPickupSchedule.schedule_date, DailyPickupSchedule.created_at)
        )
        .unique()
        .all()
    )
    schedule_ids = [schedule.id for schedule in schedules]
    stops = (
        db.scalars(
            select(DailyPickupStop)
            .where(DailyPickupStop.schedule_id.in_(schedule_ids) if schedule_ids else False)
            .options(joinedload(DailyPickupStop.pickup))
            .order_by(DailyPickupStop.schedule_id, DailyPickupStop.pickup_order)
        )
        .unique()
        .all()
    )
    stops_by_schedule: dict[object, list[DailyPickupStop]] = defaultdict(list)
    for stop in stops:
        stops_by_schedule[stop.schedule_id].append(stop)

    coverage_schedules = db.scalars(
        select(DailyPickupSchedule).where(
            DailyPickupSchedule.schedule_date >= today_start,
            DailyPickupSchedule.schedule_date < tomorrow_start,
        )
    ).all()
    coverage_schedule_ids = [schedule.id for schedule in coverage_schedules]
    coverage_stops = db.scalars(
        select(DailyPickupStop).where(
            DailyPickupStop.schedule_id.in_(coverage_schedule_ids)
            if coverage_schedule_ids
            else False
        )
    ).all()
    coverage_stops_by_zone: dict[object, list[DailyPickupStop]] = defaultdict(list)
    coverage_schedule_zones = {schedule.id: schedule.zone_id for schedule in coverage_schedules}
    for stop in coverage_stops:
        coverage_stops_by_zone[coverage_schedule_zones[stop.schedule_id]].append(stop)
    all_collectors = db.scalars(
        select(User).where(User.role == Role.COLLECTION_WORKER, User.deleted_at.is_(None))
    ).all()

    workers = (
        db.scalars(
            select(User)
            .where(
                User.role == Role.COLLECTION_WORKER,
                User.deleted_at.is_(None),
                User.zone_id.in_(zone_ids) if zone_ids else False,
            )
            .options(joinedload(User.zone))
            .order_by(User.name)
        )
        .unique()
        .all()
    )
    crew_members = workers
    schedule_by_worker = {schedule.collector_id: schedule for schedule in schedules}
    households_by_zone = dict(
        db.execute(
            select(User.zone_id, func.count(User.id))
            .where(
                User.role == Role.CITIZEN,
                User.deleted_at.is_(None),
                User.zone_id.in_(all_zone_ids) if all_zone_ids else False,
            )
            .group_by(User.zone_id)
        ).all()
    )
    stops_by_zone: dict[object, list[DailyPickupStop]] = defaultdict(list)
    schedule_zone_ids = {schedule.id: schedule.zone_id for schedule in schedules}
    for stop in stops:
        stops_by_zone[schedule_zone_ids[stop.schedule_id]].append(stop)
    bulk_requests = (
        db.scalars(
            select(BulkPickupRequest)
            .where(
                BulkPickupRequest.zone_id.in_(zone_ids) if zone_ids else False,
                BulkPickupRequest.status != BulkRequestStatus.CANCELLED,
            )
            .options(
                joinedload(BulkPickupRequest.zone),
                joinedload(BulkPickupRequest.requester),
                joinedload(BulkPickupRequest.assigned_collector),
            )
            .order_by(BulkPickupRequest.created_at.desc())
        )
        .unique()
        .all()
    )
    bulk_mixed_waste_rows = [
        {
            "id": str(request.id),
            "route_code": request.ref_code,
            "ward_code": request.zone.code,
            "point_label": request.requester.name,
            "severity": request.flag_severity.value if request.flag_severity else "ROUTINE",
            "note": request.flag_note,
            "flagged_at": request.collected_at,
        }
        for request in bulk_requests
        if request.is_flagged
    ]
    notifications = db.scalars(
        select(Notification)
        .where(Notification.user_id == manager.id, Notification.is_read.is_(False))
        .order_by(Notification.created_at.desc())
        .limit(10)
    ).all()

    delays = (
        db.scalars(
            select(DelayLog)
            .join(DelayLog.stop)
            .join(DailyPickupStop.schedule)
            .where(DailyPickupSchedule.zone_id.in_(zone_ids) if zone_ids else False)
            .options(
                joinedload(DelayLog.worker),
                joinedload(DelayLog.stop)
                .joinedload(DailyPickupStop.schedule)
                .joinedload(DailyPickupSchedule.zone),
            )
            .order_by(DelayLog.created_at.desc())
            .limit(20)
        )
        .unique()
        .all()
    )
    mixed_waste = (
        db.scalars(
            select(MixedWasteTag)
            .join(MixedWasteTag.stop)
            .join(DailyPickupStop.schedule)
            .where(DailyPickupSchedule.zone_id.in_(zone_ids) if zone_ids else False)
            .options(
                joinedload(MixedWasteTag.stop).joinedload(DailyPickupStop.pickup),
                joinedload(MixedWasteTag.stop)
                .joinedload(DailyPickupStop.schedule)
                .joinedload(DailyPickupSchedule.zone),
            )
            .order_by(MixedWasteTag.created_at.desc())
            .limit(20)
        )
        .unique()
        .all()
    )

    complaint_rows = [
        {
            "id": str(ticket.id),
            "ref_code": ticket.ref_code,
            "ward_code": ticket.zone.code if ticket.zone else "Unassigned",
            "citizen_name": ticket.raised_by.name if ticket.raised_by else "Unknown resident",
            "citizen_type": "RESIDENT",
            "issue_type": ticket.issue_type.value,
            "severity": _ticket_severity(ticket),
            "status": ticket.status.value,
            "description": ticket.description,
            "resolution_notes": ticket.resolution_notes,
            "resolved_at": ticket.resolved_at,
            "resolver_name": ticket.resolved_by.name if ticket.resolved_by else None,
            "created_at": ticket.created_at,
        }
        for ticket in tickets
    ]
    all_open_counts = dict(
        db.execute(
            select(Ticket.zone_id, func.count(Ticket.id))
            .where(Ticket.status.in_(OPEN_TICKET_STATUSES))
            .group_by(Ticket.zone_id)
        ).all()
    )
    route_rows = []
    for schedule in schedules:
        route_stops = stops_by_schedule[schedule.id]
        collected = sum(stop.status == PickupStopStatus.COLLECTED for stop in route_stops)
        route_rows.append(
            {
                "id": str(schedule.id),
                "code": f"SCH-{str(schedule.id)[:8].upper()}",
                "ward_code": schedule.zone.code,
                "worker_id": str(schedule.collector_id),
                "worker_name": schedule.collector.name,
                "vehicle": "Not recorded",
                "shift": "MORNING" if schedule.schedule_date.hour < 12 else "EVENING",
                "status": _schedule_status(schedule),
                "started_at": schedule.generated_at,
                "last_update_at": schedule.updated_at,
                "points_total": len(route_stops),
                "points_collected": collected,
                "points": [
                    {
                        "seq": stop.pickup_order,
                        "label": stop.pickup.ref_code,
                        "status": stop.status.value,
                        "updated_at": stop.completed_at,
                    }
                    for stop in route_stops
                ],
            }
        )

    filed_by_day: dict[datetime.date, int] = defaultdict(int)
    resolved_by_day: dict[datetime.date, int] = defaultdict(int)
    for ticket in tickets:
        if ticket.created_at >= today_start - timedelta(days=6):
            filed_by_day[ticket.created_at.date()] += 1
        if ticket.resolved_at and ticket.resolved_at >= today_start - timedelta(days=6):
            resolved_by_day[ticket.resolved_at.date()] += 1
    trend = []
    for days_ago in range(6, -1, -1):
        day = (today_start - timedelta(days=days_ago)).date()
        trend.append(
            {
                "day": day.strftime("%a"),
                "filed": filed_by_day[day],
                "resolved": resolved_by_day[day],
            }
        )

    resolved_this_week = sum(
        ticket.resolved_at is not None and ticket.resolved_at >= today_start - timedelta(days=6)
        for ticket in tickets
    )
    resolution_hours = [
        (ticket.resolved_at - ticket.created_at).total_seconds() / 3600
        for ticket in tickets
        if ticket.resolved_at
    ]
    return {
        "stats": {
            "open_complaints": sum(ticket.status in OPEN_TICKET_STATUSES for ticket in tickets),
            "escalated_complaints": 0,
            "routes_completed_today": sum(route["status"] == "COMPLETED" for route in route_rows),
            "routes_today": len(route_rows),
            "route_points_collected": sum(route["points_collected"] for route in route_rows),
            "route_points_total": sum(route["points_total"] for route in route_rows),
            "active_workers": sum(
                worker.availability == Availability.ON_ROUTE for worker in workers
            ),
            "collectors_assigned": len(workers),
            "wards_supervised": len(zones),
            "resolved_this_week": resolved_this_week,
            "avg_resolution_hours": round(sum(resolution_hours) / len(resolution_hours), 1)
            if resolution_hours
            else 0,
        },
        "wards": [
            {
                "id": str(zone.id),
                "code": zone.code,
                "name": zone.name,
                "households": households_by_zone.get(zone.id, 0),
                "stops_today": len(stops_by_zone[zone.id]),
                "active_workers": sum(worker.zone_id == zone.id for worker in workers),
                "coverage_pct": round(
                    100
                    * sum(
                        stop.status == PickupStopStatus.COLLECTED for stop in stops_by_zone[zone.id]
                    )
                    / len(stops_by_zone[zone.id])
                )
                if stops_by_zone[zone.id]
                else 0,
            }
            for zone in zones
        ],
        "ward_coverage": [
            {
                "id": str(zone.id),
                "code": zone.code,
                "name": zone.name,
                "is_managed": zone.id in managed_ids,
                "households": households_by_zone.get(zone.id, 0),
                "stops_today": len(coverage_stops_by_zone[zone.id]),
                "active_workers": sum(worker.zone_id == zone.id for worker in all_collectors),
                "coverage_pct": round(
                    100
                    * sum(
                        stop.status == PickupStopStatus.COLLECTED
                        for stop in coverage_stops_by_zone[zone.id]
                    )
                    / len(coverage_stops_by_zone[zone.id])
                )
                if coverage_stops_by_zone[zone.id]
                else 0,
            }
            for zone in all_zones
        ],
        "complaints": complaint_rows,
        "complaints_trend": trend,
        "routes": route_rows,
        "all_ward_open_complaints": [
            {"ward": zone.code, "open": all_open_counts.get(zone.id, 0)} for zone in all_zones
        ],
        "delay_logs": [
            {
                "id": str(delay.id),
                "route_code": f"SCH-{str(delay.stop.schedule_id)[:8].upper()}",
                "ward_code": delay.stop.schedule.zone.code,
                "worker_name": delay.worker.name,
                "reason": delay.reason.value,
                "note": delay.note,
                "logged_at": delay.created_at,
            }
            for delay in delays
        ],
        "mixed_waste_flags": [
            {
                "id": str(tag.id),
                "route_code": f"SCH-{str(tag.stop.schedule_id)[:8].upper()}",
                "ward_code": tag.stop.schedule.zone.code,
                "point_label": tag.stop.pickup.ref_code,
                "severity": tag.severity.value,
                "note": tag.note,
                "flagged_at": tag.created_at,
            }
            for tag in mixed_waste
        ]
        + bulk_mixed_waste_rows,
        "bulk_pickups": [
            {
                "id": str(request.id),
                "ref_code": request.ref_code,
                "ward_code": request.zone.code,
                "resident_name": request.requester.name,
                "requested_date": request.requested_date,
                "time_slot": request.time_slot,
                "estimated_weight": float(request.estimated_weight or 0),
                "notes": request.notes,
                "status": request.status.value,
                "assigned_collector_id": str(request.assigned_collector_id)
                if request.assigned_collector_id
                else None,
                "assigned_collector_name": request.assigned_collector.name
                if request.assigned_collector
                else None,
            }
            for request in bulk_requests
        ],
        "workers": [
            {
                "id": str(worker.id),
                "name": worker.name,
                "phone": worker.phone,
                "role": "COLLECTOR" if worker.role == Role.COLLECTION_WORKER else "RECYCLER",
                "crew_role": "Collector" if worker.role == Role.COLLECTION_WORKER else "Recycler",
                "ward_code": worker.zone.code if worker.zone else "All wards",
                "route_id": str(schedule_by_worker[worker.id].id)
                if worker.id in schedule_by_worker
                else None,
                "shift": "MORNING",
                "status": "ACTIVE" if worker.status.value == "ACTIVE" else "INACTIVE",
            }
            for worker in crew_members
        ],
        "notifications": [
            {
                "id": str(notification.id),
                "title": notification.title,
                "body": notification.body,
                "is_read": notification.is_read,
                "created_at": notification.created_at,
            }
            for notification in notifications
        ],
    }
