from datetime import datetime, timedelta
from unittest.mock import AsyncMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from app.core.database import get_db
from app.core.security import hash_password
from app.main import app
from tests.integration.auth_integration_helpers import (
    TEST_EMAIL,
    TEST_NAME,
    TEST_PASSWORD,
    clean_auth_integration_db,
)

pytestmark = pytest.mark.integration


@pytest.mark.asyncio
@patch("app.services.email_service.send_otp_email", new_callable=AsyncMock)
async def test_registration_validation(mock_send_email):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        await clean_auth_integration_db()

        payload = {
            "email": "4901104172@gmail.com",
            "password": TEST_PASSWORD,
            "password_confirm": TEST_PASSWORD,
            "full_name": TEST_NAME,
            "accept_terms": True,
        }
        res = await client.post("/api/auth/register", json=payload)
        assert res.status_code == 422

        payload["email"] = "490110417@student.hcmue.edu.vn"
        res = await client.post("/api/auth/register", json=payload)
        assert res.status_code == 422

        payload["email"] = TEST_EMAIL
        payload["password"] = "123"
        payload["password_confirm"] = "123"
        res = await client.post("/api/auth/register", json=payload)
        assert res.status_code == 422

        payload["password"] = TEST_PASSWORD
        payload["password_confirm"] = "differentpassword"
        res = await client.post("/api/auth/register", json=payload)
        assert res.status_code == 422

        payload["password_confirm"] = TEST_PASSWORD
        payload["full_name"] = "A"
        res = await client.post("/api/auth/register", json=payload)
        assert res.status_code == 422

        payload["full_name"] = TEST_NAME
        payload["accept_terms"] = False
        res = await client.post("/api/auth/register", json=payload)
        assert res.status_code == 422


@pytest.mark.asyncio
@patch("app.services.email_service.send_otp_email", new_callable=AsyncMock)
async def test_duplicate_email_registration(mock_send_email):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        await clean_auth_integration_db()

        db = get_db()
        await db["students"].insert_one(
            {
                "email": TEST_EMAIL,
                "password_hash": hash_password(TEST_PASSWORD),
                "full_name": TEST_NAME,
                "status": "active",
                "created_at": datetime.utcnow(),
            }
        )

        payload = {
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD,
            "password_confirm": TEST_PASSWORD,
            "full_name": TEST_NAME,
            "accept_terms": True,
        }
        res = await client.post("/api/auth/register", json=payload)
        assert res.status_code == 400
        assert res.json()["error"]["code"] == "AUTH_EMAIL_EXISTS"


@pytest.mark.asyncio
@patch("app.services.email_service.send_otp_email", new_callable=AsyncMock)
async def test_otp_cooldown_and_rate_limit(mock_send_email):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        await clean_auth_integration_db()

        payload = {
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD,
            "password_confirm": TEST_PASSWORD,
            "full_name": TEST_NAME,
            "accept_terms": True,
        }
        await client.post("/api/auth/register", json=payload)
        mock_send_email.assert_called_once()

        res = await client.post(
            "/api/auth/otp/resend", json={"email": TEST_EMAIL, "purpose": "activation"}
        )
        assert res.status_code == 429
        assert res.json()["error"]["code"] == "AUTH_OTP_COOLDOWN"

        db = get_db()
        now = datetime.utcnow()
        await db["otp_tokens"].delete_many({"email": TEST_EMAIL})

        for i in range(3):
            await db["otp_tokens"].insert_one(
                {
                    "email": TEST_EMAIL,
                    "purpose": "activation",
                    "otp_hash": "hash",
                    "sent_at": now - timedelta(minutes=5 * i),
                    "expires_at": now + timedelta(minutes=15),
                    "resend_available_at": now - timedelta(seconds=10),
                    "send_ip": "127.0.0.1",
                    "created_at": now - timedelta(minutes=5 * i),
                }
            )

        res = await client.post(
            "/api/auth/otp/resend", json={"email": TEST_EMAIL, "purpose": "activation"}
        )
        assert res.status_code == 429
        assert res.json()["error"]["code"] == "AUTH_OTP_RATE_LIMIT"


