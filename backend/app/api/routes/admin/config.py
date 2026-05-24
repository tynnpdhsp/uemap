from fastapi import APIRouter, Depends, Request

from app.api.deps import get_current_admin
from app.schemas.admin_config import (
    AdminEmailTemplatesUpdateRequest,
    AdminEmailTestRequest,
    AdminMapConfigUpdateRequest,
)
from app.services import config_service

router = APIRouter()


@router.get("/map")
async def get_map_config(current_admin: dict = Depends(get_current_admin)):
    data = await config_service.get_map_config()
    return {"success": True, "data": data}


@router.patch("/map")
async def update_map_config(
    payload: AdminMapConfigUpdateRequest, request: Request, current_admin: dict = Depends(get_current_admin),
):
    ip = request.client.host if request.client else "127.0.0.1"
    data = await config_service.update_map_config(payload.model_dump(exclude_unset=True), current_admin["_id"], ip)
    return {"success": True, "data": data}


@router.get("/email-templates")
async def get_email_templates(current_admin: dict = Depends(get_current_admin)):
    data = await config_service.get_email_templates()
    return {"success": True, "data": data}


@router.patch("/email-templates")
async def update_email_templates(
    payload: AdminEmailTemplatesUpdateRequest, request: Request, current_admin: dict = Depends(get_current_admin),
):
    ip = request.client.host if request.client else "127.0.0.1"
    data = await config_service.update_email_templates(payload.model_dump(exclude_unset=True), current_admin["_id"], ip)
    return {"success": True, "data": data}


@router.post("/email-templates/test")
async def test_email(
    payload: AdminEmailTestRequest, request: Request, current_admin: dict = Depends(get_current_admin),
):
    ip = request.client.host if request.client else "127.0.0.1"
    data = await config_service.test_email(payload.to_email, payload.template_type, current_admin["_id"], ip)
    return {"success": True, "data": data}
