import pytest
from bson import ObjectId

from app.services import audit_service

pytestmark = pytest.mark.unit

AUTH_AUDIT_EVENT_CODES = [
    ("AUTH_REGISTER", "guest", "student"),
    ("AUTH_OTP_SEND", "system", "otp"),
    ("AUTH_OTP_VERIFY", "guest", "student"),
    ("AUTH_LOGIN", "student", "session"),
    ("AUTH_LOGOUT", "student", "session"),
    ("AUTH_PASSWORD_RESET", "student", "student"),
    ("AUTH_PASSWORD_CHANGE", "student", "student"),
]


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "event_code,actor_role,object_type",
    AUTH_AUDIT_EVENT_CODES,
)
async def test_log_event_auth_module_codes(mock_db, event_code, actor_role, object_type):
    actor_id = ObjectId() if actor_role == "student" else None
    await audit_service.log_event(
        event_code=event_code,
        actor_role=actor_role,
        actor_id=actor_id,
        object_type=object_type,
        object_id=str(actor_id) if actor_id else None,
        result="success",
        description=f"Test {event_code}",
        ip_address="127.0.0.1",
    )
    log = await mock_db["audit_logs"].find_one({"event_code": event_code})
    assert log is not None
    assert log["actor_role"] == actor_role
    assert log["object_type"] == object_type
    assert log["result"] == "success"
    assert "occurred_at" in log
    assert "123456" not in log["description"]
