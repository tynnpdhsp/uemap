from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from bson import ObjectId

from app.api.routes.student import me as me_routes
from app.schemas.student import ChangePasswordRequest, StudentProfileUpdateRequest
from tests.unit.conftest import TEST_EMAIL, TEST_NAME, TEST_PASSWORD

pytestmark = pytest.mark.unit


def _request() -> MagicMock:
    req = MagicMock()
    req.client = MagicMock()
    req.client.host = "127.0.0.1"
    return req


@pytest.mark.asyncio
async def test_get_profile_route():
    student = {
        "_id": ObjectId(),
        "email": TEST_EMAIL,
        "full_name": TEST_NAME,
        "status": "active",
        "activated_at": datetime(2026, 5, 22, 10, 0, 0),
        "locked_reason": None,
    }
    response = await me_routes.get_profile(current_student=student)
    assert response["success"] is True
    assert response["data"]["email"] == TEST_EMAIL
    assert response["data"]["status_label"] == "Đã kích hoạt"


@pytest.mark.asyncio
async def test_update_profile_route(mock_db):
    student_id = ObjectId()
    await mock_db["students"].insert_one(
        {
            "_id": student_id,
            "email": TEST_EMAIL,
            "full_name": TEST_NAME,
            "status": "active",
            "locked_reason": None,
        }
    )
    student = {
        "_id": student_id,
        "email": TEST_EMAIL,
        "full_name": TEST_NAME,
        "status": "active",
        "locked_reason": None,
    }
    payload = StudentProfileUpdateRequest(full_name="Nguyễn Văn Cập Nhật")
    response = await me_routes.update_profile(payload, current_student=student)
    assert response["success"] is True
    assert response["data"]["full_name"] == "Nguyễn Văn Cập Nhật"
    stored = await mock_db["students"].find_one({"_id": student_id})
    assert stored["full_name"] == "Nguyễn Văn Cập Nhật"
    assert "updated_at" in stored


@pytest.mark.asyncio
async def test_change_password_route(mock_db):
    student_id = ObjectId()
    student = {"_id": student_id, "jti": "current-jti", "email": TEST_EMAIL}
    payload = ChangePasswordRequest(
        current_password=TEST_PASSWORD,
        password="newpassword99",
        password_confirm="newpassword99",
    )
    with patch(
        "app.api.routes.student.me.auth_service.change_password",
        AsyncMock(),
    ) as mock_change:
        response = await me_routes.change_password(payload, _request(), current_student=student)
    mock_change.assert_called_once_with(
        student_id=student_id,
        current_jti="current-jti",
        current_password=TEST_PASSWORD,
        new_password="newpassword99",
        ip_address="127.0.0.1",
    )
    assert response["data"]["message"] == "Đổi mật khẩu thành công."
