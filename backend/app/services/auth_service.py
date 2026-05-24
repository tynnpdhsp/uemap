from datetime import datetime, timedelta, timezone
from fastapi import HTTPException, status
from jose import jwt
from bson import ObjectId
from app.core.config import settings
from app.core.database import get_db
from app.core.security import hash_password, verify_password
from app.services import audit_service, email_service, otp_service, session_service


def create_reset_token(email: str) -> str:
    expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode = {"sub": email, "purpose": "password_reset", "exp": expire}
    return jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_reset_token(token: str, email: str) -> None:
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        if payload.get("sub") != email or payload.get("purpose") != "password_reset":
            raise ValueError()
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "success": False,
                "error": {
                    "code": "AUTH_RESET_TOKEN_INVALID",
                    "message": "Token đặt lại mật khẩu không hợp lệ hoặc đã hết hạn.",
                    "details": [],
                },
            },
        )


async def register_student(email: str, password: str, full_name: str, ip_address: str) -> dict:
    db = get_db()
    
    existing = await db["students"].find_one({"email": email})
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "success": False,
                "error": {
                    "code": "AUTH_EMAIL_EXISTS",
                    "message": "Email này đã được sử dụng trong hệ thống.",
                    "details": [],
                },
            },
        )

    password_hash = hash_password(password)
    now = datetime.utcnow()

    student_doc = {
        "email": email,
        "password_hash": password_hash,
        "full_name": full_name,
        "status": "pending_activation",
        "locked_reason": None,
        "activated_at": None,
        "otp_locked_until": None,
        "failed_otp_attempts": 0,
        "created_at": now,
        "updated_at": now
    }

    result = await db["students"].insert_one(student_doc)
    student_id = result.inserted_id

    otp_code = await otp_service.create_otp(email, "activation", ip_address)
    await email_service.send_otp_email(email, full_name, otp_code, "activation")

    otp_doc = await db["otp_tokens"].find_one(
        {"email": email, "purpose": "activation", "used_at": None},
        sort=[("created_at", -1)]
    )
    resend_avail = otp_doc["resend_available_at"] if otp_doc else now + timedelta(seconds=60)

    await audit_service.log_event(
        event_code="AUTH_REGISTER",
        actor_role="guest",
        actor_id=None,
        object_type="student",
        object_id=str(student_id),
        result="success",
        description="Đăng ký tài khoản sinh viên mới thành công",
        ip_address=ip_address
    )

    await audit_service.log_event(
        event_code="AUTH_OTP_SEND",
        actor_role="system",
        actor_id=None,
        object_type="otp",
        object_id=str(otp_doc["_id"]) if otp_doc else None,
        result="success",
        description="Gửi mã OTP kích hoạt tài khoản",
        ip_address=ip_address
    )

    return {
        "email": email,
        "status": "pending_activation",
        "otp_resend_available_at": resend_avail
    }


async def activate_student_account(email: str, otp: str, ip_address: str) -> dict:
    db = get_db()
    now = datetime.utcnow()

    await otp_service.verify_otp(email, otp, "activation")

    student = await db["students"].find_one({"email": email})
    
    await db["students"].update_one(
        {"_id": student["_id"]},
        {"$set": {"status": "active", "activated_at": now, "updated_at": now}}
    )

    vn_time = now + timedelta(hours=7)
    activated_at_display = vn_time.strftime("%d/%m/%Y %H:%M")

    await audit_service.log_event(
        event_code="AUTH_OTP_VERIFY",
        actor_role="guest",
        actor_id=None,
        object_type="student",
        object_id=str(student["_id"]),
        result="success",
        description="Kích hoạt tài khoản thành công qua OTP",
        ip_address=ip_address
    )

    return {
        "success": True,
        "activated_at_display": activated_at_display
    }


async def login_student(email: str, password: str, ip_address: str, user_agent: str) -> dict:
    db = get_db()
    now = datetime.utcnow()

    fifteen_minutes_ago = now - timedelta(minutes=15)
    failed_attempts_count = await db["login_attempts"].count_documents({
        "email": email,
        "ip_address": ip_address,
        "failed_at": {"$gte": fifteen_minutes_ago}
    })

    if failed_attempts_count >= 10:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={
                "success": False,
                "error": {
                    "code": "AUTH_LOGIN_RATE_LIMIT",
                    "message": "Đăng nhập sai quá nhiều lần. Vui lòng thử lại sau 15 phút.",
                    "details": [],
                },
            },
        )

    student = await db["students"].find_one({"email": email})
    
    if not student:
        await db["login_attempts"].insert_one({
            "email": email,
            "ip_address": ip_address,
            "failed_at": now
        })
        await audit_service.log_event(
            event_code="AUTH_LOGIN",
            actor_role="guest",
            actor_id=None,
            object_type="student",
            object_id=None,
            result="failure",
            description=f"Đăng nhập thất bại: Không tìm thấy email {email}",
            ip_address=ip_address
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "success": False,
                "error": {
                    "code": "AUTH_LOGIN_FAILED",
                    "message": "Email hoặc mật khẩu không đúng.",
                    "details": [],
                },
            },
        )

    student_id = student["_id"]

    if student.get("status") == "pending_activation":
        await audit_service.log_event(
            event_code="AUTH_LOGIN",
            actor_role="guest",
            actor_id=student_id,
            object_type="student",
            object_id=str(student_id),
            result="failure",
            description="Đăng nhập thất bại: Tài khoản chưa kích hoạt",
            ip_address=ip_address
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "success": False,
                "error": {
                    "code": "AUTH_LOGIN_NOT_ACTIVATED",
                    "message": "Tài khoản chưa được kích hoạt. Vui lòng nhập mã OTP trong email.",
                    "details": [],
                },
            },
        )

    if student.get("status") == "locked":
        await audit_service.log_event(
            event_code="AUTH_LOGIN",
            actor_role="guest",
            actor_id=student_id,
            object_type="student",
            object_id=str(student_id),
            result="failure",
            description=f"Đăng nhập thất bại: Tài khoản bị khóa. Lý do: {student.get('locked_reason')}",
            ip_address=ip_address
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "success": False,
                "error": {
                    "code": "AUTH_LOGIN_LOCKED",
                    "message": "Tài khoản đã bị khóa. Vui lòng liên hệ quản trị.",
                    "details": [],
                },
            },
        )

    if not verify_password(password, student["password_hash"]):
        await db["login_attempts"].insert_one({
            "email": email,
            "ip_address": ip_address,
            "failed_at": now
        })
        await audit_service.log_event(
            event_code="AUTH_LOGIN",
            actor_role="guest",
            actor_id=student_id,
            object_type="student",
            object_id=str(student_id),
            result="failure",
            description="Đăng nhập thất bại: Sai mật khẩu",
            ip_address=ip_address
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "success": False,
                "error": {
                    "code": "AUTH_LOGIN_FAILED",
                    "message": "Email hoặc mật khẩu không đúng.",
                    "details": [],
                },
            },
        )

    access_token = await session_service.create_session(student_id, ip_address, user_agent)

    await audit_service.log_event(
        event_code="AUTH_LOGIN",
        actor_role="student",
        actor_id=student_id,
        object_type="session",
        object_id=None,
        result="success",
        description="Đăng nhập thành công",
        ip_address=ip_address
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "student": {
            "email": student["email"],
            "full_name": student["full_name"],
            "status": student["status"]
        }
    }


