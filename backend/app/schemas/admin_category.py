from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class AdminCategoryCreateRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    color: str = Field(..., pattern=r"^#[0-9A-Fa-f]{6}$")
    order: int = Field(default=0, ge=0)
    description: Optional[str] = None
    icon_url: Optional[str] = None
    is_hidden: bool = False


class AdminCategoryUpdateRequest(BaseModel):
    name: Optional[str] = Field(default=None, min_length=2, max_length=100)
    color: Optional[str] = Field(default=None, pattern=r"^#[0-9A-Fa-f]{6}$")
    order: Optional[int] = Field(default=None, ge=0)
    description: Optional[str] = None
    icon_url: Optional[str] = None


class AdminCategoryHideRequest(BaseModel):
    is_hidden: bool


class AdminCategoryResponse(BaseModel):
    id: str
    name: str
    color: str
    order: int
    description: Optional[str] = None
    icon_url: Optional[str] = None
    is_hidden: bool
    place_count: int = 0
    created_at: datetime
    updated_at: datetime
