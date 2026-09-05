from __future__ import annotations

import uuid
from datetime import datetime, timezone, timedelta
import pytest
from backend.app.domain.models.audit_event import AuditEvent
from backend.app.domain.models.enums import AuditEventType, AuditOutcome
from backend.app.engines.audit.hasher import AuditHasher, GENESIS_HASH
from backend.app.engines.audit.verifier import AuditChainVerifier


def test_canonical_serialization_deterministic():
    now = datetime(2026, 9, 5, 12, 0, 0, tzinfo=timezone.utc)
    details = {"role": "TOURIST", "ip": "127.0.0.1", "nested": {"b": 2, "a": 1}}

    s1 = AuditHasher.serialize_canonical(
        sequence_number=1,
        event_type="AUTH_LOGIN_SUCCESS",
        actor_id="user-123",
        actor_role="TOURIST",
        resource_type="USER",
        resource_id="user-123",
        action="LOGIN",
        outcome="SUCCESS",
        details=details,
        previous_hash=GENESIS_HASH,
        created_at=now,
    )

    # Scramble dict insertion order in details
    scrambled_details = {"nested": {"a": 1, "b": 2}, "ip": "127.0.0.1", "role": "TOURIST"}
    s2 = AuditHasher.serialize_canonical(
        sequence_number=1,
        event_type="AUTH_LOGIN_SUCCESS",
        actor_id="user-123",
        actor_role="TOURIST",
        resource_type="USER",
        resource_id="user-123",
        action="LOGIN",
        outcome="SUCCESS",
        details=scrambled_details,
        previous_hash=GENESIS_HASH,
        created_at=now,
    )

    assert s1 == s2
    hash1 = AuditHasher.calculate_event_hash(
        sequence_number=1,
        event_type="AUTH_LOGIN_SUCCESS",
        actor_id="user-123",
        actor_role="TOURIST",
        resource_type="USER",
        resource_id="user-123",
        action="LOGIN",
        outcome="SUCCESS",
        details=details,
        previous_hash=GENESIS_HASH,
        created_at=now,
    )
    hash2 = AuditHasher.calculate_event_hash(
        sequence_number=1,
        event_type="AUTH_LOGIN_SUCCESS",
        actor_id="user-123",
        actor_role="TOURIST",
        resource_type="USER",
        resource_id="user-123",
        action="LOGIN",
        outcome="SUCCESS",
        details=scrambled_details,
        previous_hash=GENESIS_HASH,
        created_at=now,
    )
    assert hash1 == hash2
    assert len(hash1) == 64  # SHA-256 hex length
