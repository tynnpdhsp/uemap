from datetime import datetime, timedelta
import random
from fastapi import HTTPException, status
from app.core.config import settings
from app.core.database import get_db
from app.core.security import hash_password, verify_password


async def create_otp(email: str, purpose: str, send_ip: str) -> str:
    db = get_db()
    now = datetime.utcnow()

    last_otp = await db["otp_tokens"].find_one(
        {"email": email, "purpose": purpose},
        sort=[("created_at", -1)]
    )

    if last_otp:
        resend_avail = last_otp.get("resend_available_at")
        if resend_avail and resend_avail > now:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail={
                    "success": False,
                    "error": {
                        "code": "AUTH_OTP_COOLDOWN",
                        "message": "Vui lòng đợi 60 giây trước khi yêu cầu gửi lại mã mới.",
                        "details": [],
                    },
                },
            )

    one_hour_ago = now - timedelta(hours=1)
    recent_otps_count = await db["otp_tokens"].count_documents({
        "email": email,
        "purpose": purpose,
        "created_at": {"$gte": one_hour_ago}
    })

    if recent_otps_count >= 3:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={
                "success": False,
                "error": {
                    "code": "AUTH_OTP_RATE_LIMIT",
                    "message": "Vượt quá giới hạn gửi OTP (tối đa 3 lần/giờ). Vui lòng thử lại sau.",
                    "details": [],
                },
            },
        )

    await db["otp_tokens"].update_many(
        {"email": email, "purpose": purpose, "used_at": None},
        {"$set": {"expires_at": now}}
    )

    otp_code = "".join([str(random.randint(0, 9)) for _ in range(6)])
    otp_hash = hash_password(otp_code)
    
    expires_at = now + timedelta(minutes=15)
    resend_available_at = now + timedelta(seconds=60)

    otp_doc = {
        "email": email,
        "purpose": purpose,
        "otp_hash": otp_hash,
        "sent_at": now,
        "expires_at": expires_at,
        "used_at": None,
        "resend_available_at": resend_available_at,
        "send_ip": send_ip,
        "created_at": now
    }

    await db["otp_tokens"].insert_one(otp_doc)
    return otp_code


async def verify_otp(email: str, otp: str, purpose: str) -> bool:
    db = get_db()
    now = datetime.utcnow()

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

    otp_locked_until = student.get("otp_locked_until")
    if otp_locked_until and otp_locked_until > now:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "success": False,
                "error": {
                    "code": "AUTH_OTP_LOCKED",
                    "message": "Chức năng nhập OTP của bạn đang bị khóa do nhập sai nhiều lần. Vui lòng thử lại sau.",
                    "details": [],
                },
            },
        )

    otp_doc = await db["otp_tokens"].find_one(
        {
            "email": email,
            "purpose": purpose,
            "used_at": None,
            "expires_at": {"$gt": now}
        },
        sort=[("created_at", -1)]
    )

    is_valid = False
    if otp_doc:
        is_valid = verify_password(otp, otp_doc["otp_hash"])

    if not is_valid:
        failed_attempts = student.get("failed_otp_attempts", 0) + 1
        update_doc = {"failed_otp_attempts": failed_attempts}
        
        if failed_attempts >= 5:
            update_doc["otp_locked_until"] = now + timedelta(minutes=30)
            update_doc["failed_otp_attempts"] = 0
            await db["students"].update_one({"_id": student["_id"]}, {"$set": update_doc})
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "success": False,
                    "error": {
                        "code": "AUTH_OTP_LOCKED",
                        "message": "Nhập sai mã OTP liên tiếp 5 lần. Chức năng OTP đã bị khóa trong 30 phút.",
                        "details": [],
                    },
                },
            )
        else:
            await db["students"].update_one({"_id": student["_id"]}, {"$set": update_doc})
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "success": False,
                    "error": {
                        "code": "AUTH_OTP_INVALID",
                        "message": f"Mã OTP không đúng hoặc đã hết hạn. Bạn còn {5 - failed_attempts} lần thử.",
                        "details": [],
                    },
                },
            )

    await db["otp_tokens"].update_one({"_id": otp_doc["_id"]}, {"$set": {"used_at": now}})
    await db["students"].update_one(
        {"_id": student["_id"]},
        {"$set": {"failed_otp_attempts": 0, "otp_locked_until": None}}
    )
    return True
