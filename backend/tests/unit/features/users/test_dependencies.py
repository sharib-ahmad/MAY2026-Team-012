from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from app.features.users.dependencies import require_citizen, require_collector, require_recycler
from app.models.enums import Role


def test_require_citizen():
    user = SimpleNamespace(role=Role.CITIZEN)
    assert require_citizen(user) == user

    unauthorized_user = SimpleNamespace(role=Role.RECYCLER)
    with pytest.raises(HTTPException) as exc:
        require_citizen(unauthorized_user)
    assert exc.value.status_code == 403
    assert "Citizen access required" in exc.value.detail


def test_require_collector():
    user = SimpleNamespace(role=Role.COLLECTION_WORKER)
    assert require_collector(user) == user

    unauthorized_user = SimpleNamespace(role=Role.CITIZEN)
    with pytest.raises(HTTPException) as exc:
        require_collector(unauthorized_user)
    assert exc.value.status_code == 403
    assert "Collector access required" in exc.value.detail


def test_require_recycler():
    user = SimpleNamespace(role=Role.RECYCLER)
    assert require_recycler(user) == user

    unauthorized_user = SimpleNamespace(role=Role.CITIZEN)
    with pytest.raises(HTTPException) as exc:
        require_recycler(unauthorized_user)
    assert exc.value.status_code == 403
    assert "Recycler access required" in exc.value.detail
