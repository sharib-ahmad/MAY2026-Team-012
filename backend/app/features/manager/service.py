"""Query/aggregation logic backing the manager (municipal officer) API.

Notes on schema fit: the manager dashboard was originally designed against a
richer mock dataset (ticket severity, an ESCALATED status, denormalised
route/vehicle/shift fields, a ward "households" count). Those fields do not
exist on the current models (``Ticket``, ``DailyPickupSchedule``, ``Zone``),
so this module derives the closest equivalent from what is actually
persisted rather than inventing columns:

* "needs attention" / aging uses ``TicketStatus`` (OPEN, REOPENED) and ticket
  age instead of a severity/escalation flag.
* Route status (ASSIGNED / IN_PROGRESS / DELAYED / COMPLETED) is derived from
  ``RouteHistory.started_at`` / ``completed_at`` plus whether any delay log
  is attached, since ``DailyPickupSchedule`` has no status column of its own.
* Ward "residents_count" is a live count of CITIZEN users in the zone,
  standing in for the mock dataset's static "households" figure.
"""

import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.features.collection_ops.models import (
    DailyPickupSchedule,
    DailyPickupStop,
    DelayLog,
    MixedWasteTag,
    RouteHistory,
)
from app.features.complaints.models import Ticket
from app.features.manager.schemas import (
    ComplaintListResponse,
    ComplaintOut,
    ComplaintTrendPoint,
    ComplaintUpdate,
    DelayLogOut,
    ManagerOverviewResponse,
    MixedWasteFlagOut,
    OverviewStats,
    RouteDetailOut,
    RouteListResponse,
    RouteOut,
    RouteStopOut,
    WardSummary,
    WorkerListResponse,
    WorkerOut,
    WorkerReassignRequest,
)
from app.features.users.models import User
from app.models.enums import Availability, Role, TicketStatus, UserStatus
from app.models.zone import Zone

AGING_THRESHOLD = timedelta(days=3)
NEEDS_ATTENTION_STATUSES = (TicketStatus.OPEN, TicketStatus.REOPENED)
CLOSED_TICKET_STATUSES = (TicketStatus.RESOLVED, TicketStatus.CLOSED)


def _zone_scope_filter(column, zone_ids: list[uuid.UUID] | None):
    """Return a SQLAlchemy filter clause scoping ``column`` to allowed zones.

    ``None`` means unrestricted (system admin). An empty list means the
    manager has no assigned ward yet, so the filter must exclude everything.
    """
    if zone_ids is None:
        return None
    if not zone_ids:
        return column.in_([])
    return column.in_(zone_ids)


def _is_aging(ticket: Ticket) -> bool:
    if ticket.status in CLOSED_TICKET_STATUSES:
        return False
    now = datetime.now(UTC)
    created = ticket.created_at
    if created.tzinfo is None:
        created = created.replace(tzinfo=UTC)
    return now - created > AGING_THRESHOLD


def _complaint_out(ticket: Ticket) -> ComplaintOut:
    zone = ticket.zone
    return ComplaintOut(
        id=ticket.id,
        ref_code=ticket.ref_code,
        zone_id=ticket.zone_id,
        zone_code=zone.code if zone else None,
        zone_name=zone.name if zone else None,
        citizen_name=ticket.raised_by.name if ticket.raised_by else "Unknown",
        issue_type=ticket.issue_type.name,
        status=ticket.status.name,
        description=ticket.description,
        created_at=ticket.created_at,
        resolved_at=ticket.resolved_at,
        resolved_by_name=ticket.resolved_by.name if ticket.resolved_by else None,
        resolution_notes=ticket.resolution_notes,
        is_aging=_is_aging(ticket),
    )


# ---------------------------------------------------------------------------
# Overview
# ---------------------------------------------------------------------------


