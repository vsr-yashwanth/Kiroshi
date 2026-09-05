from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field
from backend.app.domain.models.enums import CameraStatus, InvestigationStatus
from ml.interfaces import DetectionResult


class CameraCreate(BaseModel):
    name: str = Field(..., max_length=100)
    description: Optional[str] = Field(None, max_length=255)
    latitude: float = Field(..., ge=-90.0, le=90.0)
    longitude: float = Field(..., ge=-180.0, le=180.0)
    coverage_radius_meters: float = Field(default=50.0, gt=0.0)
    is_simulated: bool = True
    stream_url: Optional[str] = None
    camera_metadata: Dict[str, Any] = Field(default_factory=dict)


class CameraResponse(BaseModel):
    id: uuid.UUID
    name: str
    description: Optional[str] = None
    status: CameraStatus
    latitude: float
    longitude: float
    coverage_radius_meters: float
    is_simulated: bool
    stream_url: Optional[str] = None
    distance_meters: Optional[float] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CCTVInvestigationRequest(BaseModel):
    incident_id: uuid.UUID
    search_radius_meters: float = Field(default=200.0, ge=10.0, le=2000.0, description="Spatial search radius in meters")
    time_window_minutes_before: float = Field(default=5.0, ge=1.0, le=60.0, description="Time window prior to incident")
    time_window_minutes_after: float = Field(default=5.0, ge=1.0, le=60.0, description="Time window after incident")


class CCTVInvestigationResponse(BaseModel):
    id: uuid.UUID
    incident_id: uuid.UUID
    requested_by: uuid.UUID
    status: InvestigationStatus
    search_radius_meters: float
    time_window_start: datetime
    time_window_end: datetime
    cameras_queried_count: int
    cameras_queried: List[str]
    detection_results: List[Dict[str, Any]]
    summary: Optional[str] = None
    investigation_metadata: Dict[str, Any]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
