from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.db.session import get_db
from app.features.bulk_pickups.models import BulkPickupRequest
from app.features.bulk_pickups.service import resident_requests, serialize_request
from app.features.collection_ops.models import DailyPickupSchedule, DailyPickupStop, Pickup
from app.features.credits.models import Credit, UserBadge
from app.features.sorting_guide.models import WasteCategory
from app.features.users.dependencies import require_resident
from app.features.users.models import User
from app.features.users.schemas import ImpactResponse
from app.models.enums import CreditStatus, PickupStatus

router = APIRouter(tags=["Resident"])


@router.get("/impact", response_model=ImpactResponse)
def get_impact(
    current_user: User = Depends(require_resident), db: Session = Depends(get_db)
) -> dict:
    """Return impact based on completed collection records and confirmed credits."""

    completed_pickups = (
        db.scalars(
            select(Pickup)
            .where(
                Pickup.resident_id == current_user.id,
                Pickup.status.in_([PickupStatus.COMPLETED, PickupStatus.COLLECTED]),
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
    completed_pickups = db.scalars(
        select(Pickup).where(
            Pickup.resident_id == current_user.id,
            Pickup.status.in_([PickupStatus.COMPLETED, PickupStatus.COLLECTED]),
        )
    )
    total_kg_diverted = sum(float(pickup.actual_weight or 0) for pickup in completed_pickups)

    now = datetime.now(UTC)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
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
            .options(joinedload(DailyPickupStop.resident), joinedload(DailyPickupStop.schedule))
            .order_by(DailyPickupStop.pickup_order)
        )
        .unique()
        .all()
    )
    resident_stop = next(
        (stop for stop in today_stops if stop.resident_id == current_user.id), None
    )
    queue = (
        {
            "pickup_number": resident_stop.pickup_order,
            "status": resident_stop.status.value,
            "ref_code": resident_stop.pickup.ref_code,
        }
        if resident_stop
        else None
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
            "total_kg_diverted": total_kg_diverted,
            "credits_balance": sum(float(credit.amount) for credit in credits),
            "co2_saved_kg": sum(float(credit.co2_saved) for credit in credits),
            "badges": [
                {
                    "code": entry.badge.code,
                    "name": entry.badge.name,
                    "icon": entry.badge.icon_key or "",
                    "earned": True,
                }
                for entry in badges
            ],
        },
        "queue": queue,
        "flow": {
            "stops": [
                {
                    "id": str(stop.id),
                    "pickup_order": stop.pickup_order,
                    "status": stop.status.value,
                    "resident_name": (
                        "You" if stop.resident_id == current_user.id else stop.resident.name
                    ),
                    "address": "Scheduled collection",
                }
                for stop in today_stops
            ]
        },
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
