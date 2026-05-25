from datetime import datetime, timedelta

from bson import ObjectId
from fastapi import HTTPException, status

from app.core.database import get_db
from app.services import audit_service

STATUS_LABELS = {
    "new": "mới",
    "in_progress": "đang xử lý",
    "resolved": "đã xử lý",
}

VALID_TRANSITIONS = {
    "new": ["in_progress"],
    "in_progress": ["resolved"],
}


def _vn_display(dt: datetime) -> str:
    vn = dt + timedelta(hours=7)
    return vn.strftime("%d/%m/%Y %H:%M")


async def list_reports(params: dict) -> dict:
    db = get_db()
    query: dict = {}

    if params.get("status"):
        query["status"] = params["status"]
    if params.get("report_type"):
        query["report_type"] = params["report_type"]
    if params.get("from_date"):
        query.setdefault("created_at", {})["$gte"] = params["from_date"]
    if params.get("to_date"):
        query.setdefault("created_at", {})["$lte"] = params["to_date"]

    page = max(params.get("page", 1), 1)
    page_size = min(max(params.get("page_size", 20), 1), 100)
    skip = (page - 1) * page_size

    total = await db["reports"].count_documents(query)
    cursor = db["reports"].find(query).sort("created_at", -1).skip(skip).limit(page_size)
    reports = await cursor.to_list(page_size)

    items = []
    for r in reports:
        reporter = await db["students"].find_one({"_id": r.get("reporter_student_id")})
        items.append(
            {
                "id": str(r["_id"]),
                "report_code": r["report_code"],
                "target_type": r["target_type"],
                "report_type": r["report_type"],
                "status": r["status"],
                "status_label": STATUS_LABELS.get(r["status"], r["status"]),
                "reporter_email": reporter["email"] if reporter else None,
                "place_public_id": r.get("place_public_id"),
                "created_at_display": _vn_display(r["created_at"]),
            }
        )

    return {
        "items": items,
        "meta": {"page": page, "page_size": page_size, "total": total},
    }


async def get_report_detail(report_id: str) -> dict:
    db = get_db()
    try:
        oid = ObjectId(report_id)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "success": False,
                "error": {
                    "code": "REPORT_NOT_FOUND",
                    "message": "Không tìm thấy báo cáo.",
                    "details": [],
                },
            },
        )

    report = await db["reports"].find_one({"_id": oid})
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "success": False,
                "error": {
                    "code": "REPORT_NOT_FOUND",
                    "message": "Không tìm thấy báo cáo.",
                    "details": [],
                },
            },
        )

    reporter = await db["students"].find_one({"_id": report.get("reporter_student_id")})

    target_preview = None
    if report["target_type"] == "place" and report.get("target_place_id"):
        place = await db["places"].find_one({"_id": report["target_place_id"]})
        if place:
            target_preview = {
                "type": "place",
                "public_id": place["public_id"],
                "name": place["name"],
                "status": place["status"],
            }
    elif report["target_type"] == "comment" and report.get("target_comment_id"):
        comment = await db["comments"].find_one({"_id": report["target_comment_id"]})
        if comment:
            target_preview = {
                "type": "comment",
                "id": str(comment["_id"]),
                "content": comment["content"],
                "status": comment["status"],
            }

    return {
        "id": str(report["_id"]),
        "report_code": report["report_code"],
        "reporter_email": reporter["email"] if reporter else None,
        "target_type": report["target_type"],
        "target_place_id": str(report["target_place_id"])
        if report.get("target_place_id")
        else None,
        "target_comment_id": str(report["target_comment_id"])
        if report.get("target_comment_id")
        else None,
        "place_public_id": report.get("place_public_id"),
        "report_type": report["report_type"],
        "reason": report["reason"],
        "status": report["status"],
        "status_label": STATUS_LABELS.get(report["status"], report["status"]),
        "admin_note": report.get("admin_note"),
        "target_preview": target_preview,
        "resolved_at": report.get("resolved_at"),
        "created_at": report["created_at"],
        "created_at_display": _vn_display(report["created_at"]),
    }


