from datetime import datetime
from unittest.mock import AsyncMock, patch
import pytest
from bson import ObjectId
from fastapi import HTTPException

from app.services import place_service
from app.schemas.place import PlaceCreateRequest
from tests.unit.conftest import TEST_EMAIL, TEST_NAME

pytestmark = pytest.mark.unit

@pytest.mark.asyncio
async def test_create_place_draft_success(mock_db):
    cat_id = ObjectId()
    await mock_db["categories"].insert_one({
        "_id": cat_id,
        "name": "Quán ăn",
        "is_hidden": False,
        "order": 1
    })

    payload = PlaceCreateRequest(
        name="Quán cơm sinh viên",
        category_id=str(cat_id),
        scope_type="near_campus",
        description="Quán cơm tấm bình dân ngon bổ rẻ dành cho sinh viên.",
        address="280 An Dương Vương",
        lat=10.7628,
        lng=106.6824,
        status="draft",
        image_object_keys=[],
        video=None
    )

    student_id = ObjectId()
    
    with patch("app.services.place_service.upload_service.confirm_media_keys", AsyncMock(return_value=([], None))):
        result = await place_service.create_place(student_id, payload, "127.0.0.1")

    assert result["status"] == "draft"
    assert result["public_id"] == 1
    
    db_place = await mock_db["places"].find_one({"public_id": 1})
    assert db_place is not None
    assert db_place["name"] == "Quán cơm sinh viên"
    assert db_place["status"] == "draft"

@pytest.mark.asyncio
async def test_create_place_published_out_of_bounds(mock_db):
    cat_id = ObjectId()
    await mock_db["categories"].insert_one({
        "_id": cat_id,
        "name": "Quán ăn",
        "is_hidden": False,
        "order": 1
    })

    await mock_db["app_config"].insert_one({
        "_id": "map",
        "geofence": {
            "type": "rectangle",
            "bounds": {
                "sw": {"lat": 10.75, "lng": 106.66},
                "ne": {"lat": 10.78, "lng": 106.71}
            }
        }
    })

    payload = PlaceCreateRequest(
        name="Quán ở xa",
        category_id=str(cat_id),
        scope_type="near_campus",
        description="Địa điểm nằm xa ngoài rìa thành phố gần khu ngoại ô.",
        address="Bình Dương",
        lat=11.0,  # Ngoài geofence
        lng=106.6824,
        status="published",
        image_object_keys=[],
        video=None
    )

    student_id = ObjectId()
    
    with pytest.raises(HTTPException) as exc:
        await place_service.create_place(student_id, payload, "127.0.0.1")
    
    assert exc.value.status_code == 400
    assert exc.value.detail["error"]["code"] == "PLACE_OUT_OF_BOUNDS"

@pytest.mark.asyncio
async def test_create_place_published_success(mock_db):
    cat_id = ObjectId()
    await mock_db["categories"].insert_one({
        "_id": cat_id,
        "name": "Quán ăn",
        "is_hidden": False,
        "order": 1
    })

    # Cấu hình Geofence
    await mock_db["app_config"].insert_one({
        "_id": "map",
        "geofence": {
            "type": "rectangle",
            "bounds": {
                "sw": {"lat": 10.75, "lng": 106.66},
                "ne": {"lat": 10.78, "lng": 106.71}
            }
        }
    })

    payload = PlaceCreateRequest(
        name="Quán trong trường",
        category_id=str(cat_id),
        scope_type="near_campus",
        description="Quán cơm tấm bình dân ngon bổ rẻ dành cho sinh viên.",
        address="280 An Dương Vương",
        lat=10.7628,
        lng=106.6824,
        status="published",
        image_object_keys=[],
        video=None
    )

    student_id = ObjectId()
    
    with patch("app.services.place_service.upload_service.confirm_media_keys", AsyncMock(return_value=([], None))):
        result = await place_service.create_place(student_id, payload, "127.0.0.1")

    assert result["status"] == "published"
    db_place = await mock_db["places"].find_one({"public_id": 1})
    assert db_place["status"] == "published"

