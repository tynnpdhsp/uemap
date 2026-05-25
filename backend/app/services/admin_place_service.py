from datetime import datetime, timedelta

from bson import ObjectId
from fastapi import HTTPException, status

from app.core.database import get_db
from app.services import audit_service, geofence_service

STATUS_LABELS = {
    "draft": "bản nháp",
    "published": "đã đăng",
    "hidden": "ẩn",
    "deleted": "đã xóa",
}


def _vn_display(dt: datetime) -> str:
    vn = dt + timedelta(hours=7)
    return vn.strftime("%d/%m/%Y %H:%M")


async def list_places(params: dict) -> dict:
    db = get_db()
    query: dict = {}

    if params.get("q"):
        query["$or"] = [
            {"name": {"$regex": params["q"], "$options": "i"}},
            {"address": {"$regex": params["q"], "$options": "i"}},
        ]
    if params.get("category_id"):
        query["category_id"] = ObjectId(params["category_id"])
    if params.get("status"):
        query["status"] = params["status"]
    if params.get("creator_student_id"):
        query["creator_student_id"] = ObjectId(params["creator_student_id"])

    date_field = "updated_at"
    if params.get("from_date"):
        query.setdefault(date_field, {})["$gte"] = params["from_date"]
    if params.get("to_date"):
        query.setdefault(date_field, {})["$lte"] = params["to_date"]

    if params.get("range") == "7d":
        seven_days_ago = datetime.utcnow() - timedelta(days=7)
        query.setdefault("published_at", {})["$gte"] = seven_days_ago

    page = max(params.get("page", 1), 1)
    page_size = min(max(params.get("page_size", 20), 1), 100)
    skip = (page - 1) * page_size

    total = await db["places"].count_documents(query)
    cursor = db["places"].find(query).sort("updated_at", -1).skip(skip).limit(page_size)
    places = await cursor.to_list(page_size)

    items = []
    for p in places:
        cat = await db["categories"].find_one({"_id": p.get("category_id")})
        creator = await db["students"].find_one({"_id": p.get("creator_student_id")})
        items.append(
            {
                "public_id": p["public_id"],
                "name": p["name"],
                "category_name": cat["name"] if cat else None,
                "status": p["status"],
                "status_label": STATUS_LABELS.get(p["status"], p["status"]),
                "creator_email": creator["email"] if creator else None,
                "updated_at_display": _vn_display(p["updated_at"]),
            }
        )

    return {
        "items": items,
        "meta": {"page": page, "page_size": page_size, "total": total},
    }


async def get_place_detail(public_id: int) -> dict:
    db = get_db()
    place = await db["places"].find_one({"public_id": public_id})
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

    cat = await db["categories"].find_one({"_id": place.get("category_id")})
    creator = await db["students"].find_one({"_id": place.get("creator_student_id")})

    return {
        "public_id": place["public_id"],
        "name": place["name"],
        "description": place.get("description"),
        "address": place.get("address"),
        "category_id": str(place["category_id"]) if place.get("category_id") else None,
        "category_name": cat["name"] if cat else None,
        "scope_type": place.get("scope_type"),
        "location": place.get("location"),
        "hours": place.get("hours"),
        "contact": place.get("contact"),
        "status": place["status"],
        "status_label": STATUS_LABELS.get(place["status"], place["status"]),
        "hidden_note": place.get("hidden_note"),
        "images": place.get("images", []),
        "video": place.get("video"),
        "creator_student_id": str(place["creator_student_id"])
        if place.get("creator_student_id")
        else None,
        "creator_email": creator["email"] if creator else None,
        "published_at": place.get("published_at"),
        "created_at": place["created_at"],
        "updated_at": place["updated_at"],
        "updated_at_display": _vn_display(place["updated_at"]),
    }


