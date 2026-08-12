from unittest.mock import MagicMock, patch

from app.features.notifications.models import Notification
from app.features.users.models import User
from app.features.users.router import delete_account
from app.features.users.schemas import DeleteAccountRequest
from app.models.enums import UserStatus


@patch("app.features.users.router.create_audit_log")
def test_delete_account_logic(mock_create_audit_log):
    db = MagicMock()
    current_user = MagicMock(spec=User)
    current_user.id = "fake-user-id"
    current_user.name = "John Doe"
    current_user.email = "john@example.com"
    current_user.phone = "+919876543214"
    current_user.zone_id = "fake-zone-id"
    current_user.status = UserStatus.ACTIVE
    current_user.token_version = 1
    current_user.deleted_at = None
    current_user.role.value = "CITIZEN"

    payload = DeleteAccountRequest(reason="Moving away")

    # Mock db.scalar to return a manager_id
    db.scalar.return_value = "fake-manager-id"

    res = delete_account(payload, current_user, db)

    # Check notification got created
    db.add.assert_called_once()
    notification_arg = db.add.call_args[0][0]
    assert isinstance(notification_arg, Notification)
    assert notification_arg.user_id == "fake-manager-id"
    assert "john@example.com" in notification_arg.body
    assert "Moving away" in notification_arg.body

    # Check user fields updated
    assert current_user.status == UserStatus.DISABLED
    assert current_user.token_version == 2
    assert current_user.deleted_at is not None

    # Check email and phone were anonymized
    assert current_user.email.startswith("john@example.com-deleted-")
    assert current_user.phone.startswith("del-")
    assert len(current_user.phone) <= 20  # Fits in phone varchar(20)

    # Check audit log was created
    mock_create_audit_log.assert_called_once_with(
        db=db,
        actor_id="fake-user-id",
        actor_name="John Doe",
        actor_role="CITIZEN",
        action="DELETE_ACCOUNT",
        entity_type="USER",
        entity_id="fake-user-id",
        description=(
            "Citizen deleted their account (Email: john@example.com, "
            "Phone: +919876543214). Reason: Moving away"
        ),
        commit=False,
    )

    db.commit.assert_called_once()
    assert res == {"status": "ok"}
