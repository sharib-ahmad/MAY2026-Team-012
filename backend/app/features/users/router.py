import math
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.db.session import get_db
from app.features.bulk_pickups.models import BulkPickupRequest
from app.features.bulk_pickups.service import citizen_requests, serialize_request
from app.features.collection_ops.models import DailyPickupSchedule, DailyPickupStop, Pickup
from app.features.credits.models import Credit
from app.features.notifications.models import Notification
from app.features.sorting_guide.models import WasteCategory
from app.features.users.dependencies import require_citizen
from app.features.users.models import User
from app.features.users.schemas import (
    ChatRequest,
    ChatResponse,
    DeleteAccountRequest,
    ImpactResponse,
)
from app.features.users.service import execute_chatbot_turn
from app.models.audit import create_audit_log
from app.models.enums import CreditStatus, PickupStatus, PickupStopStatus, UserStatus
from app.models.zone import Zone


def _calculate_haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 6371.0  # Earth radius in kilometers
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (
        math.sin(dlat / 2.0) ** 2
        + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2.0) ** 2
    )
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return R * c


router = APIRouter(tags=["Citizen"])


@router.get("/impact", response_model=ImpactResponse)
def get_impact(
    current_user: User = Depends(require_citizen), db: Session = Depends(get_db)
) -> dict:
    """Return impact based on completed collection records and confirmed credits."""

    completed_pickups = (
        db.scalars(
            select(Pickup)
            .where(
                Pickup.citizen_id == current_user.id,
                Pickup.status.in_(
                    [
                        PickupStatus.COMPLETED,
                        PickupStatus.COLLECTED,
                        PickupStatus.RECYCLER_ASSIGNED,
                        PickupStatus.PROCESSING,
                        PickupStatus.PROCESSED,
                    ]
                ),
            )
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
    current_user: User = Depends(require_citizen), db: Session = Depends(get_db)
) -> dict:
    requests = (
        db.scalars(citizen_requests(current_user.id).order_by(BulkPickupRequest.created_at.desc()))
        .unique()
        .all()
    )
    credits = db.scalars(
        select(Credit).where(
            Credit.user_id == current_user.id, Credit.status == CreditStatus.CONFIRMED
        )
    ).all()
    completed_pickups = (
        db.scalars(
            select(Pickup).where(
                Pickup.citizen_id == current_user.id,
                Pickup.status.in_(
                    [
                        PickupStatus.COMPLETED,
                        PickupStatus.COLLECTED,
                        PickupStatus.RECYCLER_ASSIGNED,
                        PickupStatus.PROCESSING,
                        PickupStatus.PROCESSED,
                    ]
                ),
            )
        )
        .unique()
        .all()  # materialise so we can iterate twice
    )
    total_kg_diverted = sum(
        float(pickup.actual_weight or pickup.estimated_weight or 0)
        for pickup in completed_pickups
    )

    from zoneinfo import ZoneInfo

    from app.core.config import get_settings

    settings = get_settings()
    tz_str = getattr(settings, "PILOT_TIMEZONE", "Asia/Kolkata") or "Asia/Kolkata"
    pilot_tz = ZoneInfo(tz_str)
    now = datetime.now(UTC)
    local_now = now.astimezone(pilot_tz)
    local_midnight = local_now.replace(hour=0, minute=0, second=0, microsecond=0)
    today_start = local_midnight.astimezone(UTC)
    tomorrow_start = today_start + timedelta(days=1)
    today_stops = (
        db.scalars(
            select(DailyPickupStop)
            .join(DailyPickupStop.schedule)
            .where(
                DailyPickupSchedule.schedule_date >= today_start,
                DailyPickupSchedule.schedule_date < tomorrow_start,
                DailyPickupSchedule.zone_id == current_user.zone_id,
            )
            .options(joinedload(DailyPickupStop.citizen), joinedload(DailyPickupStop.schedule))
            .order_by(DailyPickupStop.pickup_order)
        )
        .unique()
        .all()
    )
    citizen_stop = next((stop for stop in today_stops if stop.citizen_id == current_user.id), None)
    queue = (
        {
            "pickup_number": citizen_stop.pickup_order,
            "status": citizen_stop.status.value,
            "ref_code": citizen_stop.pickup.ref_code,
        }
        if citizen_stop
        else None
    )
    # Compute badges the same way /impact does — dynamic from completed pickups,
    # not from the unpopulated user_badges table.
    _badge_definitions = (
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
            "earned": total_kg_diverted >= minimum_kg
            if minimum_kg is not None
            else len(completed_pickups) >= minimum_pickups,
        }
        for code, name, icon, minimum_pickups, minimum_kg in _badge_definitions
    ]
    distance_km = None
    eta_min = None
    if citizen_stop and citizen_stop.status != PickupStopStatus.COLLECTED:
        pending_before = [
            s
            for s in today_stops
            if s.pickup_order < citizen_stop.pickup_order and s.status != PickupStopStatus.COLLECTED
        ]
        completed_stops = [s for s in today_stops if s.status == PickupStopStatus.COLLECTED]
        collector_lat, collector_lon = None, None
        if completed_stops:
            last_comp = max(completed_stops, key=lambda s: s.completed_at or datetime.min)
            if last_comp.latitude is not None and last_comp.longitude is not None:
                collector_lat, collector_lon = last_comp.latitude, last_comp.longitude
        elif today_stops:
            first_stop = today_stops[0]
            if first_stop.latitude is not None and first_stop.longitude is not None:
                collector_lat, collector_lon = first_stop.latitude, first_stop.longitude

        if (
            collector_lat is not None
            and collector_lon is not None
            and citizen_stop.latitude is not None
            and citizen_stop.longitude is not None
        ):
            dist = _calculate_haversine_distance(
                collector_lat, collector_lon, citizen_stop.latitude, citizen_stop.longitude
            )
            distance_km = round(dist, 1)
            eta_min = max(1, math.ceil((dist / 25.0) * 60.0 + len(pending_before) * 3.0))
        elif pending_before:
            eta_min = max(1, len(pending_before) * 5)

    return {
        "pickups": [serialize_request(request).model_dump() for request in requests[:5]],
        "impact": {
            "total_pickups": len(completed_pickups),
            "total_kg_diverted": total_kg_diverted,
            "credits_balance": sum(float(credit.amount) for credit in credits),
            "co2_saved_kg": sum(float(credit.co2_saved) for credit in credits),
            "badges": badges,
        },
        "queue": queue,
        "flow": {
            "stops": [
                {
                    "id": str(stop.id),
                    "pickup_order": stop.pickup_order,
                    "status": stop.status.value,
                    "citizen_name": (
                        "You" if stop.citizen_id == current_user.id else stop.citizen.name
                    ),
                    "address": "Scheduled collection",
                }
                for stop in today_stops
            ],
            "distance_km": distance_km,
            "eta_min": eta_min,
        },
    }


