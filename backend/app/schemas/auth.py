import re
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, field_validator, model_validator


def validate_student_email(email: str) -> str:
    email = email.strip().lower()
    if not re.match(r"^[0-9]{10}@student\.hcmue\.edu\.vn$", email):
        raise ValueError("Email phải đúng định dạng mã số sinh viên 10 chữ số @student.hcmue.edu.vn")
    return email


class StudentRegisterRequest(BaseModel):
    email: str
    password: str = Field(..., min_length=8, max_length=128)
    password_confirm: str
    full_name: str = Field(..., min_length=5, max_length=100)
    accept_terms: bool

    @field_validator("email")
    @classmethod
    def check_email(cls, v: str) -> str:
        return validate_student_email(v)

    @field_validator("full_name")
    @classmethod
    def clean_name(cls, v: str) -> str:
        return " ".join(v.split())

    @model_validator(mode="after")
    def verify_passwords(self) -> "StudentRegisterRequest":
        if self.password != self.password_confirm:
            raise ValueError("Mật khẩu xác nhận không khớp")
        if not self.accept_terms:
            raise ValueError("Bạn phải đồng ý với điều khoản dịch vụ")
        return self


class StudentRegisterResponse(BaseModel):
    email: str
    status: str
    otp_resend_available_at: datetime


class OTPVerifyRequest(BaseModel):
    email: str
    otp: str
    purpose: str

    @field_validator("email")
    @classmethod
    def check_email(cls, v: str) -> str:
        return validate_student_email(v)

    @field_validator("otp")
    @classmethod
    def check_otp(cls, v: str) -> str:
        v = v.strip()
        if not re.match(r"^\d{6}$", v):
            raise ValueError("Mã OTP phải gồm đúng 6 chữ số")
        return v

    @field_validator("purpose")
    @classmethod
    def check_purpose(cls, v: str) -> str:
        if v not in ("activation", "password_reset"):
            raise ValueError("Mục đích OTP không hợp lệ")
        return v


class OTPResendRequest(BaseModel):
    email: str
    purpose: str

    @field_validator("email")
    @classmethod
    def check_email(cls, v: str) -> str:
        return validate_student_email(v)

    @field_validator("purpose")
    @classmethod
    def check_purpose(cls, v: str) -> str:
        if v not in ("activation", "password_reset"):
            raise ValueError("Mục đích OTP không hợp lệ")
        return v


class LoginRequest(BaseModel):
    email: str
    password: str

    @field_validator("email")
    @classmethod
    def check_email(cls, v: str) -> str:
        return validate_student_email(v)


class StudentProfileShort(BaseModel):
    email: str
    full_name: str
    status: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    student: StudentProfileShort


class ForgotPasswordRequest(BaseModel):
    email: str

    @field_validator("email")
    @classmethod
    def check_email(cls, v: str) -> str:
        return validate_student_email(v)


class ForgotPasswordVerifyRequest(BaseModel):
    email: str
    otp: str

    @field_validator("email")
    @classmethod
    def check_email(cls, v: str) -> str:
        return validate_student_email(v)

    @field_validator("otp")
    @classmethod
    def check_otp(cls, v: str) -> str:
        if not re.match(r"^\d{6}$", v):
            raise ValueError("Mã OTP phải gồm đúng 6 chữ số")
        return v


class ForgotPasswordVerifyResponse(BaseModel):
    reset_token: str


class ResetPasswordRequest(BaseModel):
    email: str
    reset_token: str
    password: str = Field(..., min_length=8, max_length=128)
    password_confirm: str

    @field_validator("email")
    @classmethod
    def check_email(cls, v: str) -> str:
        return validate_student_email(v)

    @model_validator(mode="after")
    def verify_passwords(self) -> "ResetPasswordRequest":
        if self.password != self.password_confirm:
            raise ValueError("Mật khẩu xác nhận không khớp")
        return self
