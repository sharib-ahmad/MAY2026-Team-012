import uuid
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.db.session import get_db
from app.features.auth.dependencies import get_current_user
from app.features.bulk_pickups.models import BulkPickupRequest
from app.features.collection_ops.models import DailyPickupSchedule, DailyPickupStop, Pickup
from app.features.complaints.models import Ticket
from app.features.credits.models import Credit, UserBadge
from app.features.notifications.models import Notification
from app.features.sorting_guide.models import WasteCategory
from app.features.users.models import User
from app.features.users.schemas import (
    DailyPickupScheduleResponse,
    ImpactResponse,
    NotificationResponse,
    PickupCreate,
    PickupResponse,
    PickupsResponse,
    PickupTrackingResponse,
    TicketCreate,
    TicketResponse,
    TicketsResponse,
    TrackingEvent,
)
from app.models.enums import (
    BulkRequestStatus,
    CreditStatus,
    PickupStatus,
    Role,
    TicketStatus,
    TicketType,
)
from app.models.zone import Zone

router = APIRouter(tags=["Resident"])


def require_resident(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != Role.CITIZEN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Resident access required."
        )
    return current_user


def serialize_request(request: BulkPickupRequest) -> PickupResponse:
    category = request.waste_category.label if request.waste_category else request.category
    return PickupResponse(
        id=request.id,
        ref_code=request.ref_code,
        category=category,
        estimated_weight=float(request.estimated_weight or 0),
        scheduled_date=request.requested_date,
        time_slot=request.time_slot,
        notes=request.notes,
        status=request.status.value,
        zone_name=f"{request.zone.code} - {request.zone.name}" if request.zone else None,
        created_at=request.created_at,
    )


def resident_requests(user_id: uuid.UUID):
    return (
        select(BulkPickupRequest)
        .where(BulkPickupRequest.requester_id == user_id)
        .options(joinedload(BulkPickupRequest.zone), joinedload(BulkPickupRequest.waste_category))
    )


@router.get("/impact", response_model=ImpactResponse)
def get_impact(
    current_user: User = Depends(require_resident), db: Session = Depends(get_db)
) -> dict:
    """Return impact based on completed collection records and confirmed credits."""

    completed_pickups = (
        db.scalars(
            select(Pickup)
            .where(Pickup.resident_id == current_user.id, Pickup.status == PickupStatus.COMPLETED)
            .options(joinedload(Pickup.waste_category))
        )
        .unique()
        .all()
    )
    confirmed_credits = db.scalars(
        select(Credit).where(
            Credit.user_id == current_user.id, Credit.status == CreditStatus.CONFIRMED
        )
    ).all()

    by_category: dict[str, dict[str, float | str]] = {}
    monthly_weights: dict[tuple[int, int], float] = {}
    total_weight = 0.0
    total_co2 = 0.0

    for pickup in completed_pickups:
        weight = float(pickup.actual_weight or pickup.estimated_weight)
        co2_saved = float(pickup.co2_saved or 0)
        credits_earned = float(pickup.credits_earned or 0)
        category = pickup.waste_category.label if pickup.waste_category else pickup.category
        summary = by_category.setdefault(
            category,
            {"category": category, "weight_kg": 0.0, "credits": 0.0, "co2_kg": 0.0},
        )
        summary["weight_kg"] = float(summary["weight_kg"]) + weight
        summary["credits"] = float(summary["credits"]) + credits_earned
        summary["co2_kg"] = float(summary["co2_kg"]) + co2_saved
        total_weight += weight
        total_co2 += co2_saved

        impact_date = pickup.completed_at or pickup.created_at
        key = (impact_date.year, impact_date.month)
        monthly_weights[key] = monthly_weights.get(key, 0.0) + weight

    now = datetime.now(UTC)
    monthly_trend = []
    for months_ago in range(5, -1, -1):
        month_index = now.month - months_ago
        year = now.year + (month_index - 1) // 12
        month = (month_index - 1) % 12 + 1
        monthly_trend.append(
            {
                "month": datetime(year, month, 1, tzinfo=UTC).strftime("%b"),
                "weight_kg": round(monthly_weights.get((year, month), 0.0), 3),
            }
        )

    badge_definitions = (
        ("FIRST_PICKUP", "First Pickup", "🌱", 1, None),
        ("FIVE_PICKUPS", "5 Pickups", "♻️", 5, None),
        ("TEN_PICKUPS", "10 Pickups", "🏆", 10, None),
        ("FIFTY_KG", "50kg Diverted", "🌍", None, 50),
    )
    badges = [
        {
            "code": code,
            "name": name,
            "icon": icon,
            "earned": total_weight >= minimum_kg
            if minimum_kg is not None
            else len(completed_pickups) >= minimum_pickups,
        }
        for code, name, icon, minimum_pickups, minimum_kg in badge_definitions
    ]

    return {
        "total_pickups": len(completed_pickups),
        "total_kg_diverted": round(total_weight, 3),
        "co2_saved_kg": round(total_co2, 3),
        "credits_balance": round(sum(float(credit.amount) for credit in confirmed_credits), 2),
        "by_category": list(by_category.values()),
        "monthly_trend": monthly_trend,
        "badges": badges,
    }


