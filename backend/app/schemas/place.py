from typing import List, Optional

from pydantic import BaseModel, Field, field_validator


class GeoJSONPointSchema(BaseModel):
    type: str = "Point"
    coordinates: List[float]


class PlaceImageSchema(BaseModel):
    object_key: str
    url: Optional[str] = None
    sort_order: int = 0
    mime: str


class PlaceVideoSchema(BaseModel):
    kind: str
    object_key: Optional[str] = None
    mime: Optional[str] = None
    url: Optional[str] = None


class PlaceMarkerResponse(BaseModel):
    public_id: int
    name: str
    lat: float
    lng: float
    category_id: str
    category_color: str
    category_icon_url: Optional[str] = None
    address_short: str


class PlaceListResponseItem(BaseModel):
    public_id: int
    name: str
    category_name: str
    address_short: str
    updated_at_display: str


class PlaceDetailResponse(BaseModel):
    public_id: int
    creator_student_id: str
    creator_student_name: str
    category_id: str
    category_name: str
    scope_type: str
    scope_label: str
    name: str
    description: str
    address: str
    location: GeoJSONPointSchema
    hours: Optional[str] = None
    contact: Optional[str] = None
    images: List[PlaceImageSchema]
    video: Optional[PlaceVideoSchema] = None
    updated_at_display: str


class PlaceCreateRequest(BaseModel):
    name: str = Field(..., min_length=5, max_length=200)
    category_id: Optional[str] = None
    scope_type: Optional[str] = None
    description: Optional[str] = Field(None, max_length=5000)
    address: Optional[str] = Field(None, max_length=500)
    lat: Optional[float] = None
    lng: Optional[float] = None
    hours: Optional[str] = None
    contact: Optional[str] = None
    image_object_keys: List[str] = Field(default_factory=list)
    video: Optional[PlaceVideoSchema] = None
    status: str = "draft"
    publish: bool = False

    @field_validator("name")
    @classmethod
    def clean_name(cls, v: str) -> str:
        return " ".join(v.split())

    @field_validator("description", "address")
    @classmethod
    def clean_optional_text(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        return " ".join(v.split())


class PlaceCreateResponse(BaseModel):
    public_id: int
    status: str
    status_label: str
