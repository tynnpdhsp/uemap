from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field
from app.models.student import PyObjectId


class StudentSessionModel(BaseModel):
    id: Optional[PyObjectId] = Field(default=None, alias="_id")
    student_id: PyObjectId
    jti: str
    expires_at: datetime
    revoked_at: Optional[datetime] = None
    ip_address: str
    user_agent: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
