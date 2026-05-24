from datetime import datetime, timedelta

from bson import ObjectId
from fastapi import HTTPException, status

from app.core.database import get_db
from app.services import audit_service


async def create_comment(
    place_public_id: int, student_id: ObjectId, student_name: str, content: str, ip_address: str
) -> dict:
    db = get_db()
    place = await db["places"].find_one({"public_id": place_public_id, "status": "published"})
    if not place:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "success": False,
                "error": {
                    "code": "COMMENT_FORBIDDEN",
                    "message": "Không thể bình luận trên địa điểm không tồn tại hoặc chưa công khai.",
                    "details": [],
                },
            },
        )

    now = datetime.utcnow()
    comment_doc = {
        "place_id": place["_id"],
        "place_public_id": place_public_id,
        "student_id": student_id,
        "author_display_name": student_name,
        "content": content,
        "status": "visible",
        "deleted_at": None,
        "created_at": now,
        "updated_at": now,
    }

    result = await db["comments"].insert_one(comment_doc)
    comment_id = result.inserted_id

    await audit_service.log_event(
        event_code="COMMENT_CREATE",
        actor_role="student",
        actor_id=student_id,
        object_type="comment",
        object_id=str(comment_id),
        result="success",
        description="Gửi bình luận mới thành công.",
        ip_address=ip_address,
    )

    vn_time = now + timedelta(hours=7)
    created_at_display = vn_time.strftime("%d/%m/%Y %H:%M")

    return {
        "id": str(comment_id),
        "author_display_name": student_name,
        "content": content,
        "created_at_display": created_at_display,
    }


async def update_comment(
    comment_id: str, student_id: ObjectId, content: str, ip_address: str
) -> None:
    db = get_db()
    try:
        oid = ObjectId(comment_id)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "success": False,
                "error": {
                    "code": "COMMENT_NOT_FOUND",
                    "message": "Không tìm thấy bình luận.",
                    "details": [],
                },
            },
        )

    comment = await db["comments"].find_one({"_id": oid, "status": "visible"})
    if not comment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "success": False,
                "error": {
                    "code": "COMMENT_NOT_FOUND",
                    "message": "Không tìm thấy bình luận hoặc bình luận đã bị xóa.",
                    "details": [],
                },
            },
        )

    if comment["student_id"] != student_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "success": False,
                "error": {
                    "code": "COMMENT_FORBIDDEN",
                    "message": "Bạn không có quyền chỉnh sửa bình luận này.",
                    "details": [],
                },
            },
        )

    now = datetime.utcnow()
    await db["comments"].update_one({"_id": oid}, {"$set": {"content": content, "updated_at": now}})

    await audit_service.log_event(
        event_code="COMMENT_UPDATE",
        actor_role="student",
        actor_id=student_id,
        object_type="comment",
        object_id=comment_id,
        result="success",
        description="Chỉnh sửa bình luận thành công.",
        ip_address=ip_address,
    )


async def delete_comment(comment_id: str, student_id: ObjectId, ip_address: str) -> None:
    db = get_db()
    try:
        oid = ObjectId(comment_id)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "success": False,
                "error": {
                    "code": "COMMENT_NOT_FOUND",
                    "message": "Không tìm thấy bình luận.",
                    "details": [],
                },
            },
        )

    comment = await db["comments"].find_one({"_id": oid, "status": "visible"})
    if not comment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "success": False,
                "error": {
                    "code": "COMMENT_NOT_FOUND",
                    "message": "Không tìm thấy bình luận hoặc bình luận đã bị xóa.",
                    "details": [],
                },
            },
        )

    if comment["student_id"] != student_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "success": False,
                "error": {
                    "code": "COMMENT_FORBIDDEN",
                    "message": "Bạn không có quyền xóa bình luận này.",
                    "details": [],
                },
            },
        )

    now = datetime.utcnow()
    await db["comments"].update_one(
        {"_id": oid}, {"$set": {"status": "deleted", "deleted_at": now, "updated_at": now}}
    )

    await audit_service.log_event(
        event_code="COMMENT_SOFT_DELETE",
        actor_role="student",
        actor_id=student_id,
        object_type="comment",
        object_id=comment_id,
        result="success",
        description="Xóa mềm bình luận thành công.",
        ip_address=ip_address,
    )
