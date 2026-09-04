import uuid
import pytest
from unittest.mock import MagicMock

from backend.app.domain.models.enums import IncidentStatus, UserRole
from backend.app.services.incident_state_machine import (
    IncidentStateMachine,
    InvalidStateTransitionError,
    UnauthorizedTransitionError,
)


def make_mock_user(role: UserRole, user_id=None):
    user = MagicMock()
    user.id = user_id or uuid.uuid4()
    user.role = role
    return user


def make_mock_incident(status: IncidentStatus, responder_id=None):
    incident = MagicMock()
    incident.id = uuid.uuid4()
    incident.status = status
    incident.assigned_responder_id = responder_id
    return incident


def test_valid_forward_transitions():
    sm = IncidentStateMachine()
    authority = make_mock_user(UserRole.AUTHORITY)
    responder_id = uuid.uuid4()
    responder = make_mock_user(UserRole.RESPONDER, user_id=responder_id)

    # DETECTED -> VERIFYING (AUTHORITY)
    assert sm.can_transition(IncidentStatus.DETECTED, IncidentStatus.VERIFYING) is True
    sm.validate_transition(make_mock_incident(IncidentStatus.DETECTED), IncidentStatus.VERIFYING, authority)

    # VERIFYING -> VERIFIED (AUTHORITY)
    assert sm.can_transition(IncidentStatus.VERIFYING, IncidentStatus.VERIFIED) is True
    sm.validate_transition(make_mock_incident(IncidentStatus.VERIFYING), IncidentStatus.VERIFIED, authority)

    # VERIFIED -> ESCALATED (AUTHORITY)
    assert sm.can_transition(IncidentStatus.VERIFIED, IncidentStatus.ESCALATED) is True
    sm.validate_transition(make_mock_incident(IncidentStatus.VERIFIED), IncidentStatus.ESCALATED, authority)

    # ESCALATED -> ASSIGNED (AUTHORITY) with responder assigned
    assert sm.can_transition(IncidentStatus.ESCALATED, IncidentStatus.ASSIGNED) is True
    sm.validate_transition(make_mock_incident(IncidentStatus.ESCALATED, responder_id=responder_id), IncidentStatus.ASSIGNED, authority)

    # ASSIGNED -> RESPONDING (RESPONDER)
    assert sm.can_transition(IncidentStatus.ASSIGNED, IncidentStatus.RESPONDING) is True
    sm.validate_transition(make_mock_incident(IncidentStatus.ASSIGNED, responder_id=responder_id), IncidentStatus.RESPONDING, responder)

    # RESPONDING -> RESOLVED (RESPONDER)
    assert sm.can_transition(IncidentStatus.RESPONDING, IncidentStatus.RESOLVED) is True
    sm.validate_transition(make_mock_incident(IncidentStatus.RESPONDING, responder_id=responder_id), IncidentStatus.RESOLVED, responder)

    # RESOLVED -> CLOSED (AUTHORITY)
    assert sm.can_transition(IncidentStatus.RESOLVED, IncidentStatus.CLOSED) is True
    sm.validate_transition(make_mock_incident(IncidentStatus.RESOLVED), IncidentStatus.CLOSED, authority)


def test_valid_dismissal_transitions():
    sm = IncidentStateMachine()
    authority = make_mock_user(UserRole.AUTHORITY)

    # DETECTED -> DISMISSED (AUTHORITY)
    sm.validate_transition(make_mock_incident(IncidentStatus.DETECTED), IncidentStatus.DISMISSED, authority)

    # VERIFYING -> DISMISSED (AUTHORITY)
    sm.validate_transition(make_mock_incident(IncidentStatus.VERIFYING), IncidentStatus.DISMISSED, authority)

    # VERIFIED -> DISMISSED (AUTHORITY)
    sm.validate_transition(make_mock_incident(IncidentStatus.VERIFIED), IncidentStatus.DISMISSED, authority)


def test_invalid_transitions_throw_exception():
    sm = IncidentStateMachine()
    admin = make_mock_user(UserRole.ADMIN)

    # CLOSED is terminal
    with pytest.raises(InvalidStateTransitionError):
        sm.validate_transition(make_mock_incident(IncidentStatus.CLOSED), IncidentStatus.RESPONDING, admin)

    with pytest.raises(InvalidStateTransitionError):
        sm.validate_transition(make_mock_incident(IncidentStatus.CLOSED), IncidentStatus.DETECTED, admin)

    # DISMISSED is terminal
    with pytest.raises(InvalidStateTransitionError):
        sm.validate_transition(make_mock_incident(IncidentStatus.DISMISSED), IncidentStatus.VERIFIED, admin)

    # Skip states
    with pytest.raises(InvalidStateTransitionError):
        sm.validate_transition(make_mock_incident(IncidentStatus.DETECTED), IncidentStatus.RESOLVED, admin)

    with pytest.raises(InvalidStateTransitionError):
        sm.validate_transition(make_mock_incident(IncidentStatus.DETECTED), IncidentStatus.CLOSED, admin)


def test_role_authorization_enforcement():
    sm = IncidentStateMachine()
    tourist = make_mock_user(UserRole.TOURIST)
    authority = make_mock_user(UserRole.AUTHORITY)
    responder = make_mock_user(UserRole.RESPONDER)
    admin = make_mock_user(UserRole.ADMIN)

    # TOURIST cannot verify or dismiss
    with pytest.raises(UnauthorizedTransitionError):
        sm.validate_transition(make_mock_incident(IncidentStatus.DETECTED), IncidentStatus.VERIFYING, tourist)

    with pytest.raises(UnauthorizedTransitionError):
        sm.validate_transition(make_mock_incident(IncidentStatus.DETECTED), IncidentStatus.DISMISSED, tourist)

    # TOURIST cannot resolve
    with pytest.raises(UnauthorizedTransitionError):
        sm.validate_transition(make_mock_incident(IncidentStatus.RESPONDING), IncidentStatus.RESOLVED, tourist)

    # AUTHORITY cannot mark as RESPONDING (only RESPONDER or ADMIN)
    with pytest.raises(UnauthorizedTransitionError):
        sm.validate_transition(make_mock_incident(IncidentStatus.ASSIGNED), IncidentStatus.RESPONDING, authority)

    # RESPONDER cannot close or dismiss
    with pytest.raises(UnauthorizedTransitionError):
        sm.validate_transition(make_mock_incident(IncidentStatus.RESOLVED), IncidentStatus.CLOSED, responder)

    with pytest.raises(UnauthorizedTransitionError):
        sm.validate_transition(make_mock_incident(IncidentStatus.DETECTED), IncidentStatus.DISMISSED, responder)

    # ADMIN can execute valid transitions
    sm.validate_transition(make_mock_incident(IncidentStatus.DETECTED), IncidentStatus.VERIFYING, admin)
    sm.validate_transition(make_mock_incident(IncidentStatus.RESOLVED), IncidentStatus.CLOSED, admin)
