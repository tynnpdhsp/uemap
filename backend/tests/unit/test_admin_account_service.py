from datetime import datetime

import pytest
from bson import ObjectId
from fastapi import HTTPException

from app.core.security import hash_password, verify_password
from app.services import admin_account_service

pytestmark = pytest.mark.unit

IP = "127.0.0.1"


async def _seed_admin(mock_db, **overrides):
    now = datetime.utcnow()
    doc = {
        "_id": overrides.pop("_id", ObjectId()),
        "username": "admin01",
        "password_hash": hash_password("password123"),
        "display_name": "Admin 01",
        "is_system_admin": False,
        "status": "active",
        "last_login_at": None,
        "created_at": now,
        "updated_at": now,
    }
    doc.update(overrides)
    await mock_db["admins"].insert_one(doc)
    return doc


@pytest.mark.asyncio
async def test_list_admins_empty(mock_db):
    result = await admin_account_service.list_admins()
    assert result == []


@pytest.mark.asyncio
async def test_list_admins(mock_db):
    await _seed_admin(mock_db, username="a1")
    await _seed_admin(mock_db, username="a2")
    result = await admin_account_service.list_admins()
    assert len(result) == 2


@pytest.mark.asyncio
async def test_create_admin_success(mock_db):
    sys_admin_id = ObjectId()
    result = await admin_account_service.create_admin(
        "newadmin", "newpass1234", "Admin Mới", sys_admin_id, IP
    )
    assert result["username"] == "newadmin"
    assert result["display_name"] == "Admin Mới"
    assert result["is_system_admin"] is False

    admin_doc = await mock_db["admins"].find_one({"username": "newadmin"})
    assert admin_doc is not None
    assert verify_password("newpass1234", admin_doc["password_hash"])

    logs = [d for d in mock_db["audit_logs"].docs if d["event_code"] == "ADMIN_ACCOUNT_CREATE"]
    assert len(logs) == 1


@pytest.mark.asyncio
async def test_create_admin_duplicate_username(mock_db):
    await _seed_admin(mock_db, username="taken")
    sys_admin_id = ObjectId()
    with pytest.raises(HTTPException) as exc:
        await admin_account_service.create_admin("taken", "password123", "Dup", sys_admin_id, IP)
    assert exc.value.detail["error"]["code"] == "ADMIN_USERNAME_EXISTS"


@pytest.mark.asyncio
async def test_update_admin_display_name(mock_db):
    admin = await _seed_admin(mock_db)
    sys_admin_id = ObjectId()
    result = await admin_account_service.update_admin(
        str(admin["_id"]),
        {"display_name": "Tên mới"},
        sys_admin_id,
        IP,
    )
    assert result["display_name"] == "Tên mới"

    logs = [d for d in mock_db["audit_logs"].docs if d["event_code"] == "ADMIN_ACCOUNT_UPDATE"]
    assert len(logs) == 1


@pytest.mark.asyncio
async def test_update_admin_password(mock_db):
    admin = await _seed_admin(mock_db)
    sys_admin_id = ObjectId()
    await admin_account_service.update_admin(
        str(admin["_id"]),
        {"password": "newpassword99"},
        sys_admin_id,
        IP,
    )
    updated = await mock_db["admins"].find_one({"_id": admin["_id"]})
    assert verify_password("newpassword99", updated["password_hash"])


@pytest.mark.asyncio
async def test_update_admin_not_found(mock_db):
    with pytest.raises(HTTPException) as exc:
        await admin_account_service.update_admin(
            str(ObjectId()), {"display_name": "X"}, ObjectId(), IP
        )
    assert exc.value.detail["error"]["code"] == "ADMIN_NOT_FOUND"


@pytest.mark.asyncio
async def test_disable_admin_success(mock_db):
    target = await _seed_admin(mock_db, username="victim", is_system_admin=False)
    sys_admin_id = ObjectId()

    await mock_db["admin_sessions"].insert_one(
        {
            "admin_id": target["_id"],
            "jti": "ses1",
            "revoked_at": None,
        }
    )

    await admin_account_service.disable_admin(str(target["_id"]), sys_admin_id, IP)

    updated = await mock_db["admins"].find_one({"_id": target["_id"]})
    assert updated["status"] == "disabled"

    session = await mock_db["admin_sessions"].find_one({"jti": "ses1"})
    assert session["revoked_at"] is not None

    logs = [d for d in mock_db["audit_logs"].docs if d["event_code"] == "ADMIN_ACCOUNT_DISABLE"]
    assert len(logs) == 1


@pytest.mark.asyncio
async def test_disable_admin_cannot_self_disable(mock_db):
    admin_id = ObjectId()
    await _seed_admin(mock_db, _id=admin_id, username="self")
    with pytest.raises(HTTPException) as exc:
        await admin_account_service.disable_admin(str(admin_id), admin_id, IP)
    assert exc.value.detail["error"]["code"] == "ADMIN_CANNOT_DISABLE_SELF"


@pytest.mark.asyncio
async def test_disable_admin_last_system_admin_blocked(mock_db):
    sys_id = ObjectId()
    actor_id = ObjectId()
    await _seed_admin(
        mock_db, _id=sys_id, username="only_sys", is_system_admin=True, status="active"
    )

    with pytest.raises(HTTPException) as exc:
        await admin_account_service.disable_admin(str(sys_id), actor_id, IP)
    assert exc.value.detail["error"]["code"] == "ADMIN_CANNOT_DISABLE_SELF"

    admin = await mock_db["admins"].find_one({"_id": sys_id})
    assert admin["status"] == "active"


@pytest.mark.asyncio
async def test_disable_admin_system_admin_allowed_if_another_exists(mock_db):
    sys1 = ObjectId()
    sys2 = ObjectId()
    await _seed_admin(mock_db, _id=sys1, username="sys1", is_system_admin=True, status="active")
    await _seed_admin(mock_db, _id=sys2, username="sys2", is_system_admin=True, status="active")

    await admin_account_service.disable_admin(str(sys1), sys2, IP)
    disabled = await mock_db["admins"].find_one({"_id": sys1})
    assert disabled["status"] == "disabled"


@pytest.mark.asyncio
async def test_disable_admin_not_found(mock_db):
    with pytest.raises(HTTPException) as exc:
        await admin_account_service.disable_admin(str(ObjectId()), ObjectId(), IP)
    assert exc.value.detail["error"]["code"] == "ADMIN_NOT_FOUND"


@pytest.mark.asyncio
async def test_disable_admin_invalid_id(mock_db):
    with pytest.raises(HTTPException) as exc:
        await admin_account_service.disable_admin("invalid-id", ObjectId(), IP)
    assert exc.value.detail["error"]["code"] == "ADMIN_NOT_FOUND"
