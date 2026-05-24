from datetime import datetime, timedelta

from bson import ObjectId
from fastapi import HTTPException, status

from app.core.database import get_db
from app.services import audit_service

STATUS_LABELS = {
    "pending_activation": "chờ kích hoạt",
    "active": "hoạt động",
    "locked": "đã khóa",
}


def _vn_display(dt: datetime) -> str:
    vn = dt + timedelta(hours=7)
    return vn.strftime("%d/%m/%Y %H:%M")


async def list_students(params: dict) -> dict:
    db = get_db()
    query: dict = {}

    if params.get("email"):
        query["email"] = {"$regex": params["email"], "$options": "i"}
    if params.get("status"):
        query["status"] = params["status"]

    page = max(params.get("page", 1), 1)
    page_size = min(max(params.get("page_size", 20), 1), 100)
    skip = (page - 1) * page_size

    total = await db["students"].count_documents(query)
    cursor = db["students"].find(query).sort("created_at", -1).skip(skip).limit(page_size)
    students = await cursor.to_list(page_size)

    items = []
    for s in students:
        items.append({
            "id": str(s["_id"]),
            "email": s["email"],
            "full_name": s["full_name"],
            "status": s["status"],
            "status_label": STATUS_LABELS.get(s["status"], s["status"]),
            "created_at_display": _vn_display(s["created_at"]),
        })

    return {
        "items": items,
        "meta": {"page": page, "page_size": page_size, "total": total},
    }


async def get_student_detail(student_id: str) -> dict:
    db = get_db()
    try:
        oid = ObjectId(student_id)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"success": False, "error": {"code": "STUDENT_NOT_FOUND", "message": "Không tìm thấy sinh viên.", "details": []}},
        )

    student = await db["students"].find_one({"_id": oid})
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"success": False, "error": {"code": "STUDENT_NOT_FOUND", "message": "Không tìm thấy sinh viên.", "details": []}},
        )

    places_count = await db["places"].count_documents({"creator_student_id": oid})
    comments_count = await db["comments"].count_documents({"student_id": oid})
    reports_count = await db["reports"].count_documents({"reporter_student_id": oid})

    return {
        "id": str(student["_id"]),
        "email": student["email"],
        "full_name": student["full_name"],
        "status": student["status"],
        "status_label": STATUS_LABELS.get(student["status"], student["status"]),
        "locked_reason": student.get("locked_reason"),
        "activated_at": student.get("activated_at"),
        "created_at": student["created_at"],
        "created_at_display": _vn_display(student["created_at"]),
        "places_count": places_count,
        "comments_count": comments_count,
        "reports_count": reports_count,
    }


async def lock_student(student_id: str, locked_reason: str, admin_id: ObjectId, ip_address: str) -> dict:
    db = get_db()
    try:
        oid = ObjectId(student_id)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"success": False, "error": {"code": "STUDENT_NOT_FOUND", "message": "Không tìm thấy sinh viên.", "details": []}},
        )

    student = await db["students"].find_one({"_id": oid})
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"success": False, "error": {"code": "STUDENT_NOT_FOUND", "message": "Không tìm thấy sinh viên.", "details": []}},
        )

    now = datetime.utcnow()
    await db["students"].update_one(
        {"_id": oid},
        {"$set": {"status": "locked", "locked_reason": locked_reason, "updated_at": now}},
    )

    await db["student_sessions"].update_many(
        {"student_id": oid, "revoked_at": None},
        {"$set": {"revoked_at": now}},
    )

    await audit_service.log_event(
        event_code="STUDENT_LOCK",
        actor_role="admin",
        actor_id=admin_id,
        object_type="student",
        object_id=student_id,
        result="success",
        description=f"Khóa tài khoản sinh viên {student['email']}. Lý do: {locked_reason}",
        ip_address=ip_address,
    )

    return await get_student_detail(student_id)


async def unlock_student(student_id: str, admin_id: ObjectId, ip_address: str) -> dict:
    db = get_db()
    try:
        oid = ObjectId(student_id)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"success": False, "error": {"code": "STUDENT_NOT_FOUND", "message": "Không tìm thấy sinh viên.", "details": []}},
        )

    student = await db["students"].find_one({"_id": oid, "status": "locked"})
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"success": False, "error": {"code": "STUDENT_NOT_FOUND", "message": "Không tìm thấy sinh viên bị khóa.", "details": []}},
        )

    now = datetime.utcnow()
    await db["students"].update_one(
        {"_id": oid},
        {"$set": {"status": "active", "locked_reason": None, "updated_at": now}},
    )

    await audit_service.log_event(
        event_code="STUDENT_UNLOCK",
        actor_role="admin",
        actor_id=admin_id,
        object_type="student",
        object_id=student_id,
        result="success",
        description=f"Mở khóa tài khoản sinh viên {student['email']}.",
        ip_address=ip_address,
    )

    return await get_student_detail(student_id)
