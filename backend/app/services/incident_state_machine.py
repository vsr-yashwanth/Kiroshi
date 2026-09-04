from typing import Set, Dict, Tuple, Optional
import uuid
from fastapi import HTTPException, status

from backend.app.domain.models.enums import IncidentStatus, UserRole
from backend.app.domain.models.incident import Incident
from backend.app.domain.models.user import User


class StateMachineError(HTTPException):
    def __init__(self, status_code: int, detail: str):
        super().__init__(status_code=status_code, detail=detail)


class InvalidStateTransitionError(StateMachineError):
    def __init__(self, from_state: IncidentStatus, to_state: IncidentStatus, reason: Optional[str] = None):
        detail = f"Invalid state transition from '{from_state.value}' to '{to_state.value}'."
        if reason:
            detail += f" {reason}"
        super().__init__(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)


class UnauthorizedTransitionError(StateMachineError):
    def __init__(self, required_roles: Set[UserRole], user_role: UserRole, action: str):
        allowed_str = ", ".join(r.value for r in required_roles)
        detail = f"Unauthorized: User with role '{user_role.value}' cannot perform '{action}'. Required role(s): {allowed_str}."
        super().__init__(status_code=status.HTTP_403_FORBIDDEN, detail=detail)


class IncidentStateMachine:
    """
    Strict authoritative server-side state machine for KIROSHI incident lifecycles.
    Enforces allowed state transitions and strict role-based access control.
    """

    # Allowed state transition graph
    ALLOWED_TRANSITIONS: Dict[IncidentStatus, Set[IncidentStatus]] = {
        IncidentStatus.DETECTED: {
            IncidentStatus.VERIFYING,
            IncidentStatus.VERIFIED,
            IncidentStatus.DISMISSED,
        },
        IncidentStatus.VERIFYING: {
            IncidentStatus.VERIFIED,
            IncidentStatus.DISMISSED,
        },
        IncidentStatus.VERIFIED: {
            IncidentStatus.ESCALATED,
            IncidentStatus.ASSIGNED,
            IncidentStatus.DISMISSED,
        },
        IncidentStatus.ESCALATED: {
            IncidentStatus.ASSIGNED,
            IncidentStatus.DISMISSED,
        },
        IncidentStatus.ASSIGNED: {
            IncidentStatus.RESPONDING,
            IncidentStatus.ESCALATED,
            IncidentStatus.DISMISSED,
        },
        IncidentStatus.RESPONDING: {
            IncidentStatus.RESOLVED,
            IncidentStatus.ESCALATED,
        },
        IncidentStatus.RESOLVED: {
            IncidentStatus.CLOSED,
            IncidentStatus.RESPONDING,  # Re-open for further on-site response
        },
        IncidentStatus.CLOSED: set(),     # Terminal state
        IncidentStatus.DISMISSED: set(),  # Terminal state
    }

    # Role permissions for each transition: (from_state, to_state) -> set[UserRole]
    TRANSITION_ROLES: Dict[Tuple[IncidentStatus, IncidentStatus], Set[UserRole]] = {
        # Detection & Triage
        (IncidentStatus.DETECTED, IncidentStatus.VERIFYING): {UserRole.AUTHORITY, UserRole.ADMIN},
        (IncidentStatus.DETECTED, IncidentStatus.VERIFIED): {UserRole.AUTHORITY, UserRole.ADMIN},
        (IncidentStatus.DETECTED, IncidentStatus.DISMISSED): {UserRole.AUTHORITY, UserRole.ADMIN},

        # Verification
        (IncidentStatus.VERIFYING, IncidentStatus.VERIFIED): {UserRole.AUTHORITY, UserRole.ADMIN},
        (IncidentStatus.VERIFYING, IncidentStatus.DISMISSED): {UserRole.AUTHORITY, UserRole.ADMIN},

        # Escalation & Assignment
        (IncidentStatus.VERIFIED, IncidentStatus.ESCALATED): {UserRole.AUTHORITY, UserRole.ADMIN},
        (IncidentStatus.VERIFIED, IncidentStatus.ASSIGNED): {UserRole.AUTHORITY, UserRole.ADMIN},
        (IncidentStatus.VERIFIED, IncidentStatus.DISMISSED): {UserRole.AUTHORITY, UserRole.ADMIN},

        (IncidentStatus.ESCALATED, IncidentStatus.ASSIGNED): {UserRole.AUTHORITY, UserRole.ADMIN},
        (IncidentStatus.ESCALATED, IncidentStatus.DISMISSED): {UserRole.AUTHORITY, UserRole.ADMIN},

        # Response
        (IncidentStatus.ASSIGNED, IncidentStatus.RESPONDING): {UserRole.RESPONDER, UserRole.ADMIN},
        (IncidentStatus.ASSIGNED, IncidentStatus.ESCALATED): {UserRole.AUTHORITY, UserRole.ADMIN},
        (IncidentStatus.ASSIGNED, IncidentStatus.DISMISSED): {UserRole.AUTHORITY, UserRole.ADMIN},

        (IncidentStatus.RESPONDING, IncidentStatus.RESOLVED): {UserRole.RESPONDER, UserRole.AUTHORITY, UserRole.ADMIN},
        (IncidentStatus.RESPONDING, IncidentStatus.ESCALATED): {UserRole.RESPONDER, UserRole.AUTHORITY, UserRole.ADMIN},

        # Resolution & Closure
        (IncidentStatus.RESOLVED, IncidentStatus.CLOSED): {UserRole.AUTHORITY, UserRole.ADMIN},
        (IncidentStatus.RESOLVED, IncidentStatus.RESPONDING): {UserRole.AUTHORITY, UserRole.ADMIN},
    }

    @classmethod
    def can_transition(cls, from_state: IncidentStatus, to_state: IncidentStatus) -> bool:
        allowed = cls.ALLOWED_TRANSITIONS.get(from_state, set())
        return to_state in allowed

    @classmethod
    def validate_transition(
        cls,
        incident: Incident,
        to_state: IncidentStatus,
        actor: User,
        notes: Optional[str] = None,
    ) -> None:
        """
        Validates whether the requested state transition is valid and authorized for the actor.
        Raises InvalidStateTransitionError or UnauthorizedTransitionError.
        """
        from_state = incident.status

        # 1. Terminal state check
        if from_state in [IncidentStatus.CLOSED, IncidentStatus.DISMISSED]:
            raise InvalidStateTransitionError(
                from_state, to_state, reason="Incident is in a terminal state and cannot be modified."
            )

        # 2. Transition validity check
        if not cls.can_transition(from_state, to_state):
            raise InvalidStateTransitionError(from_state, to_state)

        # 3. Role authorization check
        required_roles = cls.TRANSITION_ROLES.get((from_state, to_state), set())
        if actor.role not in required_roles:
            raise UnauthorizedTransitionError(
                required_roles=required_roles,
                user_role=actor.role,
                action=f"transition from {from_state.value} to {to_state.value}",
            )

        # 4. Responder specific assignment check (Anti-IDOR)
        if actor.role == UserRole.RESPONDER:
            if incident.assigned_responder_id != actor.id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Responders can only update incidents assigned to them.",
                )

        # 5. Precondition checks
        if to_state == IncidentStatus.ASSIGNED and not incident.assigned_responder_id:
            raise InvalidStateTransitionError(
                from_state, to_state, reason="Incident cannot move to ASSIGNED without an assigned responder."
            )
