from datetime import datetime, timedelta

import pytest
from bson import ObjectId
from fastapi import HTTPException

from app.services import admin_student_service

pytestmark = pytest.mark.unit

ADMIN_ID = ObjectId()
IP = "127.0.0.1"


async def _seed_student(mock_db, **overrides):
    now = datetime.utcnow()
    doc = {
        "_id": overrides.pop("_id", ObjectId()),
        "email": "sv@student.hcmue.edu.vn",
        "full_name": "Nguyễn Văn A",
        "status": "active",
        "locked_reason": None,
        "activated_at": now,
        "created_at": now,
        "updated_at": now,
    }
    doc.update(overrides)
    await mock_db["students"].insert_one(doc)
    return doc


@pytest.mark.asyncio
async def test_list_students_empty(mock_db):
    result = await admin_student_service.list_students({"page": 1, "page_size": 20})
    assert result["items"] == []
    assert result["meta"]["total"] == 0


@pytest.mark.asyncio
async def test_list_students_pagination(mock_db):
    for i in range(5):
        await _seed_student(mock_db, email=f"sv{i}@test.vn")
    result = await admin_student_service.list_students({"page": 1, "page_size": 3})
    assert len(result["items"]) <= 3
    assert result["meta"]["total"] == 5


@pytest.mark.asyncio
async def test_list_students_filter_by_email(mock_db):
    await _seed_student(mock_db, email="alice@test.vn")
    await _seed_student(mock_db, email="bob@test.vn")
    result = await admin_student_service.list_students(
        {"page": 1, "page_size": 20, "email": "alice"}
    )
    assert result["meta"]["total"] == 1
    assert result["items"][0]["email"] == "alice@test.vn"


@pytest.mark.asyncio
async def test_list_students_filter_by_status(mock_db):
    await _seed_student(mock_db, email="a@test.vn", status="active")
    await _seed_student(mock_db, email="b@test.vn", status="locked")
    result = await admin_student_service.list_students(
        {"page": 1, "page_size": 20, "status": "locked"}
    )
    assert result["meta"]["total"] == 1


@pytest.mark.asyncio
async def test_get_student_detail(mock_db):
    student = await _seed_student(mock_db)
    await mock_db["places"].insert_one({"creator_student_id": student["_id"]})
    await mock_db["comments"].insert_one({"student_id": student["_id"]})

    detail = await admin_student_service.get_student_detail(str(student["_id"]))
    assert detail["email"] == student["email"]
    assert detail["places_count"] == 1
    assert detail["comments_count"] == 1
    assert detail["status_label"] == "hoạt động"


@pytest.mark.asyncio
async def test_get_student_detail_not_found(mock_db):
    with pytest.raises(HTTPException) as exc:
        await admin_student_service.get_student_detail(str(ObjectId()))
    assert exc.value.detail["error"]["code"] == "STUDENT_NOT_FOUND"


@pytest.mark.asyncio
async def test_get_student_detail_invalid_id(mock_db):
    with pytest.raises(HTTPException) as exc:
        await admin_student_service.get_student_detail("invalid-id")
    assert exc.value.detail["error"]["code"] == "STUDENT_NOT_FOUND"


@pytest.mark.asyncio
async def test_lock_student_success(mock_db):
    student = await _seed_student(mock_db, status="active")

    expires = datetime.utcnow() + timedelta(days=7)
    await mock_db["student_sessions"].insert_one(
        {
            "student_id": student["_id"],
            "jti": "s1",
            "revoked_at": None,
            "expires_at": expires,
        }
    )
    await mock_db["student_sessions"].insert_one(
        {
            "student_id": student["_id"],
            "jti": "s2",
            "revoked_at": None,
            "expires_at": expires,
        }
    )

    result = await admin_student_service.lock_student(
        str(student["_id"]),
        "Vi phạm quy định sử dụng",
        ADMIN_ID,
        IP,
    )

    assert result["status"] == "locked"
    assert result["locked_reason"] == "Vi phạm quy định sử dụng"

    s1 = await mock_db["student_sessions"].find_one({"jti": "s1"})
    s2 = await mock_db["student_sessions"].find_one({"jti": "s2"})
    assert s1["revoked_at"] is not None
    assert s2["revoked_at"] is not None


@pytest.mark.asyncio
async def test_lock_student_not_found(mock_db):
    with pytest.raises(HTTPException) as exc:
        await admin_student_service.lock_student(
            str(ObjectId()), "Lý do khóa dài cho đủ ký tự", ADMIN_ID, IP
        )
    assert exc.value.detail["error"]["code"] == "STUDENT_NOT_FOUND"


@pytest.mark.asyncio
async def test_lock_student_audit_log(mock_db):
    student = await _seed_student(mock_db)
    await admin_student_service.lock_student(
        str(student["_id"]), "Vi phạm nội quy nhiều lần", ADMIN_ID, IP
    )
    logs = [d for d in mock_db["audit_logs"].docs if d["event_code"] == "STUDENT_LOCK"]
    assert len(logs) == 1
    assert str(ADMIN_ID) == logs[0]["actor_id"]


@pytest.mark.asyncio
async def test_unlock_student_success(mock_db):
    student = await _seed_student(mock_db, status="locked", locked_reason="test")
    result = await admin_student_service.unlock_student(str(student["_id"]), ADMIN_ID, IP)
    assert result["status"] == "active"
    assert result["locked_reason"] is None


@pytest.mark.asyncio
async def test_unlock_student_not_locked(mock_db):
    student = await _seed_student(mock_db, status="active")
    with pytest.raises(HTTPException) as exc:
        await admin_student_service.unlock_student(str(student["_id"]), ADMIN_ID, IP)
    assert exc.value.detail["error"]["code"] == "STUDENT_NOT_FOUND"


@pytest.mark.asyncio
async def test_unlock_student_not_found(mock_db):
    with pytest.raises(HTTPException) as exc:
        await admin_student_service.unlock_student(str(ObjectId()), ADMIN_ID, IP)
    assert exc.value.detail["error"]["code"] == "STUDENT_NOT_FOUND"


@pytest.mark.asyncio
async def test_unlock_student_audit_log(mock_db):
    student = await _seed_student(mock_db, status="locked", locked_reason="test")
    await admin_student_service.unlock_student(str(student["_id"]), ADMIN_ID, IP)
    logs = [d for d in mock_db["audit_logs"].docs if d["event_code"] == "STUDENT_UNLOCK"]
    assert len(logs) == 1
