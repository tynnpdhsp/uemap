from dataclasses import dataclass
from typing import List, Optional
from urllib.parse import urlparse

from bson import ObjectId
from fastapi import HTTPException, status

from app.core.database import get_db
from app.schemas.place import PlaceCreateRequest, PlaceVideoSchema
from app.services import geofence_service

_EMBED_HOSTS = ("youtube.com", "youtu.be", "facebook.com")


@dataclass
class ResolvedPlacePayload:
    name: str
    category_id: ObjectId
    scope_type: str
    description: str
    address: str
    lat: float
    lng: float
    hours: Optional[str]
    contact: Optional[str]
    status: str
    image_object_keys: List[str]
    video: Optional[PlaceVideoSchema]


def _validation_error(message: str, code: str = "VALIDATION_ERROR") -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        detail={
            "success": False,
            "error": {"code": code, "message": message, "details": []},
        },
    )


async def _default_map_center() -> tuple[float, float]:
    db = get_db()
    config = await db["app_config"].find_one({"_id": "map"})
    if config and config.get("default_center"):
        center = config["default_center"]
        return float(center["lat"]), float(center["lng"])
    return 10.7628, 106.6824


async def _resolve_category_id(category_id: Optional[str], *, required: bool) -> ObjectId:
    db = get_db()
    if category_id:
        try:
            oid = ObjectId(category_id)
        except Exception:
            raise _validation_error("Danh mục không hợp lệ.", "CATEGORY_NOT_FOUND")
        cat = await db["categories"].find_one({"_id": oid})
        if not cat or cat.get("is_hidden"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "success": False,
                    "error": {
                        "code": "CATEGORY_NOT_FOUND",
                        "message": "Danh mục không tồn tại hoặc đã bị ẩn.",
                        "details": [],
                    },
                },
            )
        return oid

    if required:
        raise _validation_error("Vui lòng chọn danh mục địa điểm.", "CATEGORY_NOT_FOUND")

    cat = await db["categories"].find_one({"is_hidden": False}, sort=[("order", 1)])
    if not cat:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "success": False,
                "error": {
                    "code": "CATEGORY_NOT_FOUND",
                    "message": "Hệ thống chưa có danh mục khả dụng.",
                    "details": [],
                },
            },
        )
    return cat["_id"]


def _validate_embed_url(url: str) -> None:
    parsed = urlparse(url)
    if parsed.scheme != "https":
        raise _validation_error("URL video phải dùng HTTPS.")
    host = (parsed.netloc or "").lower().removeprefix("www.")
    if not any(host == h or host.endswith(f".{h}") for h in _EMBED_HOSTS):
        raise _validation_error("URL video chỉ hỗ trợ YouTube hoặc Facebook Watch.")
    if "facebook.com" in host and "/watch" not in parsed.path:
        raise _validation_error("URL Facebook phải là liên kết Watch (/watch).")


def _validate_video(video: Optional[PlaceVideoSchema], *, required: bool) -> None:
    if not video:
        return
    if video.kind == "embed":
        if not video.url:
            raise _validation_error("Vui lòng nhập URL video nhúng.")
        _validate_embed_url(video.url)
    elif video.kind == "file" and required and not video.object_key:
        raise _validation_error("Vui lòng tải lên tệp video.")


async def resolve_place_payload(payload: PlaceCreateRequest) -> ResolvedPlacePayload:
    status_value = "published" if payload.publish else payload.status
    if status_value not in ("draft", "published"):
        raise _validation_error("Trạng thái địa điểm không hợp lệ.")

    name = " ".join(payload.name.split())
    if len(name) < 5:
        raise _validation_error("Tên địa điểm phải từ 5 đến 200 ký tự.")

    if status_value == "published":
        if not payload.category_id:
            raise _validation_error("Vui lòng chọn danh mục.", "CATEGORY_NOT_FOUND")
        if payload.scope_type not in ("on_campus", "near_campus"):
            raise _validation_error("Loại phạm vi không hợp lệ.")
        description = (payload.description or "").strip()
        if len(description) < 20:
            raise _validation_error("Mô tả phải từ 20 đến 5000 ký tự.")
        if len(description) > 5000:
            raise _validation_error("Mô tả phải từ 20 đến 5000 ký tự.")
        address = (payload.address or "").strip()
        if len(address) < 5:
            raise _validation_error("Địa chỉ phải từ 5 đến 500 ký tự.")
        if payload.lat is None or payload.lng is None:
            raise _validation_error("Vui lòng chọn toạ độ trên bản đồ.")
        await geofence_service.validate_point(payload.lat, payload.lng)
        category_id = await _resolve_category_id(payload.category_id, required=True)
        _validate_video(payload.video, required=False)
        return ResolvedPlacePayload(
            name=name,
            category_id=category_id,
            scope_type=payload.scope_type,
            description=description,
            address=address,
            lat=payload.lat,
            lng=payload.lng,
            hours=payload.hours,
            contact=payload.contact,
            status=status_value,
            image_object_keys=payload.image_object_keys,
            video=payload.video,
        )

    default_lat, default_lng = await _default_map_center()
    lat = payload.lat if payload.lat is not None else default_lat
    lng = payload.lng if payload.lng is not None else default_lng
    category_id = await _resolve_category_id(payload.category_id, required=False)
    scope_type = (
        payload.scope_type
        if payload.scope_type
        in (
            "on_campus",
            "near_campus",
        )
        else "near_campus"
    )
    description = (payload.description or "").strip()
    if description and len(description) > 5000:
        raise _validation_error("Mô tả tối đa 5000 ký tự.")
    address = (payload.address or "").strip()
    if address and len(address) > 500:
        raise _validation_error("Địa chỉ tối đa 500 ký tự.")
    _validate_video(payload.video, required=False)

    return ResolvedPlacePayload(
        name=name,
        category_id=category_id,
        scope_type=scope_type,
        description=description,
        address=address,
        lat=lat,
        lng=lng,
        hours=payload.hours,
        contact=payload.contact,
        status="draft",
        image_object_keys=payload.image_object_keys,
        video=payload.video,
    )
