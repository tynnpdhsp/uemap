from datetime import datetime
from fastapi import HTTPException, status
from bson import ObjectId
from app.core.database import get_db
from app.schemas.place import PlaceCreateRequest
from app.services import geofence_service, upload_service, audit_service

status_label_map = {
    "draft": "bản nháp",
    "published": "đã đăng",
    "hidden": "ẩn",
    "deleted": "đã xóa"
}

async def create_place(student_id: ObjectId, payload: PlaceCreateRequest, ip_address: str) -> dict:
    db = get_db()

    if payload.status == "published":
        await geofence_service.validate_point(payload.lat, payload.lng)

    counter = await db["place_counters"].find_one_and_update(
        {"_id": "places"},
        {"$inc": {"seq": 1}},
        upsert=True,
        return_document=True
    )
    public_id = counter["seq"]

    confirmed_images, confirmed_video = await upload_service.confirm_media_keys(
        image_keys=payload.image_object_keys,
        video_key=payload.video.object_key if payload.video else None,
        public_id=public_id
    )

    now = datetime.utcnow()
    
    images_list = [{"object_key": key, "sort_order": i, "mime": "image/webp"} for i, key in enumerate(confirmed_images)]
    
    video_doc = None
    if payload.video:
        if payload.video.kind == "file" and confirmed_video:
            video_doc = {
                "kind": "file",
                "object_key": confirmed_video,
                "mime": payload.video.mime or "video/mp4"
            }
        elif payload.video.kind == "embed":
            video_doc = {
                "kind": "embed",
                "url": payload.video.url
            }

    place_doc = {
        "public_id": public_id,
        "creator_student_id": student_id,
        "category_id": ObjectId(payload.category_id),
        "scope_type": payload.scope_type,
        "name": payload.name,
        "description": payload.description,
        "address": payload.address,
        "location": {
            "type": "Point",
            "coordinates": [payload.lng, payload.lat]
        },
        "hours": payload.hours,
        "contact": payload.contact,
        "status": payload.status,
        "hidden_note": None,
        "images": images_list,
        "video": video_doc,
        "published_at": now if payload.status == "published" else None,
        "deleted_at": None,
        "created_at": now,
        "updated_at": now
    }

    await db["places"].insert_one(place_doc)

    await audit_service.log_event(
        event_code="PLACE_CREATE",
        actor_role="student",
        actor_id=student_id,
        object_type="place",
        object_id=str(public_id),
        result="success",
        description=f"Tạo địa điểm '{payload.name}' thành công ở trạng thái {payload.status}.",
        ip_address=ip_address
    )

    if payload.status == "published":
        await audit_service.log_event(
            event_code="PLACE_PUBLISH",
            actor_role="student",
            actor_id=student_id,
            object_type="place",
            object_id=str(public_id),
            result="success",
            description=f"Công khai địa điểm '{payload.name}'.",
            ip_address=ip_address
        )

    return {
        "public_id": public_id,
        "status": payload.status,
        "status_label": status_label_map.get(payload.status, payload.status)
    }

async def update_place(public_id: int, student_id: ObjectId, payload: PlaceCreateRequest, ip_address: str) -> dict:
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
                    "details": []
                }
            }
        )

    if place["creator_student_id"] != student_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "success": False,
                "error": {
                    "code": "PLACE_FORBIDDEN",
                    "message": "Bạn không phải là chủ sở hữu của địa điểm này.",
                    "details": []
                }
            }
        )

    if payload.status == "published":
        await geofence_service.validate_point(payload.lat, payload.lng)

    confirmed_images, confirmed_video = await upload_service.confirm_media_keys(
        image_keys=payload.image_object_keys,
        video_key=payload.video.object_key if payload.video else None,
        public_id=public_id
    )

    now = datetime.utcnow()
    
    images_list = [{"object_key": key, "sort_order": i, "mime": "image/webp"} for i, key in enumerate(confirmed_images)]
    
    video_doc = None
    if payload.video:
        if payload.video.kind == "file" and confirmed_video:
            video_doc = {
                "kind": "file",
                "object_key": confirmed_video,
                "mime": payload.video.mime or "video/mp4"
            }
        elif payload.video.kind == "embed":
            video_doc = {
                "kind": "embed",
                "url": payload.video.url
            }

    update_fields = {
        "category_id": ObjectId(payload.category_id),
        "scope_type": payload.scope_type,
        "name": payload.name,
        "description": payload.description,
        "address": payload.address,
        "location": {
            "type": "Point",
            "coordinates": [payload.lng, payload.lat]
        },
        "hours": payload.hours,
        "contact": payload.contact,
        "status": payload.status,
        "images": images_list,
        "video": video_doc,
        "updated_at": now
    }

    is_publishing = False
    if payload.status == "published" and place["status"] == "draft":
        update_fields["published_at"] = now
        is_publishing = True

    await db["places"].update_one({"_id": place["_id"]}, {"$set": update_fields})

    await audit_service.log_event(
        event_code="PLACE_UPDATE",
        actor_role="student",
        actor_id=student_id,
        object_type="place",
        object_id=str(public_id),
        result="success",
        description=f"Cập nhật địa điểm '{payload.name}' thành công.",
        ip_address=ip_address
    )

    if is_publishing:
        await audit_service.log_event(
            event_code="PLACE_PUBLISH",
            actor_role="student",
            actor_id=student_id,
            object_type="place",
            object_id=str(public_id),
            result="success",
            description=f"Công khai địa điểm '{payload.name}'.",
            ip_address=ip_address
        )

    return {
        "public_id": public_id,
        "status": payload.status,
        "status_label": status_label_map.get(payload.status, payload.status)
    }

async def delete_place(public_id: int, student_id: ObjectId, ip_address: str) -> None:
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
                    "details": []
                }
            }
        )

    if place["creator_student_id"] != student_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "success": False,
                "error": {
                    "code": "PLACE_FORBIDDEN",
                    "message": "Bạn không phải là chủ sở hữu của địa điểm này.",
                    "details": []
                }
            }
        )

    now = datetime.utcnow()
    await db["places"].update_one(
        {"_id": place["_id"]},
        {"$set": {"status": "deleted", "deleted_at": now, "updated_at": now}}
    )

    await audit_service.log_event(
        event_code="PLACE_SOFT_DELETE",
        actor_role="student",
        actor_id=student_id,
        object_type="place",
        object_id=str(public_id),
        result="success",
        description=f"Xóa mềm địa điểm '{place['name']}'.",
        ip_address=ip_address
    )
