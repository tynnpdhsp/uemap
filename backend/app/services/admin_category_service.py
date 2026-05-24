from datetime import datetime

from bson import ObjectId
from fastapi import HTTPException, status

from app.core.database import get_db
from app.services import audit_service


async def list_categories(admin_id: ObjectId, ip_address: str) -> list:
    db = get_db()
    categories = await db["categories"].find().sort("order", 1).to_list(None)
    result = []
    for cat in categories:
        place_count = await db["places"].count_documents({"category_id": cat["_id"]})
        result.append(_format_category(cat, place_count))
    return result


async def create_category(data: dict, admin_id: ObjectId, ip_address: str) -> dict:
    db = get_db()

    existing = await db["categories"].find_one({"name": data["name"]})
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "success": False,
                "error": {
                    "code": "CATEGORY_NAME_EXISTS",
                    "message": "Tên danh mục đã tồn tại.",
                    "details": [],
                },
            },
        )

    now = datetime.utcnow()
    doc = {
        "name": data["name"],
        "color": data["color"],
        "order": data.get("order", 0),
        "description": data.get("description"),
        "icon_url": data.get("icon_url"),
        "is_hidden": data.get("is_hidden", False),
        "created_at": now,
        "updated_at": now,
    }
    result = await db["categories"].insert_one(doc)

    await audit_service.log_event(
        event_code="CATEGORY_CREATE",
        actor_role="admin",
        actor_id=admin_id,
        object_type="category",
        object_id=str(result.inserted_id),
        result="success",
        description=f"Tạo danh mục '{data['name']}' thành công.",
        ip_address=ip_address,
    )

    doc["_id"] = result.inserted_id
    return _format_category(doc, 0)


async def update_category(
    category_id: str, data: dict, admin_id: ObjectId, ip_address: str
) -> dict:
    db = get_db()
    oid = ObjectId(category_id)
    cat = await db["categories"].find_one({"_id": oid})
    if not cat:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "success": False,
                "error": {
                    "code": "CATEGORY_NOT_FOUND",
                    "message": "Không tìm thấy danh mục.",
                    "details": [],
                },
            },
        )

    if "name" in data and data["name"] != cat["name"]:
        existing = await db["categories"].find_one({"name": data["name"], "_id": {"$ne": oid}})
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "success": False,
                    "error": {
                        "code": "CATEGORY_NAME_EXISTS",
                        "message": "Tên danh mục đã tồn tại.",
                        "details": [],
                    },
                },
            )

    update_fields = {k: v for k, v in data.items() if v is not None}
    update_fields["updated_at"] = datetime.utcnow()

    await db["categories"].update_one({"_id": oid}, {"$set": update_fields})

    await audit_service.log_event(
        event_code="CATEGORY_UPDATE",
        actor_role="admin",
        actor_id=admin_id,
        object_type="category",
        object_id=category_id,
        result="success",
        description=f"Cập nhật danh mục '{cat['name']}' thành công.",
        ip_address=ip_address,
    )

    updated = await db["categories"].find_one({"_id": oid})
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "success": False,
                "error": {
                    "code": "CATEGORY_NOT_FOUND",
                    "message": "Không tìm thấy danh mục.",
                    "details": [],
                },
            },
        )
    place_count = await db["places"].count_documents({"category_id": oid})
    return _format_category(updated, place_count)


async def hide_category(
    category_id: str, is_hidden: bool, admin_id: ObjectId, ip_address: str
) -> dict:
    db = get_db()
    oid = ObjectId(category_id)
    cat = await db["categories"].find_one({"_id": oid})
    if not cat:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "success": False,
                "error": {
                    "code": "CATEGORY_NOT_FOUND",
                    "message": "Không tìm thấy danh mục.",
                    "details": [],
                },
            },
        )

    now = datetime.utcnow()
    await db["categories"].update_one(
        {"_id": oid}, {"$set": {"is_hidden": is_hidden, "updated_at": now}}
    )

    if is_hidden:
        await audit_service.log_event(
            event_code="CATEGORY_HIDE",
            actor_role="admin",
            actor_id=admin_id,
            object_type="category",
            object_id=category_id,
            result="success",
            description=f"Ẩn danh mục '{cat['name']}'.",
            ip_address=ip_address,
        )

    updated = await db["categories"].find_one({"_id": oid})
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "success": False,
                "error": {
                    "code": "CATEGORY_NOT_FOUND",
                    "message": "Không tìm thấy danh mục.",
                    "details": [],
                },
            },
        )
    place_count = await db["places"].count_documents({"category_id": oid})
    return _format_category(updated, place_count)


async def delete_category(category_id: str, admin_id: ObjectId, ip_address: str) -> None:
    db = get_db()
    oid = ObjectId(category_id)
    cat = await db["categories"].find_one({"_id": oid})
    if not cat:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "success": False,
                "error": {
                    "code": "CATEGORY_NOT_FOUND",
                    "message": "Không tìm thấy danh mục.",
                    "details": [],
                },
            },
        )

    place_count = await db["places"].count_documents({"category_id": oid})
    if place_count > 0:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "success": False,
                "error": {
                    "code": "CATEGORY_DELETE_HAS_PLACES",
                    "message": f"Không thể xóa danh mục vì còn {place_count} địa điểm đang gắn.",
                    "details": [],
                },
            },
        )

    await db["categories"].delete_one({"_id": oid})

    await audit_service.log_event(
        event_code="CATEGORY_DELETE",
        actor_role="admin",
        actor_id=admin_id,
        object_type="category",
        object_id=category_id,
        result="success",
        description=f"Xóa danh mục '{cat['name']}' thành công.",
        ip_address=ip_address,
    )


def _format_category(cat: dict, place_count: int) -> dict:
    return {
        "id": str(cat["_id"]),
        "name": cat["name"],
        "color": cat["color"],
        "order": cat.get("order", 0),
        "description": cat.get("description"),
        "icon_url": cat.get("icon_url"),
        "is_hidden": cat.get("is_hidden", False),
        "place_count": place_count,
        "created_at": cat.get("created_at"),
        "updated_at": cat.get("updated_at"),
    }
