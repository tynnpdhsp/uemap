from datetime import datetime
from unittest.mock import AsyncMock, patch

import pytest
from bson import ObjectId
from fastapi import HTTPException

from app.services import admin_report_service

pytestmark = pytest.mark.unit

ADMIN_ID = ObjectId()
IP = "127.0.0.1"


async def _seed_report(mock_db, **overrides):
    now = datetime.utcnow()
    student_id = ObjectId()
    place_id = ObjectId()
    doc = {
        "_id": overrides.pop("_id", ObjectId()),
        "report_code": overrides.pop("report_code", "RP-20250525-0001"),
        "reporter_student_id": overrides.pop("reporter_student_id", student_id),
        "target_type": "place",
        "target_place_id": place_id,
        "target_comment_id": None,
        "place_public_id": 1,
        "report_type": "inappropriate",
        "reason": "Nội dung không phù hợp",
        "status": "new",
        "admin_note": None,
        "resolved_at": None,
        "created_at": now,
        "updated_at": now,
    }
    doc.update(overrides)
    await mock_db["reports"].insert_one(doc)

    await mock_db["students"].insert_one(
        {"_id": doc["reporter_student_id"], "email": "sv@test.vn", "created_at": now}
    )
    await mock_db["places"].insert_one(
        {"_id": place_id, "public_id": 1, "name": "Quán", "status": "published"}
    )

    return doc


@pytest.mark.asyncio
async def test_update_report_new_to_in_progress(mock_db):
    report = await _seed_report(mock_db)
    result = await admin_report_service.update_report(
        str(report["_id"]), "in_progress", None, ADMIN_ID, IP
    )
    assert result["status"] == "in_progress"


@pytest.mark.asyncio
async def test_update_report_in_progress_to_resolved(mock_db):
    report = await _seed_report(mock_db, status="in_progress")
    result = await admin_report_service.update_report(
        str(report["_id"]),
        "resolved",
        "Đã xử lý vi phạm xong rồi nhé",
        ADMIN_ID,
        IP,
    )
    assert result["status"] == "resolved"
    assert result["admin_note"] == "Đã xử lý vi phạm xong rồi nhé"
    assert result["resolved_at"] is not None


@pytest.mark.asyncio
async def test_update_report_resolved_requires_note(mock_db):
    report = await _seed_report(mock_db, status="in_progress")
    with pytest.raises(HTTPException) as exc:
        await admin_report_service.update_report(str(report["_id"]), "resolved", None, ADMIN_ID, IP)
    assert exc.value.detail["error"]["code"] == "ADMIN_NOTE_REQUIRED"


@pytest.mark.asyncio
async def test_update_report_invalid_transition_new_to_resolved(mock_db):
    report = await _seed_report(mock_db, status="new")
    with pytest.raises(HTTPException) as exc:
        await admin_report_service.update_report(
            str(report["_id"]),
            "resolved",
            "Ghi chú xử lý dài dài cho đủ",
            ADMIN_ID,
            IP,
        )
    assert exc.value.detail["error"]["code"] == "REPORT_INVALID_STATUS"


@pytest.mark.asyncio
async def test_update_report_invalid_transition_resolved_to_any(mock_db):
    report = await _seed_report(mock_db, status="resolved")
    with pytest.raises(HTTPException) as exc:
        await admin_report_service.update_report(
            str(report["_id"]), "in_progress", None, ADMIN_ID, IP
        )
    assert exc.value.detail["error"]["code"] == "REPORT_INVALID_STATUS"


@pytest.mark.asyncio
async def test_update_report_not_found(mock_db):
    with pytest.raises(HTTPException) as exc:
        await admin_report_service.update_report(str(ObjectId()), "in_progress", None, ADMIN_ID, IP)
    assert exc.value.detail["error"]["code"] == "REPORT_NOT_FOUND"


