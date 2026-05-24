from typing import Optional
from pydantic import BaseModel, Field


class AdminPlaceHideRequest(BaseModel):
    hidden_note: str = Field(..., min_length=10, max_length=500)


class AdminPlaceTransferCreatorRequest(BaseModel):
    new_creator_student_id: str


class AdminPlaceUpdateRequest(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=200)
    description: Optional[str] = None
    address: Optional[str] = None
    category_id: Optional[str] = None
    hours: Optional[str] = None
    contact: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
