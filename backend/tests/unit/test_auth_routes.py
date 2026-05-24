from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException

from app.api.routes.student import auth as auth_routes
from app.schemas.auth import (
    ForgotPasswordRequest,
    ForgotPasswordVerifyRequest,
    LoginRequest,
    OTPResendRequest,
    OTPVerifyRequest,
    ResetPasswordRequest,
    StudentRegisterRequest,
)
from tests.unit.conftest import TEST_EMAIL, TEST_NAME, TEST_PASSWORD

pytestmark = pytest.mark.unit


def _request(ip: str = "127.0.0.1", user_agent: str = "pytest-agent") -> MagicMock:
    req = MagicMock()
    req.client = MagicMock()
    req.client.host = ip
    req.headers = MagicMock()
    req.headers.get = lambda key, default="": user_agent if key == "user-agent" else default
    return req


@pytest.mark.asyncio
async def test_register_route_wraps_service_result():
    payload = StudentRegisterRequest(
        email=TEST_EMAIL,
        password=TEST_PASSWORD,
        password_confirm=TEST_PASSWORD,
        full_name=TEST_NAME,
        accept_terms=True,
    )
    fake_result = {
        "email": TEST_EMAIL,
        "status": "pending_activation",
        "otp_resend_available_at": datetime.utcnow(),
    }
    with patch(
        "app.api.routes.student.auth.auth_service.register_student",
        AsyncMock(return_value=fake_result),
    ):
        response = await auth_routes.register(payload, _request())
    assert response["success"] is True
    assert response["data"]["email"] == TEST_EMAIL


@pytest.mark.asyncio
async def test_verify_otp_route_wraps_activation():
    payload = OTPVerifyRequest(email=TEST_EMAIL, otp="111111", purpose="activation")
    fake_result = {"success": True, "activated_at_display": "22/05/2026 10:00"}
    with patch(
        "app.api.routes.student.auth.auth_service.activate_student_account",
        AsyncMock(return_value=fake_result),
    ):
        response = await auth_routes.verify_otp(payload, _request())
    assert response["success"] is True
    assert response["data"]["activated_at_display"] == "22/05/2026 10:00"


@pytest.mark.asyncio
async def test_resend_otp_student_not_found(mock_db):
    payload = OTPResendRequest(email=TEST_EMAIL, purpose="activation")
    with pytest.raises(HTTPException) as exc:
        await auth_routes.resend_otp(payload, _request())
    assert exc.value.status_code == 404
    assert exc.value.detail["error"]["code"] == "STUDENT_NOT_FOUND"


@pytest.mark.asyncio
async def test_resend_otp_success(mock_db):
    await mock_db["students"].insert_one({"email": TEST_EMAIL, "full_name": TEST_NAME})
    payload = OTPResendRequest(email=TEST_EMAIL, purpose="activation")
    with (
        patch(
            "app.api.routes.student.auth.otp_service.create_otp",
            AsyncMock(return_value="111111"),
        ),
        patch(
            "app.api.routes.student.auth.email_service.send_otp_email",
            AsyncMock(),
        ),
    ):
        response = await auth_routes.resend_otp(payload, _request())
    assert response["success"] is True
    assert "otp_resend_available_at" in response["data"]


@pytest.mark.asyncio
async def test_login_route_passes_user_agent():
    payload = LoginRequest(email=TEST_EMAIL, password=TEST_PASSWORD)
    with patch(
        "app.api.routes.student.auth.auth_service.login_student",
        AsyncMock(return_value={"access_token": "tok", "token_type": "bearer", "student": {}}),
    ) as mock_login:
        await auth_routes.login(payload, _request(user_agent="MyBrowser/1.0"))
    mock_login.assert_called_once_with(
        email=TEST_EMAIL,
        password=TEST_PASSWORD,
        ip_address="127.0.0.1",
        user_agent="MyBrowser/1.0",
    )


@pytest.mark.asyncio
async def test_logout_route():
    student = {"_id": "id", "jti": "jti-1"}
    with patch(
        "app.api.routes.student.auth.auth_service.logout_student",
        AsyncMock(),
    ) as mock_logout:
        response = await auth_routes.logout(_request(), current_student=student)
    mock_logout.assert_called_once()
    assert response == {"success": True, "data": None}


@pytest.mark.asyncio
async def test_forgot_password_route():
    payload = ForgotPasswordRequest(email=TEST_EMAIL)
    with patch(
        "app.api.routes.student.auth.auth_service.request_forgot_password",
        AsyncMock(return_value={"success": True, "message": "ok"}),
    ):
        response = await auth_routes.forgot_password(payload, _request())
    assert response["success"] is True


@pytest.mark.asyncio
async def test_forgot_password_verify_route():
    payload = ForgotPasswordVerifyRequest(email=TEST_EMAIL, otp="111111")
    with patch(
        "app.api.routes.student.auth.auth_service.verify_forgot_password_otp",
        AsyncMock(return_value="reset-jwt"),
    ):
        response = await auth_routes.forgot_password_verify(payload, _request())
    assert response["data"]["reset_token"] == "reset-jwt"


@pytest.mark.asyncio
async def test_forgot_password_reset_route():
    payload = ResetPasswordRequest(
        email=TEST_EMAIL,
        reset_token="token",
        password=TEST_PASSWORD,
        password_confirm=TEST_PASSWORD,
    )
    with patch(
        "app.api.routes.student.auth.auth_service.reset_password_with_token",
        AsyncMock(),
    ):
        response = await auth_routes.forgot_password_reset(payload, _request())
    assert response["data"]["message"] == "Đặt lại mật khẩu thành công."
