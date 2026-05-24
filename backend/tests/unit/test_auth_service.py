from datetime import datetime, timedelta
from unittest.mock import AsyncMock, patch

import pytest
from bson import ObjectId
from fastapi import HTTPException
from jose import jwt

from app.core.config import settings
from app.core.security import hash_password, verify_password
from app.services import auth_service, session_service
from tests.unit.conftest import TEST_EMAIL, TEST_NAME, TEST_PASSWORD

pytestmark = pytest.mark.unit


@pytest.mark.asyncio
async def test_register_student_success(mock_db):
    with (
        patch(
            "app.services.auth_service.otp_service.create_otp",
            AsyncMock(return_value="111111"),
        ),
        patch(
            "app.services.auth_service.email_service.send_otp_email",
            AsyncMock(),
        ) as mock_email,
    ):
        result = await auth_service.register_student(
            email=TEST_EMAIL,
            password=TEST_PASSWORD,
            full_name=TEST_NAME,
            ip_address="127.0.0.1",
        )
    assert result["email"] == TEST_EMAIL
    assert result["status"] == "pending_activation"
    mock_email.assert_called_once()
    student = await mock_db["students"].find_one({"email": TEST_EMAIL})
    assert student is not None
    assert verify_password(TEST_PASSWORD, student["password_hash"])
    assert await mock_db["audit_logs"].count_documents({"event_code": "AUTH_REGISTER"}) == 1


@pytest.mark.asyncio
async def test_register_student_duplicate_email(mock_db):
    await mock_db["students"].insert_one({"email": TEST_EMAIL, "status": "active"})
    with pytest.raises(HTTPException) as exc:
        await auth_service.register_student(TEST_EMAIL, TEST_PASSWORD, TEST_NAME, "127.0.0.1")
    assert exc.value.detail["error"]["code"] == "AUTH_EMAIL_EXISTS"


@pytest.mark.asyncio
async def test_register_student_rejects_pending_activation_otp(mock_db):
    now = datetime.utcnow()
    await mock_db["otp_tokens"].insert_one(
        {
            "email": TEST_EMAIL,
            "purpose": "activation",
            "otp_hash": "hash",
            "sent_at": now,
            "expires_at": now + timedelta(minutes=15),
            "resend_available_at": now + timedelta(seconds=60),
            "used_at": None,
            "created_at": now,
        }
    )
    with pytest.raises(HTTPException) as exc:
        await auth_service.register_student(TEST_EMAIL, TEST_PASSWORD, TEST_NAME, "127.0.0.1")
    assert exc.value.detail["error"]["code"] == "AUTH_EMAIL_EXISTS"


@pytest.mark.asyncio
async def test_activate_student_account(mock_db):
    student_id = ObjectId()
    await mock_db["students"].insert_one(
        {"_id": student_id, "email": TEST_EMAIL, "status": "pending_activation"}
    )
    with patch(
        "app.services.auth_service.otp_service.verify_otp",
        AsyncMock(return_value=True),
    ):
        result = await auth_service.activate_student_account(TEST_EMAIL, "111111", "127.0.0.1")
    assert result["success"] is True
    assert "activated_at_display" in result
    student = await mock_db["students"].find_one({"email": TEST_EMAIL})
    assert student["status"] == "active"
    assert student["activated_at"] is not None


@pytest.mark.asyncio
async def test_login_not_activated(mock_db):
    await mock_db["students"].insert_one(
        {
            "email": TEST_EMAIL,
            "password_hash": hash_password(TEST_PASSWORD),
            "status": "pending_activation",
        }
    )
    with pytest.raises(HTTPException) as exc:
        await auth_service.login_student(TEST_EMAIL, TEST_PASSWORD, "127.0.0.1", "UA")
    assert exc.value.detail["error"]["code"] == "AUTH_LOGIN_NOT_ACTIVATED"


@pytest.mark.asyncio
async def test_login_locked(mock_db):
    await mock_db["students"].insert_one(
        {
            "email": TEST_EMAIL,
            "password_hash": hash_password(TEST_PASSWORD),
            "status": "locked",
            "locked_reason": "test",
        }
    )
    with pytest.raises(HTTPException) as exc:
        await auth_service.login_student(TEST_EMAIL, TEST_PASSWORD, "127.0.0.1", "UA")
    assert exc.value.detail["error"]["code"] == "AUTH_LOGIN_LOCKED"


@pytest.mark.asyncio
async def test_login_wrong_password(mock_db):
    sid = ObjectId()
    await mock_db["students"].insert_one(
        {
            "_id": sid,
            "email": TEST_EMAIL,
            "password_hash": hash_password(TEST_PASSWORD),
            "status": "active",
            "full_name": TEST_NAME,
        }
    )
    with pytest.raises(HTTPException) as exc:
        await auth_service.login_student(TEST_EMAIL, "wrong", "127.0.0.1", "UA")
    assert exc.value.detail["error"]["code"] == "AUTH_LOGIN_FAILED"


