import uuid
from datetime import datetime
from typing import List, Optional, Any, Dict
from pydantic import BaseModel, ConfigDict

from backend.app.domain.models.enums import RiskLevel, RecommendedAction


class RiskSignalDetail(BaseModel):
    signal_type: str
    score: float
    weight: float
    contribution: float
    raw_value: Any
    unit: str
    description: str

    model_config = ConfigDict(from_attributes=True)


class RiskAssessmentResponse(BaseModel):
    id: uuid.UUID
    tourist_id: uuid.UUID
    trip_id: uuid.UUID
    location_event_id: Optional[uuid.UUID] = None
    risk_score: float
    risk_level: RiskLevel
    confidence: float
    contributing_signals: List[Dict[str, Any]]
    explanation: str
    recommended_action: RecommendedAction
    model_version: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class LiveTouristRiskSnapshot(BaseModel):
    tourist_id: uuid.UUID
    tourist_name: str
    trip_id: uuid.UUID
    trip_title: str
    risk_score: float
    risk_level: RiskLevel
    confidence: float
    explanation: str
    recommended_action: RecommendedAction
    model_version: str
    assessed_at: datetime

    model_config = ConfigDict(from_attributes=True)
