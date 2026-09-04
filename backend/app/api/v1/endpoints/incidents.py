import uuid
from typing import Optional, List
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.api.deps import get_current_active_user, require_authority_or_admin
from backend.app.domain.models.user import User
from backend.app.domain.models.enums import IncidentStatus, IncidentSeverity, IncidentSource
from backend.app.schemas.incident import (
    SOSCreateRequest,
    IncidentResponse,
    IncidentTransitionRequest,
    IncidentAssignRequest,
    IncidentEventResponse,
    ResponderUserResponse,
)
from backend.app.services.incident_service import IncidentService

router = APIRouter()


def _to_incident_response(incident) -> IncidentResponse:
    return IncidentResponse(
        id=incident.id,
        source=incident.source,
        severity=incident.severity,
        status=incident.status,
        tourist_id=incident.tourist_id,
        tourist_name=incident.tourist.full_name if incident.tourist else None,
        trip_id=incident.trip_id,
        trip_title=incident.trip.title if incident.trip else None,
        latitude=incident.latitude,
        longitude=incident.longitude,
        accuracy=incident.accuracy,
        location_freshness=incident.location_freshness,
        description=incident.description,
        risk_assessment_id=incident.risk_assessment_id,
        assigned_responder_id=incident.assigned_responder_id,
        assigned_responder_name=incident.assigned_responder.full_name if incident.assigned_responder else None,
        idempotency_key=incident.idempotency_key,
        resolution_notes=incident.resolution_notes,
        resolved_at=incident.resolved_at,
        closed_at=incident.closed_at,
        created_at=incident.created_at,
        updated_at=incident.updated_at,
    )


@router.post("/sos", response_model=IncidentResponse, status_code=status.HTTP_201_CREATED)
async def trigger_emergency_sos(
    payload: SOSCreateRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    Emergency SOS activation endpoint for tourists.
    CRITICAL: Functional even if Risk Engine / AI / CCTV services are offline.
    """
    service = IncidentService(db)
    incident = await service.create_sos(
        current_user=current_user,
        trip_id=payload.trip_id,
        latitude=payload.latitude,
        longitude=payload.longitude,
        accuracy=payload.accuracy,
        description=payload.description,
        idempotency_key=payload.idempotency_key,
    )
    return _to_incident_response(incident)


@router.get("", response_model=List[IncidentResponse])
def list_incidents(
    status: Optional[IncidentStatus] = Query(None, description="Filter by incident status"),
    severity: Optional[IncidentSeverity] = Query(None, description="Filter by severity level"),
    source: Optional[IncidentSource] = Query(None, description="Filter by incident source"),
    exclude_terminal: bool = Query(False, description="Exclude CLOSED and DISMISSED incidents"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    Retrieves a list of incidents scoped by current user's role:
    - Authority / Admin: system-wide queue with full filtering
    - Responder: assigned incidents only
    - Tourist: own created incidents only
    """
    service = IncidentService(db)
    incidents = service.list_incidents(
        current_user=current_user,
        status_filter=status,
        severity_filter=severity,
        source_filter=source,
        exclude_terminal=exclude_terminal,
        limit=limit,
        offset=offset,
    )
    return [_to_incident_response(inc) for inc in incidents]


@router.get("/responders/available", response_model=List[ResponderUserResponse])
def list_available_responders(
    current_user: User = Depends(require_authority_or_admin),
    db: Session = Depends(get_db),
):
    """Lists registered responder personnel available for dispatch."""
    service = IncidentService(db)
    responders = service.list_available_responders(current_user)
    return [ResponderUserResponse.model_validate(r) for r in responders]


@router.get("/{incident_id}", response_model=IncidentResponse)
def get_incident(
    incident_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Fetches details of a specific incident with strict role-based access control."""
    service = IncidentService(db)
    incident = service.get_incident(incident_id, current_user)
    return _to_incident_response(incident)


@router.get("/{incident_id}/timeline", response_model=List[IncidentEventResponse])
def get_incident_timeline(
    incident_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Retrieves the chronological audit timeline of events for an incident."""
    service = IncidentService(db)
    events = service.get_timeline(incident_id, current_user)
    return [
        IncidentEventResponse(
            id=ev.id,
            incident_id=ev.incident_id,
            actor_id=ev.actor_id,
            actor_name=ev.actor.full_name if ev.actor else ("SYSTEM" if ev.actor_role == "SYSTEM" else None),
            actor_role=ev.actor_role,
            event_type=ev.event_type,
            from_status=ev.from_status,
            to_status=ev.to_status,
            reason=ev.reason,
            details=ev.details,
            created_at=ev.created_at,
        )
        for ev in events
    ]


@router.post("/{incident_id}/transition", response_model=IncidentResponse)
async def transition_incident_state(
    incident_id: uuid.UUID,
    payload: IncidentTransitionRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    Executes an authoritative state machine transition.
    Server enforces allowed transitions and role authorization.
    """
    service = IncidentService(db)
    incident = await service.transition_incident(
        incident_id=incident_id,
        to_status=payload.to_status,
        actor=current_user,
        reason=payload.reason,
        resolution_notes=payload.resolution_notes,
    )
    return _to_incident_response(incident)


@router.post("/{incident_id}/assign", response_model=IncidentResponse)
async def assign_responder_to_incident(
    incident_id: uuid.UUID,
    payload: IncidentAssignRequest,
    current_user: User = Depends(require_authority_or_admin),
    db: Session = Depends(get_db),
):
    """Assigns or re-assigns a responder to an incident."""
    service = IncidentService(db)
    incident = await service.assign_responder(
        incident_id=incident_id,
        responder_id=payload.responder_id,
        assigned_by=current_user,
        notes=payload.notes,
    )
    return _to_incident_response(incident)