@router.get("/dashboard")
def get_dashboard(
    current_user: User = Depends(require_resident), db: Session = Depends(get_db)
) -> dict:
    requests = (
        db.scalars(resident_requests(current_user.id).order_by(BulkPickupRequest.created_at.desc()))
        .unique()
        .all()
    )
    credits = db.scalars(
        select(Credit).where(
            Credit.user_id == current_user.id, Credit.status == CreditStatus.CONFIRMED
        )
    ).all()
    today = datetime.now(UTC).date()
    queue = next(
        (
            serialize_request(request).model_dump()
            for request in requests
            if request.requested_date.date() == today
            and request.status == BulkRequestStatus.APPROVED
        ),
        None,
    )
    badges = (
        db.scalars(
            select(UserBadge)
            .where(UserBadge.user_id == current_user.id)
            .options(joinedload(UserBadge.badge))
        )
        .unique()
        .all()
    )
    return {
        "pickups": [serialize_request(request).model_dump() for request in requests[:5]],
        "impact": {
            "total_pickups": len(requests),
            "total_kg_diverted": 0,
            "credits_balance": sum(float(credit.amount) for credit in credits),
            "co2_saved_kg": sum(float(credit.co2_saved) for credit in credits),
            "badges": [
                {"code": entry.badge.code, "name": entry.badge.name, "icon": "🏅", "earned": True}
                for entry in badges
            ],
        },
        "queue": queue,
        "flow": {"stops": []},
    }


@router.get("/pickup-options")
def pickup_options(
    current_user: User = Depends(require_resident), db: Session = Depends(get_db)
) -> dict:
    del current_user
    categories = db.scalars(
        select(WasteCategory)
        .where(WasteCategory.is_active.is_(True))
        .order_by(WasteCategory.sort_order)
    ).all()
    return {
        "categories": [{"code": category.code, "label": category.label} for category in categories]
    }


def serialize_ticket(ticket: Ticket) -> TicketResponse:
    return TicketResponse(
        id=ticket.id,
        ref_code=ticket.ref_code,
        issue_type=ticket.issue_type.value,
        status=ticket.status.value,
        description=ticket.description,
        ward_code=ticket.zone.code if ticket.zone else None,
        ward_name=ticket.zone.name if ticket.zone else None,
        ward_sectors=ticket.zone.sectors if ticket.zone else None,
        ward_manager_name=ticket.zone.manager.name if ticket.zone and ticket.zone.manager else None,
        created_at=ticket.created_at,
    )


@router.get("/tickets", response_model=TicketsResponse)
def list_tickets(
    current_user: User = Depends(require_resident), db: Session = Depends(get_db)
) -> TicketsResponse:
    tickets = (
        db.scalars(
            select(Ticket)
            .where(Ticket.raised_by_id == current_user.id)
            .options(joinedload(Ticket.zone).joinedload(Zone.manager))
            .order_by(Ticket.created_at.desc())
        )
        .unique()
        .all()
    )
    return TicketsResponse(
        tickets=[serialize_ticket(ticket) for ticket in tickets], total=len(tickets)
    )


@router.post("/tickets", response_model=TicketResponse, status_code=status.HTTP_201_CREATED)
def create_ticket(
    payload: TicketCreate,
    current_user: User = Depends(require_resident),
    db: Session = Depends(get_db),
) -> TicketResponse:
    ticket = Ticket(
        ref_code=f"TK-{uuid.uuid4().hex[:8].upper()}",
        raised_by_id=current_user.id,
        zone_id=current_user.zone_id,
        issue_type=TicketType(payload.issue_type),
        status=TicketStatus.OPEN,
        description=payload.description.strip(),
    )
    db.add(ticket)
    db.add(
        Notification(
            user_id=current_user.id,
            title="Complaint submitted",
            body=f"Your complaint {ticket.ref_code} has been submitted.",
        )
    )
    db.commit()
    ticket = db.scalar(
        select(Ticket)
        .where(Ticket.id == ticket.id)
        .options(joinedload(Ticket.zone).joinedload(Zone.manager))
    )
    return serialize_ticket(ticket)


@router.get("/notifications", response_model=list[NotificationResponse])
def list_notifications(
    current_user: User = Depends(require_resident), db: Session = Depends(get_db)
) -> list[NotificationResponse]:
    notifications = db.scalars(
        select(Notification)
        .where(Notification.user_id == current_user.id)
        .order_by(Notification.created_at.desc())
        .limit(20)
    ).all()
    return [
        NotificationResponse(
            id=notification.id,
            title=notification.title,
            body=notification.body,
            is_read=notification.is_read,
            created_at=notification.created_at,
        )
        for notification in notifications
    ]


@router.patch("/notifications/{notification_id}/read", response_model=NotificationResponse)
def mark_notification_read(
    notification_id: uuid.UUID,
    current_user: User = Depends(require_resident),
    db: Session = Depends(get_db),
) -> NotificationResponse:
    notification = db.scalar(
        select(Notification).where(
            Notification.id == notification_id, Notification.user_id == current_user.id
        )
    )
    if not notification:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found.")
    notification.is_read = True
    db.commit()
    return NotificationResponse(
        id=notification.id,
        title=notification.title,
        body=notification.body,
        is_read=notification.is_read,
        created_at=notification.created_at,
    )


