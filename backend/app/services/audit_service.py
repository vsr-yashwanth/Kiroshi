from __future__ import annotations

import uuid
from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy.orm import Session

from backend.app.domain.models.audit_event import AuditEvent
from backend.app.domain.models.enums import AuditEventType, AuditOutcome, TrustAnchorStatus
from backend.app.repositories.audit_repository import AuditRepository
from backend.app.engines.audit.verifier import AuditChainVerifier, ChainVerificationResult
from backend.app.engines.audit.trust_anchor import BaseTrustAnchor, LocalTrustAnchor, AnchorSubmissionResult


class AuditService:
    """
    Centralized security and audit orchestrator implementing:
    - Tamper-evident logging for authentication, profiles, location, incidents, and permissions.
    - Full sequence and hash chain integrity verification.
    - Modular checkpoint trust anchoring with failure isolation.
    """

    def __init__(
        self,
        db: Session,
        trust_anchor: Optional[BaseTrustAnchor] = None,
    ):
        self.db = db
        self.repo = AuditRepository(db)
        self.trust_anchor = trust_anchor or LocalTrustAnchor()

    def record_event(
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
        return self.repo.create_event(
            event_type=event_type,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            actor_id=actor_id,
            actor_email=actor_email,
            actor_role=actor_role,
            client_ip=client_ip,
            user_agent=user_agent,
            outcome=outcome,
            details=details or {},
        )

    def verify_integrity(self) -> ChainVerificationResult:
        """Audits the complete historical chain for tampering, deletion, or reordering."""
        all_events = self.repo.get_all_events_ordered()
        return AuditChainVerifier.verify_chain(all_events)

    def create_trust_checkpoint(self, metadata: Optional[Dict[str, Any]] = None) -> AnchorSubmissionResult:
        """Anchors latest cryptographic hash checkpoint to the configured trust anchor."""
        latest = self.repo.get_latest_event()
        if not latest:
            return AnchorSubmissionResult(
                status=TrustAnchorStatus.DISABLED,
                checkpoint_sequence=0,
                checkpoint_hash="NONE",
                error_message="No audit events present to anchor",
            )

        return self.trust_anchor.anchor_checkpoint(
            checkpoint_sequence=latest.sequence_number,
            checkpoint_hash=latest.event_hash,
            metadata=metadata,
        )

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
        return self.repo.list_events(
            event_type=event_type,
            actor_id=actor_id,
            resource_type=resource_type,
            resource_id=resource_id,
            outcome=outcome,
            skip=skip,
            limit=limit,
        )
