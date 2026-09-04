import uuid
from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, ConfigDict, Field

from backend.app.domain.models.enums import (
    IncidentSource,
    IncidentSeverity,
    IncidentStatus,
    IncidentEventType,
    AssignmentStatus,
    LocationFreshness,
)


class SOSCreateRequest(BaseModel):
    trip_id: Optional[uuid.UUID] = Field(None, description="Optional active trip ID")
    latitude: Optional[float] = Field(None, ge=-90.0, le=90.0, description="Client GPS latitude")
    longitude: Optional[float] = Field(None, ge=-180.0, le=180.0, description="Client GPS longitude")
    accuracy: Optional[float] = Field(None, ge=0.0, description="GPS accuracy in meters")
    description: Optional[str] = Field(None, description="Optional emergency description")
    idempotency_key: Optional[str] = Field(None, max_length=128, description="Client idempotency key to prevent duplicate SOS triggers")


class IncidentTransitionRequest(BaseModel):
    to_status: IncidentStatus = Field(..., description="Target lifecycle state")
    reason: Optional[str] = Field(None, description="Operational reason or context for transition")
    resolution_notes: Optional[str] = Field(None, description="Resolution notes required when resolving")


class IncidentAssignRequest(BaseModel):
    responder_id: uuid.UUID = Field(..., description="User ID of the responder to assign")
    notes: Optional[str] = Field(None, description="Operational instructions or dispatch notes")


class IncidentEventResponse(BaseModel):
    id: uuid.UUID
    incident_id: uuid.UUID
    actor_id: Optional[uuid.UUID] = None
    actor_name: Optional[str] = None
    actor_role: Optional[str] = None
    event_type: IncidentEventType
    from_status: Optional[IncidentStatus] = None
    to_status: Optional[IncidentStatus] = None
    reason: Optional[str] = None
    details: Optional[Dict[str, Any]] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class IncidentAssignmentResponse(BaseModel):
    id: uuid.UUID
    responder_id: uuid.UUID
    responder_name: Optional[str] = None
    assigned_by_id: uuid.UUID
    assigned_by_name: Optional[str] = None
    assigned_at: datetime
    unassigned_at: Optional[datetime] = None
    status: AssignmentStatus
    notes: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class IncidentResponse(BaseModel):
    id: uuid.UUID
    source: IncidentSource
    severity: IncidentSeverity
    status: IncidentStatus
    tourist_id: uuid.UUID
    tourist_name: Optional[str] = None
    trip_id: Optional[uuid.UUID] = None
    trip_title: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    accuracy: Optional[float] = None
    location_freshness: LocationFreshness
    description: Optional[str] = None
    risk_assessment_id: Optional[uuid.UUID] = None
    assigned_responder_id: Optional[uuid.UUID] = None
    assigned_responder_name: Optional[str] = None
    idempotency_key: Optional[str] = None
    resolution_notes: Optional[str] = None
    resolved_at: Optional[datetime] = None
    closed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ResponderUserResponse(BaseModel):
    id: uuid.UUID
    email: str
    full_name: str
    role: str
    is_active: bool

    model_config = ConfigDict(from_attributes=True)
