"""Unit tests for request-scoped database-session cleanup."""

from types import SimpleNamespace

import pytest

from app.db.session import get_db


class FakeSession:
    def __init__(self) -> None:
        self.rollback_calls = 0
        self.close_calls = 0

    def rollback(self) -> None:
        self.rollback_calls += 1

    def close(self) -> None:
        self.close_calls += 1


def make_request(session: FakeSession):
    state = SimpleNamespace(
        session_factory=lambda: session,
    )
    application = SimpleNamespace(state=state)

    return SimpleNamespace(app=application)


@pytest.mark.unit
def test_get_db_closes_session_after_success():
    session = FakeSession()
    dependency = get_db(make_request(session))

    assert next(dependency) is session

    with pytest.raises(StopIteration):
        next(dependency)

    assert session.rollback_calls == 0
    assert session.close_calls == 1


@pytest.mark.unit
def test_get_db_rolls_back_and_closes_after_escaped_exception():
    session = FakeSession()
    dependency = get_db(make_request(session))

    assert next(dependency) is session

    with pytest.raises(RuntimeError, match="route failed"):
        dependency.throw(RuntimeError("route failed"))

    assert session.rollback_calls == 1
    assert session.close_calls == 1
