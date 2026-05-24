from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field
from app.models.student import PyObjectId


class AdminModel(BaseModel):
    id: Optional[PyObjectId] = Field(default=None, alias="_id")
    username: str
    password_hash: str
    display_name: str
    is_system_admin: bool = False
    status: str = "active"
    last_login_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