@pytest.mark.asyncio
async def test_update_place_forbidden(mock_db):
    student_owner = ObjectId()
    student_other = ObjectId()
    cat_id = ObjectId()

    await mock_db["places"].insert_one({
        "public_id": 1,
        "creator_student_id": student_owner,
        "category_id": cat_id,
        "name": "Quán gốc",
        "status": "published"
    })

    payload = PlaceCreateRequest(
        name="Sửa tên",
        category_id=str(cat_id),
        scope_type="near_campus",
        description="Quán cơm tấm bình dân ngon bổ rẻ dành cho sinh viên.",
        address="280 An Dương Vương",
        lat=10.7628,
        lng=106.6824,
        status="published",
        image_object_keys=[],
        video=None
    )

    with pytest.raises(HTTPException) as exc:
        await place_service.update_place(1, student_other, payload, "127.0.0.1")

    assert exc.value.status_code == 403
    assert exc.value.detail["error"]["code"] == "PLACE_FORBIDDEN"

@pytest.mark.asyncio
async def test_delete_place_success(mock_db):
    student_owner = ObjectId()
    cat_id = ObjectId()

    await mock_db["places"].insert_one({
        "public_id": 1,
        "creator_student_id": student_owner,
        "category_id": cat_id,
        "name": "Quán sắp xóa",
        "status": "published"
    })

    await place_service.delete_place(1, student_owner, "127.0.0.1")

    db_place = await mock_db["places"].find_one({"public_id": 1})
    assert db_place["status"] == "deleted"
    assert db_place["deleted_at"] is not None

@pytest.mark.asyncio
async def test_update_place_success(mock_db):
    student_owner = ObjectId()
    cat_id = ObjectId()

    await mock_db["places"].insert_one({
        "public_id": 2,
        "creator_student_id": student_owner,
        "category_id": cat_id,
        "name": "Quán gốc",
        "status": "draft"
    })

    payload = PlaceCreateRequest(
        name="Tên quán mới sửa",
        category_id=str(cat_id),
        scope_type="near_campus",
        description="Nội dung miêu tả địa điểm mới sửa phải trên 20 ký tự.",
        address="280 An Dương Vương",
        lat=10.7628,
        lng=106.6824,
        status="published",
        image_object_keys=[],
        video=None
    )

    with patch("app.services.place_service.upload_service.confirm_media_keys", AsyncMock(return_value=([], None))):
        result = await place_service.update_place(2, student_owner, payload, "127.0.0.1")

    assert result["status"] == "published"
    db_place = await mock_db["places"].find_one({"public_id": 2})
    assert db_place["name"] == "Tên quán mới sửa"
    assert db_place["status"] == "published"

@pytest.mark.asyncio
async def test_update_place_not_found(mock_db):
    student_owner = ObjectId()
    cat_id = ObjectId()

    payload = PlaceCreateRequest(
        name="Sửa quán ảo",
        category_id=str(cat_id),
        scope_type="near_campus",
        description="Nội dung miêu tả địa điểm mới sửa phải trên 20 ký tự.",
        address="280 An Dương Vương",
        lat=10.7628,
        lng=106.6824,
        status="published",
        image_object_keys=[],
        video=None
    )

    with pytest.raises(HTTPException) as exc:
        await place_service.update_place(999, student_owner, payload, "127.0.0.1")

    assert exc.value.status_code == 404
    assert exc.value.detail["error"]["code"] == "PLACE_NOT_FOUND"

@pytest.mark.asyncio
async def test_delete_place_not_found(mock_db):
    student_owner = ObjectId()
    with pytest.raises(HTTPException) as exc:
        await place_service.delete_place(999, student_owner, "127.0.0.1")

    assert exc.value.status_code == 404
    assert exc.value.detail["error"]["code"] == "PLACE_NOT_FOUND"

