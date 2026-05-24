import pytest
from fastapi import HTTPException

from app.services import geofence_service

pytestmark = pytest.mark.unit


@pytest.mark.asyncio
async def test_geofence_no_config(mock_db):
    result = await geofence_service.validate_point(10.0, 106.0)
    assert result is True


@pytest.mark.asyncio
async def test_geofence_rectangle_inside(mock_db):
    await mock_db["app_config"].insert_one(
        {
            "_id": "map",
            "geofence": {
                "type": "rectangle",
                "bounds": {
                    "sw": {"lat": 10.75, "lng": 106.66},
                    "ne": {"lat": 10.78, "lng": 106.71},
                },
            },
        }
    )

    result = await geofence_service.validate_point(10.76, 106.68)
    assert result is True


@pytest.mark.asyncio
async def test_geofence_rectangle_outside(mock_db):
    await mock_db["app_config"].insert_one(
        {
            "_id": "map",
            "geofence": {
                "type": "rectangle",
                "bounds": {
                    "sw": {"lat": 10.75, "lng": 106.66},
                    "ne": {"lat": 10.78, "lng": 106.71},
                },
            },
        }
    )

    with pytest.raises(HTTPException) as exc:
        await geofence_service.validate_point(11.0, 106.68)

    assert exc.value.status_code == 400
    assert exc.value.detail["error"]["code"] == "PLACE_OUT_OF_BOUNDS"


@pytest.mark.asyncio
async def test_geofence_radius_inside(mock_db):
    await mock_db["app_config"].insert_one(
        {
            "_id": "map",
            "geofence": {
                "type": "radius",
                "center": {"lat": 10.7628, "lng": 106.6824},
                "radius_meters": 1000.0,
            },
        }
    )

    result = await geofence_service.validate_point(10.7630, 106.6820)
    assert result is True


@pytest.mark.asyncio
async def test_geofence_radius_outside(mock_db):
    await mock_db["app_config"].insert_one(
        {
            "_id": "map",
            "geofence": {
                "type": "radius",
                "center": {"lat": 10.7628, "lng": 106.6824},
                "radius_meters": 1000.0,
            },
        }
    )

    with pytest.raises(HTTPException) as exc:
        await geofence_service.validate_point(10.9000, 106.8000)

    assert exc.value.status_code == 400
    assert exc.value.detail["error"]["code"] == "PLACE_OUT_OF_BOUNDS"
