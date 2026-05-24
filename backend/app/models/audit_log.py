from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from app.models.student import PyObjectId


class AuditLogModel(BaseModel):
    id: Optional[PyObjectId] = Field(default=None, alias="_id")
    event_code: str
    occurred_at: datetime = Field(default_factory=datetime.utcnow)
    actor_role: str
    actor_id: Optional[PyObjectId] = None
    object_type: str
    object_id: Optional[str] = None
    result: str
    description: str
    ip_address: str

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
