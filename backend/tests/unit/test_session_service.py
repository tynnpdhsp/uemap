from datetime import datetime, timedelta

import pytest
from bson import ObjectId

from app.core.security import decode_access_token
from app.services import session_service

pytestmark = pytest.mark.unit


@pytest.mark.asyncio
async def test_create_session_returns_valid_jwt(mock_db):
    student_id = ObjectId()
    token = await session_service.create_session(student_id, "127.0.0.1", "TestAgent")
    payload = decode_access_token(token)
    assert payload["sub"] == str(student_id)
    assert payload["role"] == "student"
    assert "jti" in payload
    assert await mock_db["student_sessions"].count_documents({"student_id": student_id}) == 1


@pytest.mark.asyncio
async def test_verify_session_active(mock_db):
    student_id = ObjectId()
    token = await session_service.create_session(student_id, "127.0.0.1", "UA")
    jti = decode_access_token(token)["jti"]
    assert await session_service.verify_session(jti) is True


@pytest.mark.asyncio
async def test_verify_session_revoked(mock_db):
    student_id = ObjectId()
    token = await session_service.create_session(student_id, "127.0.0.1", "UA")
    jti = decode_access_token(token)["jti"]
    await session_service.revoke_session(jti)
    assert await session_service.verify_session(jti) is False


@pytest.mark.asyncio
async def test_verify_session_expired(mock_db):
    jti = "expired-jti"
    await mock_db["student_sessions"].insert_one(
        {
            "jti": jti,
            "expires_at": datetime.utcnow() - timedelta(minutes=1),
            "revoked_at": None,
        }
    )
    assert await session_service.verify_session(jti) is False


@pytest.mark.asyncio
async def test_revoke_all_sessions(mock_db):
    student_id = ObjectId()
    await mock_db["student_sessions"].insert_one(
        {"student_id": student_id, "jti": "a", "revoked_at": None}
    )
    await mock_db["student_sessions"].insert_one(
        {"student_id": student_id, "jti": "b", "revoked_at": None}
    )
    await session_service.revoke_all_sessions(student_id)
    assert await session_service.verify_session("a") is False
    assert await session_service.verify_session("b") is False


@pytest.mark.asyncio
async def test_revoke_other_sessions_keeps_current(mock_db):
    student_id = ObjectId()
    expires = datetime.utcnow() + timedelta(days=7)
    await mock_db["student_sessions"].insert_one(
        {"student_id": student_id, "jti": "keep", "revoked_at": None, "expires_at": expires}
    )
    await mock_db["student_sessions"].insert_one(
        {"student_id": student_id, "jti": "drop", "revoked_at": None, "expires_at": expires}
    )
    await session_service.revoke_other_sessions(student_id, "keep")
    assert await session_service.verify_session("keep") is True
    assert await session_service.verify_session("drop") is False


@pytest.mark.asyncio
async def test_verify_session_not_found(mock_db):
    assert await session_service.verify_session("missing-jti") is False
