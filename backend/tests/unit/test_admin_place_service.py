from datetime import datetime
from unittest.mock import AsyncMock, patch

import pytest
from bson import ObjectId
from fastapi import HTTPException

from app.services import admin_place_service

pytestmark = pytest.mark.unit

ADMIN_ID = ObjectId()
IP = "127.0.0.1"


async def _seed_place(mock_db, **overrides):
    now = datetime.utcnow()
    cat_id = ObjectId()
    student_id = ObjectId()
    doc = {
        "_id": ObjectId(),
        "public_id": overrides.pop("public_id", 1),
        "creator_student_id": overrides.pop("creator_student_id", student_id),
        "category_id": overrides.pop("category_id", cat_id),
        "name": "Quán cà phê",
        "description": "Mô tả",
        "address": "123 Đường ABC",
        "scope_type": "public",
        "location": {"type": "Point", "coordinates": [106.68, 10.76]},
        "hours": None,
        "contact": None,
        "status": "published",
        "hidden_note": None,
        "images": [],
        "video": None,
        "published_at": now,
        "deleted_at": None,
        "created_at": now,
        "updated_at": now,
    }
    doc.update(overrides)
    await mock_db["places"].insert_one(doc)

    await mock_db["categories"].insert_one({"_id": doc["category_id"], "name": "Ăn uống", "is_hidden": False, "created_at": now, "updated_at": now})
    await mock_db["students"].insert_one({"_id": doc["creator_student_id"], "email": "sv@test.vn", "full_name": "SV", "status": "active", "created_at": now})

    return doc


@pytest.mark.asyncio
async def test_hide_place_success(mock_db):
    place = await _seed_place(mock_db)
    await admin_place_service.hide_place(place["public_id"], "Nội dung vi phạm quy định cộng đồng", ADMIN_ID, IP)

    updated = await mock_db["places"].find_one({"public_id": place["public_id"]})
    assert updated["status"] == "hidden"
    assert updated["hidden_note"] == "Nội dung vi phạm quy định cộng đồng"


@pytest.mark.asyncio
async def test_hide_place_not_found(mock_db):
    with pytest.raises(HTTPException) as exc:
        await admin_place_service.hide_place(999, "Lý do ẩn địa điểm rất dài", ADMIN_ID, IP)
    assert exc.value.detail["error"]["code"] == "PLACE_NOT_FOUND"


@pytest.mark.asyncio
async def test_hide_place_already_deleted(mock_db):
    await _seed_place(mock_db, status="deleted")
    with pytest.raises(HTTPException) as exc:
        await admin_place_service.hide_place(1, "Lý do ẩn địa điểm rất dài", ADMIN_ID, IP)
    assert exc.value.detail["error"]["code"] == "PLACE_NOT_FOUND"


@pytest.mark.asyncio
async def test_unhide_place_success(mock_db):
    place = await _seed_place(mock_db, status="hidden", hidden_note="Tạm ẩn")
    await admin_place_service.unhide_place(place["public_id"], ADMIN_ID, IP)

    updated = await mock_db["places"].find_one({"public_id": place["public_id"]})
    assert updated["status"] == "published"
    assert updated["hidden_note"] is None


@pytest.mark.asyncio
async def test_unhide_place_not_hidden(mock_db):
    await _seed_place(mock_db, status="published")
    with pytest.raises(HTTPException) as exc:
        await admin_place_service.unhide_place(1, ADMIN_ID, IP)
    assert exc.value.detail["error"]["code"] == "PLACE_NOT_FOUND"


@pytest.mark.asyncio
async def test_soft_delete_place(mock_db):
    place = await _seed_place(mock_db)
    await admin_place_service.soft_delete_place(place["public_id"], ADMIN_ID, IP)

    updated = await mock_db["places"].find_one({"public_id": place["public_id"]})
    assert updated["status"] == "deleted"
    assert updated["deleted_at"] is not None

    logs = [d for d in mock_db["audit_logs"].docs if d["event_code"] == "PLACE_ADMIN_SOFT_DELETE"]
    assert len(logs) == 1


@pytest.mark.asyncio
async def test_soft_delete_already_deleted(mock_db):
    await _seed_place(mock_db, status="deleted")
    with pytest.raises(HTTPException) as exc:
        await admin_place_service.soft_delete_place(1, ADMIN_ID, IP)
    assert exc.value.detail["error"]["code"] == "PLACE_NOT_FOUND"


