from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field

from backend.app.domain.models.enums import AuditEventType, AuditOutcome


class AuditEventResponse(BaseModel):
    id: uuid.UUID
    sequence_number: int
    event_type: AuditEventType
    actor_id: Optional[uuid.UUID] = None
    actor_email: Optional[str] = None
    actor_role: Optional[str] = None
    client_ip: Optional[str] = None
    user_agent: Optional[str] = None
    resource_type: str
    resource_id: Optional[str] = None
    action: str
    outcome: AuditOutcome
    details: Dict[str, Any]
    previous_hash: str
    event_hash: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AuditEventListResponse(BaseModel):
    total: int
    events: List[AuditEventResponse]


class AuditChainVerificationResponse(BaseModel):
    status: str
    is_valid: bool
    total_events_verified: int
    broken_sequence_number: Optional[int] = None
    expected_hash: Optional[str] = None
    actual_hash: Optional[str] = None
    reason: Optional[str] = None


class AuditExportRequest(BaseModel):
    format: str = Field("json", description="Export format: json or csv")
    reason: str = Field(..., min_length=5, max_length=255, description="Audited operational reason for data export")
    event_type: Optional[AuditEventType] = None


class AuditExportResponse(BaseModel):
    total_exported: int
    format: str
    exported_at: datetime
    integrity_verified: bool
    data: List[Dict[str, Any]]
