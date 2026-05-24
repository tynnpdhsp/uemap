from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class AdminLoginRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=8, max_length=128)


class AdminLoginResponse(BaseModel):
    access_token: str
    admin: dict


class AdminInfoResponse(BaseModel):
    id: str
    username: str
    display_name: str
    is_system_admin: bool
    status: str
    status_label: str
    last_login_at: Optional[datetime] = None
    created_at: datetime


class AdminCreateRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=50, pattern=r"^[a-z0-9_]+$")
    password: str = Field(..., min_length=8, max_length=128)
    display_name: str = Field(..., min_length=2, max_length=100)


class AdminUpdateRequest(BaseModel):
    display_name: Optional[str] = Field(default=None, min_length=2, max_length=100)
    password: Optional[str] = Field(default=None, min_length=8, max_length=128)
