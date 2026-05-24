from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field
from app.models.student import PyObjectId

class GeoJSONPoint(BaseModel):
    type: str = "Point"
    coordinates: List[float]

class PlaceImage(BaseModel):
    object_key: str
    sort_order: int = 0
    mime: str

class PlaceVideo(BaseModel):
    kind: str
    object_key: Optional[str] = None
    mime: Optional[str] = None
    url: Optional[str] = None

class PlaceModel(BaseModel):
    id: Optional[PyObjectId] = Field(default=None, alias="_id")
    public_id: int
    creator_student_id: PyObjectId
    category_id: PyObjectId
    scope_type: str
    name: str
    description: str
    address: str
    location: GeoJSONPoint
    hours: Optional[str] = None
    contact: Optional[str] = None
    status: str = "draft"
    hidden_note: Optional[str] = None
    images: List[PlaceImage] = Field(default_factory=list)
    video: Optional[PlaceVideo] = None
    published_at: Optional[datetime] = None
    deleted_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
