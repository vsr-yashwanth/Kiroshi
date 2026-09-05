from __future__ import annotations

from typing import List, Tuple, Optional, Dict, Any
from backend.app.domain.models.audit_event import AuditEvent
from backend.app.engines.audit.hasher import AuditHasher, GENESIS_HASH


class ChainVerificationResult:
    def __init__(
        self,
        is_valid: bool,
        total_events_verified: int,
        broken_sequence_number: Optional[int] = None,
        expected_hash: Optional[str] = None,
        actual_hash: Optional[str] = None,
        reason: Optional[str] = None,
    ):
        self.is_valid = is_valid
        self.status = "CHAIN_VALID" if is_valid else "CHAIN_BROKEN"
        self.total_events_verified = total_events_verified
        self.broken_sequence_number = broken_sequence_number
        self.expected_hash = expected_hash
        self.actual_hash = actual_hash
        self.reason = reason

    def to_dict(self) -> Dict[str, Any]:
        return {
            "status": self.status,
            "is_valid": self.is_valid,
            "total_events_verified": self.total_events_verified,
            "broken_sequence_number": self.broken_sequence_number,
            "expected_hash": self.expected_hash,
            "actual_hash": self.actual_hash,
            "reason": self.reason,
        }


class AuditChainVerifier:
    """
    Cryptographic auditor that scans sequential audit logs to verify:
    1. Genesis root hash alignment.
    2. Exact event SHA-256 payload integrity.
    3. Forward previous_hash pointer integrity.
    4. Strict sequence number continuity.
    """

    @classmethod
    def verify_chain(cls, events: List[AuditEvent]) -> ChainVerificationResult:
        if not events:
            return ChainVerificationResult(
                is_valid=True,
                total_events_verified=0,
            )

        expected_previous_hash = GENESIS_HASH

        for idx, event in enumerate(events):
            expected_seq = idx + 1
            if event.sequence_number != expected_seq:
                return ChainVerificationResult(
                    is_valid=False,
                    total_events_verified=idx,
                    broken_sequence_number=event.sequence_number,
                    reason=f"Sequence gap or reordering: expected sequence #{expected_seq}, found #{event.sequence_number}",
                )

            # 1. Check previous_hash link
            if event.previous_hash != expected_previous_hash:
                return ChainVerificationResult(
                    is_valid=False,
                    total_events_verified=idx,
                    broken_sequence_number=event.sequence_number,
                    expected_hash=expected_previous_hash,
                    actual_hash=event.previous_hash,
                    reason=f"Previous hash link broken at sequence #{event.sequence_number}",
                )

            # 2. Recalculate event hash from canonical payload
            recalculated_hash = AuditHasher.calculate_event_hash(
                sequence_number=event.sequence_number,
                event_type=event.event_type.value if hasattr(event.event_type, "value") else str(event.event_type),
                actor_id=str(event.actor_id) if event.actor_id else None,
                actor_role=event.actor_role,
                resource_type=event.resource_type,
                resource_id=event.resource_id,
                action=event.action,
                outcome=event.outcome.value if hasattr(event.outcome, "value") else str(event.outcome),
                details=event.details or {},
                previous_hash=event.previous_hash,
                created_at=event.created_at,
            )

            if recalculated_hash != event.event_hash:
                return ChainVerificationResult(
                    is_valid=False,
                    total_events_verified=idx,
                    broken_sequence_number=event.sequence_number,
                    expected_hash=recalculated_hash,
                    actual_hash=event.event_hash,
                    reason=f"Tampered payload or signature mismatch at sequence #{event.sequence_number}",
                )

            expected_previous_hash = event.event_hash

        return ChainVerificationResult(
            is_valid=True,
            total_events_verified=len(events),
        )
