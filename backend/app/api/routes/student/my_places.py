from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status

from app.api.deps import require_active_student
from app.core.database import get_db
from app.schemas.place import PlaceCreateRequest
from app.services import place_service
from app.utils.place_format import format_place_images, format_place_video

router = APIRouter()

status_label_map = {
    "draft": "bản nháp",
    "published": "đã đăng",
    "hidden": "ẩn",
    "deleted": "đã xóa",
}


@router.get("", response_model=dict)
async def get_my_places(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status_filter: Optional[str] = Query(None, alias="status"),
    current_student: dict = Depends(require_active_student),
):
    db = get_db()
    query = {"creator_student_id": current_student["_id"], "status": {"$ne": "deleted"}}

    if status_filter:
        query["status"] = status_filter

    total = await db["places"].count_documents(query)

    skip = (page - 1) * page_size
    cursor = db["places"].find(query).sort("updated_at", -1).skip(skip).limit(page_size)
    places = await cursor.to_list(length=page_size)

    formatted = []
    for p in places:
        pub_url = f"/places/{p['public_id']}" if p["status"] == "published" else None
        formatted.append(
            {
                "public_id": p["public_id"],
                "name": p["name"],
                "status": p["status"],
                "status_label": status_label_map.get(p["status"], p["status"]),
                "public_url": pub_url,
            }
        )

    return {
        "success": True,
        "data": formatted,
        "meta": {"page": page, "page_size": page_size, "total": total},
    }


@router.post("", response_model=dict, status_code=status.HTTP_201_CREATED)
async def create_student_place(
    payload: PlaceCreateRequest,
    request: Request,
    current_student: dict = Depends(require_active_student),
):
    ip = request.client.host if request.client else "127.0.0.1"
    result = await place_service.create_place(current_student["_id"], payload, ip)
    return {"success": True, "data": result}


@router.get("/{public_id}", response_model=dict)
async def get_my_place_detail(
    public_id: int, current_student: dict = Depends(require_active_student)
):
    db = get_db()
    place = await db["places"].find_one({"public_id": public_id, "status": {"$ne": "deleted"}})
    if not place:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "success": False,
                "error": {
                    "code": "PLACE_NOT_FOUND",
                    "message": "Không tìm thấy địa điểm.",
                    "details": [],
                },
            },
        )

    if place["creator_student_id"] != current_student["_id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "success": False,
                "error": {
                    "code": "PLACE_FORBIDDEN",
                    "message": "Bạn không phải là chủ sở hữu của địa điểm này.",
                    "details": [],
                },
            },
        )

    coords = place["location"]["coordinates"]

    images_list = format_place_images(place.get("images", []))
    video_data = format_place_video(place.get("video"))

    data = {
        "public_id": place["public_id"],
        "category_id": str(place["category_id"]),
        "scope_type": place["scope_type"],
        "name": place["name"],
        "description": place["description"],
        "address": place["address"],
        "lat": coords[1],
        "lng": coords[0],
        "hours": place.get("hours"),
        "contact": place.get("contact"),
        "status": place["status"],
        "image_object_keys": [img["object_key"] for img in images_list],
        "images": images_list,
        "video": video_data,
    }

    return {"success": True, "data": data}


@router.patch("/{public_id}", response_model=dict)
async def update_student_place(
    public_id: int,
    payload: PlaceCreateRequest,
    request: Request,
    current_student: dict = Depends(require_active_student),
):
    ip = request.client.host if request.client else "127.0.0.1"
    result = await place_service.update_place(public_id, current_student["_id"], payload, ip)
    return {"success": True, "data": result}


@router.delete("/{public_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_student_place(
    public_id: int, request: Request, current_student: dict = Depends(require_active_student)
):
    ip = request.client.host if request.client else "127.0.0.1"
    await place_service.delete_place(public_id, current_student["_id"], ip)
