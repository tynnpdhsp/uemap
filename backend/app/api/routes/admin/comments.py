from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Body, Depends, Query, Request, status

from app.api.deps import get_current_admin
from app.core.database import get_db
from app.services import audit_service

router = APIRouter()


@router.get("")
async def list_comments(
    request: Request,
    current_admin: dict = Depends(get_current_admin),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    place_public_id: Optional[int] = None,
    student_id: Optional[str] = None,
    status_filter: Optional[str] = Query(None, alias="status"),
    from_date: Optional[datetime] = None,
    to_date: Optional[datetime] = None,
):
    db = get_db()
    query: dict = {}

    if place_public_id:
        query["place_public_id"] = place_public_id
    if student_id:
        from bson import ObjectId
        query["student_id"] = ObjectId(student_id)
    if status_filter:
        query["status"] = status_filter
    if from_date:
        query.setdefault("created_at", {})["$gte"] = from_date
    if to_date:
        query.setdefault("created_at", {})["$lte"] = to_date

    skip = (page - 1) * page_size
    total = await db["comments"].count_documents(query)
    cursor = db["comments"].find(query).sort("created_at", -1).skip(skip).limit(page_size)
    comments = await cursor.to_list(page_size)

    from datetime import timedelta
    items = []
    for c in comments:
        vn_time = c["created_at"] + timedelta(hours=7)
        items.append({
            "id": str(c["_id"]),
            "place_public_id": c["place_public_id"],
            "author_display_name": c["author_display_name"],
            "content": c["content"],
            "status": c["status"],
            "admin_delete_reason": c.get("admin_delete_reason"),
            "created_at_display": vn_time.strftime("%d/%m/%Y %H:%M"),
        })

    return {"success": True, "data": items, "meta": {"page": page, "page_size": page_size, "total": total}}


@router.delete("/{comment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_comment(
    comment_id: str,
    request: Request,
    current_admin: dict = Depends(get_current_admin),
    admin_delete_reason: str = Body(..., min_length=10, max_length=500, embed=True),
):
    from bson import ObjectId
    ip = request.client.host if request.client else "127.0.0.1"
    db = get_db()

    try:
        oid = ObjectId(comment_id)
    except Exception:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail={"success": False, "error": {"code": "COMMENT_NOT_FOUND", "message": "Không tìm thấy bình luận.", "details": []}})

    comment = await db["comments"].find_one({"_id": oid, "status": "visible"})
    if not comment:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail={"success": False, "error": {"code": "COMMENT_NOT_FOUND", "message": "Không tìm thấy bình luận hoặc đã bị xóa.", "details": []}})

    now = datetime.utcnow()
    await db["comments"].update_one(
        {"_id": oid},
        {"$set": {"status": "deleted", "admin_delete_reason": admin_delete_reason, "deleted_at": now, "updated_at": now}},
    )

    await audit_service.log_event(
        event_code="COMMENT_ADMIN_SOFT_DELETE",
        actor_role="admin",
        actor_id=current_admin["_id"],
        object_type="comment",
        object_id=comment_id,
        result="success",
        description=f"Admin xóa mềm bình luận. Lý do: {admin_delete_reason}",
        ip_address=ip,
    )
