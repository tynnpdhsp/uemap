from typing import Optional
from pydantic import BaseModel, Field, field_validator

class ReportCreateRequest(BaseModel):
    target_type: str
    target_id: str
    report_type: str
    reason: str = Field(..., min_length=20, max_length=500)

    @field_validator("reason")
    @classmethod
    def clean_reason(cls, v: str) -> str:
        return " ".join(v.split())

class ReportCreateResponse(BaseModel):
    report_code: str
    status: str
    status_label: str
    created_at_display: str

class ReportMyResponseItem(BaseModel):
    report_code: str
    target_type: str
    target_summary: str
    report_type_label: str
    status_label: str
    created_at_display: str
