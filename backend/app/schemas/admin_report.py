from typing import Optional
from pydantic import BaseModel, Field


class AdminReportUpdateRequest(BaseModel):
    status: str = Field(..., pattern=r"^(in_progress|resolved)$")
    admin_note: Optional[str] = Field(default=None, min_length=10, max_length=500)


class AdminReportActionRequest(BaseModel):
    action: str = Field(..., pattern=r"^(hide_place|soft_delete_place|soft_delete_comment)$")
    reason: str = Field(..., min_length=10, max_length=500)
