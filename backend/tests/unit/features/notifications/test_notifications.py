from datetime import UTC, datetime
from types import SimpleNamespace
from uuid import uuid4

from app.features.notifications.service import list_for_user, mark_read, serialize_notification


class ScalarResult:
    def __init__(self, value):
        self.value = value

    def all(self):
        return self.value


class FakeDatabase:
    def __init__(self, notification=None, notifications_list=None):
        self.notification = notification
        self.notifications_list = notifications_list or []
        self.commits = 0

    def scalars(self, _statement):
        return ScalarResult(self.notifications_list)

    def scalar(self, _statement):
        return self.notification

    def commit(self):
        self.commits += 1


def test_serialize_notification():
    n = SimpleNamespace(
        id=uuid4(),
        title="Test Title",
        body="Test Body",
        is_read=False,
        created_at=datetime.now(UTC),
    )
    res = serialize_notification(n)
    assert res.id == n.id
    assert res.title == "Test Title"
    assert res.body == "Test Body"
    assert res.is_read is False


def test_list_for_user():
    n = SimpleNamespace(
        id=uuid4(),
        title="Test Title",
        body="Test Body",
        is_read=False,
        created_at=datetime.now(UTC),
    )
    db = FakeDatabase(notifications_list=[n])
    res = list_for_user(db, uuid4())
    assert len(res) == 1
    assert res[0].id == n.id


def test_mark_read():
    n = SimpleNamespace(
        id=uuid4(),
        title="Test Title",
        body="Test Body",
        is_read=False,
        created_at=datetime.now(UTC),
    )
    db = FakeDatabase(notification=n)
    res = mark_read(db, n.id, uuid4())
    assert res is not None
    assert res.is_read is True
    assert db.commits == 1

    # Not found
    db_empty = FakeDatabase(notification=None)
    res_empty = mark_read(db_empty, uuid4(), uuid4())
    assert res_empty is None
