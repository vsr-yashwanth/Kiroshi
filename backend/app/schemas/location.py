import uuid
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict
from backend.app.domain.models.enums import LocationFreshness


class LocationIngestRequest(BaseModel):
    trip_id: uuid.UUID
    latitude: float = Field(..., ge=-90.0, le=90.0, description="Latitude in decimal degrees")
    longitude: float = Field(..., ge=-180.0, le=180.0, description="Longitude in decimal degrees")
    accuracy: float = Field(..., gt=0.0, le=5000.0, description="Horizontal accuracy radius in meters")
    altitude: Optional[float] = Field(None, description="Altitude in meters above WGS 84 reference ellipsoid")
    speed: Optional[float] = Field(None, ge=0.0, description="Instantaneous ground speed in meters per second")
    heading: Optional[float] = Field(None, ge=0.0, lt=360.0, description="Direction of travel in degrees clockwise from true north")
    recorded_at: datetime = Field(..., description="Timestamp recorded by client hardware GPS clock")


class LocationEventResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    tourist_id: uuid.UUID
    trip_id: uuid.UUID
    latitude: float
    longitude: float
    accuracy: float
    altitude: Optional[float] = None
    speed: Optional[float] = None
    heading: Optional[float] = None
    freshness: LocationFreshness = LocationFreshness.UNKNOWN
    risk_level: Optional[str] = None
    risk_score: Optional[float] = None
    recorded_at: datetime
    received_at: datetime
    created_at: datetime


class LiveTouristPosition(BaseModel):
    tourist_id: uuid.UUID
    tourist_name: str
    trip_id: uuid.UUID
    trip_title: str
    latitude: float
    longitude: float
    accuracy: float
    altitude: Optional[float] = None
    speed: Optional[float] = None
    heading: Optional[float] = None
    freshness: LocationFreshness
    risk_level: Optional[str] = None
    risk_score: Optional[float] = None
    recorded_at: datetime
    received_at: datetime
    active_zones: List[str] = Field(default_factory=list)