@pytest.mark.asyncio
async def test_get_report_detail(mock_db):
    report = await _seed_report(mock_db)
    detail = await admin_report_service.get_report_detail(str(report["_id"]))
    assert detail["report_code"] == "RP-20250525-0001"
    assert detail["reporter_email"] == "sv@test.vn"
    assert detail["target_preview"] is not None
    assert detail["target_preview"]["type"] == "place"


@pytest.mark.asyncio
async def test_get_report_detail_not_found(mock_db):
    with pytest.raises(HTTPException) as exc:
        await admin_report_service.get_report_detail(str(ObjectId()))
    assert exc.value.detail["error"]["code"] == "REPORT_NOT_FOUND"


@pytest.mark.asyncio
async def test_get_report_detail_invalid_id(mock_db):
    with pytest.raises(HTTPException) as exc:
        await admin_report_service.get_report_detail("invalid-id")
    assert exc.value.detail["error"]["code"] == "REPORT_NOT_FOUND"


@pytest.mark.asyncio
async def test_list_reports_empty(mock_db):
    result = await admin_report_service.list_reports({"page": 1, "page_size": 20})
    assert result["items"] == []
    assert result["meta"]["total"] == 0


@pytest.mark.asyncio
async def test_list_reports_with_status_filter(mock_db):
    await _seed_report(mock_db, status="new", report_code="RP-001")
    await _seed_report(
        mock_db, status="resolved", report_code="RP-002", reporter_student_id=ObjectId()
    )
    result = await admin_report_service.list_reports({"page": 1, "page_size": 20, "status": "new"})
    assert result["meta"]["total"] == 1
    assert result["items"][0]["report_code"] == "RP-001"


@pytest.mark.asyncio
async def test_execute_action_soft_delete_comment(mock_db):
    comment_id = ObjectId()
    now = datetime.utcnow()
    await mock_db["comments"].insert_one(
        {
            "_id": comment_id,
            "content": "Xấu quá",
            "status": "visible",
            "place_public_id": 1,
            "created_at": now,
            "updated_at": now,
        }
    )
    report = await _seed_report(mock_db, target_type="comment", target_comment_id=comment_id)

    result = await admin_report_service.execute_action(
        str(report["_id"]),
        "soft_delete_comment",
        "Vi phạm nội quy cộng đồng",
        ADMIN_ID,
        IP,
    )
    assert result["success"] is True

    comment = await mock_db["comments"].find_one({"_id": comment_id})
    assert comment["status"] == "deleted"
    assert comment["admin_delete_reason"] == "Vi phạm nội quy cộng đồng"


@pytest.mark.asyncio
async def test_execute_action_hide_place(mock_db):
    report = await _seed_report(mock_db)

    mock_hide = AsyncMock()
    with patch("app.services.admin_place_service.hide_place", mock_hide):
        await admin_report_service.execute_action(
            str(report["_id"]),
            "hide_place",
            "Vi phạm nội quy cộng đồng",
            ADMIN_ID,
            IP,
        )
    mock_hide.assert_called_once_with(1, "Vi phạm nội quy cộng đồng", ADMIN_ID, IP)


@pytest.mark.asyncio
async def test_execute_action_invalid(mock_db):
    report = await _seed_report(mock_db, place_public_id=None)
    with pytest.raises(HTTPException) as exc:
        await admin_report_service.execute_action(
            str(report["_id"]), "hide_place", "Lý do rất dài", ADMIN_ID, IP
        )
    assert exc.value.detail["error"]["code"] == "REPORT_INVALID_STATUS"


@pytest.mark.asyncio
async def test_update_report_audit_log(mock_db):
    report = await _seed_report(mock_db)
    await admin_report_service.update_report(str(report["_id"]), "in_progress", None, ADMIN_ID, IP)
    logs = [d for d in mock_db["audit_logs"].docs if d["event_code"] == "REPORT_UPDATE"]
    assert len(logs) == 1
