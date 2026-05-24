import math

from fastapi import HTTPException, status

from app.core.database import get_db


def haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 6371000
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)
    a = (
        math.sin(delta_phi / 2) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c


async def validate_point(lat: float, lng: float) -> bool:
    db = get_db()
    config = await db["app_config"].find_one({"_id": "map"})
    if not config or "geofence" not in config:
        return True

    geofence = config["geofence"]
    g_type = geofence.get("type")

    is_inside = True

    if g_type == "rectangle":
        bounds = geofence.get("bounds", {})
        sw = bounds.get("sw", {})
        ne = bounds.get("ne", {})

        sw_lat = sw.get("lat")
        sw_lng = sw.get("lng")
        ne_lat = ne.get("lat")
        ne_lng = ne.get("lng")

        if sw_lat is not None and ne_lat is not None:
            min_lat = min(sw_lat, ne_lat)
            max_lat = max(sw_lat, ne_lat)
            if not (min_lat <= lat <= max_lat):
                is_inside = False

        if sw_lng is not None and ne_lng is not None:
            min_lng = min(sw_lng, ne_lng)
            max_lng = max(sw_lng, ne_lng)
            if not (min_lng <= lng <= max_lng):
                is_inside = False

    elif g_type == "radius":
        center = geofence.get("center", {})
        c_lat = center.get("lat")
        c_lng = center.get("lng")
        radius = geofence.get("radius_meters", 0.0)

        if c_lat is not None and c_lng is not None:
            dist = haversine(c_lat, c_lng, lat, lng)
            if dist > radius:
                is_inside = False

    if not is_inside:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "success": False,
                "error": {
                    "code": "PLACE_OUT_OF_BOUNDS",
                    "message": "Tọa độ nằm ngoài vùng địa lý cho phép. Vui lòng điều chỉnh lại trên bản đồ.",
                    "details": [],
                },
            },
        )

    return True