@pytest.mark.asyncio
@patch("app.services.email_service.send_otp_email", new_callable=AsyncMock)
async def test_otp_max_failures_locking(mock_send_email):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        await clean_auth_integration_db()

        payload = {
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD,
            "password_confirm": TEST_PASSWORD,
            "full_name": TEST_NAME,
            "accept_terms": True,
        }
        await client.post("/api/auth/register", json=payload)

        verify_payload = {"email": TEST_EMAIL, "otp": "000000", "purpose": "activation"}

        for _ in range(4):
            res = await client.post("/api/auth/otp/verify", json=verify_payload)
            assert res.status_code == 400
            assert res.json()["error"]["code"] == "AUTH_OTP_INVALID"

        res = await client.post("/api/auth/otp/verify", json=verify_payload)
        assert res.status_code == 403
        assert res.json()["error"]["code"] == "AUTH_OTP_LOCKED"

        res = await client.post("/api/auth/otp/verify", json=verify_payload)
        assert res.status_code == 403


@pytest.mark.asyncio
async def test_login_scenarios():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        await clean_auth_integration_db()

        db = get_db()
        await db["students"].insert_one(
            {
                "email": TEST_EMAIL,
                "password_hash": hash_password(TEST_PASSWORD),
                "full_name": TEST_NAME,
                "status": "pending_activation",
                "created_at": datetime.utcnow(),
            }
        )

        res = await client.post(
            "/api/auth/login", json={"email": TEST_EMAIL, "password": TEST_PASSWORD}
        )
        assert res.status_code == 401
        assert res.json()["error"]["code"] == "AUTH_LOGIN_NOT_ACTIVATED"

        await db["students"].update_one(
            {"email": TEST_EMAIL},
            {"$set": {"status": "locked", "locked_reason": "Vi phạm điều khoản"}},
        )
        res = await client.post(
            "/api/auth/login", json={"email": TEST_EMAIL, "password": TEST_PASSWORD}
        )
        assert res.status_code == 401
        assert res.json()["error"]["code"] == "AUTH_LOGIN_LOCKED"

        await db["students"].update_one({"email": TEST_EMAIL}, {"$set": {"status": "active"}})
        res = await client.post(
            "/api/auth/login", json={"email": TEST_EMAIL, "password": "wrongpassword"}
        )
        assert res.status_code == 401
        assert res.json()["error"]["code"] == "AUTH_LOGIN_FAILED"


@pytest.mark.asyncio
async def test_login_rate_limit():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        await clean_auth_integration_db()

        db = get_db()
        await db["students"].insert_one(
            {
                "email": TEST_EMAIL,
                "password_hash": hash_password(TEST_PASSWORD),
                "full_name": TEST_NAME,
                "status": "active",
                "created_at": datetime.utcnow(),
            }
        )

        now = datetime.utcnow()
        for _ in range(10):
            await db["login_attempts"].insert_one(
                {"email": TEST_EMAIL, "ip_address": "127.0.0.1", "failed_at": now}
            )

        res = await client.post(
            "/api/auth/login", json={"email": TEST_EMAIL, "password": TEST_PASSWORD}
        )
        assert res.status_code == 429
        assert res.json()["error"]["code"] == "AUTH_LOGIN_RATE_LIMIT"


@pytest.mark.asyncio
@patch("app.services.email_service.send_otp_email", new_callable=AsyncMock)
async def test_forgot_password_security(mock_send_email):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        await clean_auth_integration_db()

        res = await client.post("/api/auth/forgot-password", json={"email": TEST_EMAIL})
        assert res.status_code == 200
        assert res.json()["success"] is True
        mock_send_email.assert_not_called()

        db = get_db()
        await db["students"].insert_one(
            {
                "email": TEST_EMAIL,
                "password_hash": hash_password(TEST_PASSWORD),
                "full_name": TEST_NAME,
                "status": "locked",
                "created_at": datetime.utcnow(),
            }
        )
        res = await client.post("/api/auth/forgot-password", json={"email": TEST_EMAIL})
        assert res.status_code == 200
        assert res.json()["success"] is True
        mock_send_email.assert_not_called()