async def update_place(public_id: int, data: dict, admin_id: ObjectId, ip_address: str) -> dict:
    db = get_db()
    place = await db["places"].find_one({"public_id": public_id, "status": {"$ne": "deleted"}})
    if not place:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "success": False,
                "error": {
                    "code": "PLACE_NOT_FOUND",
                    "message": "Không tìm thấy địa điểm hoặc địa điểm đã bị xóa.",
                    "details": [],
                },
            },
        )

    update_fields: dict = {}
    if data.get("name") is not None:
        update_fields["name"] = data["name"]
    if data.get("description") is not None:
        update_fields["description"] = data["description"]
    if data.get("address") is not None:
        update_fields["address"] = data["address"]
    if data.get("hours") is not None:
        update_fields["hours"] = data["hours"]
    if data.get("contact") is not None:
        update_fields["contact"] = data["contact"]
    if data.get("category_id") is not None:
        cat = await db["categories"].find_one({"_id": ObjectId(data["category_id"])})
        if cat and cat.get("is_hidden") and place["status"] == "published":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "success": False,
                    "error": {
                        "code": "CATEGORY_HIDDEN",
                        "message": "Không thể gán danh mục đang ẩn cho địa điểm đã đăng.",
                        "details": [],
                    },
                },
            )
        update_fields["category_id"] = ObjectId(data["category_id"])

    if data.get("latitude") is not None and data.get("longitude") is not None:
        if place["status"] == "published":
            await geofence_service.validate_point(data["latitude"], data["longitude"])
        update_fields["location"] = {
            "type": "Point",
            "coordinates": [data["longitude"], data["latitude"]],
        }

    update_fields["updated_at"] = datetime.utcnow()
    await db["places"].update_one({"_id": place["_id"]}, {"$set": update_fields})

    await audit_service.log_event(
        event_code="PLACE_ADMIN_UPDATE",
        actor_role="admin",
        actor_id=admin_id,
        object_type="place",
        object_id=str(public_id),
        result="success",
        description=f"Admin cập nhật địa điểm '{place['name']}'.",
        ip_address=ip_address,
    )

    return await get_place_detail(public_id)


async def hide_place(public_id: int, hidden_note: str, admin_id: ObjectId, ip_address: str) -> None:
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

    now = datetime.utcnow()
    await db["places"].update_one(
        {"_id": place["_id"]},
        {"$set": {"status": "hidden", "hidden_note": hidden_note, "updated_at": now}},
    )

    await audit_service.log_event(
        event_code="PLACE_HIDE",
        actor_role="admin",
        actor_id=admin_id,
        object_type="place",
        object_id=str(public_id),
        result="success",
        description=f"Ẩn địa điểm '{place['name']}'.",
        ip_address=ip_address,
    )


async def unhide_place(public_id: int, admin_id: ObjectId, ip_address: str) -> None:
    db = get_db()
    place = await db["places"].find_one({"public_id": public_id, "status": "hidden"})
    if not place:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "success": False,
                "error": {
                    "code": "PLACE_NOT_FOUND",
                    "message": "Không tìm thấy địa điểm ẩn.",
                    "details": [],
                },
            },
        )

    now = datetime.utcnow()
    await db["places"].update_one(
        {"_id": place["_id"]},
        {"$set": {"status": "published", "hidden_note": None, "updated_at": now}},
    )

    await audit_service.log_event(
        event_code="PLACE_UNHIDE",
        actor_role="admin",
        actor_id=admin_id,
        object_type="place",
        object_id=str(public_id),
        result="success",
        description=f"Bỏ ẩn địa điểm '{place['name']}'.",
        ip_address=ip_address,
    )


async def soft_delete_place(public_id: int, admin_id: ObjectId, ip_address: str) -> None:
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

    now = datetime.utcnow()
    await db["places"].update_one(
        {"_id": place["_id"]},
        {"$set": {"status": "deleted", "deleted_at": now, "updated_at": now}},
    )

    await audit_service.log_event(
        event_code="PLACE_ADMIN_SOFT_DELETE",
        actor_role="admin",
        actor_id=admin_id,
        object_type="place",
        object_id=str(public_id),
        result="success",
        description=f"Admin xóa mềm địa điểm '{place['name']}'.",
        ip_address=ip_address,
    )


async def transfer_creator(
    public_id: int, new_student_id_str: str, admin_id: ObjectId, ip_address: str
) -> None:
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

    try:
        new_student_oid = ObjectId(new_student_id_str)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "success": False,
                "error": {
                    "code": "STUDENT_NOT_FOUND",
                    "message": "Mã sinh viên không hợp lệ.",
                    "details": [],
                },
            },
        )

    student = await db["students"].find_one({"_id": new_student_oid})
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "success": False,
                "error": {
                    "code": "STUDENT_NOT_FOUND",
                    "message": "Không tìm thấy sinh viên.",
                    "details": [],
                },
            },
        )

    if student.get("status") != "active":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "success": False,
                "error": {
                    "code": "STUDENT_NOT_ACTIVE",
                    "message": "Sinh viên không ở trạng thái hoạt động.",
                    "details": [],
                },
            },
        )

    now = datetime.utcnow()
    await db["places"].update_one(
        {"_id": place["_id"]},
        {"$set": {"creator_student_id": new_student_oid, "updated_at": now}},
    )

    await audit_service.log_event(
        event_code="PLACE_TRANSFER_CREATOR",
        actor_role="admin",
        actor_id=admin_id,
        object_type="place",
        object_id=str(public_id),
        result="success",
        description=f"Đổi người tạo địa điểm '{place['name']}' sang sinh viên {student['email']}.",
        ip_address=ip_address,
    )