@pytest.mark.asyncio
async def test_login_unknown_email(mock_db):
    with pytest.raises(HTTPException) as exc:
        await auth_service.login_student(TEST_EMAIL, TEST_PASSWORD, "127.0.0.1", "UA")
    assert exc.value.detail["error"]["code"] == "AUTH_LOGIN_FAILED"


@pytest.mark.asyncio
async def test_login_rate_limit(mock_db):
    await mock_db["students"].insert_one(
        {
            "email": TEST_EMAIL,
            "password_hash": hash_password(TEST_PASSWORD),
            "status": "active",
            "full_name": TEST_NAME,
        }
    )
    now = datetime.utcnow()
    for _ in range(10):
        await mock_db["login_attempts"].insert_one(
            {"email": TEST_EMAIL, "ip_address": "127.0.0.1", "failed_at": now}
        )
    with pytest.raises(HTTPException) as exc:
        await auth_service.login_student(TEST_EMAIL, TEST_PASSWORD, "127.0.0.1", "UA")
    assert exc.value.detail["error"]["code"] == "AUTH_LOGIN_RATE_LIMIT"


@pytest.mark.asyncio
async def test_login_success(mock_db):
    await mock_db["students"].insert_one(
        {
            "email": TEST_EMAIL,
            "password_hash": hash_password(TEST_PASSWORD),
            "status": "active",
            "full_name": TEST_NAME,
        }
    )
    result = await auth_service.login_student(TEST_EMAIL, TEST_PASSWORD, "127.0.0.1", "UA")
    assert "access_token" in result
    assert result["student"]["email"] == TEST_EMAIL


@pytest.mark.asyncio
async def test_logout_student():
    student_id = ObjectId()
    with (
        patch(
            "app.services.auth_service.session_service.revoke_session",
            AsyncMock(),
        ) as mock_revoke,
        patch(
            "app.services.auth_service.audit_service.log_event",
            AsyncMock(),
        ) as mock_log,
    ):
        await auth_service.logout_student(student_id, "jti-abc", "127.0.0.1")
    mock_revoke.assert_called_once_with("jti-abc")
    mock_log.assert_called_once()


@pytest.mark.asyncio
async def test_forgot_password_sends_for_active(mock_db):
    await mock_db["students"].insert_one(
        {
            "email": TEST_EMAIL,
            "full_name": TEST_NAME,
            "status": "active",
        }
    )
    with (
        patch(
            "app.services.auth_service.otp_service.create_otp",
            AsyncMock(return_value="111111"),
        ),
        patch(
            "app.services.auth_service.email_service.send_otp_email",
            AsyncMock(),
        ) as mock_email,
    ):
        result = await auth_service.request_forgot_password(TEST_EMAIL, "127.0.0.1")
    assert result["success"] is True
    mock_email.assert_called_once()


@pytest.mark.asyncio
async def test_forgot_password_pending_activation(mock_db):
    await mock_db["students"].insert_one(
        {
            "email": TEST_EMAIL,
            "full_name": TEST_NAME,
            "status": "pending_activation",
        }
    )
    with (
        patch(
            "app.services.auth_service.otp_service.create_otp",
            AsyncMock(return_value="111111"),
        ),
        patch(
            "app.services.auth_service.email_service.send_otp_email",
            AsyncMock(),
        ) as mock_email,
    ):
        await auth_service.request_forgot_password(TEST_EMAIL, "127.0.0.1")
    mock_email.assert_called_once()


@pytest.mark.asyncio
async def test_forgot_password_skips_locked_status(mock_db):
    await mock_db["students"].insert_one(
        {"email": TEST_EMAIL, "full_name": TEST_NAME, "status": "locked"}
    )
    with patch(
        "app.services.auth_service.email_service.send_otp_email",
        AsyncMock(),
    ) as mock_email:
        await auth_service.request_forgot_password(TEST_EMAIL, "127.0.0.1")
    mock_email.assert_not_called()


@pytest.mark.asyncio
async def test_forgot_password_skips_unknown_email(mock_db):
    with patch(
        "app.services.auth_service.email_service.send_otp_email",
        AsyncMock(),
    ) as mock_email:
        result = await auth_service.request_forgot_password(TEST_EMAIL, "127.0.0.1")
    assert result["success"] is True
    mock_email.assert_not_called()


@pytest.mark.asyncio
async def test_verify_forgot_password_otp_returns_token(mock_db):
    await mock_db["students"].insert_one({"email": TEST_EMAIL, "status": "active"})
    with patch(
        "app.services.auth_service.otp_service.verify_otp",
        AsyncMock(return_value=True),
    ):
        token = await auth_service.verify_forgot_password_otp(TEST_EMAIL, "111111", "127.0.0.1")
    payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
    assert payload["sub"] == TEST_EMAIL
    assert payload["purpose"] == "password_reset"


