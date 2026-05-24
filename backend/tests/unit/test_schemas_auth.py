import pytest
from pydantic import ValidationError

from app.schemas.auth import (
    ForgotPasswordRequest,
    LoginRequest,
    OTPResendRequest,
    OTPVerifyRequest,
    ResetPasswordRequest,
    StudentRegisterRequest,
    validate_student_email,
)

pytestmark = pytest.mark.unit

VALID_EMAIL = "4901104172@student.hcmue.edu.vn"


def test_validate_student_email_normalizes_and_accepts_valid():
    assert validate_student_email(" 4901104172@STUDENT.HCMUE.EDU.VN ") == VALID_EMAIL


@pytest.mark.parametrize(
    "email",
    [
        "490110417@gmail.com",
        "490110417@student.hcmue.edu.vn",
        "abc@student.hcmue.edu.vn",
    ],
)
def test_validate_student_email_rejects_invalid(email: str):
    with pytest.raises(ValueError):
        validate_student_email(email)


def test_student_register_request_valid():
    req = StudentRegisterRequest(
        email=VALID_EMAIL,
        password="password123",
        password_confirm="password123",
        full_name="Nguyễn Văn A",
        accept_terms=True,
    )
    assert req.full_name == "Nguyễn Văn A"


def test_student_register_password_mismatch():
    with pytest.raises(ValidationError):
        StudentRegisterRequest(
            email=VALID_EMAIL,
            password="password123",
            password_confirm="different",
            full_name="Nguyễn Văn A",
            accept_terms=True,
        )


def test_student_register_requires_terms():
    with pytest.raises(ValidationError):
        StudentRegisterRequest(
            email=VALID_EMAIL,
            password="password123",
            password_confirm="password123",
            full_name="Nguyễn Văn A",
            accept_terms=False,
        )


def test_otp_verify_request_validates_otp_digits():
    with pytest.raises(ValidationError):
        OTPVerifyRequest(email=VALID_EMAIL, otp="12345", purpose="activation")


def test_otp_verify_request_rejects_invalid_purpose():
    with pytest.raises(ValidationError):
        OTPVerifyRequest(email=VALID_EMAIL, otp="123456", purpose="invalid")


def test_login_request_accepts_valid_email():
    req = LoginRequest(email=VALID_EMAIL, password="x")
    assert req.email == VALID_EMAIL


def test_reset_password_request_validates_confirm():
    with pytest.raises(ValidationError):
        ResetPasswordRequest(
            email=VALID_EMAIL,
            reset_token="token",
            password="newpassword1",
            password_confirm="other",
        )


def test_forgot_password_and_otp_resend_schemas():
    assert ForgotPasswordRequest(email=VALID_EMAIL).email == VALID_EMAIL
    assert OTPResendRequest(email=VALID_EMAIL, purpose="password_reset").purpose == "password_reset"
