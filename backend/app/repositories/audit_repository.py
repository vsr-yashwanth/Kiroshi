from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import List, Optional, Tuple, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import desc, func, select

from backend.app.domain.models.audit_event import AuditEvent
from backend.app.domain.models.enums import AuditEventType, AuditOutcome
from backend.app.engines.audit.hasher import AuditHasher, GENESIS_HASH


class AuditRepository:
    """
    Append-only repository for audit events enforcing cryptographic hash chaining
    and sequential ordering.
    """

    def __init__(self, db: Session):
        self.db = db

    def get_latest_event(self) -> Optional[AuditEvent]:
        return self.db.query(AuditEvent).order_by(AuditEvent.sequence_number.desc()).first()

    def create_event(
        self,
        event_type: AuditEventType,
        action: str,
        resource_type: str,
        resource_id: Optional[str] = None,
        actor_id: Optional[uuid.UUID] = None,
        actor_email: Optional[str] = None,
        actor_role: Optional[str] = None,
        client_ip: Optional[str] = None,
        user_agent: Optional[str] = None,
        outcome: AuditOutcome = AuditOutcome.SUCCESS,
        details: Optional[Dict[str, Any]] = None,
    ) -> AuditEvent:
        latest = self.get_latest_event()
        seq = (latest.sequence_number + 1) if latest else 1
        prev_hash = latest.event_hash if latest else GENESIS_HASH
        created_at = datetime.now(timezone.utc)
        safe_details = details or {}

        event_hash = AuditHasher.calculate_event_hash(
            sequence_number=seq,
            event_type=event_type.value if hasattr(event_type, "value") else str(event_type),
            actor_id=str(actor_id) if actor_id else None,
            actor_role=actor_role,
            resource_type=resource_type,
            resource_id=resource_id,
            action=action,
            outcome=outcome.value if hasattr(outcome, "value") else str(outcome),
            details=safe_details,
            previous_hash=prev_hash,
            created_at=created_at,
        )

        audit_event = AuditEvent(
            sequence_number=seq,
            event_type=event_type,
            actor_id=actor_id,
            actor_email=actor_email,
            actor_role=actor_role,
            client_ip=client_ip,
            user_agent=user_agent,
            resource_type=resource_type,
            resource_id=resource_id,
            action=action,
            outcome=outcome,
            details=safe_details,
            previous_hash=prev_hash,
            event_hash=event_hash,
        )
        audit_event.created_at = created_at

        self.db.add(audit_event)
        self.db.commit()
        self.db.refresh(audit_event)
        return audit_event

    def get_all_events_ordered(self) -> List[AuditEvent]:
        return self.db.query(AuditEvent).order_by(AuditEvent.sequence_number.asc()).all()

    def list_events(
        self,
        event_type: Optional[AuditEventType] = None,
        actor_id: Optional[uuid.UUID] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        outcome: Optional[AuditOutcome] = None,
        skip: int = 0,
        limit: int = 50,
    ) -> Tuple[List[AuditEvent], int]:
        query = self.db.query(AuditEvent)

        if event_type is not None:
            query = query.filter(AuditEvent.event_type == event_type)
        if actor_id is not None:
            query = query.filter(AuditEvent.actor_id == actor_id)
        if resource_type is not None:
            query = query.filter(AuditEvent.resource_type == resource_type)
        if resource_id is not None:
            query = query.filter(AuditEvent.resource_id == resource_id)
        if outcome is not None:
            query = query.filter(AuditEvent.outcome == outcome)

        total = query.count()
        events = query.order_by(AuditEvent.sequence_number.desc()).offset(skip).limit(limit).all()
        return events, total
