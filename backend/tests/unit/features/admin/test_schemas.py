import pytest
from pydantic import ValidationError

from app.features.admin.schemas import UserUpdate


@pytest.mark.parametrize(
    "role",
    ["CITIZEN", "COLLECTION_WORKER", "RECYCLER", "MUNICIPAL_OFFICER", "SYSTEM_ADMIN"],
)
def test_user_update_accepts_canonical_role_names(role: str) -> None:
    assert UserUpdate(role=role).role == role


def test_user_update_rejects_unknown_role() -> None:
    with pytest.raises(ValidationError):
        UserUpdate(role="NOT_A_ROLE")
