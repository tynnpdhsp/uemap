from bson import ObjectId
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.database import get_db
from app.core.security import decode_access_token
from app.services import session_service

security = HTTPBearer()


async def get_current_student(
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    try:
        payload = decode_access_token(credentials.credentials)
        if payload.get("role") != "student":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "success": False,
                    "error": {
                        "code": "AUTH_FORBIDDEN",
                        "message": "Token không hợp lệ hoặc sai vai trò.",
                        "details": [],
                    },
                },
            )

        jti = payload.get("jti")
        student_id_str = payload.get("sub")
        if not jti or not student_id_str:
            raise ValueError()

        is_active_session = await session_service.verify_session(jti)
        if not is_active_session:
            raise ValueError()

        db = get_db()
        student = await db["students"].find_one({"_id": ObjectId(student_id_str)})
        if not student:
            raise ValueError()

        student["jti"] = jti
        return student

    except HTTPException as e:
        raise e
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "success": False,
                "error": {
                    "code": "AUTH_UNAUTHORIZED",
                    "message": "Chưa đăng nhập hoặc token hết hạn.",
                    "details": [],
                },
            },
        )


# Xác thực token quản trị viên
async def get_current_admin(
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    try:
        payload = decode_access_token(credentials.credentials)
        if payload.get("role") != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "success": False,
                    "error": {
                        "code": "ADMIN_FORBIDDEN",
                        "message": "Tài khoản quản trị không đủ quyền.",
                        "details": [],
                    },
                },
            )

        jti = payload.get("jti")
        admin_id_str = payload.get("sub")
        if not jti or not admin_id_str:
            raise ValueError()

        from app.services import admin_auth_service
        is_active = await admin_auth_service.verify_admin_session(jti)
        if not is_active:
            raise ValueError()

        db = get_db()
        admin = await db["admins"].find_one({"_id": ObjectId(admin_id_str)})
        if not admin or admin.get("status") != "active":
            raise ValueError()

        admin["jti"] = jti
        return admin

    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "success": False,
                "error": {
                    "code": "AUTH_UNAUTHORIZED",
                    "message": "Chưa đăng nhập hoặc token hết hạn.",
                    "details": [],
                },
            },
        )


async def require_system_admin(
    current_admin: dict = Depends(get_current_admin),
) -> dict:
    if not current_admin.get("is_system_admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "success": False,
                "error": {
                    "code": "ADMIN_FORBIDDEN",
                    "message": "Tài khoản quản trị không đủ quyền.",
                    "details": [],
                },
            },
        )
    return current_admin


async def require_active_student(
    current_student: dict = Depends(get_current_student),
) -> dict:
    if current_student.get("status") != "active":
        if current_student.get("status") == "pending_activation":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "success": False,
                    "error": {
                        "code": "AUTH_FORBIDDEN",
                        "message": "Tài khoản chưa được kích hoạt.",
                        "details": [],
                    },
                },
            )
        elif current_student.get("status") == "locked":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "success": False,
                    "error": {
                        "code": "AUTH_LOGIN_LOCKED",
                        "message": "Tài khoản đã bị khóa. Vui lòng liên hệ quản trị.",
                        "details": [],
                    },
                },
            )
    return current_student
