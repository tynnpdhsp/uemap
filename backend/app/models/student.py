from datetime import datetime
from typing import Any, Optional, Annotated
from bson import ObjectId
from pydantic import BaseModel, Field, GetCoreSchemaHandler
from pydantic_core import core_schema


class PyObjectId(ObjectId):
    @classmethod
    def __get_pydantic_core_schema__(
        cls, source_type: Any, handler: GetCoreSchemaHandler
    ) -> core_schema.CoreSchema:
        return core_schema.json_or_python_schema(
            json_schema=core_schema.str_schema(),
            python_schema=core_schema.is_instance_schema(ObjectId),
            serialization=core_schema.plain_serializer_function_broker(
                lambda val: str(val)
            ),
        )


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
