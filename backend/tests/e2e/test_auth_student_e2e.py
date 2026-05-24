from datetime import datetime

import pytest

from app.core.database import get_db
from app.core.security import hash_password
from app.services import session_service
from tests.e2e.helpers import (
    FIXED_OTP,
    TEST_EMAIL,
    TEST_NAME,
    TEST_NEW_PASSWORD,
    TEST_PASSWORD,
    activate_account,
    api_client,
    assert_error,
    assert_student_status,
    auth_headers,
    clean_auth_db,
    login,
    mock_auth_otp_and_email,
    register_student,
    setup_active_student,
)

pytestmark = pytest.mark.e2e


@pytest.mark.asyncio
async def test_e2e_student_onboarding_through_logout():
    async with api_client() as client:
        await clean_auth_db()
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

            await activate_account(client)
        await assert_student_status("active")

        token = await login(client)
        res = await client.get("/api/me", headers=auth_headers(token))
        assert res.status_code == 200
        profile = res.json()["data"]
        assert profile["email"] == TEST_EMAIL
        assert profile["status"] == "active"
        assert profile["status_label"] == "Đã kích hoạt"
        assert profile["activated_at_display"] is not None

        res = await client.post("/api/auth/logout", headers=auth_headers(token))
        assert res.status_code == 200
        assert res.json()["success"] is True

        res = await client.get("/api/me", headers=auth_headers(token))
        assert_error(res, 401, "AUTH_UNAUTHORIZED")


@pytest.mark.asyncio
async def test_e2e_pending_activation_cannot_login():
    async with api_client() as client:
        await clean_auth_db()
        with mock_auth_otp_and_email():
            await register_student(client)
        res = await client.post(
            "/api/auth/login",
            json={"email": TEST_EMAIL, "password": TEST_PASSWORD},
        )
        assert_error(res, 401, "AUTH_LOGIN_NOT_ACTIVATED")


@pytest.mark.asyncio
async def test_e2e_duplicate_registration_rejected():
    async with api_client() as client:
        await clean_auth_db()
        db = get_db()
        assert await db["students"].count_documents({"email": TEST_EMAIL}) == 0
        assert await db["otp_tokens"].count_documents({"email": TEST_EMAIL}) == 0

        with mock_auth_otp_and_email():
            await register_student(client)
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
        assert_error(res, 400, "AUTH_EMAIL_EXISTS")


@pytest.mark.asyncio
async def test_e2e_otp_resend_then_activate():
    async with api_client() as client:
        await clean_auth_db()
        with mock_auth_otp_and_email() as email_mock:
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
            assert email_mock.call_count >= 2
            await activate_account(client)
        await assert_student_status("active")


@pytest.mark.asyncio
async def test_e2e_profile_update_and_change_password():
    async with api_client() as client:
        token = await setup_active_student(client)

        new_name = "Nguyễn Văn E2E"
        res = await client.patch(
            "/api/me",
            headers=auth_headers(token),
            json={"full_name": new_name},
        )
        assert res.status_code == 200
        assert res.json()["data"]["full_name"] == new_name

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
        assert_error(res, 401, "AUTH_LOGIN_FAILED")


@pytest.mark.asyncio
async def test_e2e_forgot_password_revokes_old_sessions():
    async with api_client() as client:
        token = await setup_active_student(client)

        with mock_auth_otp_and_email():
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
        assert_error(res, 401, "AUTH_UNAUTHORIZED")

        new_token = await login(client, TEST_NEW_PASSWORD)
        res = await client.get("/api/me", headers=auth_headers(new_token))
        assert res.status_code == 200


@pytest.mark.asyncio
async def test_e2e_protected_routes_require_valid_token():
    async with api_client() as client:
        res = await client.get("/api/me")
        assert res.status_code in (401, 403)

        res = await client.get(
            "/api/me",
            headers={"Authorization": "Bearer not-a-valid-jwt"},
        )
        assert res.status_code in (401, 403)

        res = await client.post("/api/auth/logout")
        assert res.status_code in (401, 403)


@pytest.mark.asyncio
async def test_e2e_audit_events_on_full_registration():
    async with api_client() as client:
        await clean_auth_db()
        with mock_auth_otp_and_email():
            await register_student(client)
            await activate_account(client)

        db = get_db()
        logs = (
            await db["audit_logs"]
            .find(
                {
                    "event_code": {
                        "$in": ["AUTH_REGISTER", "AUTH_OTP_SEND", "AUTH_OTP_VERIFY"],
                    }
                }
            )
            .to_list(20)
        )
        codes = {doc["event_code"] for doc in logs}
        assert "AUTH_REGISTER" in codes
        assert "AUTH_OTP_SEND" in codes
        assert "AUTH_OTP_VERIFY" in codes
        for doc in logs:
            assert FIXED_OTP not in doc.get("description", "")


@pytest.mark.asyncio
async def test_e2e_locked_student_login_blocked_profile_readable():
    async with api_client() as client:
        await clean_auth_db()
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
        assert_error(res, 401, "AUTH_LOGIN_LOCKED")

        student = await db["students"].find_one({"email": TEST_EMAIL})
        token = await session_service.create_session(student["_id"], "127.0.0.1", "pytest-e2e")
        res = await client.get("/api/me", headers=auth_headers(token))
        assert res.status_code == 200
        data = res.json()["data"]
        assert data["status"] == "locked"
        assert data["status_label"] == "Bị khóa"
        assert data["locked_reason"] == "Vi phạm quy chế hệ thống"
