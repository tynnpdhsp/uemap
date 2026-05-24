from typing import Optional

from fastapi import APIRouter, Body, Depends, Query, Request

from app.api.deps import get_current_admin
from app.services import admin_student_service

router = APIRouter()


@router.get("")
async def list_students(
    request: Request,
    current_admin: dict = Depends(get_current_admin),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    email: Optional[str] = None,
    status_filter: Optional[str] = Query(None, alias="status"),
):
    params = {"page": page, "page_size": page_size, "email": email, "status": status_filter}
    data = await admin_student_service.list_students(params)
    return {"success": True, "data": data["items"], "meta": data["meta"]}


@router.get("/{student_id}")
async def get_student(student_id: str, current_admin: dict = Depends(get_current_admin)):
    data = await admin_student_service.get_student_detail(student_id)
    return {"success": True, "data": data}


@router.patch("/{student_id}/lock")
async def lock_student(
    student_id: str,
    request: Request,
    current_admin: dict = Depends(get_current_admin),
    locked_reason: str = Body(..., min_length=10, max_length=500, embed=True),
):
    ip = request.client.host if request.client else "127.0.0.1"
    data = await admin_student_service.lock_student(student_id, locked_reason, current_admin["_id"], ip)
    return {"success": True, "data": data}


@router.patch("/{student_id}/unlock")
async def unlock_student(
    student_id: str, request: Request, current_admin: dict = Depends(get_current_admin),
):
    ip = request.client.host if request.client else "127.0.0.1"
    data = await admin_student_service.unlock_student(student_id, current_admin["_id"], ip)
    return {"success": True, "data": data}
