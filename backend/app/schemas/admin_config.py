from typing import Optional
from pydantic import BaseModel, Field


class MapCenterSchema(BaseModel):
    lat: float
    lng: float


class MapBoundsSchema(BaseModel):
    sw: MapCenterSchema
    ne: MapCenterSchema


class GeofenceSchema(BaseModel):
    type: str = Field(..., pattern=r"^(rectangle|radius)$")
    bounds: Optional[MapBoundsSchema] = None
    center: Optional[MapCenterSchema] = None
    radius_meters: Optional[float] = Field(default=None, gt=0)


class AdminMapConfigUpdateRequest(BaseModel):
    default_center: Optional[MapCenterSchema] = None
    default_zoom: Optional[int] = Field(default=None, ge=1, le=22)
    geofence: Optional[GeofenceSchema] = None
    cluster_zoom_threshold: Optional[int] = Field(default=None, ge=1, le=22)


class EmailTemplateItemSchema(BaseModel):
    subject: str = Field(..., min_length=1)
    html_body: str = Field(..., min_length=1)
    text_body: str = Field(..., min_length=1)


class AdminEmailTemplatesUpdateRequest(BaseModel):
    activation: Optional[EmailTemplateItemSchema] = None
    password_reset: Optional[EmailTemplateItemSchema] = None


class AdminEmailTestRequest(BaseModel):
    to_email: str = Field(..., min_length=5)
    template_type: str = Field(..., pattern=r"^(activation|password_reset)$")
