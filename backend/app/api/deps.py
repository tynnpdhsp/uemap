from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.security import decode_access_token

security = HTTPBearer()

# Xác thực token sinh viên
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
        return payload
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "success": False,
                "error": {
                    "code": "AUTH_FORBIDDEN",
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
        return payload
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "success": False,
                "error": {
                    "code": "AUTH_FORBIDDEN",
                    "message": "Chưa đăng nhập hoặc token hết hạn.",
                    "details": [],
                },
            },
        )
