from sqlalchemy import select
from sqlalchemy.orm import sessionmaker

from app.core.security import verify_password
from app.features.users.models import User
from app.main import seed_database
from app.models.enums import Role
from app.models.zone import Zone


def test_seed_database_creates_requested_zones_and_demo_users(db) -> None:
    factory = sessionmaker(
        bind=db.connection(),
        expire_on_commit=False,
        join_transaction_mode="create_savepoint",
    )

    seed_database(factory)
    seed_database(factory)

    zones = db.scalars(select(Zone).order_by(Zone.code)).all()
    assert [(zone.code, zone.name, zone.sectors) for zone in zones] == [
        ("WARD-01", "Gomti Nagar", "Sector 1, Sector 2"),
        ("WARD-02", "Hazratganj", "Sector 3, Sector 4"),
        ("WARD-03", "Alambagh", "Sector 5"),
        ("WARD-04", "Indira Nagar", "Sector 6"),
        ("WARD-05", "Chowk", "Sector 7"),
    ]
    users = {user.email: user for user in db.scalars(select(User)).all()}
    expected_roles = {
        "admin@verdeza.test": Role.SYSTEM_ADMIN,
        "manager@verdeza.test": Role.MUNICIPAL_OFFICER,
        "citizen@verdeza.test": Role.CITIZEN,
        "collector@verdeza.test": Role.COLLECTION_WORKER,
        "recycler@verdeza.test": Role.RECYCLER,
    }
    assert {email: users[email].role for email in expected_roles} == expected_roles
    assert verify_password("password123", users["citizen@verdeza.test"].password_hash)
