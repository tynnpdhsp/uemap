from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field
from app.models.student import PyObjectId

class CommentModel(BaseModel):
    id: Optional[PyObjectId] = Field(default=None, alias="_id")
    place_id: PyObjectId
    place_public_id: int
    student_id: PyObjectId
    author_display_name: str
    content: str
    status: str = "visible"
    deleted_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