def get_overview(db: Session, zone_ids: list[uuid.UUID] | None) -> ManagerOverviewResponse:
    """Assemble everything the Overview tab needs in one pass."""

    zones = db.scalars(
        select(Zone).where(*_scoped(_zone_scope_filter(Zone.id, zone_ids)))
    ).all()

    today = datetime.now(UTC).date()

    ward_summaries: list[WardSummary] = []
    routes_today_total = 0
    routes_completed_today_total = 0
    route_points_total = 0
    route_points_collected = 0
    active_workers_total = 0

    for zone in zones:
        residents_count = db.scalar(
            select(func.count(User.id)).where(
                User.zone_id == zone.id,
                User.role == Role.CITIZEN,
                User.deleted_at.is_(None),
            )
        ) or 0

        active_workers = db.scalar(
            select(func.count(User.id)).where(
                User.zone_id == zone.id,
                User.role == Role.COLLECTION_WORKER,
                User.status == UserStatus.ACTIVE,
                User.deleted_at.is_(None),
            )
        ) or 0

        todays_schedules = db.scalars(
            select(DailyPickupSchedule).where(
                DailyPickupSchedule.zone_id == zone.id,
                func.date(DailyPickupSchedule.schedule_date) == today,
            )
        ).all()

        routes_today = len(todays_schedules)
        total_stops = sum(s.total_stops for s in todays_schedules)
        completed_stops = sum(s.completed_stops for s in todays_schedules)
        routes_completed_today = sum(
            1 for s in todays_schedules if s.total_stops > 0 and s.completed_stops >= s.total_stops
        )
        coverage_pct = round((completed_stops / total_stops) * 100) if total_stops else 0

        ward_summaries.append(
            WardSummary(
                id=zone.id,
                code=zone.code,
                name=zone.name,
                residents_count=residents_count,
                routes_today=routes_today,
                routes_completed_today=routes_completed_today,
                active_workers=active_workers,
                coverage_pct=coverage_pct,
            )
        )

        routes_today_total += routes_today
        routes_completed_today_total += routes_completed_today
        route_points_total += total_stops
        route_points_collected += completed_stops
        active_workers_total += active_workers

    zone_id_list = [z.id for z in zones] if zone_ids is not None else None

    ticket_zone_filter = _zone_scope_filter(Ticket.zone_id, zone_id_list)
    open_complaints = db.scalar(
        select(func.count(Ticket.id)).where(
            Ticket.status == TicketStatus.OPEN, *_scoped(ticket_zone_filter)
        )
    ) or 0
    needs_attention_count = db.scalar(
        select(func.count(Ticket.id)).where(
            Ticket.status.in_(NEEDS_ATTENTION_STATUSES), *_scoped(ticket_zone_filter)
        )
    ) or 0

    week_ago = datetime.now(UTC) - timedelta(days=7)
    resolved_this_week_tickets = db.scalars(
        select(Ticket).where(
            Ticket.status == TicketStatus.RESOLVED,
            Ticket.resolved_at.is_not(None),
            Ticket.resolved_at >= week_ago,
            *_scoped(ticket_zone_filter),
        )
    ).all()
    resolved_this_week = len(resolved_this_week_tickets)
    if resolved_this_week:
        total_hours = sum(
            (t.resolved_at - t.created_at).total_seconds() / 3600.0
            for t in resolved_this_week_tickets
        )
        avg_resolution_hours = round(total_hours / resolved_this_week, 1)
    else:
        avg_resolution_hours = 0.0

    stats = OverviewStats(
        open_complaints=open_complaints,
        needs_attention_complaints=needs_attention_count,
        resolved_this_week=resolved_this_week,
        avg_resolution_hours=avg_resolution_hours,
        routes_today=routes_today_total,
        routes_completed_today=routes_completed_today_total,
        route_points_total=route_points_total,
        route_points_collected=route_points_collected,
        active_workers=active_workers_total,
        wards_supervised=len(zones),
    )

    needs_attention_tickets = db.scalars(
        select(Ticket)
        .options(selectinload(Ticket.raised_by), selectinload(Ticket.zone))
        .where(Ticket.status.in_(NEEDS_ATTENTION_STATUSES), *_scoped(ticket_zone_filter))
        .order_by(Ticket.created_at.desc())
        .limit(5)
    ).all()
    needs_attention = [_complaint_out(t) for t in needs_attention_tickets]

    complaints_trend = _complaints_trend(db, ticket_zone_filter)
    mixed_waste_flags = _mixed_waste_flags(db, zone_id_list, limit=5)

    return ManagerOverviewResponse(
        stats=stats,
        wards=ward_summaries,
        complaints_trend=complaints_trend,
        needs_attention=needs_attention,
        mixed_waste_flags=mixed_waste_flags,
    )


