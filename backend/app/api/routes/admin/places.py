from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Query, Request, status

from app.api.deps import get_current_admin
from app.schemas.admin_place import (
    AdminPlaceHideRequest,
    AdminPlaceTransferCreatorRequest,
    AdminPlaceUpdateRequest,
)
from app.services import admin_place_service

router = APIRouter()


@router.get("")
async def list_places(
    request: Request,
    current_admin: dict = Depends(get_current_admin),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    q: Optional[str] = None,
    category_id: Optional[str] = None,
    status_filter: Optional[str] = Query(None, alias="status"),
    creator_student_id: Optional[str] = None,
    from_date: Optional[datetime] = None,
    to_date: Optional[datetime] = None,
    range: Optional[str] = None,
):
    params = {
        "page": page, "page_size": page_size, "q": q, "category_id": category_id,
        "status": status_filter, "creator_student_id": creator_student_id,
        "from_date": from_date, "to_date": to_date, "range": range,
    }
    data = await admin_place_service.list_places(params)
    return {"success": True, "data": data["items"], "meta": data["meta"]}


@router.get("/{public_id}")
async def get_place(public_id: int, current_admin: dict = Depends(get_current_admin)):
    data = await admin_place_service.get_place_detail(public_id)
    return {"success": True, "data": data}


@router.patch("/{public_id}")
async def update_place(
    public_id: int, payload: AdminPlaceUpdateRequest, request: Request, current_admin: dict = Depends(get_current_admin),
):
    ip = request.client.host if request.client else "127.0.0.1"
    data = await admin_place_service.update_place(public_id, payload.model_dump(exclude_unset=True), current_admin["_id"], ip)
    return {"success": True, "data": data}


@router.patch("/{public_id}/hide")
async def hide_place(
    public_id: int, payload: AdminPlaceHideRequest, request: Request, current_admin: dict = Depends(get_current_admin),
):
    ip = request.client.host if request.client else "127.0.0.1"
    await admin_place_service.hide_place(public_id, payload.hidden_note, current_admin["_id"], ip)
    return {"success": True, "data": None}


@router.patch("/{public_id}/unhide")
async def unhide_place(
    public_id: int, request: Request, current_admin: dict = Depends(get_current_admin),
):
    ip = request.client.host if request.client else "127.0.0.1"
    await admin_place_service.unhide_place(public_id, current_admin["_id"], ip)
    return {"success": True, "data": None}


@router.delete("/{public_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_place(
    public_id: int, request: Request, current_admin: dict = Depends(get_current_admin),
):
    ip = request.client.host if request.client else "127.0.0.1"
    await admin_place_service.soft_delete_place(public_id, current_admin["_id"], ip)


@router.patch("/{public_id}/transfer-creator")
async def transfer_creator(
    public_id: int, payload: AdminPlaceTransferCreatorRequest, request: Request, current_admin: dict = Depends(get_current_admin),
):
    ip = request.client.host if request.client else "127.0.0.1"
    await admin_place_service.transfer_creator(public_id, payload.new_creator_student_id, current_admin["_id"], ip)
    return {"success": True, "data": None}
