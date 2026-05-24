from datetime import datetime

import pytest

from app.core.database import get_db
from app.core.security import hash_password
from app.services import session_service
from tests.auth_integration_helpers import (
    FIXED_OTP,
    TEST_EMAIL,
    TEST_NAME,
    TEST_NEW_PASSWORD,
    TEST_PASSWORD,
    activate_account,
    api_client,
    assert_student_status,
    auth_headers,
    clean_auth_integration_db,
    login,
    mock_auth_otp_and_email,
    register_student,
)

pytestmark = pytest.mark.integration


@pytest.mark.asyncio
async def test_register_returns_pending_activation():
    async with api_client() as client:
        await clean_auth_integration_db()
        with mock_auth_otp_and_email() as email_mock:
            res = await client.post(
                "/api/auth/register",
                json={
                    "email": TEST_EMAIL,
                    "password": TEST_PASSWORD,
                    "password_confirm": TEST_PASSWORD,
                    "full_name": TEST_NAME,
                    "accept_terms": True,
                },
            )
        assert res.status_code == 201
        data = res.json()["data"]
        assert data["email"] == TEST_EMAIL
        assert data["status"] == "pending_activation"
        assert "otp_resend_available_at" in data
        email_mock.assert_called()
        await assert_student_status("pending_activation")


@pytest.mark.asyncio
async def test_full_flow_register_activate_login_logout():
    async with api_client() as client:
        await clean_auth_integration_db()
        with mock_auth_otp_and_email():
            await register_student(client)
            await activate_account(client)
        await assert_student_status("active")

        token = await login(client)
        res = await client.get("/api/me", headers=auth_headers(token))
        assert res.status_code == 200
        assert res.json()["data"]["status"] == "active"
        assert res.json()["data"]["status_label"] == "Đã kích hoạt"
        assert res.json()["data"]["activated_at_display"] is not None

        res = await client.post("/api/auth/logout", headers=auth_headers(token))
        assert res.status_code == 200

        res = await client.get("/api/me", headers=auth_headers(token))
        assert res.status_code == 401
        assert res.json()["error"]["code"] == "AUTH_UNAUTHORIZED"


@pytest.mark.asyncio
async def test_forgot_password_full_flow():
    async with api_client() as client:
        await clean_auth_integration_db()
        with mock_auth_otp_and_email():
            await register_student(client)
            await activate_account(client)
            token = await login(client)

            res = await client.post("/api/auth/forgot-password", json={"email": TEST_EMAIL})
            assert res.status_code == 200

            res = await client.post(
                "/api/auth/forgot-password/verify",
                json={"email": TEST_EMAIL, "otp": FIXED_OTP},
            )
            assert res.status_code == 200
            reset_token = res.json()["data"]["reset_token"]

            res = await client.post(
                "/api/auth/forgot-password/reset",
                json={
                    "email": TEST_EMAIL,
                    "reset_token": reset_token,
                    "password": TEST_NEW_PASSWORD,
                    "password_confirm": TEST_NEW_PASSWORD,
                },
            )
            assert res.status_code == 200

        res = await client.get("/api/me", headers=auth_headers(token))
        assert res.status_code == 401

        new_token = await login(client, TEST_NEW_PASSWORD)
        res = await client.get("/api/me", headers=auth_headers(new_token))
        assert res.status_code == 200

        res = await client.post(
            "/api/auth/login",
            json={"email": TEST_EMAIL, "password": TEST_PASSWORD},
        )
        assert res.status_code == 401
        assert res.json()["error"]["code"] == "AUTH_LOGIN_FAILED"


