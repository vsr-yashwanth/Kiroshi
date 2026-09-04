import uuid
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict
from backend.app.domain.models.enums import TripStatus, EmergencyStatus
from backend.app.schemas.auth import UserResponse


class ItineraryBase(BaseModel):
    destination_name: str = Field(..., min_length=1, max_length=255)
    planned_arrival: Optional[datetime] = None
    planned_departure: Optional[datetime] = None
    latitude: float = Field(..., ge=-90.0, le=90.0)
    longitude: float = Field(..., ge=-180.0, le=180.0)
    sequence_order: int = Field(default=1, ge=1)


class ItineraryCreate(ItineraryBase):
    pass


class ItineraryResponse(ItineraryBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    trip_id: uuid.UUID
    created_at: datetime


class TripBase(BaseModel):
    title: str = Field(..., min_length=2, max_length=255)
    description: Optional[str] = None
    start_date: datetime
    end_date: datetime


class TripCreate(TripBase):
    itineraries: Optional[List[ItineraryCreate]] = Field(default_factory=list)


class TripUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=2, max_length=255)
    description: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    status: Optional[TripStatus] = None
    emergency_status: Optional[EmergencyStatus] = None


class TripResponse(TripBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    tourist_id: uuid.UUID
    status: TripStatus
    emergency_status: EmergencyStatus
    created_at: datetime
    updated_at: datetime
    tourist: Optional[UserResponse] = None
    itineraries: List[ItineraryResponse] = Field(default_factory=list)