def test_create_and_decode_reset_token_valid():
    token = auth_service.create_reset_token(TEST_EMAIL)
    auth_service.decode_reset_token(token, TEST_EMAIL)


def test_decode_reset_token_wrong_email():
    token = auth_service.create_reset_token(TEST_EMAIL)
    with pytest.raises(HTTPException) as exc:
        auth_service.decode_reset_token(token, "9999999999@student.hcmue.edu.vn")
    assert exc.value.detail["error"]["code"] == "AUTH_RESET_TOKEN_INVALID"


def test_decode_reset_token_invalid():
    with pytest.raises(HTTPException) as exc:
        auth_service.decode_reset_token("invalid-token", TEST_EMAIL)
    assert exc.value.detail["error"]["code"] == "AUTH_RESET_TOKEN_INVALID"


@pytest.mark.asyncio
async def test_reset_password_student_not_found(mock_db):
    token = auth_service.create_reset_token(TEST_EMAIL)
    with pytest.raises(HTTPException) as exc:
        await auth_service.reset_password_with_token(TEST_EMAIL, token, "newpass12345", "127.0.0.1")
    assert exc.value.status_code == 404
    assert exc.value.detail["error"]["code"] == "STUDENT_NOT_FOUND"


@pytest.mark.asyncio
async def test_reset_password_with_token(mock_db):
    student_id = ObjectId()
    await mock_db["students"].insert_one(
        {
            "_id": student_id,
            "email": TEST_EMAIL,
            "password_hash": hash_password("oldpass123"),
            "status": "active",
        }
    )
    expires = datetime.utcnow() + timedelta(days=7)
    await mock_db["student_sessions"].insert_one(
        {
            "student_id": student_id,
            "jti": "old",
            "revoked_at": None,
            "expires_at": expires,
        }
    )
    reset_token = auth_service.create_reset_token(TEST_EMAIL)
    await auth_service.reset_password_with_token(
        TEST_EMAIL, reset_token, "newpass12345", "127.0.0.1"
    )
    student = await mock_db["students"].find_one({"email": TEST_EMAIL})
    assert verify_password("newpass12345", student["password_hash"])
    assert await session_service.verify_session("old") is False


@pytest.mark.asyncio
async def test_change_password_success(mock_db):
    student_id = ObjectId()
    await mock_db["students"].insert_one(
        {
            "_id": student_id,
            "email": TEST_EMAIL,
            "password_hash": hash_password(TEST_PASSWORD),
            "status": "active",
        }
    )
    expires = datetime.utcnow() + timedelta(days=7)
    await mock_db["student_sessions"].insert_one(
        {"student_id": student_id, "jti": "current", "revoked_at": None, "expires_at": expires}
    )
    await mock_db["student_sessions"].insert_one(
        {"student_id": student_id, "jti": "other", "revoked_at": None, "expires_at": expires}
    )
    await auth_service.change_password(
        student_id, "current", TEST_PASSWORD, "newpassword99", "127.0.0.1"
    )
    student = await mock_db["students"].find_one({"_id": student_id})
    assert verify_password("newpassword99", student["password_hash"])


@pytest.mark.asyncio
async def test_change_password_student_not_found(mock_db):
    with pytest.raises(HTTPException) as exc:
        await auth_service.change_password(
            ObjectId(), "jti", TEST_PASSWORD, "newpassword99", "127.0.0.1"
        )
    assert exc.value.detail["error"]["code"] == "STUDENT_NOT_FOUND"


@pytest.mark.asyncio
async def test_login_success_writes_audit_log(mock_db):
    await mock_db["students"].insert_one(
        {
            "email": TEST_EMAIL,
            "password_hash": hash_password(TEST_PASSWORD),
            "status": "active",
            "full_name": TEST_NAME,
        }
    )
    await auth_service.login_student(TEST_EMAIL, TEST_PASSWORD, "127.0.0.1", "UA")
    logs = mock_db["audit_logs"].docs
    assert any(log["event_code"] == "AUTH_LOGIN" and log["result"] == "success" for log in logs)


@pytest.mark.asyncio
async def test_change_password_wrong_current(mock_db):
    student_id = ObjectId()
    await mock_db["students"].insert_one(
        {
            "_id": student_id,
            "email": TEST_EMAIL,
            "password_hash": hash_password(TEST_PASSWORD),
        }
    )
    with pytest.raises(HTTPException) as exc:
        await auth_service.change_password(student_id, "jti", "wrong", "newpassword99", "127.0.0.1")
    assert exc.value.detail["error"]["code"] == "AUTH_PASSWORD_CHANGE_FAILED"
