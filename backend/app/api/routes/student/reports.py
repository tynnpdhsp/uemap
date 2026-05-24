from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, Query, Request, HTTPException, status
from bson import ObjectId
from app.api.deps import require_active_student
from app.core.database import get_db
from app.schemas.report import ReportCreateRequest
from app.services import report_service

router = APIRouter()

report_type_label_map = {
    "wrong_info": "thông tin sai",
    "inappropriate": "nội dung không phù hợp",
    "spam": "spam",
    "other": "khác"
}

status_label_map = {
    "new": "mới",
    "in_progress": "đang xử lý",
    "resolved": "đã xử lý"
}

@router.post("/reports", response_model=dict, status_code=status.HTTP_201_CREATED)
async def post_student_report(
    payload: ReportCreateRequest,
    request: Request,
    current_student: dict = Depends(require_active_student)
):
    ip = request.client.host if request.client else "127.0.0.1"
    result = await report_service.create_report(current_student["_id"], payload, ip)
    return {"success": True, "data": result}

@router.get("/my/reports", response_model=dict)
async def get_my_reports(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_student: dict = Depends(require_active_student)
):
    db = get_db()
    query = {"reporter_student_id": current_student["_id"]}

    total = await db["reports"].count_documents(query)

    skip = (page - 1) * page_size
    cursor = db["reports"].find(query).sort("created_at", -1).skip(skip).limit(page_size)
    reports = await cursor.to_list(length=page_size)

    place_ids = list(set([r["target_place_id"] for r in reports if r["target_place_id"]]))
    comment_ids = list(set([r["target_comment_id"] for r in reports if r["target_comment_id"]]))

    places = await db["places"].find({"_id": {"$in": place_ids}}).to_list(length=100)
    place_map = {p["_id"]: p for p in places}

    comments = await db["comments"].find({"_id": {"$in": comment_ids}}).to_list(length=100)
    comment_map = {c["_id"]: c for c in comments}

    formatted = []
    for r in reports:
        target_summary = "Không xác định"
        if r["target_type"] == "place":
            p = place_map.get(r["target_place_id"])
            if p:
                target_summary = f"Địa điểm: {p['name']}"
            else:
                target_summary = "Địa điểm đã bị xóa"
        elif r["target_type"] == "comment":
            c = comment_map.get(r["target_comment_id"])
            if c:
                preview = c["content"][:40] + "..." if len(c["content"]) > 40 else c["content"]
                target_summary = f"Bình luận: \"{preview}\""
            else:
                target_summary = "Bình luận đã bị xóa"

        vn_time = r["created_at"] + timedelta(hours=7)
        created_at_display = vn_time.strftime("%d/%m/%Y %H:%M")

        formatted.append({
            "report_code": r["report_code"],
            "target_type": r["target_type"],
            "target_summary": target_summary,
            "report_type_label": report_type_label_map.get(r["report_type"], r["report_type"]),
            "status_label": status_label_map.get(r["status"], r["status"]),
            "created_at_display": created_at_display
        })

    return {
        "success": True,
        "data": formatted,
        "meta": {
            "page": page,
            "page_size": page_size,
            "total": total
        }
    }
