import pytest
from bson import ObjectId

from app.schemas.place import PlaceCreateRequest
from app.services import place_payload

pytestmark = pytest.mark.unit


@pytest.mark.asyncio
async def test_resolve_draft_name_only(mock_db):
    await mock_db["categories"].insert_one(
        {
            "_id": ObjectId(),
            "name": "quán ăn và uống",
            "color": "#F97316",
            "order": 1,
            "is_hidden": False,
        }
    )
    await mock_db["app_config"].insert_one(
        {
            "_id": "map",
            "default_center": {"lat": 10.7628, "lng": 106.6824},
            "default_zoom": 16,
        }
    )

    payload = PlaceCreateRequest(name="Quán nháp mới")
    resolved = await place_payload.resolve_place_payload(payload)

    assert resolved.status == "draft"
    assert resolved.name == "Quán nháp mới"
    assert resolved.description == ""
    assert resolved.address == ""


@pytest.mark.asyncio
async def test_resolve_publish_flag(mock_db):
    cat_id = ObjectId()
    await mock_db["categories"].insert_one(
        {
            "_id": cat_id,
            "name": "hành chính",
            "color": "#1E40AF",
            "order": 1,
            "is_hidden": False,
        }
    )
    await mock_db["app_config"].insert_one(
        {
            "_id": "map",
            "default_center": {"lat": 10.7628, "lng": 106.6824},
            "geofence": {
                "type": "rectangle",
                "bounds": {
                    "sw": {"lat": 10.75, "lng": 106.66},
                    "ne": {"lat": 10.78, "lng": 106.71},
                },
            },
        }
    )

    payload = PlaceCreateRequest(
        name="Phòng học A",
        category_id=str(cat_id),
        scope_type="on_campus",
        description="Mô tả đủ dài cho địa điểm trong khuôn viên trường.",
        address="280 An Dương Vương",
        lat=10.7628,
        lng=106.6824,
        publish=True,
    )
    resolved = await place_payload.resolve_place_payload(payload)
    assert resolved.status == "published"
