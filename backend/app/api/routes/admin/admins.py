from fastapi import APIRouter, Depends, Request, status

from app.api.deps import require_system_admin
from app.schemas.admin import AdminCreateRequest, AdminUpdateRequest
from app.services import admin_account_service

router = APIRouter()


@router.get("")
async def list_admins(current_admin: dict = Depends(require_system_admin)):
    data = await admin_account_service.list_admins()
    return {"success": True, "data": data}


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_admin(
    payload: AdminCreateRequest,
    request: Request,
    current_admin: dict = Depends(require_system_admin),
):
    ip = request.client.host if request.client else "127.0.0.1"
    data = await admin_account_service.create_admin(
        payload.username,
        payload.password,
        payload.display_name,
        current_admin["_id"],
        ip,
    )
    return {"success": True, "data": data}


@router.patch("/{admin_id}")
async def update_admin(
    admin_id: str,
    payload: AdminUpdateRequest,
    request: Request,
    current_admin: dict = Depends(require_system_admin),
):
    ip = request.client.host if request.client else "127.0.0.1"
    data = await admin_account_service.update_admin(
        admin_id, payload.model_dump(exclude_unset=True), current_admin["_id"], ip
    )
    return {"success": True, "data": data}


@router.patch("/{admin_id}/disable", status_code=status.HTTP_204_NO_CONTENT)
async def disable_admin(
    admin_id: str,
    request: Request,
    current_admin: dict = Depends(require_system_admin),
):
    ip = request.client.host if request.client else "127.0.0.1"
    await admin_account_service.disable_admin(admin_id, current_admin["_id"], ip)
