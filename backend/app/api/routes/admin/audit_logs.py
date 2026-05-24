from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, Query, Request

from app.api.deps import get_current_admin
from app.services import audit_export_service

router = APIRouter()


def _default_from_date() -> datetime:
    return datetime.utcnow() - timedelta(days=7)


@router.get("")
async def list_audit_logs(
    request: Request,
    current_admin: dict = Depends(get_current_admin),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    from_date: Optional[datetime] = None,
    to_date: Optional[datetime] = None,
    event_code: Optional[str] = None,
    actor_id: Optional[str] = None,
    result: Optional[str] = None,
):
    if from_date is None:
        from_date = _default_from_date()

    params = {
        "page": page,
        "page_size": page_size,
        "from_date": from_date,
        "to_date": to_date,
        "event_code": event_code,
        "actor_id": actor_id,
        "result": result,
    }
    data = await audit_export_service.list_audit_logs(params)
    return {"success": True, "data": data["items"], "meta": data["meta"]}


@router.get("/export")
async def export_audit_logs(
    request: Request,
    current_admin: dict = Depends(get_current_admin),
    from_date: Optional[datetime] = None,
    to_date: Optional[datetime] = None,
    event_code: Optional[str] = None,
    actor_id: Optional[str] = None,
    result: Optional[str] = None,
):
    if from_date is None:
        from_date = _default_from_date()

    params = {
        "from_date": from_date,
        "to_date": to_date,
        "event_code": event_code,
        "actor_id": actor_id,
        "result": result,
    }
    return await audit_export_service.export_csv(params)
