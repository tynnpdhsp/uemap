import csv
import io
from datetime import datetime, timedelta

from fastapi import HTTPException, status
from fastapi.responses import StreamingResponse

from app.core.database import get_db

MAX_EXPORT_ROWS = 10000

CSV_HEADERS = [
    "Mã sự kiện",
    "Thời gian",
    "Vai trò",
    "Mã người dùng",
    "Loại đối tượng",
    "Mã đối tượng",
    "Kết quả",
    "Mô tả",
    "IP",
]


def _vn_display(dt: datetime) -> str:
    vn = dt + timedelta(hours=7)
    return vn.strftime("%d/%m/%Y %H:%M")


def _build_query(params: dict) -> dict:
    query: dict = {}
    if params.get("from_date"):
        query.setdefault("occurred_at", {})["$gte"] = params["from_date"]
    if params.get("to_date"):
        query.setdefault("occurred_at", {})["$lte"] = params["to_date"]
    if params.get("event_code"):
        query["event_code"] = params["event_code"]
    if params.get("actor_id"):
        query["actor_id"] = params["actor_id"]
    if params.get("result"):
        query["result"] = params["result"]
    return query


async def list_audit_logs(params: dict) -> dict:
    db = get_db()
    query = _build_query(params)

    page = max(params.get("page", 1), 1)
    page_size = min(max(params.get("page_size", 50), 1), 100)
    skip = (page - 1) * page_size

    total = await db["audit_logs"].count_documents(query)
    cursor = db["audit_logs"].find(query).sort("occurred_at", -1).skip(skip).limit(page_size)
    logs = await cursor.to_list(page_size)

    items = []
    for log in logs:
        items.append(
            {
                "id": str(log["_id"]),
                "event_code": log["event_code"],
                "occurred_at": log["occurred_at"],
                "occurred_at_display": _vn_display(log["occurred_at"]),
                "actor_role": log["actor_role"],
                "actor_id": str(log["actor_id"]) if log.get("actor_id") else None,
                "object_type": log["object_type"],
                "object_id": log.get("object_id"),
                "result": log["result"],
                "description": log["description"],
                "ip_address": log["ip_address"],
            }
        )

    return {
        "items": items,
        "meta": {"page": page, "page_size": page_size, "total": total},
    }


async def export_csv(params: dict) -> StreamingResponse:
    db = get_db()
    query = _build_query(params)

    total = await db["audit_logs"].count_documents(query)
    if total > MAX_EXPORT_ROWS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "success": False,
                "error": {
                    "code": "AUDIT_EXPORT_LIMIT_EXCEEDED",
                    "message": f"Số dòng xuất ({total}) vượt quá giới hạn {MAX_EXPORT_ROWS}. Vui lòng thu hẹp bộ lọc.",
                    "details": [],
                },
            },
        )

    cursor = db["audit_logs"].find(query).sort("occurred_at", -1).limit(MAX_EXPORT_ROWS)

    output = io.StringIO()
    output.write("\ufeff")
    writer = csv.writer(output)
    writer.writerow(CSV_HEADERS)

    async for log in cursor:
        writer.writerow(
            [
                log["event_code"],
                _vn_display(log["occurred_at"]),
                log["actor_role"],
                str(log["actor_id"]) if log.get("actor_id") else "",
                log["object_type"],
                log.get("object_id", ""),
                log["result"],
                log["description"],
                log["ip_address"],
            ]
        )

    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": "attachment; filename=audit_logs.csv"},
    )
