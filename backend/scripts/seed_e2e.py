"""Deterministic seed for the Playwright end-to-end journeys.

Destructive: the schema is rebuilt through the real Alembic migrations before
seeding, so the same guard used by tests/conftest.py applies here — APP_ENV
must be 'test' and the database name must end in '_test'. Nothing else is
allowed to run this.

Every journey owns its own identities and rows, so the three Playwright tests
can run in any order (and in parallel) without sharing mutable state.
"""

import re
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

BACKEND_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_ROOT))

from alembic.config import Config  # noqa: E402
from sqlalchemy import create_engine, make_url  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402

from alembic import command  # noqa: E402
from app.core.config import get_database_settings, get_settings  # noqa: E402
from app.core.security import get_password_hash  # noqa: E402
from app.db import registry as _registry  # noqa: E402,F401
from app.features.collection_ops.models import (  # noqa: E402
    DailyPickupSchedule,
    DailyPickupStop,
    Pickup,
)
from app.features.sorting_guide.models import WasteCategory  # noqa: E402
from app.features.users.models import User  # noqa: E402
from app.models.enums import (  # noqa: E402
    PickupStatus,
    PickupStopStatus,
    Role,
    UserStatus,
)
from app.models.zone import Zone  # noqa: E402

E2E_PASSWORD = "E2ePassw0rd!"


def _assert_safe_database(database_settings) -> None:
    if not database_settings.is_test:
        raise RuntimeError(
            f"Refusing e2e seed: APP_ENV is {database_settings.APP_ENV!r}, not 'test'."
        )
    name = make_url(database_settings.DATABASE_URL).database or ""
    if not re.search(r"_test$", name):
        raise RuntimeError(f"Refusing e2e seed: database {name!r} does not end in '_test'.")


def _rebuild_schema() -> None:
    config = Config(str(BACKEND_ROOT / "alembic.ini"))
    config.set_main_option("script_location", str(BACKEND_ROOT / "alembic"))
    command.downgrade(config, "base")
    command.upgrade(config, "head")


def _today_start() -> datetime:
    tz = ZoneInfo(get_settings().PILOT_TIMEZONE or "Asia/Kolkata")
    local_midnight = (
        datetime.now(UTC).astimezone(tz).replace(hour=0, minute=0, second=0, microsecond=0)
    )
    return local_midnight.astimezone(UTC)


def _user(name, email, phone, role, zone_id=None, lat=None, lon=None) -> User:
    return User(
        name=name,
        email=email,
        phone=phone,
        password_hash=get_password_hash(E2E_PASSWORD),
        role=role,
        zone_id=zone_id,
        status=UserStatus.ACTIVE,
        latitude=lat,
        longitude=lon,
    )


def main() -> None:
    database_settings = get_database_settings()
    _assert_safe_database(database_settings)
    _rebuild_schema()

    engine = create_engine(database_settings.DATABASE_URL, future=True)
    session_factory = sessionmaker(bind=engine, future=True)

    with session_factory() as db:
        db.add(WasteCategory(code="DRY", label="Dry Waste", sort_order=1, is_active=True))

        # Journey 1 — authentication persistence (its own ward + citizen).
        auth_ward = Zone(name="E2E Auth Ward", code="W-E2E-AUTH", sectors="Sector A")
        db.add(auth_ward)
        db.flush()
        db.add(
            _user(
                "E2E Auth Citizen",
                "e2e-auth-citizen@verdeza.test",
                "+919000000101",
                Role.CITIZEN,
                auth_ward.id,
            )
        )

        # Journey 2 — cross-role complaint (its own ward, citizen and manager).
        complaint_ward = Zone(name="E2E Complaint Ward", code="W-E2E-CMP", sectors="Sector B")
        db.add(complaint_ward)
        db.flush()
        manager = _user(
            "E2E Ward Manager",
            "e2e-manager@verdeza.test",
            "+919000000102",
            Role.MUNICIPAL_OFFICER,
            complaint_ward.id,
        )
        db.add(manager)
        db.add(
            _user(
                "E2E Complaint Citizen",
                "e2e-complaint-citizen@verdeza.test",
                "+919000000103",
                Role.CITIZEN,
                complaint_ward.id,
            )
        )
        db.flush()
        complaint_ward.manager_id = manager.id

        # Journey 3 — collector live route (its own ward, collector, citizen, stops).
        route_ward = Zone(name="E2E Route Ward", code="W-E2E-RTE", sectors="Sector C")
        db.add(route_ward)
        db.flush()
        collector = _user(
            "E2E Collector",
            "e2e-collector@verdeza.test",
            "+919000000104",
            Role.COLLECTION_WORKER,
            route_ward.id,
            lat=26.8467,
            lon=80.9462,
        )
        route_citizen = _user(
            "E2E Route Citizen",
            "e2e-route-citizen@verdeza.test",
            "+919000000105",
            Role.CITIZEN,
            route_ward.id,
            lat=26.8500,
            lon=80.9500,
        )
        db.add_all([collector, route_citizen])
        db.flush()

        today = _today_start()
        schedule = DailyPickupSchedule(
            collector_id=collector.id,
            zone_id=route_ward.id,
            schedule_date=today,
            total_stops=2,
            completed_stops=0,
        )
        db.add(schedule)
        db.flush()

        for order, (ref, lat, lon) in enumerate(
            [("COL-E2E-STOP-1", 26.8480, 80.9470), ("COL-E2E-STOP-2", 26.8490, 80.9490)], start=1
        ):
            pickup = Pickup(
                ref_code=ref,
                citizen_id=route_citizen.id,
                collector_id=collector.id,
                zone_id=route_ward.id,
                category="DRY",
                estimated_weight=10,
                status=PickupStatus.ASSIGNED,
                scheduled_date=today + timedelta(hours=9),
                time_slot="09:00-11:00",
            )
            db.add(pickup)
            db.flush()
            db.add(
                DailyPickupStop(
                    pickup_id=pickup.id,
                    schedule_id=schedule.id,
                    citizen_id=route_citizen.id,
                    pickup_order=order,
                    status=PickupStopStatus.PENDING,
                    latitude=lat,
                    longitude=lon,
                    notes=f"{ref} Address",
                )
            )

        db.commit()

    engine.dispose()
    print("E2E seed complete.")


if __name__ == "__main__":
    main()
