from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, Request, status, HTTPException
from app.api.deps import get_current_student
from app.core.database import get_db
from app.schemas.student import StudentProfileUpdateRequest, ChangePasswordRequest
from app.services import auth_service

router = APIRouter()


def format_student_profile(student: dict) -> dict:
    status_label_map = {
        "active": "Đã kích hoạt",
        "pending_activation": "Chưa kích hoạt",
        "locked": "Bị khóa"
    }
    
    activated_at_display = None
    activated_at = student.get("activated_at")
    if activated_at:
        vn_time = activated_at + timedelta(hours=7)
        activated_at_display = vn_time.strftime("%d/%m/%Y %H:%M")

    return {
        "email": student["email"],
        "full_name": student["full_name"],
        "status": student["status"],
        "status_label": status_label_map.get(student["status"], student["status"]),
        "activated_at_display": activated_at_display,
        "locked_reason": student.get("locked_reason")
    }


@router.get("")
async def get_profile(current_student: dict = Depends(get_current_student)):
    return {
        "success": True,
        "data": format_student_profile(current_student)
    }


@router.patch("")
async def update_profile(
    payload: StudentProfileUpdateRequest,
    current_student: dict = Depends(get_current_student)
):
    db = get_db()
    now = datetime.utcnow()
    
    await db["students"].update_one(
        {"_id": current_student["_id"]},
        {"$set": {"full_name": payload.full_name, "updated_at": now}}
    )
    
    current_student["full_name"] = payload.full_name
    return {
        "success": True,
        "data": format_student_profile(current_student)
    }


@router.post("/change-password")
async def change_password(
    payload: ChangePasswordRequest,
    request: Request,
    current_student: dict = Depends(get_current_student)
):
    ip = request.client.host if request.client else "127.0.0.1"
    
    await auth_service.change_password(
        student_id=current_student["_id"],
        current_jti=current_student["jti"],
        current_password=payload.current_password,
        new_password=payload.password,
        ip_address=ip
    )
    
    return {
        "success": True,
        "data": {
            "message": "Đổi mật khẩu thành công."
        }
    }
