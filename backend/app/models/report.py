from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field
from app.models.student import PyObjectId

class ReportModel(BaseModel):
    id: Optional[PyObjectId] = Field(default=None, alias="_id")
    report_code: str
    reporter_student_id: PyObjectId
    target_type: str
    target_place_id: Optional[PyObjectId] = None
    target_comment_id: Optional[PyObjectId] = None
    place_public_id: int
    report_type: str
    reason: str
    status: str = "new"
    admin_note: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    resolved_at: Optional[datetime] = None

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
