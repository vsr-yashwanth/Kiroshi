import uuid
from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict

from backend.app.domain.models.enums import SyncEventType, SyncEventStatus


class SyncEventItem(BaseModel):
    local_event_id: str = Field(
        ...,
        min_length=1,
        max_length=128,
        description="Client-generated unique event ID / idempotency key",
    )
    event_type: SyncEventType = Field(
        ...,
        description="Type of offline event (SOS_EVENT, LOCATION_EVENT, TRIP_UPDATE, INCIDENT_ACTION)",
    )
    timestamp: datetime = Field(
        ...,
        description="Hardware or application timestamp when the event was generated offline",
    )
    payload: Dict[str, Any] = Field(
        default_factory=dict,
        description="Event specific payload data",
    )
    retry_count: int = Field(
        default=0,
        ge=0,
        description="Number of sync transmission retries attempted by client",
    )


class SyncBatchRequest(BaseModel):
    events: List[SyncEventItem] = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Batch of chronological offline events to synchronize",
    )


class SyncEventResult(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    local_event_id: str
    status: SyncEventStatus
    server_id: Optional[uuid.UUID] = None
    message: Optional[str] = None
    server_timestamp: datetime
    conflict_details: Optional[Dict[str, Any]] = None


class SyncBatchResponse(BaseModel):
    results: List[SyncEventResult]
    synced_count: int
    duplicate_count: int
    failed_count: int
