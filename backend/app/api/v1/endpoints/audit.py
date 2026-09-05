from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Optional, List
from fastapi import APIRouter, Depends, Query, status, HTTPException
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.api.deps import require_role
from backend.app.domain.models.user import User
from backend.app.domain.models.enums import UserRole, AuditEventType, AuditOutcome
from backend.app.services.audit_service import AuditService
from backend.app.schemas.audit import (
    AuditEventResponse,
    AuditEventListResponse,
    AuditChainVerificationResponse,
    AuditExportRequest,
    AuditExportResponse,
)

router = APIRouter()


@router.get(
    "/events",
    response_model=AuditEventListResponse,
    summary="Query tamper-evident audit events (Authority/Admin only)",
    description="Retrieves chronological audit events with cryptographic hash chains. Restricted strictly to Authority and Admin roles.",
)
def list_audit_events(
    event_type: Optional[AuditEventType] = Query(None, description="Filter by event type"),
    actor_id: Optional[uuid.UUID] = Query(None, description="Filter by actor user ID"),
    resource_type: Optional[str] = Query(None, description="Filter by resource type"),
    resource_id: Optional[str] = Query(None, description="Filter by resource ID"),
    outcome: Optional[AuditOutcome] = Query(None, description="Filter by outcome"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    current_user: User = Depends(require_role(UserRole.AUTHORITY, UserRole.ADMIN)),
    db: Session = Depends(get_db),
):
    audit_service = AuditService(db)
    events, total = audit_service.list_events(
        event_type=event_type,
        actor_id=actor_id,
        resource_type=resource_type,
        resource_id=resource_id,
        outcome=outcome,
        skip=skip,
        limit=limit,
    )
    return AuditEventListResponse(
        total=total,
        events=[AuditEventResponse.model_validate(e) for e in events],
    )


@router.post(
    "/verify",
    response_model=AuditChainVerificationResponse,
    summary="Cryptographically verify audit log integrity (Authority/Admin only)",
    description="Sequentially verifies hash chain pointers, SHA-256 signatures, and sequence continuity to detect any tampering, modification, reordering, or deletion.",
)
def verify_audit_chain(
    current_user: User = Depends(require_role(UserRole.AUTHORITY, UserRole.ADMIN)),
    db: Session = Depends(get_db),
):
    audit_service = AuditService(db)
    result = audit_service.verify_integrity()

    # Audit the verification action itself
    audit_service.record_event(
        event_type=AuditEventType.AUDIT_CHAIN_VERIFY,
        action="VERIFY",
        resource_type="AUDIT_CHAIN",
        resource_id=None,
        actor_id=current_user.id,
        actor_email=current_user.email,
        actor_role=current_user.role.value,
        outcome=AuditOutcome.SUCCESS if result.is_valid else AuditOutcome.FAILURE,
        details=result.to_dict(),
    )

    return AuditChainVerificationResponse(
        status=result.status,
        is_valid=result.is_valid,
        total_events_verified=result.total_events_verified,
        broken_sequence_number=result.broken_sequence_number,
        expected_hash=result.expected_hash,
        actual_hash=result.actual_hash,
        reason=result.reason,
    )


@router.post(
    "/export",
    response_model=AuditExportResponse,
    summary="Export verifiable audit trail with mandatory audit record (Admin only)",
    description="Generates an export of audit records while recording an un-erasable DATA_EXPORT audit event.",
)
def export_audit_log(
    payload: AuditExportRequest,
    current_user: User = Depends(require_role(UserRole.ADMIN)),
    db: Session = Depends(get_db),
):
    audit_service = AuditService(db)
    verification = audit_service.verify_integrity()
    events, total = audit_service.list_events(
        event_type=payload.event_type,
        skip=0,
        limit=1000,
    )

    # 1. Audit the export request
    audit_service.record_event(
        event_type=AuditEventType.DATA_EXPORT,
        action="EXPORT",
        resource_type="AUDIT_LOG",
        resource_id=None,
        actor_id=current_user.id,
        actor_email=current_user.email,
        actor_role=current_user.role.value,
        outcome=AuditOutcome.SUCCESS,
        details={
            "format": payload.format,
            "reason": payload.reason,
            "records_count": total,
            "integrity_valid": verification.is_valid,
        },
    )

    export_data = [
        {
            "sequence_number": e.sequence_number,
            "event_type": e.event_type.value if hasattr(e.event_type, "value") else str(e.event_type),
            "actor_id": str(e.actor_id) if e.actor_id else None,
            "actor_role": e.actor_role,
            "resource_type": e.resource_type,
            "resource_id": e.resource_id,
            "action": e.action,
            "outcome": e.outcome.value if hasattr(e.outcome, "value") else str(e.outcome),
            "details": e.details,
            "previous_hash": e.previous_hash,
            "event_hash": e.event_hash,
            "created_at": e.created_at.isoformat(),
        }
        for e in events
    ]

    return AuditExportResponse(
        total_exported=len(export_data),
        format=payload.format,
        exported_at=datetime.now(timezone.utc),
        integrity_verified=verification.is_valid,
        data=export_data,
    )
