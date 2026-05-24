from unittest.mock import AsyncMock, patch

import pytest
from bson import ObjectId
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials

from app.api.deps import get_current_admin, get_current_student
from app.core.security import create_access_token

pytestmark = pytest.mark.unit


def _credentials(token: str) -> HTTPAuthorizationCredentials:
    return HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)


@pytest.mark.asyncio
async def test_get_current_student_success(mock_db):
    student_id = ObjectId()
    await mock_db["students"].insert_one(
        {
            "_id": student_id,
            "email": "4901104172@student.hcmue.edu.vn",
            "full_name": "Nguyễn Văn A",
            "status": "active",
        }
    )
    token = create_access_token({"sub": str(student_id), "jti": "test-jti"}, role="student")
    with patch(
        "app.api.deps.session_service.verify_session",
        AsyncMock(return_value=True),
    ):
        student = await get_current_student(_credentials(token))
    assert student["email"] == "4901104172@student.hcmue.edu.vn"
    assert student["jti"] == "test-jti"


@pytest.mark.asyncio
async def test_get_current_student_invalid_session():
    token = create_access_token({"sub": str(ObjectId()), "jti": "jti"}, role="student")
    with patch(
        "app.api.deps.session_service.verify_session",
        AsyncMock(return_value=False),
    ):
        with pytest.raises(HTTPException) as exc:
            await get_current_student(_credentials(token))
    assert exc.value.status_code == 401
    assert exc.value.detail["error"]["code"] == "AUTH_UNAUTHORIZED"


@pytest.mark.asyncio
async def test_get_current_student_forbidden_role():
    token = create_access_token({"sub": "admin-id", "jti": "jti"}, role="admin")
    with pytest.raises(HTTPException) as exc:
        await get_current_student(_credentials(token))
    assert exc.value.status_code == 403
    assert exc.value.detail["error"]["code"] == "AUTH_FORBIDDEN"


@pytest.mark.asyncio
async def test_get_current_admin_success():
    token = create_access_token({"sub": "admin-id"}, role="admin")
    payload = await get_current_admin(_credentials(token))
    assert payload["role"] == "admin"


@pytest.mark.asyncio
async def test_get_current_student_missing_in_database(mock_db):
    token = create_access_token({"sub": str(ObjectId()), "jti": "orphan-jti"}, role="student")
    with patch(
        "app.api.deps.session_service.verify_session",
        AsyncMock(return_value=True),
    ):
        with pytest.raises(HTTPException) as exc:
            await get_current_student(_credentials(token))
    assert exc.value.status_code == 401
    assert exc.value.detail["error"]["code"] == "AUTH_UNAUTHORIZED"


@pytest.mark.asyncio
async def test_get_current_admin_rejects_student_token():
    token = create_access_token({"sub": str(ObjectId()), "jti": "j"}, role="student")
    with pytest.raises(HTTPException) as exc:
        await get_current_admin(_credentials(token))
    assert exc.value.status_code == 403
