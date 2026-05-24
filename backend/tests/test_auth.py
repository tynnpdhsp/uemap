from datetime import datetime, timedelta
from unittest.mock import AsyncMock, patch
import pytest
from httpx import ASGITransport, AsyncClient
from app.main import app
from app.core.database import get_db

TEST_EMAIL = "4901104172@student.hcmue.edu.vn"
TEST_PASSWORD = "testpassword123"
TEST_NAME = "Nguyễn Văn A"


async def clean_db():
    db = get_db()
    await db["students"].delete_many({"email": TEST_EMAIL})
    await db["otp_tokens"].delete_many({"email": TEST_EMAIL})
    await db["student_sessions"].delete_many({})
    await db["login_attempts"].delete_many({"email": TEST_EMAIL})
    await db["audit_logs"].delete_many({})


@pytest.mark.asyncio
@patch("app.services.email_service.send_otp_email", new_callable=AsyncMock)
async def test_auth_flow(mock_send_email):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        await clean_db()

        reg_payload = {
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD,
            "password_confirm": TEST_PASSWORD,
            "full_name": TEST_NAME,
            "accept_terms": True
        }
        res = await client.post("/api/auth/register", json=reg_payload)
        assert res.status_code == 201
        data = res.json()
        assert data["success"] is True
        assert data["data"]["email"] == TEST_EMAIL
        assert data["data"]["status"] == "pending_activation"
        mock_send_email.assert_called_once()

        db = get_db()
        otp_doc = await db["otp_tokens"].find_one({"email": TEST_EMAIL, "purpose": "activation"})
        assert otp_doc is not None
        
        verify_payload = {
            "email": TEST_EMAIL,
            "otp": "000000",
            "purpose": "activation"
        }
        res = await client.post("/api/auth/otp/verify", json=verify_payload)
        assert res.status_code == 400
        assert res.json()["success"] is False

        with patch("app.services.otp_service.verify_password", return_value=True):
            verify_payload["otp"] = "123456"
            res = await client.post("/api/auth/otp/verify", json=verify_payload)
            assert res.status_code == 200
            assert res.json()["success"] is True

        login_payload = {
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        }
        res = await client.post("/api/auth/login", json=login_payload)
        assert res.status_code == 200
        login_data = res.json()
        assert login_data["success"] is True
        token = login_data["data"]["access_token"]
        assert token is not None

        headers = {"Authorization": f"Bearer {token}"}
        res = await client.post("/api/auth/logout", headers=headers)
        assert res.status_code == 200
        assert res.json()["success"] is True

        res = await client.post("/api/auth/logout", headers=headers)
        assert res.status_code == 401


@pytest.mark.asyncio
@patch("app.services.email_service.send_otp_email", new_callable=AsyncMock)
async def test_forgot_password_flow(mock_send_email):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        await clean_db()

        db = get_db()
        from app.core.security import hash_password
        await db["students"].insert_one({
            "email": TEST_EMAIL,
            "password_hash": hash_password(TEST_PASSWORD),
            "full_name": TEST_NAME,
            "status": "active",
            "created_at": datetime.utcnow()
        })

        res = await client.post("/api/auth/forgot-password", json={"email": TEST_EMAIL})
        assert res.status_code == 200
        assert res.json()["success"] is True
        mock_send_email.assert_called_once()

        with patch("app.services.otp_service.verify_password", return_value=True):
            verify_payload = {
                "email": TEST_EMAIL,
                "otp": "123456"
            }
            res = await client.post("/api/auth/forgot-password/verify", json=verify_payload)
            assert res.status_code == 200
            data = res.json()
            assert data["success"] is True
            reset_token = data["data"]["reset_token"]
            assert reset_token is not None

        new_password = "newpassword12345"
        reset_payload = {
            "email": TEST_EMAIL,
            "reset_token": reset_token,
            "password": new_password,
            "password_confirm": new_password
        }
        res = await client.post("/api/auth/forgot-password/reset", json=reset_payload)
        assert res.status_code == 200
        assert res.json()["success"] is True

        login_payload = {
            "email": TEST_EMAIL,
            "password": new_password
        }
        res = await client.post("/api/auth/login", json=login_payload)
        assert res.status_code == 200
        assert res.json()["success"] is True
