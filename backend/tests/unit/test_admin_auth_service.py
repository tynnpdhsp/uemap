from datetime import datetime, timedelta

import pytest
from bson import ObjectId
from fastapi import HTTPException

from app.core.security import decode_access_token, hash_password
from app.services import admin_auth_service

pytestmark = pytest.mark.unit

ADMIN_USER = "sysadmin"
ADMIN_PASS = "admin12345"


def _make_admin(mock_db, **overrides):
    doc = {
        "_id": overrides.pop("_id", ObjectId()),
        "username": ADMIN_USER,
        "password_hash": hash_password(ADMIN_PASS),
        "display_name": "Quản trị",
        "is_system_admin": True,
        "status": "active",
        "last_login_at": None,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
    }
    doc.update(overrides)
    return doc


@pytest.mark.asyncio
async def test_login_success(mock_db):
    admin = _make_admin(mock_db)
    await mock_db["admins"].insert_one(admin)

    result = await admin_auth_service.login(ADMIN_USER, ADMIN_PASS, "127.0.0.1", "UA")

    assert "access_token" in result
    assert result["admin"]["username"] == ADMIN_USER
    assert result["admin"]["is_system_admin"] is True

    payload = decode_access_token(result["access_token"])
    assert payload["role"] == "admin"
    assert payload["sub"] == str(admin["_id"])
    assert "jti" in payload

    session = await mock_db["admin_sessions"].find_one({"admin_id": admin["_id"]})
    assert session is not None
    assert session["jti"] == payload["jti"]

    updated = await mock_db["admins"].find_one({"_id": admin["_id"]})
    assert updated["last_login_at"] is not None


@pytest.mark.asyncio
async def test_login_wrong_username(mock_db):
    await mock_db["admins"].insert_one(_make_admin(mock_db))
    with pytest.raises(HTTPException) as exc:
        await admin_auth_service.login("wrong_user", ADMIN_PASS, "127.0.0.1", "UA")
    assert exc.value.detail["error"]["code"] == "ADMIN_LOGIN_FAILED"


@pytest.mark.asyncio
async def test_login_wrong_password(mock_db):
    await mock_db["admins"].insert_one(_make_admin(mock_db))
    with pytest.raises(HTTPException) as exc:
        await admin_auth_service.login(ADMIN_USER, "wrongpass1", "127.0.0.1", "UA")
    assert exc.value.detail["error"]["code"] == "ADMIN_LOGIN_FAILED"

    count = await mock_db["admin_login_attempts"].count_documents({"username": ADMIN_USER})
    assert count == 1


@pytest.mark.asyncio
async def test_login_disabled_account(mock_db):
    admin = _make_admin(mock_db, status="disabled")
    await mock_db["admins"].insert_one(admin)
    with pytest.raises(HTTPException) as exc:
        await admin_auth_service.login(ADMIN_USER, ADMIN_PASS, "127.0.0.1", "UA")
    assert exc.value.detail["error"]["code"] == "ADMIN_ACCOUNT_DISABLED"


@pytest.mark.asyncio
async def test_login_rate_limit(mock_db):
    admin = _make_admin(mock_db)
    await mock_db["admins"].insert_one(admin)
    now = datetime.utcnow()
    for _ in range(10):
        await mock_db["admin_login_attempts"].insert_one({
            "username": ADMIN_USER, "ip_address": "127.0.0.1", "failed_at": now,
        })
    with pytest.raises(HTTPException) as exc:
        await admin_auth_service.login(ADMIN_USER, ADMIN_PASS, "127.0.0.1", "UA")
    assert exc.value.status_code == 429
    assert exc.value.detail["error"]["code"] == "AUTH_LOGIN_RATE_LIMIT"


@pytest.mark.asyncio
async def test_login_rate_limit_ip_only(mock_db):
    admin = _make_admin(mock_db)
    await mock_db["admins"].insert_one(admin)
    now = datetime.utcnow()
    for _ in range(10):
        await mock_db["admin_login_attempts"].insert_one({
            "username": "other_user", "ip_address": "10.0.0.1", "failed_at": now,
        })
    with pytest.raises(HTTPException) as exc:
        await admin_auth_service.login(ADMIN_USER, ADMIN_PASS, "10.0.0.1", "UA")
    assert exc.value.status_code == 429


