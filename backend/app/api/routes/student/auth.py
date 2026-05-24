from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, Request, status, HTTPException
from app.api.deps import get_current_student
from app.core.database import get_db
from app.schemas.auth import (
    StudentRegisterRequest,
    OTPVerifyRequest,
    OTPResendRequest,
    LoginRequest,
    ForgotPasswordRequest,
    ForgotPasswordVerifyRequest,
    ResetPasswordRequest,
)
from app.services import auth_service, otp_service, email_service

router = APIRouter()


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(payload: StudentRegisterRequest, request: Request):
    ip = request.client.host if request.client else "127.0.0.1"
    result = await auth_service.register_student(
        email=payload.email,
        password=payload.password,
        full_name=payload.full_name,
        ip_address=ip
    )
    return {
        "success": True,
        "data": result
    }


@router.post("/otp/verify")
async def verify_otp(payload: OTPVerifyRequest, request: Request):
    ip = request.client.host if request.client else "127.0.0.1"
    result = await auth_service.activate_student_account(
        email=payload.email,
        otp=payload.otp,
        ip_address=ip
    )
    return {
        "success": True,
        "data": result
    }


@router.post("/otp/resend")
async def resend_otp(payload: OTPResendRequest, request: Request):
    ip = request.client.host if request.client else "127.0.0.1"
    db = get_db()
    
    student = await db["students"].find_one({"email": payload.email})
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "success": False,
                "error": {
                    "code": "STUDENT_NOT_FOUND",
                    "message": "Không tìm thấy thông tin sinh viên.",
                    "details": [],
                },
            },
        )

    otp = await otp_service.create_otp(payload.email, payload.purpose, ip)
    await email_service.send_otp_email(payload.email, student["full_name"], otp, payload.purpose)

    otp_doc = await db["otp_tokens"].find_one(
        {"email": payload.email, "purpose": payload.purpose, "used_at": None},
        sort=[("created_at", -1)]
    )
    resend_avail = otp_doc["resend_available_at"] if otp_doc else datetime.utcnow() + timedelta(seconds=60)

    return {
        "success": True,
        "data": {
            "otp_resend_available_at": resend_avail
        }
    }


@router.post("/login")
async def login(payload: LoginRequest, request: Request):
    ip = request.client.host if request.client else "127.0.0.1"
    ua = request.headers.get("user-agent", "")
    result = await auth_service.login_student(
        email=payload.email,
        password=payload.password,
        ip_address=ip,
        user_agent=ua
    )
    return {
        "success": True,
        "data": result
    }


@router.post("/logout")
async def logout(request: Request, current_student: dict = Depends(get_current_student)):
    ip = request.client.host if request.client else "127.0.0.1"
    await auth_service.logout_student(
        student_id=current_student["_id"],
        jti=current_student["jti"],
        ip_address=ip
    )
    return {
        "success": True,
        "data": None
    }


@router.post("/forgot-password")
async def forgot_password(payload: ForgotPasswordRequest, request: Request):
    ip = request.client.host if request.client else "127.0.0.1"
    result = await auth_service.request_forgot_password(email=payload.email, ip_address=ip)
    return {
        "success": True,
        "data": result
    }


@router.post("/forgot-password/verify")
async def forgot_password_verify(payload: ForgotPasswordVerifyRequest, request: Request):
    ip = request.client.host if request.client else "127.0.0.1"
    reset_token = await auth_service.verify_forgot_password_otp(
        email=payload.email,
        otp=payload.otp,
        ip_address=ip
    )
    return {
        "success": True,
        "data": {
            "reset_token": reset_token
        }
    }


@router.post("/forgot-password/reset")
async def forgot_password_reset(payload: ResetPasswordRequest, request: Request):
    ip = request.client.host if request.client else "127.0.0.1"
    await auth_service.reset_password_with_token(
        email=payload.email,
        reset_token=payload.reset_token,
        password=payload.password,
        ip_address=ip
    )
    return {
        "success": True,
        "data": {
            "message": "Đặt lại mật khẩu thành công."
        }
    }