def _scoped(clause):
    """Wrap an optional filter clause for splatting into a ``where()`` call."""
    return [clause] if clause is not None else []


def _complaints_trend(db: Session, ticket_zone_filter) -> list[ComplaintTrendPoint]:
    since = datetime.now(UTC) - timedelta(days=7)

    filed_rows = db.execute(
        select(func.date(Ticket.created_at), func.count(Ticket.id))
        .where(Ticket.created_at >= since, *_scoped(ticket_zone_filter))
        .group_by(func.date(Ticket.created_at))
    ).all()
    resolved_rows = db.execute(
        select(func.date(Ticket.resolved_at), func.count(Ticket.id))
        .where(
            Ticket.resolved_at.is_not(None),
            Ticket.resolved_at >= since,
            *_scoped(ticket_zone_filter),
        )
        .group_by(func.date(Ticket.resolved_at))
    ).all()

    filed_by_day = {str(day): count for day, count in filed_rows}
    resolved_by_day = {str(day): count for day, count in resolved_rows}

    points: list[ComplaintTrendPoint] = []
    for i in range(6, -1, -1):
        day = (datetime.now(UTC) - timedelta(days=i)).date()
        key = str(day)
        points.append(
            ComplaintTrendPoint(
                day=day.strftime("%a"),
                filed=filed_by_day.get(key, 0),
                resolved=resolved_by_day.get(key, 0),
            )
        )
    return points


def _mixed_waste_flags(
    db: Session, zone_id_list: list[uuid.UUID] | None, limit: int | None = None
) -> list[MixedWasteFlagOut]:
    query = (
        select(MixedWasteTag)
        .join(DailyPickupStop, MixedWasteTag.stop_id == DailyPickupStop.id)
        .join(
            DailyPickupSchedule,
            DailyPickupStop.schedule_id == DailyPickupSchedule.id,
        )
        .options(
            selectinload(MixedWasteTag.worker),
            selectinload(MixedWasteTag.stop).selectinload(DailyPickupStop.schedule),
            selectinload(MixedWasteTag.stop).selectinload(DailyPickupStop.resident),
        )
        .order_by(MixedWasteTag.created_at.desc())
    )
    if zone_id_list is not None:
        query = query.where(DailyPickupSchedule.zone_id.in_(zone_id_list))
    if limit:
        query = query.limit(limit)

    tags = db.scalars(query).all()
    out: list[MixedWasteFlagOut] = []
    for tag in tags:
        schedule = tag.stop.schedule
        zone = db.get(Zone, schedule.zone_id)
        out.append(
            MixedWasteFlagOut(
                id=tag.id,
                route_id=schedule.id,
                zone_code=zone.code if zone else None,
                point_label=tag.stop.resident.name if tag.stop.resident else "Stop",
                severity=tag.severity.name,
                note=tag.note,
                flagged_at=tag.created_at,
                worker_name=tag.worker.name if tag.worker else "Unknown",
            )
        )
    return out


# ---------------------------------------------------------------------------
# Complaints
# ---------------------------------------------------------------------------


