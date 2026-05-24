from fastapi import APIRouter

from app.core.database import get_db

router = APIRouter()


@router.get("/map", response_model=dict)
async def get_map_config():
    db = get_db()
    config = await db["app_config"].find_one({"_id": "map"})
    if not config:
        config = {
            "default_center": {"lat": 10.7628, "lng": 106.6824},
            "default_zoom": 16,
            "geofence": {
                "type": "rectangle",
                "bounds": {
                    "sw": {"lat": 10.75, "lng": 106.66},
                    "ne": {"lat": 10.78, "lng": 106.71},
                },
            },
            "cluster_zoom_threshold": 14,
        }
    return {"success": True, "data": config}
