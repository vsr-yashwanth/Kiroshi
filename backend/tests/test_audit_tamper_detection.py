from __future__ import annotations

import uuid
from datetime import datetime, timezone, timedelta
import pytest
from backend.app.domain.models.audit_event import AuditEvent
from backend.app.domain.models.enums import AuditEventType, AuditOutcome
from backend.app.engines.audit.hasher import AuditHasher, GENESIS_HASH
from backend.app.engines.audit.verifier import AuditChainVerifier


def build_synthetic_chain(count: int = 5) -> list[AuditEvent]:
    events = []
    prev_hash = GENESIS_HASH
    base_time = datetime(2026, 9, 5, 8, 0, 0, tzinfo=timezone.utc)

    for i in range(1, count + 1):
        created_at = base_time + timedelta(minutes=i)
        details = {"step": i, "action": f"test_op_{i}"}
        actor_id = uuid.uuid4()
        event_hash = AuditHasher.calculate_event_hash(
            sequence_number=i,
            event_type="AUTH_LOGIN_SUCCESS",
            actor_id=str(actor_id),
            actor_role="ADMIN",
            resource_type="USER",
            resource_id="user-xyz",
            action="LOGIN",
            outcome="SUCCESS",
            details=details,
            previous_hash=prev_hash,
            created_at=created_at,
        )

        event = AuditEvent(
            sequence_number=i,
            event_type=AuditEventType.AUTH_LOGIN_SUCCESS,
            actor_id=actor_id,
            actor_email="admin@example.com",
            actor_role="ADMIN",
            resource_type="USER",
            resource_id="user-xyz",
            action="LOGIN",
            outcome=AuditOutcome.SUCCESS,
            details=details,
            previous_hash=prev_hash,
            event_hash=event_hash,
        )
        event.created_at = created_at
        events.append(event)
        prev_hash = event_hash

    return events


def test_1_valid_chain_passes():
    chain = build_synthetic_chain(5)
    res = AuditChainVerifier.verify_chain(chain)
    assert res.is_valid is True
    assert res.status == "CHAIN_VALID"
    assert res.total_events_verified == 5


def test_2_modify_event_payload_breaks_chain():
    chain = build_synthetic_chain(5)
    # Tamper with payload of event #3
    chain[2].details = {"step": 3, "action": "MALICIOUS_INJECTION"}
    res = AuditChainVerifier.verify_chain(chain)
    assert res.is_valid is False
    assert res.status == "CHAIN_BROKEN"
    assert res.broken_sequence_number == 3
    assert "Tampered payload" in res.reason


def test_3_modify_previous_hash_breaks_chain():
    chain = build_synthetic_chain(5)
    # Alter previous_hash pointer of event #4
    chain[3].previous_hash = "ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff"
    res = AuditChainVerifier.verify_chain(chain)
    assert res.is_valid is False
    assert res.status == "CHAIN_BROKEN"
    assert res.broken_sequence_number == 4
    assert "Previous hash link broken" in res.reason


def test_4_delete_event_breaks_chain():
    chain = build_synthetic_chain(5)
    # Delete event #3
    del chain[2]
    res = AuditChainVerifier.verify_chain(chain)
    assert res.is_valid is False
    assert res.status == "CHAIN_BROKEN"
    assert res.broken_sequence_number == 4
    assert "Sequence gap or reordering" in res.reason


def test_5_reorder_events_breaks_chain():
    chain = build_synthetic_chain(5)
    # Swap event #2 and #3
    chain[1], chain[2] = chain[2], chain[1]
    res = AuditChainVerifier.verify_chain(chain)
    assert res.is_valid is False
    assert res.status == "CHAIN_BROKEN"


def test_6_modify_event_hash_breaks_chain():
    chain = build_synthetic_chain(5)
    # Alter signature of event #2
    chain[1].event_hash = "deadbeefdeadbeefdeadbeefdeadbeefdeadbeefdeadbeefdeadbeefdeadbeef"
    res = AuditChainVerifier.verify_chain(chain)
    assert res.is_valid is False
    assert res.status == "CHAIN_BROKEN"
    assert res.broken_sequence_number == 2


def test_7_valid_appended_event_maintains_chain():
    chain = build_synthetic_chain(4)
    # Append valid 5th event
    prev_hash = chain[-1].event_hash
    created_at = datetime(2026, 9, 5, 8, 5, 0, tzinfo=timezone.utc)
    details = {"step": 5, "action": "test_op_5"}
    actor_5_id = uuid.uuid4()
    h5 = AuditHasher.calculate_event_hash(
        sequence_number=5,
        event_type="AUTH_LOGOUT",
        actor_id=str(actor_5_id),
        actor_role="ADMIN",
        resource_type="USER",
        resource_id="user-xyz",
        action="LOGOUT",
        outcome="SUCCESS",
        details=details,
        previous_hash=prev_hash,
        created_at=created_at,
    )
    e5 = AuditEvent(
        sequence_number=5,
        event_type=AuditEventType.AUTH_LOGOUT,
        actor_id=actor_5_id,
        actor_email="admin@example.com",
        actor_role="ADMIN",
        resource_type="USER",
        resource_id="user-xyz",
        action="LOGOUT",
        outcome=AuditOutcome.SUCCESS,
        details=details,
        previous_hash=prev_hash,
        event_hash=h5,
    )
    e5.created_at = created_at
    chain.append(e5)

    res = AuditChainVerifier.verify_chain(chain)
    assert res.is_valid is True
    assert res.status == "CHAIN_VALID"
    assert res.total_events_verified == 5
