from unittest.mock import AsyncMock, patch

import pytest

from app.services import email_service

pytestmark = pytest.mark.unit

SETTINGS_TARGET = "app.services.email_service.settings"


@pytest.mark.asyncio
async def test_send_otp_email_dev_mode_prints_without_smtp(capsys):
    with patch.multiple(
        SETTINGS_TARGET,
        ENV="dev",
        SMTP_USER="",
        SMTP_PASSWORD="",
    ):
        await email_service.send_otp_email(
            "4901104172@student.hcmue.edu.vn",
            "Nguyễn Văn A",
            "123456",
            "activation",
        )
    captured = capsys.readouterr()
    assert "123456" in captured.out
    assert "kích hoạt" in captured.out.lower() or "kich hoat" in captured.out.lower()


@pytest.mark.asyncio
@patch("app.services.email_service.aiosmtplib.send", new_callable=AsyncMock)
async def test_send_otp_email_activation_subject(mock_send):
    with patch.multiple(
        SETTINGS_TARGET,
        ENV="prod",
        SMTP_USER="user@test.com",
        SMTP_PASSWORD="secret",
        SMTP_FROM_EMAIL="noreply@test.com",
    ):
        await email_service.send_otp_email(
            "4901104172@student.hcmue.edu.vn",
            "Nguyễn Văn A",
            "123456",
            "activation",
        )
    mock_send.assert_called_once()
    message = mock_send.call_args[0][0]
    assert message["Subject"] == "mã kích hoạt tài khoản bản đồ sinh viên sư phạm"


@pytest.mark.asyncio
@patch("app.services.email_service.aiosmtplib.send", new_callable=AsyncMock)
async def test_send_otp_email_password_reset_subject(mock_send):
    with patch.multiple(
        SETTINGS_TARGET,
        ENV="prod",
        SMTP_USER="user@test.com",
        SMTP_PASSWORD="secret",
        SMTP_FROM_EMAIL="noreply@test.com",
    ):
        await email_service.send_otp_email(
            "4901104172@student.hcmue.edu.vn",
            "Nguyễn Văn A",
            "654321",
            "password_reset",
        )
    mock_send.assert_called_once()
    message = mock_send.call_args[0][0]
    assert message["Subject"] == "mã đặt lại mật khẩu bản đồ sinh viên sư phạm"
