from fastapi import APIRouter, Depends, Request, status

from app.api.deps import get_current_admin
from app.schemas.admin_category import (
    AdminCategoryCreateRequest,
    AdminCategoryHideRequest,
    AdminCategoryUpdateRequest,
)
from app.services import admin_category_service

router = APIRouter()


@router.get("")
async def list_categories(request: Request, current_admin: dict = Depends(get_current_admin)):
    ip = request.client.host if request.client else "127.0.0.1"
    data = await admin_category_service.list_categories(current_admin["_id"], ip)
    return {"success": True, "data": data}


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_category(
    payload: AdminCategoryCreateRequest,
    request: Request,
    current_admin: dict = Depends(get_current_admin),
):
    ip = request.client.host if request.client else "127.0.0.1"
    data = await admin_category_service.create_category(
        payload.model_dump(), current_admin["_id"], ip
    )
    return {"success": True, "data": data}


@router.patch("/{category_id}")
async def update_category(
    category_id: str,
    payload: AdminCategoryUpdateRequest,
    request: Request,
    current_admin: dict = Depends(get_current_admin),
):
    ip = request.client.host if request.client else "127.0.0.1"
    update_data = payload.model_dump(exclude_unset=True)
    data = await admin_category_service.update_category(
        category_id, update_data, current_admin["_id"], ip
    )
    return {"success": True, "data": data}


@router.patch("/{category_id}/hide")
async def hide_category(
    category_id: str,
    payload: AdminCategoryHideRequest,
    request: Request,
    current_admin: dict = Depends(get_current_admin),
):
    ip = request.client.host if request.client else "127.0.0.1"
    data = await admin_category_service.hide_category(
        category_id, payload.is_hidden, current_admin["_id"], ip
    )
    return {"success": True, "data": data}


@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_category(
    category_id: str,
    request: Request,
    current_admin: dict = Depends(get_current_admin),
):
    ip = request.client.host if request.client else "127.0.0.1"
    await admin_category_service.delete_category(category_id, current_admin["_id"], ip)
