from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from app.models.student import PyObjectId


class OTPTokenModel(BaseModel):
    id: Optional[PyObjectId] = Field(default=None, alias="_id")
    email: str
    purpose: str
    otp_hash: str
    sent_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: datetime
    used_at: Optional[datetime] = None
    resend_available_at: datetime
    send_ip: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
