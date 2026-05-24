from datetime import datetime
import pytest
from bson import ObjectId
from fastapi import HTTPException

from app.services import report_service
from app.schemas.report import ReportCreateRequest

pytestmark = pytest.mark.unit

@pytest.mark.asyncio
async def test_report_place_success(mock_db):
    place_id = ObjectId()
    await mock_db["places"].insert_one({
        "_id": place_id,
        "public_id": 1,
        "status": "published",
        "name": "Địa điểm vi phạm"
    })

    payload = ReportCreateRequest(
        target_type="place",
        target_id="1",
        report_type="inappropriate_content",
        reason="Có từ ngữ tục tĩu và vô cùng phản cảm trên trang này."
    )

    student_id = ObjectId()
    result = await report_service.create_report(student_id, payload, "127.0.0.1")

    assert "report_code" in result
    assert result["report_code"].startswith("RP-")
    assert result["status"] == "new"

    db_report = await mock_db["reports"].find_one({"report_code": result["report_code"]})
    assert db_report is not None
    assert db_report["target_type"] == "place"
    assert db_report["target_place_id"] == place_id

@pytest.mark.asyncio
async def test_report_place_not_found(mock_db):
    payload = ReportCreateRequest(
        target_type="place",
        target_id="999",
        report_type="inappropriate_content",
        reason="Địa điểm này thực tế không hề tồn tại trên bản đồ."
    )

    student_id = ObjectId()
    with pytest.raises(HTTPException) as exc:
        await report_service.create_report(student_id, payload, "127.0.0.1")

    assert exc.value.status_code == 404
    assert exc.value.detail["error"]["code"] == "PLACE_NOT_FOUND"

@pytest.mark.asyncio
async def test_report_comment_success(mock_db):
    comment_id = ObjectId()
    await mock_db["comments"].insert_one({
        "_id": comment_id,
        "content": "Bình luận xấu",
        "place_public_id": 1,
        "status": "visible"
    })

    payload = ReportCreateRequest(
        target_type="comment",
        target_id=str(comment_id),
        report_type="harassment",
        reason="Bình luận này mang tính chất quấy rối người khác nghiêm trọng."
    )

    student_id = ObjectId()
    result = await report_service.create_report(student_id, payload, "127.0.0.1")

    assert "report_code" in result
    assert result["report_code"].startswith("RP-")
    assert result["status"] == "new"

    db_report = await mock_db["reports"].find_one({"report_code": result["report_code"]})
    assert db_report is not None
    assert db_report["target_type"] == "comment"
    assert db_report["target_comment_id"] == comment_id

@pytest.mark.asyncio
async def test_report_comment_not_found(mock_db):
    payload = ReportCreateRequest(
        target_type="comment",
        target_id=str(ObjectId()),
        report_type="harassment",
        reason="Bình luận này hiện tại không tìm thấy trên hệ thống."
    )

    student_id = ObjectId()
    with pytest.raises(HTTPException) as exc:
        await report_service.create_report(student_id, payload, "127.0.0.1")

    assert exc.value.status_code == 404
    assert exc.value.detail["error"]["code"] == "COMMENT_NOT_FOUND"
