from typing import Optional
from pydantic import BaseModel, Field, field_validator, model_validator


class StudentProfileResponse(BaseModel):
    email: str
    full_name: str
    status: str
    status_label: str
    activated_at_display: Optional[str] = None
    locked_reason: Optional[str] = None


class StudentProfileUpdateRequest(BaseModel):
    full_name: str = Field(..., min_length=5, max_length=100)

    @field_validator("full_name")
    @classmethod
    def clean_name(cls, v: str) -> str:
        return " ".join(v.split())


class ChangePasswordRequest(BaseModel):
    current_password: str
    password: str = Field(..., min_length=8, max_length=128)
    password_confirm: str

    @model_validator(mode="after")
    def verify_passwords(self) -> "ChangePasswordRequest":
        if self.password != self.password_confirm:
            raise ValueError("Mật khẩu xác nhận không khớp")
        return self