@pytest.mark.asyncio
async def test_change_password_keeps_current_session():
    async with api_client() as client:
        await clean_auth_integration_db()
        with mock_auth_otp_and_email():
            await register_student(client)
            await activate_account(client)
        token = await login(client)

        res = await client.post(
            "/api/me/change-password",
            headers=auth_headers(token),
            json={
                "current_password": TEST_PASSWORD,
                "password": TEST_NEW_PASSWORD,
                "password_confirm": TEST_NEW_PASSWORD,
            },
        )
        assert res.status_code == 200

        res = await client.get("/api/me", headers=auth_headers(token))
        assert res.status_code == 200

        res = await client.post(
            "/api/auth/login",
            json={"email": TEST_EMAIL, "password": TEST_NEW_PASSWORD},
        )
        assert res.status_code == 200

        res = await client.post(
            "/api/auth/login",
            json={"email": TEST_EMAIL, "password": TEST_PASSWORD},
        )
        assert res.status_code == 401


@pytest.mark.asyncio
async def test_resend_otp_student_not_found():
    async with api_client() as client:
        await clean_auth_integration_db()
        res = await client.post(
            "/api/auth/otp/resend",
            json={"email": TEST_EMAIL, "purpose": "activation"},
        )
        assert res.status_code == 404
        assert res.json()["error"]["code"] == "STUDENT_NOT_FOUND"


@pytest.mark.asyncio
async def test_resend_otp_success_after_register():
    async with api_client() as client:
        await clean_auth_integration_db()
        with mock_auth_otp_and_email():
            await register_student(client)
            db = get_db()
            await db["otp_tokens"].update_many(
                {"email": TEST_EMAIL},
                {"$set": {"resend_available_at": datetime.utcnow()}},
            )
            res = await client.post(
                "/api/auth/otp/resend",
                json={"email": TEST_EMAIL, "purpose": "activation"},
            )
        assert res.status_code == 200
        assert "otp_resend_available_at" in res.json()["data"]


@pytest.mark.asyncio
async def test_me_requires_authentication():
    async with api_client() as client:
        res = await client.get("/api/me")
        assert res.status_code in (401, 403)


@pytest.mark.asyncio
async def test_audit_logs_on_register_without_otp_plaintext():
    async with api_client() as client:
        await clean_auth_integration_db()
        with mock_auth_otp_and_email():
            await register_student(client)

        db = get_db()
        logs = (
            await db["audit_logs"]
            .find({"event_code": {"$in": ["AUTH_REGISTER", "AUTH_OTP_SEND"]}})
            .to_list(10)
        )
        assert len(logs) >= 2
        for log in logs:
            assert FIXED_OTP not in log.get("description", "")


@pytest.mark.asyncio
async def test_profile_update_after_login():
    async with api_client() as client:
        await clean_auth_integration_db()
        with mock_auth_otp_and_email():
            await register_student(client)
            await activate_account(client)
        token = await login(client)

        new_name = "Nguyễn Văn Integration"
        res = await client.patch(
            "/api/me",
            headers=auth_headers(token),
            json={"full_name": new_name},
        )
        assert res.status_code == 200
        assert res.json()["data"]["full_name"] == new_name

        db = get_db()
        student = await db["students"].find_one({"email": TEST_EMAIL})
        assert student["full_name"] == new_name


@pytest.mark.asyncio
async def test_locked_student_profile_via_api():
    async with api_client() as client:
        await clean_auth_integration_db()
        db = get_db()
        await db["students"].insert_one(
            {
                "email": TEST_EMAIL,
                "password_hash": hash_password(TEST_PASSWORD),
                "full_name": TEST_NAME,
                "status": "locked",
                "locked_reason": "Vi phạm quy chế hệ thống",
                "created_at": datetime.utcnow(),
            }
        )

        res = await client.post(
            "/api/auth/login",
            json={"email": TEST_EMAIL, "password": TEST_PASSWORD},
        )
        assert res.status_code == 401
        assert res.json()["error"]["code"] == "AUTH_LOGIN_LOCKED"

        student = await db["students"].find_one({"email": TEST_EMAIL})
        token = await session_service.create_session(student["_id"], "127.0.0.1", "pytest")
        res = await client.get("/api/me", headers=auth_headers(token))
        assert res.status_code == 200
        assert res.json()["data"]["status"] == "locked"
        assert res.json()["data"]["locked_reason"] == "Vi phạm quy chế hệ thống"
