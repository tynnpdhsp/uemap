from datetime import datetime
from typing import Annotated, Optional

from bson import ObjectId
from pydantic import BaseModel, BeforeValidator, Field, PlainSerializer

PyObjectId = Annotated[
    ObjectId,
    BeforeValidator(lambda x: ObjectId(x) if ObjectId.is_valid(x) else x),
    PlainSerializer(lambda x: str(x), return_type=str),
]


class StudentModel(BaseModel):
    id: Optional[PyObjectId] = Field(default=None, alias="_id")
    email: str
    password_hash: str
    full_name: str
    status: str = "pending_activation"
    locked_reason: Optional[str] = None
    activated_at: Optional[datetime] = None
    otp_locked_until: Optional[datetime] = None
    failed_otp_attempts: int = 0
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
