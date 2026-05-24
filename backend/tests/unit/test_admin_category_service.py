from datetime import datetime

import pytest
from bson import ObjectId
from fastapi import HTTPException

from app.services import admin_category_service

pytestmark = pytest.mark.unit

ADMIN_ID = ObjectId()
IP = "127.0.0.1"


async def _seed_category(mock_db, **overrides):
    now = datetime.utcnow()
    doc = {
        "_id": overrides.pop("_id", ObjectId()),
        "name": "Ăn uống",
        "color": "#FF0000",
        "order": 0,
        "description": None,
        "icon_url": None,
        "is_hidden": False,
        "created_at": now,
        "updated_at": now,
    }
    doc.update(overrides)
    await mock_db["categories"].insert_one(doc)
    return doc


@pytest.mark.asyncio
async def test_list_categories_empty(mock_db):
    result = await admin_category_service.list_categories(ADMIN_ID, IP)
    assert result == []


@pytest.mark.asyncio
async def test_list_categories_with_place_count(mock_db):
    cat = await _seed_category(mock_db)
    await mock_db["places"].insert_one({"category_id": cat["_id"]})
    await mock_db["places"].insert_one({"category_id": cat["_id"]})

    result = await admin_category_service.list_categories(ADMIN_ID, IP)
    assert len(result) == 1
    assert result[0]["place_count"] == 2
    assert result[0]["name"] == "Ăn uống"


@pytest.mark.asyncio
async def test_create_category_success(mock_db):
    data = {"name": "Thể thao", "color": "#00FF00", "order": 1}
    result = await admin_category_service.create_category(data, ADMIN_ID, IP)

    assert result["name"] == "Thể thao"
    assert result["color"] == "#00FF00"
    assert result["id"] is not None

    logs = [d for d in mock_db["audit_logs"].docs if d["event_code"] == "CATEGORY_CREATE"]
    assert len(logs) == 1


@pytest.mark.asyncio
async def test_create_category_duplicate_name(mock_db):
    await _seed_category(mock_db, name="Thể thao")
    with pytest.raises(HTTPException) as exc:
        await admin_category_service.create_category({"name": "Thể thao", "color": "#00FF00"}, ADMIN_ID, IP)
    assert exc.value.detail["error"]["code"] == "CATEGORY_NAME_EXISTS"


@pytest.mark.asyncio
async def test_update_category_success(mock_db):
    cat = await _seed_category(mock_db, name="Cũ")
    result = await admin_category_service.update_category(str(cat["_id"]), {"name": "Mới"}, ADMIN_ID, IP)
    assert result["name"] == "Mới"


@pytest.mark.asyncio
async def test_update_category_not_found(mock_db):
    with pytest.raises(HTTPException) as exc:
        await admin_category_service.update_category(str(ObjectId()), {"name": "X"}, ADMIN_ID, IP)
    assert exc.value.detail["error"]["code"] == "CATEGORY_NOT_FOUND"


@pytest.mark.asyncio
async def test_update_category_duplicate_name(mock_db):
    cat1 = await _seed_category(mock_db, name="A")
    await _seed_category(mock_db, name="B")
    with pytest.raises(HTTPException) as exc:
        await admin_category_service.update_category(str(cat1["_id"]), {"name": "B"}, ADMIN_ID, IP)
    assert exc.value.detail["error"]["code"] == "CATEGORY_NAME_EXISTS"


@pytest.mark.asyncio
async def test_hide_category(mock_db):
    cat = await _seed_category(mock_db, is_hidden=False)
    result = await admin_category_service.hide_category(str(cat["_id"]), True, ADMIN_ID, IP)
    assert result["is_hidden"] is True

    logs = [d for d in mock_db["audit_logs"].docs if d["event_code"] == "CATEGORY_HIDE"]
    assert len(logs) == 1


@pytest.mark.asyncio
async def test_hide_category_not_found(mock_db):
    with pytest.raises(HTTPException) as exc:
        await admin_category_service.hide_category(str(ObjectId()), True, ADMIN_ID, IP)
    assert exc.value.detail["error"]["code"] == "CATEGORY_NOT_FOUND"


@pytest.mark.asyncio
async def test_delete_category_success(mock_db):
    cat = await _seed_category(mock_db)
    await admin_category_service.delete_category(str(cat["_id"]), ADMIN_ID, IP)
    assert await mock_db["categories"].find_one({"_id": cat["_id"]}) is None

    logs = [d for d in mock_db["audit_logs"].docs if d["event_code"] == "CATEGORY_DELETE"]
    assert len(logs) == 1


@pytest.mark.asyncio
async def test_delete_category_not_found(mock_db):
    with pytest.raises(HTTPException) as exc:
        await admin_category_service.delete_category(str(ObjectId()), ADMIN_ID, IP)
    assert exc.value.detail["error"]["code"] == "CATEGORY_NOT_FOUND"


@pytest.mark.asyncio
async def test_delete_category_has_places_conflict(mock_db):
    cat = await _seed_category(mock_db)
    await mock_db["places"].insert_one({"category_id": cat["_id"]})

    with pytest.raises(HTTPException) as exc:
        await admin_category_service.delete_category(str(cat["_id"]), ADMIN_ID, IP)
    assert exc.value.status_code == 409
    assert exc.value.detail["error"]["code"] == "CATEGORY_DELETE_HAS_PLACES"

    assert await mock_db["categories"].find_one({"_id": cat["_id"]}) is not None
