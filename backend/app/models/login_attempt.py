from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from app.models.student import PyObjectId


class LoginAttemptModel(BaseModel):
    id: Optional[PyObjectId] = Field(default=None, alias="_id")
    email: str
    ip_address: str
    failed_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
