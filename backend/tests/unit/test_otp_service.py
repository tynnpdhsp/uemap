from datetime import datetime, timedelta
from unittest.mock import patch

import pytest
from fastapi import HTTPException

from app.core.security import hash_password
from app.services import otp_service
from tests.unit.conftest import TEST_EMAIL

pytestmark = pytest.mark.unit


def _otp_side_effect(_a: int, _b: int) -> int:
    return 1


@pytest.mark.asyncio
async def test_create_otp_returns_six_digit_code(mock_db):
    with patch("app.services.otp_service.random.randint", side_effect=_otp_side_effect):
        code = await otp_service.create_otp(TEST_EMAIL, "activation", "127.0.0.1")
    assert code == "111111"
    assert await mock_db["otp_tokens"].count_documents({"email": TEST_EMAIL}) == 1


@pytest.mark.asyncio
async def test_create_otp_cooldown(mock_db):
    now = datetime.utcnow()
    await mock_db["otp_tokens"].insert_one(
        {
            "email": TEST_EMAIL,
            "purpose": "activation",
            "resend_available_at": now + timedelta(seconds=30),
            "created_at": now,
        }
    )
    with pytest.raises(HTTPException) as exc:
        await otp_service.create_otp(TEST_EMAIL, "activation", "127.0.0.1")
    assert exc.value.status_code == 429
    assert exc.value.detail["error"]["code"] == "AUTH_OTP_COOLDOWN"


@pytest.mark.asyncio
async def test_create_otp_rate_limit(mock_db):
    now = datetime.utcnow()
    for i in range(3):
        await mock_db["otp_tokens"].insert_one(
            {
                "email": TEST_EMAIL,
                "purpose": "activation",
                "created_at": now - timedelta(minutes=i),
            }
        )
    with pytest.raises(HTTPException) as exc:
        await otp_service.create_otp(TEST_EMAIL, "activation", "127.0.0.1")
    assert exc.value.detail["error"]["code"] == "AUTH_OTP_RATE_LIMIT"


@pytest.mark.asyncio
async def test_verify_otp_success(mock_db):
    await mock_db["students"].insert_one(
        {"email": TEST_EMAIL, "failed_otp_attempts": 2, "status": "pending_activation"}
    )
    now = datetime.utcnow()
    await mock_db["otp_tokens"].insert_one(
        {
            "email": TEST_EMAIL,
            "purpose": "activation",
            "otp_hash": hash_password("111111"),
            "used_at": None,
            "expires_at": now + timedelta(minutes=15),
            "created_at": now,
        }
    )
    assert await otp_service.verify_otp(TEST_EMAIL, "111111", "activation") is True
    student = await mock_db["students"].find_one({"email": TEST_EMAIL})
    assert student["failed_otp_attempts"] == 0


@pytest.mark.asyncio
async def test_verify_otp_student_not_found(mock_db):
    with pytest.raises(HTTPException) as exc:
        await otp_service.verify_otp(TEST_EMAIL, "111111", "activation")
    assert exc.value.status_code == 404


@pytest.mark.asyncio
async def test_verify_otp_locked_account(mock_db):
    now = datetime.utcnow()
    await mock_db["students"].insert_one(
        {
            "email": TEST_EMAIL,
            "otp_locked_until": now + timedelta(minutes=10),
        }
    )
    with pytest.raises(HTTPException) as exc:
        await otp_service.verify_otp(TEST_EMAIL, "111111", "activation")
    assert exc.value.detail["error"]["code"] == "AUTH_OTP_LOCKED"


@pytest.mark.asyncio
async def test_verify_otp_invalid_increments_attempts(mock_db):
    await mock_db["students"].insert_one({"email": TEST_EMAIL, "failed_otp_attempts": 0})
    with pytest.raises(HTTPException) as exc:
        await otp_service.verify_otp(TEST_EMAIL, "000000", "activation")
    assert exc.value.detail["error"]["code"] == "AUTH_OTP_INVALID"
    student = await mock_db["students"].find_one({"email": TEST_EMAIL})
    assert student["failed_otp_attempts"] == 1


@pytest.mark.asyncio
async def test_verify_otp_fifth_failure_locks(mock_db):
    await mock_db["students"].insert_one({"email": TEST_EMAIL, "failed_otp_attempts": 4})
    with pytest.raises(HTTPException) as exc:
        await otp_service.verify_otp(TEST_EMAIL, "000000", "activation")
    assert exc.value.detail["error"]["code"] == "AUTH_OTP_LOCKED"


@pytest.mark.asyncio
async def test_verify_otp_expired_token(mock_db):
    await mock_db["students"].insert_one({"email": TEST_EMAIL, "failed_otp_attempts": 0})
    now = datetime.utcnow()
    await mock_db["otp_tokens"].insert_one(
        {
            "email": TEST_EMAIL,
            "purpose": "activation",
            "otp_hash": hash_password("111111"),
            "used_at": None,
            "expires_at": now - timedelta(minutes=1),
            "created_at": now - timedelta(minutes=20),
        }
    )
    with pytest.raises(HTTPException) as exc:
        await otp_service.verify_otp(TEST_EMAIL, "111111", "activation")
    assert exc.value.detail["error"]["code"] == "AUTH_OTP_INVALID"


@pytest.mark.asyncio
async def test_create_otp_invalidates_previous_unused(mock_db):
    now = datetime.utcnow()
    old_id = (
        await mock_db["otp_tokens"].insert_one(
            {
                "email": TEST_EMAIL,
                "purpose": "activation",
                "used_at": None,
                "expires_at": now + timedelta(minutes=15),
                "resend_available_at": now - timedelta(seconds=120),
                "created_at": now - timedelta(minutes=10),
            }
        )
    ).inserted_id
    with patch("app.services.otp_service.random.randint", side_effect=_otp_side_effect):
        await otp_service.create_otp(TEST_EMAIL, "activation", "127.0.0.1")
    old_doc = next(d for d in mock_db["otp_tokens"].docs if d["_id"] == old_id)
    assert old_doc["expires_at"] <= datetime.utcnow()