@router.get("/pickup-options")
def pickup_options(
    current_user: User = Depends(require_citizen), db: Session = Depends(get_db)
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


@router.delete("/account")
def delete_account(
    payload: DeleteAccountRequest,
    current_user: User = Depends(require_citizen),
    db: Session = Depends(get_db),
) -> dict:
    """Soft delete citizen account, notify manager, and create audit log."""
    import uuid

    # 1. Notify manager if user has a zone manager
    if current_user.zone_id:
        manager_id = db.scalar(select(Zone.manager_id).where(Zone.id == current_user.zone_id))
        if manager_id:
            notification = Notification(
                user_id=manager_id,
                title="Citizen Account Deleted",
                body=(
                    f"Citizen {current_user.name} ({current_user.email}) has "
                    f"deleted their account. Reason: {payload.reason or 'No reason provided.'}"
                ),
            )
            db.add(notification)

    # Store original identifiers for the audit log
    original_email = current_user.email
    original_phone = current_user.phone

    # 2. Anonymize identifiers to free up unique constraints for re-registration
    short_id = uuid.uuid4().hex[:8]
    current_user.email = f"{original_email}-deleted-{short_id}"
    current_user.phone = f"del-{short_id}"

    # 3. Soft delete and disable user session
    current_user.deleted_at = datetime.now(UTC)
    current_user.status = UserStatus.DISABLED
    current_user.token_version += 1

    # 4. Create Audit Log
    create_audit_log(
        db=db,
        actor_id=str(current_user.id),
        actor_name=current_user.name,
        actor_role=current_user.role.value
        if hasattr(current_user.role, "value")
        else str(current_user.role),
        action="DELETE_ACCOUNT",
        entity_type="USER",
        entity_id=str(current_user.id),
        description=(
            f"Citizen deleted their account (Email: {original_email}, "
            f"Phone: {original_phone}). "
            f"Reason: {payload.reason or 'No reason provided.'}"
        ),
        commit=False,
    )

    db.commit()
    return {"status": "ok"}


@router.post("/chatbot/message", response_model=ChatResponse)
async def chat_message(
    payload: ChatRequest,
    current_user: User = Depends(require_citizen),
    db: Session = Depends(get_db),
) -> ChatResponse:
    result = await execute_chatbot_turn(
        message=payload.message, history=payload.history, current_user=current_user, db=db
    )
    return ChatResponse(reply=result["reply"], history=result["history"])