def list_complaints(
    db: Session,
    zone_ids: list[uuid.UUID] | None,
    zone_code: str | None = None,
    status: str | None = None,
    search: str | None = None,
    skip: int = 0,
    limit: int = 50,
) -> ComplaintListResponse:
    query = select(Ticket).options(
        selectinload(Ticket.raised_by),
        selectinload(Ticket.zone),
        selectinload(Ticket.resolved_by),
    )
    count_query = select(func.count(Ticket.id))

    filters = list(_scoped(_zone_scope_filter(Ticket.zone_id, zone_ids)))

    if zone_code:
        zone = db.scalar(select(Zone).where(Zone.code == zone_code.strip().upper()))
        filters.append(Ticket.zone_id == (zone.id if zone else uuid.uuid4()))

    if status:
        try:
            filters.append(Ticket.status == TicketStatus[status.upper()])
        except KeyError:
            filters.append(Ticket.status.in_([]))

    if search:
        needle = f"%{search.strip()}%"
        query = query.join(User, Ticket.raised_by_id == User.id)
        count_query = count_query.join(User, Ticket.raised_by_id == User.id)
        filters.append(
            (Ticket.ref_code.ilike(needle))
            | (Ticket.description.ilike(needle))
            | (User.name.ilike(needle))
        )

    for clause in filters:
        query = query.where(clause)
        count_query = count_query.where(clause)

    total = db.scalar(count_query) or 0
    tickets = db.scalars(
        query.order_by(Ticket.created_at.desc()).offset(skip).limit(limit)
    ).all()

    return ComplaintListResponse(complaints=[_complaint_out(t) for t in tickets], total=total)


def update_complaint(
    db: Session,
    ticket_id: str,
    update: ComplaintUpdate,
    current_user: User,
    zone_ids: list[uuid.UUID] | None,
) -> ComplaintOut:
    try:
        ticket_uuid = uuid.UUID(ticket_id)
    except ValueError as err:
        raise ValueError("Invalid complaint ID format.") from err

    ticket = db.scalar(
        select(Ticket)
        .options(
            selectinload(Ticket.raised_by),
            selectinload(Ticket.zone),
            selectinload(Ticket.resolved_by),
        )
        .where(Ticket.id == ticket_uuid)
    )
    if not ticket:
        raise ValueError("Complaint not found.")

    if zone_ids is not None and ticket.zone_id not in zone_ids:
        raise PermissionError("This complaint is outside your assigned wards.")

    try:
        new_status = TicketStatus[update.status.upper()]
    except KeyError as err:
        raise ValueError(f"Unsupported status: {update.status}") from err

    if new_status == TicketStatus.RESOLVED and not (update.resolution_notes or "").strip():
        raise ValueError("A resolution note is required to resolve a complaint.")

    ticket.status = new_status
    if update.resolution_notes is not None:
        ticket.resolution_notes = update.resolution_notes.strip() or ticket.resolution_notes

    if new_status == TicketStatus.RESOLVED:
        ticket.resolved_at = datetime.now(UTC)
        ticket.resolved_by_id = current_user.id
    elif new_status == TicketStatus.REOPENED:
        ticket.resolved_at = None
        ticket.resolved_by_id = None

    db.commit()
    db.refresh(ticket)
    return _complaint_out(ticket)


# ---------------------------------------------------------------------------
# Route tracking
# ---------------------------------------------------------------------------


def _route_status(schedule: DailyPickupSchedule, has_delay: bool) -> str:
    history = schedule.routes[-1] if schedule.routes else None
    if history and history.completed_at:
        return "COMPLETED"
    if history and history.started_at:
        return "DELAYED" if has_delay else "IN_PROGRESS"
    return "ASSIGNED"