@pytest.mark.asyncio
async def test_login_rate_limit_expired_attempts_ignored(mock_db):
    admin = _make_admin(mock_db)
    await mock_db["admins"].insert_one(admin)
    old = datetime.utcnow() - timedelta(minutes=20)
    for _ in range(10):
        await mock_db["admin_login_attempts"].insert_one({
            "username": ADMIN_USER, "ip_address": "127.0.0.1", "failed_at": old,
        })
    result = await admin_auth_service.login(ADMIN_USER, ADMIN_PASS, "127.0.0.1", "UA")
    assert "access_token" in result


@pytest.mark.asyncio
async def test_logout_revokes_session(mock_db):
    admin = _make_admin(mock_db)
    await mock_db["admins"].insert_one(admin)
    result = await admin_auth_service.login(ADMIN_USER, ADMIN_PASS, "127.0.0.1", "UA")
    jti = decode_access_token(result["access_token"])["jti"]

    await admin_auth_service.logout(admin["_id"], jti, "127.0.0.1")

    assert await admin_auth_service.verify_admin_session(jti) is False
    logs = [d for d in mock_db["audit_logs"].docs if d["event_code"] == "ADMIN_LOGOUT"]
    assert len(logs) == 1


@pytest.mark.asyncio
async def test_verify_session_active(mock_db):
    admin = _make_admin(mock_db)
    await mock_db["admins"].insert_one(admin)
    result = await admin_auth_service.login(ADMIN_USER, ADMIN_PASS, "127.0.0.1", "UA")
    jti = decode_access_token(result["access_token"])["jti"]

    assert await admin_auth_service.verify_admin_session(jti) is True


@pytest.mark.asyncio
async def test_verify_session_not_found(mock_db):
    assert await admin_auth_service.verify_admin_session("nonexistent") is False


@pytest.mark.asyncio
async def test_verify_session_expired(mock_db):
    await mock_db["admin_sessions"].insert_one({
        "jti": "expired-jti",
        "expires_at": datetime.utcnow() - timedelta(minutes=1),
        "revoked_at": None,
    })
    assert await admin_auth_service.verify_admin_session("expired-jti") is False


@pytest.mark.asyncio
async def test_verify_session_revoked(mock_db):
    await mock_db["admin_sessions"].insert_one({
        "jti": "revoked-jti",
        "expires_at": datetime.utcnow() + timedelta(hours=8),
        "revoked_at": datetime.utcnow(),
    })
    assert await admin_auth_service.verify_admin_session("revoked-jti") is False


def test_format_admin_info():
    admin_id = ObjectId()
    now = datetime.utcnow()
    info = admin_auth_service.format_admin_info({
        "_id": admin_id,
        "username": "testadmin",
        "display_name": "Test",
        "is_system_admin": False,
        "status": "active",
        "last_login_at": now,
        "created_at": now,
    })
    assert info["id"] == str(admin_id)
    assert info["status_label"] == "hoạt động"
    assert info["is_system_admin"] is False


@pytest.mark.asyncio
async def test_login_writes_audit_logs(mock_db):
    admin = _make_admin(mock_db)
    await mock_db["admins"].insert_one(admin)
    await admin_auth_service.login(ADMIN_USER, ADMIN_PASS, "127.0.0.1", "UA")

    logs = [d for d in mock_db["audit_logs"].docs if d["event_code"] == "ADMIN_LOGIN"]
    assert len(logs) == 1
    assert logs[0]["result"] == "success"


@pytest.mark.asyncio
async def test_login_failure_writes_audit_log(mock_db):
    admin = _make_admin(mock_db)
    await mock_db["admins"].insert_one(admin)
    with pytest.raises(HTTPException):
        await admin_auth_service.login(ADMIN_USER, "wrongpass1", "127.0.0.1", "UA")

    logs = [d for d in mock_db["audit_logs"].docs if d["event_code"] == "ADMIN_LOGIN"]
    assert len(logs) == 1
    assert logs[0]["result"] == "failure"
