from datetime import datetime, timedelta
from fastapi import HTTPException, status
from bson import ObjectId
from app.core.database import get_db
from app.schemas.report import ReportCreateRequest
from app.services import audit_service

status_label_map = {
    "new": "mới",
    "in_progress": "đang xử lý",
    "resolved": "đã xử lý"
}

async def create_report(student_id: ObjectId, payload: ReportCreateRequest, ip_address: str) -> dict:
    db = get_db()
    
    target_place_id = None
    target_comment_id = None
    place_public_id = 0

    if payload.target_type == "place":
        try:
            pub_id = int(payload.target_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "success": False,
                    "error": {
                        "code": "REPORT_FORBIDDEN",
                        "message": "Mã định danh địa điểm không hợp lệ.",
                        "details": []
                    }
                }
            )
        place = await db["places"].find_one({"public_id": pub_id, "status": "published"})
        if not place:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "success": False,
                    "error": {
                        "code": "PLACE_NOT_FOUND",
                        "message": "Không tìm thấy địa điểm được báo cáo hoặc địa điểm chưa công khai.",
                        "details": []
                    }
                }
            )
        target_place_id = place["_id"]
        place_public_id = pub_id

    elif payload.target_type == "comment":
        try:
            oid = ObjectId(payload.target_id)
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "success": False,
                    "error": {
                        "code": "REPORT_FORBIDDEN",
                        "message": "Mã định danh bình luận không hợp lệ.",
                        "details": []
                    }
                }
            )
        comment = await db["comments"].find_one({"_id": oid, "status": "visible"})
        if not comment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "success": False,
                    "error": {
                        "code": "COMMENT_NOT_FOUND",
                        "message": "Không tìm thấy bình luận được báo cáo hoặc bình luận đã bị xóa.",
                        "details": []
                    }
                }
            )
        target_comment_id = comment["_id"]
        place_public_id = comment["place_public_id"]
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "success": False,
                "error": {
                    "code": "REPORT_FORBIDDEN",
                    "message": "Loại đối tượng báo cáo không hợp lệ.",
                    "details": []
                }
            }
        )

    now = datetime.utcnow()
    vn_now = now + timedelta(hours=7)
    today_str = vn_now.strftime("%Y%m%d")

    counter = await db["report_counters"].find_one_and_update(
        {"_id": today_str},
        {"$inc": {"seq": 1}},
        upsert=True,
        return_document=True
    )
    seq_num = counter["seq"]
    report_code = f"RP-{today_str}-{seq_num:04d}"

    report_doc = {
        "report_code": report_code,
        "reporter_student_id": student_id,
        "target_type": payload.target_type,
        "target_place_id": target_place_id,
        "target_comment_id": target_comment_id,
        "place_public_id": place_public_id,
        "report_type": payload.report_type,
        "reason": payload.reason,
        "status": "new",
        "admin_note": None,
        "created_at": now,
        "updated_at": now,
        "resolved_at": None
    }

    result = await db["reports"].insert_one(report_doc)

    await audit_service.log_event(
        event_code="REPORT_CREATE",
        actor_role="student",
        actor_id=student_id,
        object_type="report",
        object_id=str(result.inserted_id),
        result="success",
        description=f"Gửi báo cáo vi phạm {report_code} thành công.",
        ip_address=ip_address
    )

    return {
        "report_code": report_code,
        "status": "new",
        "status_label": status_label_map["new"],
        "created_at_display": vn_now.strftime("%d/%m/%Y %H:%M")
    }
