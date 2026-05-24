from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field
from app.models.student import PyObjectId

class CategoryModel(BaseModel):
    id: Optional[PyObjectId] = Field(default=None, alias="_id")
    name: str
    color: str
    order: int = 0
    description: Optional[str] = None
    icon_url: Optional[str] = None
    is_hidden: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
