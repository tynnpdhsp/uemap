from fastapi import APIRouter, Depends, Request, status

from app.api.deps import get_current_admin
from app.schemas.admin import AdminLoginRequest
from app.services import admin_auth_service

router = APIRouter()


@router.post("/login")
async def login(payload: AdminLoginRequest, request: Request):
    ip = request.client.host if request.client else "127.0.0.1"
    ua = request.headers.get("user-agent", "")
    result = await admin_auth_service.login(
        username=payload.username, password=payload.password, ip_address=ip, user_agent=ua,
    )
    return {"success": True, "data": result}


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(request: Request, current_admin: dict = Depends(get_current_admin)):
    ip = request.client.host if request.client else "127.0.0.1"
    await admin_auth_service.logout(
        admin_id=current_admin["_id"], jti=current_admin["jti"], ip_address=ip,
    )


@router.get("/me")
async def me(current_admin: dict = Depends(get_current_admin)):
    return {"success": True, "data": admin_auth_service.format_admin_info(current_admin)}
