from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field

class MapBoundsPoint(BaseModel):
    lat: float
    lng: float

class MapBounds(BaseModel):
    sw: MapBoundsPoint
    ne: MapBoundsPoint

class MapGeofence(BaseModel):
    type: str
    bounds: Optional[MapBounds] = None
    center: Optional[MapBoundsPoint] = None
    radius_meters: Optional[float] = None

class AppConfigModel(BaseModel):
    id: str = Field(default="map", alias="_id")
    default_center: MapBoundsPoint
    default_zoom: int
    geofence: MapGeofence
    cluster_zoom_threshold: int = 14
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
