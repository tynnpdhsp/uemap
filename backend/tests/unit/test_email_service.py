from unittest.mock import AsyncMock, patch

import pytest

from app.core.config import settings
from app.services import email_service

pytestmark = pytest.mark.unit


@pytest.mark.asyncio
async def test_send_otp_email_dev_mode_prints_without_smtp(capsys):
    original_env = settings.ENV
    original_user = settings.SMTP_USER
    original_pass = settings.SMTP_PASSWORD
    settings.ENV = "dev"
    settings.SMTP_USER = ""
    settings.SMTP_PASSWORD = ""
    try:
        await email_service.send_otp_email(
            "4901104172@student.hcmue.edu.vn",
            "Nguyễn Văn A",
            "123456",
            "activation",
        )
        captured = capsys.readouterr()
        assert "123456" in captured.out
        assert "kích hoạt" in captured.out.lower() or "kich hoat" in captured.out.lower()
    finally:
        settings.ENV = original_env
        settings.SMTP_USER = original_user
        settings.SMTP_PASSWORD = original_pass


@pytest.mark.asyncio
@patch("app.services.email_service.aiosmtplib.send", new_callable=AsyncMock)
async def test_send_otp_email_activation_subject(mock_send):
    original_env = settings.ENV
    original_user = settings.SMTP_USER
    original_pass = settings.SMTP_PASSWORD
    settings.ENV = "prod"
    settings.SMTP_USER = "user@test.com"
    settings.SMTP_PASSWORD = "secret"
    try:
        await email_service.send_otp_email(
            "4901104172@student.hcmue.edu.vn",
            "Nguyễn Văn A",
            "123456",
            "activation",
        )
        message = mock_send.call_args[0][0]
        assert message["Subject"] == "mã kích hoạt tài khoản bản đồ sinh viên sư phạm"
    finally:
        settings.ENV = original_env
        settings.SMTP_USER = original_user
        settings.SMTP_PASSWORD = original_pass


@pytest.mark.asyncio
@patch("app.services.email_service.aiosmtplib.send", new_callable=AsyncMock)
async def test_send_otp_email_password_reset_subject(mock_send):
    original_env = settings.ENV
    original_user = settings.SMTP_USER
    original_pass = settings.SMTP_PASSWORD
    settings.ENV = "prod"
    settings.SMTP_USER = "user@test.com"
    settings.SMTP_PASSWORD = "secret"
    try:
        await email_service.send_otp_email(
            "4901104172@student.hcmue.edu.vn",
            "Nguyễn Văn A",
            "654321",
            "password_reset",
        )
        mock_send.assert_called_once()
        message = mock_send.call_args[0][0]
        assert message["Subject"] == "mã đặt lại mật khẩu bản đồ sinh viên sư phạm"
    finally:
        settings.ENV = original_env
        settings.SMTP_USER = original_user
        settings.SMTP_PASSWORD = original_pass