def _route_out(db: Session, schedule: DailyPickupSchedule) -> RouteOut:
    has_delay = db.scalar(
        select(func.count(DelayLog.id))
        .join(DailyPickupStop, DelayLog.stop_id == DailyPickupStop.id)
        .where(DailyPickupStop.schedule_id == schedule.id)
    ) or 0
    history = schedule.routes[-1] if schedule.routes else None
    zone = schedule.zone
    last_update = max(
        [s.completed_at for s in schedule.stops if s.completed_at] + [schedule.updated_at],
        default=schedule.updated_at,
    )
    return RouteOut(
        id=schedule.id,
        zone_id=schedule.zone_id,
        zone_code=zone.code if zone else None,
        zone_name=zone.name if zone else None,
        worker_id=schedule.collector_id,
        worker_name=schedule.collector.name if schedule.collector else "Unassigned",
        schedule_date=schedule.schedule_date,
        status=_route_status(schedule, bool(has_delay)),
        points_total=schedule.total_stops,
        points_collected=schedule.completed_stops,
        started_at=history.started_at if history else None,
        completed_at=history.completed_at if history else None,
        last_update_at=last_update,
    )


def list_routes(
    db: Session,
    zone_ids: list[uuid.UUID] | None,
    zone_code: str | None = None,
    status: str | None = None,
) -> RouteListResponse:
    query = select(DailyPickupSchedule).options(
        selectinload(DailyPickupSchedule.zone),
        selectinload(DailyPickupSchedule.collector),
        selectinload(DailyPickupSchedule.routes),
        selectinload(DailyPickupSchedule.stops),
    )

    filters = list(_scoped(_zone_scope_filter(DailyPickupSchedule.zone_id, zone_ids)))
    zone_id_list = None

    if zone_code:
        zone = db.scalar(select(Zone).where(Zone.code == zone_code.strip().upper()))
        filters.append(DailyPickupSchedule.zone_id == (zone.id if zone else uuid.uuid4()))

    for clause in filters:
        query = query.where(clause)

    schedules = db.scalars(query.order_by(DailyPickupSchedule.schedule_date.desc())).all()

    routes = [_route_out(db, s) for s in schedules]
    if status:
        routes = [r for r in routes if r.status == status.upper()]

    if zone_ids is not None:
        zone_id_list = [z for z in zone_ids]

    delay_logs = _delay_logs(db, zone_id_list)
    mixed_waste_flags = _mixed_waste_flags(db, zone_id_list)

    return RouteListResponse(
        routes=routes,
        total=len(routes),
        delay_logs=delay_logs,
        mixed_waste_flags=mixed_waste_flags,
    )


def _delay_logs(db: Session, zone_id_list: list[uuid.UUID] | None) -> list[DelayLogOut]:
    query = (
        select(DelayLog)
        .join(DailyPickupStop, DelayLog.stop_id == DailyPickupStop.id)
        .join(DailyPickupSchedule, DailyPickupStop.schedule_id == DailyPickupSchedule.id)
        .options(
            selectinload(DelayLog.worker),
            selectinload(DelayLog.stop).selectinload(DailyPickupStop.schedule),
        )
        .order_by(DelayLog.created_at.desc())
        .limit(20)
    )
    if zone_id_list is not None:
        query = query.where(DailyPickupSchedule.zone_id.in_(zone_id_list))

    logs = db.scalars(query).all()
    out: list[DelayLogOut] = []
    for log in logs:
        schedule = log.stop.schedule
        zone = db.get(Zone, schedule.zone_id)
        out.append(
            DelayLogOut(
                id=log.id,
                route_id=schedule.id,
                zone_code=zone.code if zone else None,
                worker_name=log.worker.name if log.worker else "Unknown",
                reason=log.reason.name,
                note=log.note,
                logged_at=log.created_at,
            )
        )
    return out


