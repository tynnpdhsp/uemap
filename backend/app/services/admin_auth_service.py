import uuid
from datetime import datetime, timedelta

from bson import ObjectId
from fastapi import HTTPException, status

from app.core.config import settings
from app.core.database import get_db
from app.core.security import create_access_token, verify_password
from app.services import audit_service

ADMIN_STATUS_LABELS = {
    "active": "hoạt động",
    "disabled": "vô hiệu hóa",
}


async def check_rate_limit(username: str, ip_address: str) -> None:
    db = get_db()
    fifteen_minutes_ago = datetime.utcnow() - timedelta(minutes=15)
    count = await db["admin_login_attempts"].count_documents(
        {
            "$or": [{"username": username}, {"ip_address": ip_address}],
            "failed_at": {"$gte": fifteen_minutes_ago},
        }
    )
    if count >= 10:
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


async def record_failed_attempt(username: str, ip_address: str) -> None:
    db = get_db()
    await db["admin_login_attempts"].insert_one(
        {
            "username": username,
            "ip_address": ip_address,
            "failed_at": datetime.utcnow(),
        }
    )


async def login(username: str, password: str, ip_address: str, user_agent: str) -> dict:
    db = get_db()
    await check_rate_limit(username, ip_address)

    admin = await db["admins"].find_one({"username": username})

    if not admin or not verify_password(password, admin["password_hash"]):
        if admin:
            await record_failed_attempt(username, ip_address)
        else:
            await record_failed_attempt(username, ip_address)
        await audit_service.log_event(
            event_code="ADMIN_LOGIN",
            actor_role="admin",
            actor_id=admin["_id"] if admin else None,
            object_type="admin",
            object_id=str(admin["_id"]) if admin else None,
            result="failure",
            description="Tên đăng nhập hoặc mật khẩu không đúng.",
            ip_address=ip_address,
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "success": False,
                "error": {
                    "code": "ADMIN_LOGIN_FAILED",
                    "message": "Tên đăng nhập hoặc mật khẩu không đúng.",
                    "details": [],
                },
            },
        )

    if admin["status"] == "disabled":
        await audit_service.log_event(
            event_code="ADMIN_LOGIN",
            actor_role="admin",
            actor_id=admin["_id"],
            object_type="admin",
            object_id=str(admin["_id"]),
            result="failure",
            description="Tài khoản quản trị đã bị vô hiệu hóa.",
            ip_address=ip_address,
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "success": False,
                "error": {
                    "code": "ADMIN_ACCOUNT_DISABLED",
                    "message": "Tài khoản quản trị đã bị vô hiệu hóa.",
                    "details": [],
                },
            },
        )

    now = datetime.utcnow()
    jti = str(uuid.uuid4())
    expires_at = now + timedelta(minutes=settings.JWT_ADMIN_ACCESS_TOKEN_EXPIRE_MINUTES)

    await db["admin_sessions"].insert_one(
        {
            "admin_id": admin["_id"],
            "jti": jti,
            "expires_at": expires_at,
            "revoked_at": None,
            "ip_address": ip_address,
            "user_agent": user_agent,
            "created_at": now,
        }
    )

    token = create_access_token(
        {"sub": str(admin["_id"]), "jti": jti, "is_system_admin": admin["is_system_admin"]},
        role="admin",
    )

    await db["admins"].update_one(
        {"_id": admin["_id"]},
        {"$set": {"last_login_at": now}},
    )

    await audit_service.log_event(
        event_code="ADMIN_LOGIN",
        actor_role="admin",
        actor_id=admin["_id"],
        object_type="session",
        object_id=jti,
        result="success",
        description="Đăng nhập quản trị thành công.",
        ip_address=ip_address,
    )

    return {
        "access_token": token,
        "admin": {
            "id": str(admin["_id"]),
            "username": admin["username"],
            "display_name": admin["display_name"],
            "is_system_admin": admin["is_system_admin"],
            "status_label": ADMIN_STATUS_LABELS.get(admin["status"], admin["status"]),
        },
    }


async def logout(admin_id: ObjectId, jti: str, ip_address: str) -> None:
    db = get_db()
    now = datetime.utcnow()
    await db["admin_sessions"].update_one(
        {"jti": jti, "revoked_at": None},
        {"$set": {"revoked_at": now}},
    )
    await audit_service.log_event(
        event_code="ADMIN_LOGOUT",
        actor_role="admin",
        actor_id=admin_id,
        object_type="session",
        object_id=jti,
        result="success",
        description="Đăng xuất quản trị thành công.",
        ip_address=ip_address,
    )


async def verify_admin_session(jti: str) -> bool:
    db = get_db()
    now = datetime.utcnow()
    session = await db["admin_sessions"].find_one({"jti": jti})
    if not session:
        return False
    if session.get("revoked_at") is not None:
        return False
    if session.get("expires_at") < now:
        return False
    return True


def format_admin_info(admin: dict) -> dict:
    return {
        "id": str(admin["_id"]),
        "username": admin["username"],
        "display_name": admin["display_name"],
        "is_system_admin": admin["is_system_admin"],
        "status": admin["status"],
        "status_label": ADMIN_STATUS_LABELS.get(admin["status"], admin["status"]),
        "last_login_at": admin.get("last_login_at"),
        "created_at": admin["created_at"],
    }