async def logout_student(student_id: ObjectId, jti: str, ip_address: str) -> None:
    await session_service.revoke_session(jti)
    await audit_service.log_event(
        event_code="AUTH_LOGOUT",
        actor_role="student",
        actor_id=student_id,
        object_type="session",
        object_id=jti,
        result="success",
        description="Đăng xuất thành công",
        ip_address=ip_address
    )


async def request_forgot_password(email: str, ip_address: str) -> dict:
    db = get_db()
    student = await db["students"].find_one({"email": email})

    if not student or student.get("status") not in ("active", "pending_activation"):
        return {
            "success": True,
            "message": "Nếu email tồn tại trong hệ thống, mã OTP đã được gửi."
        }

    otp_code = await otp_service.create_otp(email, "password_reset", ip_address)
    await email_service.send_otp_email(email, student["full_name"], otp_code, "password_reset")

    otp_doc = await db["otp_tokens"].find_one(
        {"email": email, "purpose": "password_reset", "used_at": None},
        sort=[("created_at", -1)]
    )

    await audit_service.log_event(
        event_code="AUTH_OTP_SEND",
        actor_role="system",
        actor_id=None,
        object_type="otp",
        object_id=str(otp_doc["_id"]) if otp_doc else None,
        result="success",
        description="Gửi mã OTP đặt lại mật khẩu",
        ip_address=ip_address
    )

    return {
        "success": True,
        "message": "Nếu email tồn tại trong hệ thống, mã OTP đã được gửi."
    }


async def verify_forgot_password_otp(email: str, otp: str, ip_address: str) -> str:
    db = get_db()
    await otp_service.verify_otp(email, otp, "password_reset")

    student = await db["students"].find_one({"email": email})
    reset_token = create_reset_token(email)

    await audit_service.log_event(
        event_code="AUTH_OTP_VERIFY",
        actor_role="guest",
        actor_id=student["_id"] if student else None,
        object_type="student",
        object_id=str(student["_id"]) if student else None,
        result="success",
        description="Xác thực OTP đặt lại mật khẩu thành công",
        ip_address=ip_address
    )

    return reset_token


async def reset_password_with_token(email: str, reset_token: str, password: str, ip_address: str) -> None:
    db = get_db()
    
    decode_reset_token(reset_token, email)

    student = await db["students"].find_one({"email": email})
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

    password_hash = hash_password(password)
    now = datetime.utcnow()

    await db["students"].update_one(
        {"_id": student["_id"]},
        {"$set": {"password_hash": password_hash, "updated_at": now}}
    )

    await session_service.revoke_all_sessions(student["_id"])

    await audit_service.log_event(
        event_code="AUTH_PASSWORD_RESET",
        actor_role="student",
        actor_id=student["_id"],
        object_type="student",
        object_id=str(student["_id"]),
        result="success",
        description="Đặt lại mật khẩu thành công qua reset token",
        ip_address=ip_address
    )


async def change_password(student_id: ObjectId, current_jti: str, current_password: str, new_password: str, ip_address: str) -> None:
    db = get_db()
    student = await db["students"].find_one({"_id": student_id})
    
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

    if not verify_password(current_password, student["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "success": False,
                "error": {
                    "code": "AUTH_PASSWORD_CHANGE_FAILED",
                    "message": "Mật khẩu hiện tại không đúng.",
                    "details": [],
                },
            },
        )

    password_hash = hash_password(new_password)
    now = datetime.utcnow()

    await db["students"].update_one(
        {"_id": student_id},
        {"$set": {"password_hash": password_hash, "updated_at": now}}
    )

    await session_service.revoke_other_sessions(student_id, current_jti)

    await audit_service.log_event(
        event_code="AUTH_PASSWORD_CHANGE",
        actor_role="student",
        actor_id=student_id,
        object_type="student",
        object_id=str(student_id),
        result="success",
        description="Đổi mật khẩu thành công trong hồ sơ",
        ip_address=ip_address
    )
