import uuid
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict, field_validator
from backend.app.domain.models.enums import GeoZoneType, ZoneEventType


class GeoZoneCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    zone_type: GeoZoneType = GeoZoneType.SAFE
    coordinates: List[List[float]] = Field(
        ...,
        min_length=4,
        description="Linear ring coordinates [[lng, lat], ...] with at least 4 points where first and last match",
    )

    @field_validator("coordinates")
    @classmethod
    def validate_polygon_ring(cls, coords: List[List[float]]) -> List[List[float]]:
        if len(coords) < 4:
            raise ValueError("Polygon linear ring must contain at least 4 coordinate vertices.")
        for pt in coords:
            if len(pt) != 2:
                raise ValueError(f"Each coordinate pair must be [longitude, latitude], got {pt}")
            lng, lat = pt[0], pt[1]
            if not (-180.0 <= lng <= 180.0):
                raise ValueError(f"Longitude must be between -180 and 180, got {lng}")
            if not (-90.0 <= lat <= 90.0):
                raise ValueError(f"Latitude must be between -90 and 90, got {lat}")
        # Ensure polygon ring is closed (first point equals last point)
        if coords[0] != coords[-1]:
            coords.append(coords[0])
        return coords


class GeoZoneResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    description: Optional[str] = None
    zone_type: GeoZoneType
    coordinates: List[List[float]]
    is_active: bool
    created_at: datetime
    updated_at: datetime


class ZoneEventResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    tourist_id: uuid.UUID
    trip_id: uuid.UUID
    zone_id: uuid.UUID
    zone_name: Optional[str] = None
    zone_type: Optional[GeoZoneType] = None
    event_type: ZoneEventType
    location_event_id: Optional[uuid.UUID] = None
    occurred_at: datetime
