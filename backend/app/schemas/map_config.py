from typing import Optional

from pydantic import BaseModel


class MapBoundsPointSchema(BaseModel):
    lat: float
    lng: float


class MapBoundsSchema(BaseModel):
    sw: MapBoundsPointSchema
    ne: MapBoundsPointSchema


class MapGeofenceSchema(BaseModel):
    type: str
    bounds: Optional[MapBoundsSchema] = None
    center: Optional[MapBoundsPointSchema] = None
    radius_meters: Optional[float] = None


class AppConfigResponse(BaseModel):
    default_center: MapBoundsPointSchema
    default_zoom: int
    geofence: MapGeofenceSchema
    cluster_zoom_threshold: int
