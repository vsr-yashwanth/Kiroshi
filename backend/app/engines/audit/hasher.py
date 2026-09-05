from __future__ import annotations

import json
import hashlib
from datetime import datetime, timezone
from typing import Any, Dict, Optional

GENESIS_HASH = "0000000000000000000000000000000000000000000000000000000000000000"


class AuditHasher:
    """
    Deterministic cryptographic canonicalization and SHA-256 hash calculation
    for tamper-evident audit chaining.
    """

    @staticmethod
    def serialize_canonical(
        sequence_number: int,
        event_type: str,
        actor_id: Optional[str],
        actor_role: Optional[str],
        resource_type: str,
        resource_id: Optional[str],
        action: str,
        outcome: str,
        details: Dict[str, Any],
        previous_hash: str,
        created_at: datetime,
    ) -> str:
        """
        Produces an immutable, canonically sorted JSON string representation of the audit event.
        - Dict keys strictly sorted.
        - Timestamps normalized to ISO 8601 UTC strings.
        - Stripped of unconstrained whitespace.
        """
        # Ensure UTC timezone formatting
        if created_at.tzinfo is None:
            utc_timestamp = created_at.replace(tzinfo=timezone.utc).isoformat()
        else:
            utc_timestamp = created_at.astimezone(timezone.utc).isoformat()

        canonical_dict = {
            "action": action,
            "actor_id": str(actor_id) if actor_id else None,
            "actor_role": str(actor_role) if actor_role else None,
            "created_at": utc_timestamp,
            "details": details,
            "event_type": str(event_type),
            "outcome": str(outcome),
            "previous_hash": str(previous_hash),
            "resource_id": str(resource_id) if resource_id else None,
            "resource_type": str(resource_type),
            "sequence_number": int(sequence_number),
        }

        return json.dumps(canonical_dict, sort_keys=True, separators=(",", ":"), default=str)

    @classmethod
    def calculate_event_hash(
        cls,
        sequence_number: int,
        event_type: str,
        actor_id: Optional[str],
        actor_role: Optional[str],
        resource_type: str,
        resource_id: Optional[str],
        action: str,
        outcome: str,
        details: Dict[str, Any],
        previous_hash: str,
        created_at: datetime,
    ) -> str:
        """Computes SHA-256 hex digest over canonical serialization."""
        canonical_str = cls.serialize_canonical(
            sequence_number=sequence_number,
            event_type=event_type,
            actor_id=actor_id,
            actor_role=actor_role,
            resource_type=resource_type,
            resource_id=resource_id,
            action=action,
            outcome=outcome,
            details=details,
            previous_hash=previous_hash,
            created_at=created_at,
        )
        return hashlib.sha256(canonical_str.encode("utf-8")).hexdigest()