def get_route_detail(
    db: Session, schedule_id: str, zone_ids: list[uuid.UUID] | None
) -> RouteDetailOut:
    try:
        schedule_uuid = uuid.UUID(schedule_id)
    except ValueError as err:
        raise ValueError("Invalid route ID format.") from err

    schedule = db.scalar(
        select(DailyPickupSchedule)
        .options(
            selectinload(DailyPickupSchedule.zone),
            selectinload(DailyPickupSchedule.collector),
            selectinload(DailyPickupSchedule.routes),
            selectinload(DailyPickupSchedule.stops).selectinload(DailyPickupStop.resident),
        )
        .where(DailyPickupSchedule.id == schedule_uuid)
    )
    if not schedule:
        raise ValueError("Route not found.")

    if zone_ids is not None and schedule.zone_id not in zone_ids:
        raise PermissionError("This route is outside your assigned wards.")

    base = _route_out(db, schedule)
    points = [
        RouteStopOut(
            id=stop.id,
            seq=stop.pickup_order,
            label=stop.resident.name if stop.resident else "Stop",
            status=stop.status.name,
            updated_at=stop.completed_at,
        )
        for stop in sorted(schedule.stops, key=lambda s: s.pickup_order)
    ]
    return RouteDetailOut(**base.model_dump(), points=points)


# ---------------------------------------------------------------------------
# Crews
# ---------------------------------------------------------------------------


def _worker_out(db: Session, worker: User) -> WorkerOut:
    zone = worker.zone
    active_route = db.scalar(
        select(DailyPickupSchedule)
        .where(DailyPickupSchedule.collector_id == worker.id, DailyPickupSchedule.is_active.is_(True))
        .order_by(DailyPickupSchedule.schedule_date.desc())
    )
    return WorkerOut(
        id=worker.id,
        name=worker.name,
        phone=worker.phone,
        zone_id=worker.zone_id,
        zone_code=zone.code if zone else None,
        availability=worker.availability.name if worker.availability else None,
        status=worker.status.name,
        active_route_id=active_route.id if active_route else None,
    )


def list_workers(
    db: Session,
    zone_ids: list[uuid.UUID] | None,
    zone_code: str | None = None,
    availability: str | None = None,
    search: str | None = None,
) -> WorkerListResponse:
    query = select(User).options(selectinload(User.zone)).where(
        User.role == Role.COLLECTION_WORKER, User.deleted_at.is_(None)
    )

    scope_filter = _zone_scope_filter(User.zone_id, zone_ids)
    if scope_filter is not None:
        query = query.where(scope_filter)

    if zone_code:
        zone = db.scalar(select(Zone).where(Zone.code == zone_code.strip().upper()))
        query = query.where(User.zone_id == (zone.id if zone else uuid.uuid4()))

    if availability:
        try:
            query = query.where(User.availability == Availability[availability.upper()])
        except KeyError:
            query = query.where(User.availability.is_(None) & (User.id != User.id))

    if search:
        needle = f"%{search.strip()}%"
        query = query.where(User.name.ilike(needle))

    workers = db.scalars(query.order_by(User.name)).all()
    return WorkerListResponse(
        workers=[_worker_out(db, w) for w in workers], total=len(workers)
    )


def reassign_worker(
    db: Session,
    worker_id: str,
    req: WorkerReassignRequest,
    zone_ids: list[uuid.UUID] | None,
) -> WorkerOut:
    try:
        worker_uuid = uuid.UUID(worker_id)
    except ValueError as err:
        raise ValueError("Invalid worker ID format.") from err

    worker = db.scalar(
        select(User).where(
            User.id == worker_uuid,
            User.role == Role.COLLECTION_WORKER,
            User.deleted_at.is_(None),
        )
    )
    if not worker:
        raise ValueError("Worker not found.")

    if zone_ids is not None and worker.zone_id not in zone_ids:
        raise PermissionError("This worker is outside your assigned wards.")

    if req.zone_id is not None:
        new_zone = db.get(Zone, req.zone_id)
        if not new_zone:
            raise ValueError("Selected ward does not exist.")
        if zone_ids is not None and new_zone.id not in zone_ids:
            raise PermissionError("You cannot reassign a worker outside your assigned wards.")
        worker.zone_id = new_zone.id

    if req.availability is not None:
        try:
            worker.availability = Availability[req.availability.upper()]
        except KeyError as err:
            raise ValueError(f"Unsupported availability: {req.availability}") from err

    db.commit()
    db.refresh(worker)
    return _worker_out(db, worker)