@pytest.mark.asyncio
async def test_transfer_creator_success(mock_db):
    place = await _seed_place(mock_db)
    new_student_id = ObjectId()
    now = datetime.utcnow()
    await mock_db["students"].insert_one({"_id": new_student_id, "email": "new@test.vn", "full_name": "Mới", "status": "active", "created_at": now})

    await admin_place_service.transfer_creator(place["public_id"], str(new_student_id), ADMIN_ID, IP)

    updated = await mock_db["places"].find_one({"public_id": place["public_id"]})
    assert updated["creator_student_id"] == new_student_id


@pytest.mark.asyncio
async def test_transfer_creator_student_not_found(mock_db):
    place = await _seed_place(mock_db)
    with pytest.raises(HTTPException) as exc:
        await admin_place_service.transfer_creator(place["public_id"], str(ObjectId()), ADMIN_ID, IP)
    assert exc.value.detail["error"]["code"] == "STUDENT_NOT_FOUND"


@pytest.mark.asyncio
async def test_transfer_creator_student_not_active(mock_db):
    place = await _seed_place(mock_db)
    locked_id = ObjectId()
    now = datetime.utcnow()
    await mock_db["students"].insert_one({"_id": locked_id, "email": "locked@test.vn", "full_name": "Khóa", "status": "locked", "created_at": now})

    with pytest.raises(HTTPException) as exc:
        await admin_place_service.transfer_creator(place["public_id"], str(locked_id), ADMIN_ID, IP)
    assert exc.value.detail["error"]["code"] == "STUDENT_NOT_ACTIVE"


@pytest.mark.asyncio
async def test_transfer_creator_invalid_id(mock_db):
    place = await _seed_place(mock_db)
    with pytest.raises(HTTPException) as exc:
        await admin_place_service.transfer_creator(place["public_id"], "invalid-id", ADMIN_ID, IP)
    assert exc.value.detail["error"]["code"] == "STUDENT_NOT_FOUND"


@pytest.mark.asyncio
async def test_get_place_detail(mock_db):
    place = await _seed_place(mock_db)
    detail = await admin_place_service.get_place_detail(place["public_id"])
    assert detail["public_id"] == place["public_id"]
    assert detail["name"] == "Quán cà phê"
    assert detail["status"] == "published"
    assert detail["creator_email"] == "sv@test.vn"
    assert "updated_at_display" in detail


@pytest.mark.asyncio
async def test_get_place_detail_not_found(mock_db):
    with pytest.raises(HTTPException) as exc:
        await admin_place_service.get_place_detail(999)
    assert exc.value.detail["error"]["code"] == "PLACE_NOT_FOUND"


@pytest.mark.asyncio
async def test_update_place_basic_fields(mock_db):
    place = await _seed_place(mock_db)
    result = await admin_place_service.update_place(
        place["public_id"], {"name": "Tên mới", "address": "Địa chỉ mới"}, ADMIN_ID, IP,
    )
    assert result["name"] == "Tên mới"
    assert result["address"] == "Địa chỉ mới"

    logs = [d for d in mock_db["audit_logs"].docs if d["event_code"] == "PLACE_ADMIN_UPDATE"]
    assert len(logs) == 1


@pytest.mark.asyncio
async def test_update_place_not_found(mock_db):
    with pytest.raises(HTTPException) as exc:
        await admin_place_service.update_place(999, {"name": "X"}, ADMIN_ID, IP)
    assert exc.value.detail["error"]["code"] == "PLACE_NOT_FOUND"


@pytest.mark.asyncio
async def test_update_place_with_geofence_validation(mock_db):
    place = await _seed_place(mock_db, status="published")
    with patch(
        "app.services.admin_place_service.geofence_service.validate_point",
        AsyncMock(return_value=True),
    ) as mock_geo:
        await admin_place_service.update_place(
            place["public_id"], {"latitude": 10.77, "longitude": 106.69}, ADMIN_ID, IP,
        )
    mock_geo.assert_called_once_with(10.77, 106.69)


@pytest.mark.asyncio
async def test_list_places_returns_paginated(mock_db):
    for i in range(3):
        await _seed_place(mock_db, public_id=i + 1, category_id=ObjectId(), creator_student_id=ObjectId())
    result = await admin_place_service.list_places({"page": 1, "page_size": 2})
    assert len(result["items"]) <= 2
    assert result["meta"]["total"] == 3


@pytest.mark.asyncio
async def test_hide_place_audit_log(mock_db):
    place = await _seed_place(mock_db)
    await admin_place_service.hide_place(place["public_id"], "Vi phạm nội quy cộng đồng", ADMIN_ID, IP)

    logs = [d for d in mock_db["audit_logs"].docs if d["event_code"] == "PLACE_HIDE"]
    assert len(logs) == 1
    assert logs[0]["actor_id"] == str(ADMIN_ID)