async def update_report(
    report_id: str, new_status: str, admin_note: str | None, admin_id: ObjectId, ip_address: str
) -> dict:
    db = get_db()
    try:
        oid = ObjectId(report_id)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "success": False,
                "error": {
                    "code": "REPORT_NOT_FOUND",
                    "message": "Không tìm thấy báo cáo.",
                    "details": [],
                },
            },
        )

    report = await db["reports"].find_one({"_id": oid})
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "success": False,
                "error": {
                    "code": "REPORT_NOT_FOUND",
                    "message": "Không tìm thấy báo cáo.",
                    "details": [],
                },
            },
        )

    allowed = VALID_TRANSITIONS.get(report["status"], [])
    if new_status not in allowed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "success": False,
                "error": {
                    "code": "REPORT_INVALID_STATUS",
                    "message": f"Không thể chuyển từ '{report['status']}' sang '{new_status}'.",
                    "details": [],
                },
            },
        )

    if new_status == "resolved" and not admin_note:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "success": False,
                "error": {
                    "code": "ADMIN_NOTE_REQUIRED",
                    "message": "Ghi chú xử lý bắt buộc khi đánh dấu đã xử lý.",
                    "details": [],
                },
            },
        )

    now = datetime.utcnow()
    update_fields: dict = {"status": new_status, "updated_at": now}
    if admin_note:
        update_fields["admin_note"] = admin_note
    if new_status == "resolved":
        update_fields["resolved_at"] = now

    await db["reports"].update_one({"_id": oid}, {"$set": update_fields})

    await audit_service.log_event(
        event_code="REPORT_UPDATE",
        actor_role="admin",
        actor_id=admin_id,
        object_type="report",
        object_id=report_id,
        result="success",
        description=f"Cập nhật báo cáo {report['report_code']} sang '{new_status}'.",
        ip_address=ip_address,
    )

    return await get_report_detail(report_id)


async def execute_action(
    report_id: str, action: str, reason: str, admin_id: ObjectId, ip_address: str
) -> dict:
    db = get_db()
    try:
        oid = ObjectId(report_id)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "success": False,
                "error": {
                    "code": "REPORT_NOT_FOUND",
                    "message": "Không tìm thấy báo cáo.",
                    "details": [],
                },
            },
        )

    report = await db["reports"].find_one({"_id": oid})
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "success": False,
                "error": {
                    "code": "REPORT_NOT_FOUND",
                    "message": "Không tìm thấy báo cáo.",
                    "details": [],
                },
            },
        )

    from app.services import admin_place_service

    if action == "hide_place" and report.get("place_public_id"):
        await admin_place_service.hide_place(
            report["place_public_id"], reason, admin_id, ip_address
        )
    elif action == "soft_delete_place" and report.get("place_public_id"):
        await admin_place_service.soft_delete_place(report["place_public_id"], admin_id, ip_address)
    elif action == "soft_delete_comment" and report.get("target_comment_id"):
        now = datetime.utcnow()
        await db["comments"].update_one(
            {"_id": report["target_comment_id"], "status": "visible"},
            {
                "$set": {
                    "status": "deleted",
                    "admin_delete_reason": reason,
                    "deleted_at": now,
                    "updated_at": now,
                }
            },
        )
        await audit_service.log_event(
            event_code="COMMENT_ADMIN_SOFT_DELETE",
            actor_role="admin",
            actor_id=admin_id,
            object_type="comment",
            object_id=str(report["target_comment_id"]),
            result="success",
            description=f"Admin xóa mềm bình luận từ báo cáo {report['report_code']}.",
            ip_address=ip_address,
        )
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "success": False,
                "error": {
                    "code": "REPORT_INVALID_STATUS",
                    "message": "Hành động không hợp lệ.",
                    "details": [],
                },
            },
        )

    return {"success": True, "message": f"Đã thực hiện hành động '{action}' thành công."}
