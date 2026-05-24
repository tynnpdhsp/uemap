from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Query, Request

from app.api.deps import get_current_admin
from app.schemas.admin_report import AdminReportActionRequest, AdminReportUpdateRequest
from app.services import admin_report_service

router = APIRouter()


@router.get("")
async def list_reports(
    request: Request,
    current_admin: dict = Depends(get_current_admin),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status_filter: Optional[str] = Query(None, alias="status"),
    report_type: Optional[str] = None,
    from_date: Optional[datetime] = None,
    to_date: Optional[datetime] = None,
):
    params = {
        "page": page, "page_size": page_size, "status": status_filter,
        "report_type": report_type, "from_date": from_date, "to_date": to_date,
    }
    data = await admin_report_service.list_reports(params)
    return {"success": True, "data": data["items"], "meta": data["meta"]}


@router.get("/{report_id}")
async def get_report(report_id: str, current_admin: dict = Depends(get_current_admin)):
    data = await admin_report_service.get_report_detail(report_id)
    return {"success": True, "data": data}


@router.patch("/{report_id}")
async def update_report(
    report_id: str, payload: AdminReportUpdateRequest, request: Request, current_admin: dict = Depends(get_current_admin),
):
    ip = request.client.host if request.client else "127.0.0.1"
    data = await admin_report_service.update_report(
        report_id, payload.status, payload.admin_note, current_admin["_id"], ip,
    )
    return {"success": True, "data": data}


@router.post("/{report_id}/actions")
async def report_action(
    report_id: str, payload: AdminReportActionRequest, request: Request, current_admin: dict = Depends(get_current_admin),
):
    ip = request.client.host if request.client else "127.0.0.1"
    data = await admin_report_service.execute_action(
        report_id, payload.action, payload.reason, current_admin["_id"], ip,
    )
    return {"success": True, "data": data}