@router.get("/daily-pickup-schedules", response_model=list[DailyPickupScheduleResponse])
def list_daily_pickup_schedules(
    current_user: User = Depends(require_resident), db: Session = Depends(get_db)
) -> list[DailyPickupScheduleResponse]:
    stops = (
        db.scalars(
            select(DailyPickupStop)
            .where(DailyPickupStop.resident_id == current_user.id)
            .join(DailyPickupStop.schedule)
            .options(joinedload(DailyPickupStop.schedule).joinedload(DailyPickupSchedule.collector))
            .order_by(DailyPickupSchedule.schedule_date.desc())
        )
        .unique()
        .all()
    )
    return [
        DailyPickupScheduleResponse(
            schedule_id=stop.schedule.id,
            schedule_date=stop.schedule.schedule_date,
            collector_name=stop.schedule.collector.name if stop.schedule.collector else None,
            pickup_order=stop.pickup_order,
            stop_status=stop.status.value,
            total_stops=stop.schedule.total_stops,
            completed_stops=stop.schedule.completed_stops,
        )
        for stop in stops
    ]


@router.get("/pickups", response_model=PickupsResponse)
def list_pickups(
    current_user: User = Depends(require_resident), db: Session = Depends(get_db)
) -> PickupsResponse:
    requests = (
        db.scalars(resident_requests(current_user.id).order_by(BulkPickupRequest.created_at.desc()))
        .unique()
        .all()
    )
    return PickupsResponse(
        pickups=[serialize_request(request) for request in requests], total=len(requests)
    )


@router.post("/pickups", response_model=PickupResponse, status_code=status.HTTP_201_CREATED)
def create_pickup(
    payload: PickupCreate,
    current_user: User = Depends(require_resident),
    db: Session = Depends(get_db),
) -> PickupResponse:
    if not current_user.zone_id:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Assign a ward before scheduling a pickup.",
        )
    category = db.scalar(
        select(WasteCategory).where(
            WasteCategory.code == payload.category, WasteCategory.is_active.is_(True)
        )
    )
    if not category:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid waste category."
        )
    if payload.scheduled_date < datetime.now(UTC) + timedelta(hours=24):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Pickup requests require at least 24 hours' notice.",
        )
    request = BulkPickupRequest(
        ref_code=f"BPR-{uuid.uuid4().hex[:8].upper()}",
        requester_id=current_user.id,
        zone_id=current_user.zone_id,
        category=category.code,
        requested_date=payload.scheduled_date,
        estimated_weight=payload.estimated_weight,
        time_slot=payload.time_slot,
        notes=payload.notes,
        status=BulkRequestStatus.PENDING,
    )
    db.add(request)
    db.add(
        Notification(
            user_id=current_user.id,
            title="Pickup scheduled",
            body=(
                f"Your pickup {request.ref_code} is scheduled for "
                f"{request.requested_date:%d %b %Y}."
            ),
        )
    )
    db.commit()
    request = db.scalar(
        resident_requests(current_user.id).where(BulkPickupRequest.id == request.id)
    )
    return serialize_request(request)


@router.patch("/pickups/{pickup_id}/cancel", response_model=PickupResponse)
def cancel_pickup(
    pickup_id: uuid.UUID,
    current_user: User = Depends(require_resident),
    db: Session = Depends(get_db),
) -> PickupResponse:
    request = db.scalar(resident_requests(current_user.id).where(BulkPickupRequest.id == pickup_id))
    if not request:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pickup not found.")
    if request.status not in {BulkRequestStatus.PENDING, BulkRequestStatus.APPROVED}:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="This pickup can no longer be cancelled."
        )
    request.status = BulkRequestStatus.CANCELLED
    db.commit()
    return serialize_request(request)


def build_tracking_response(request: BulkPickupRequest) -> PickupTrackingResponse:
    timeline = [
        TrackingEvent(stage="PENDING", label="Pickup request submitted", at=request.created_at)
    ]
    if request.status != BulkRequestStatus.PENDING:
        timeline.append(
            TrackingEvent(
                stage=request.status.value,
                label=f"Request {request.status.value.lower()}",
                at=request.updated_at,
            )
        )
    return PickupTrackingResponse(
        ref_code=request.ref_code,
        status=request.status.value,
        stops_remaining=0,
        estimated_arrival=request.time_slot,
        timeline=timeline,
    )


@router.get("/pickups/{pickup_id}/tracking", response_model=PickupTrackingResponse)
def pickup_tracking(
    pickup_id: uuid.UUID,
    current_user: User = Depends(require_resident),
    db: Session = Depends(get_db),
) -> PickupTrackingResponse:
    request = db.scalar(resident_requests(current_user.id).where(BulkPickupRequest.id == pickup_id))
    if not request:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pickup not found.")
    return build_tracking_response(request)
