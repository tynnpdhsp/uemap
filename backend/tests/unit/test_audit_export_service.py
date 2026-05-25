from datetime import datetime, timedelta

import pytest
from bson import ObjectId
from fastapi import HTTPException

from app.services import audit_export_service

pytestmark = pytest.mark.unit


async def _seed_logs(mock_db, count=5):
    now = datetime.utcnow()
    for i in range(count):
        await mock_db["audit_logs"].insert_one(
            {
                "event_code": f"EVENT_{i}",
                "occurred_at": now - timedelta(minutes=i),
                "actor_role": "admin",
                "actor_id": ObjectId(),
                "object_type": "test",
                "object_id": str(i),
                "result": "success",
                "description": f"Sự kiện {i}",
                "ip_address": "127.0.0.1",
            }
        )


@pytest.mark.asyncio
async def test_list_audit_logs_empty(mock_db):
    result = await audit_export_service.list_audit_logs({"page": 1, "page_size": 50})
    assert result["items"] == []
    assert result["meta"]["total"] == 0


@pytest.mark.asyncio
async def test_list_audit_logs_pagination(mock_db):
    await _seed_logs(mock_db, 10)
    result = await audit_export_service.list_audit_logs({"page": 1, "page_size": 3})
    assert len(result["items"]) <= 3
    assert result["meta"]["total"] == 10
    assert result["meta"]["page"] == 1


@pytest.mark.asyncio
async def test_list_audit_logs_with_event_code_filter(mock_db):
    await _seed_logs(mock_db, 5)
    result = await audit_export_service.list_audit_logs(
        {"page": 1, "page_size": 50, "event_code": "EVENT_0"}
    )
    assert result["meta"]["total"] == 1


@pytest.mark.asyncio
async def test_list_audit_logs_with_result_filter(mock_db):
    now = datetime.utcnow()
    await mock_db["audit_logs"].insert_one(
        {
            "event_code": "E1",
            "occurred_at": now,
            "actor_role": "admin",
            "actor_id": None,
            "object_type": "t",
            "object_id": None,
            "result": "failure",
            "description": "Lỗi",
            "ip_address": "1.2.3.4",
        }
    )
    await mock_db["audit_logs"].insert_one(
        {
            "event_code": "E2",
            "occurred_at": now,
            "actor_role": "admin",
            "actor_id": None,
            "object_type": "t",
            "object_id": None,
            "result": "success",
            "description": "OK",
            "ip_address": "1.2.3.4",
        }
    )
    result = await audit_export_service.list_audit_logs(
        {"page": 1, "page_size": 50, "result": "failure"}
    )
    assert result["meta"]["total"] == 1


@pytest.mark.asyncio
async def test_list_audit_logs_date_range_filter(mock_db):
    now = datetime.utcnow()
    old = now - timedelta(days=10)
    await mock_db["audit_logs"].insert_one(
        {
            "event_code": "OLD",
            "occurred_at": old,
            "actor_role": "admin",
            "actor_id": None,
            "object_type": "t",
            "object_id": None,
            "result": "success",
            "description": "Cũ",
            "ip_address": "1.2.3.4",
        }
    )
    await mock_db["audit_logs"].insert_one(
        {
            "event_code": "NEW",
            "occurred_at": now,
            "actor_role": "admin",
            "actor_id": None,
            "object_type": "t",
            "object_id": None,
            "result": "success",
            "description": "Mới",
            "ip_address": "1.2.3.4",
        }
    )
    result = await audit_export_service.list_audit_logs(
        {
            "page": 1,
            "page_size": 50,
            "from_date": now - timedelta(days=1),
            "to_date": now + timedelta(days=1),
        }
    )
    assert result["meta"]["total"] == 1


@pytest.mark.asyncio
async def test_list_audit_logs_item_format(mock_db):
    await _seed_logs(mock_db, 1)
    result = await audit_export_service.list_audit_logs({"page": 1, "page_size": 50})
    item = result["items"][0]
    assert "id" in item
    assert "event_code" in item
    assert "occurred_at_display" in item
    assert "actor_role" in item
    assert "ip_address" in item


@pytest.mark.asyncio
async def test_export_csv_success(mock_db):
    await _seed_logs(mock_db, 3)
    response = await audit_export_service.export_csv({})
    assert response.media_type == "text/csv; charset=utf-8"


@pytest.mark.asyncio
async def test_export_csv_limit_exceeded(mock_db):
    for i in range(10001):
        await mock_db["audit_logs"].insert_one(
            {
                "event_code": f"E{i}",
                "occurred_at": datetime.utcnow(),
                "actor_role": "admin",
                "actor_id": None,
                "object_type": "t",
                "object_id": None,
                "result": "success",
                "description": f"D{i}",
                "ip_address": "1.2.3.4",
            }
        )
    with pytest.raises(HTTPException) as exc:
        await audit_export_service.export_csv({})
    assert exc.value.detail["error"]["code"] == "AUDIT_EXPORT_LIMIT_EXCEEDED"


@pytest.mark.asyncio
async def test_export_csv_empty(mock_db):
    response = await audit_export_service.export_csv({})
    assert response.media_type == "text/csv; charset=utf-8"
