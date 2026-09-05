import uuid
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from backend.app.core.logging import logger
from backend.app.domain.models.enums import (
    IncidentSource,
    IncidentSeverity,
    IncidentStatus,
    IncidentEventType,
    AssignmentStatus,
    LocationFreshness,
    UserRole,
    EmergencyStatus,
    TripStatus,
    AuditEventType,
    AuditOutcome,
)
from backend.app.domain.models.incident import Incident
from backend.app.domain.models.incident_event import IncidentEvent
from backend.app.domain.models.incident_assignment import IncidentAssignment
from backend.app.domain.models.risk_assessment import RiskAssessment
from backend.app.domain.models.user import User
from backend.app.repositories.incident_repository import IncidentRepository
from backend.app.repositories.location_repository import LocationRepository
from backend.app.repositories.trip_repository import TripRepository
from backend.app.repositories.user_repository import UserRepository
from backend.app.repositories.audit_repository import AuditRepository
from backend.app.services.incident_state_machine import IncidentStateMachine
from backend.app.services.notification_service import NotificationService
from backend.app.services.websocket_manager import ws_manager


class IncidentService:
    def __init__(self, db: Session):
        self.db = db
        self.incident_repo = IncidentRepository(db)
        self.location_repo = LocationRepository(db)
        self.trip_repo = TripRepository(db)
        self.user_repo = UserRepository(db)
        self.audit_repo = AuditRepository(db)
        self.notification_service = NotificationService(db)

    async def create_sos(
        self,
        current_user: User,
        trip_id: Optional[uuid.UUID] = None,
        latitude: Optional[float] = None,
        longitude: Optional[float] = None,
        accuracy: Optional[float] = None,
        description: Optional[str] = None,
        idempotency_key: Optional[str] = None,
    ) -> Incident:
        """
        Creates an emergency SOS incident triggered by a tourist.
        CRITICAL: Completely decoupled from AI/Risk Engine/CCTV/Blockchain.
        """
        if current_user.role != UserRole.TOURIST:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only tourists can activate emergency SOS.",
            )

        # 1. Idempotency Check
        if idempotency_key:
            existing = self.incident_repo.get_by_idempotency_key(idempotency_key)
            if existing:
                logger.info(f"Duplicate SOS suppressed by idempotency_key: {idempotency_key}")
                return existing

        # 2. Location Resolution (provided -> latest DB location -> UNKNOWN)
        freshness = LocationFreshness.UNKNOWN
        if latitude is not None and longitude is not None:
            freshness = LocationFreshness.LIVE
        else:
            # Fallback: attempt to retrieve latest recorded location from DB
            latest_loc = self.location_repo.get_latest_for_tourist(current_user.id)
            if latest_loc:
                latitude = latest_loc.latitude
                longitude = latest_loc.longitude
                accuracy = latest_loc.accuracy
                # Determine freshness based on age
                age = (datetime.now(timezone.utc) - latest_loc.recorded_at).total_seconds()
                freshness = LocationFreshness.RECENT if age < 300 else LocationFreshness.STALE

        # 3. Trip association validation
        if trip_id:
            trip = self.trip_repo.get(trip_id)
            if trip and trip.tourist_id == current_user.id:
                trip.emergency_status = EmergencyStatus.SOS
                self.db.add(trip)
                self.db.commit()
            else:
                trip_id = None
        else:
            # Auto-associate active trip if any exists
            active_trips = self.trip_repo.get_by_tourist_id(
                tourist_id=current_user.id,
                status=TripStatus.ACTIVE,
            )
            if active_trips:
                trip_id = active_trips[0].id
                active_trips[0].emergency_status = EmergencyStatus.SOS
                self.db.add(active_trips[0])
                self.db.commit()

        # 4. Create Incident
        incident = Incident(
            source=IncidentSource.SOS,
            severity=IncidentSeverity.CRITICAL,
            status=IncidentStatus.DETECTED,
            tourist_id=current_user.id,
            trip_id=trip_id,
            latitude=latitude,
            longitude=longitude,
            accuracy=accuracy,
            location_freshness=freshness,
            description=description or "Manual SOS emergency activated by tourist.",
            idempotency_key=idempotency_key,
        )
        saved = self.incident_repo.create(incident)

        # 5. Create Initial IncidentEvent and Cryptographic AuditEvent
        event = IncidentEvent(
            incident_id=saved.id,
            actor_id=current_user.id,
            actor_role=current_user.role.value,
            event_type=IncidentEventType.INCIDENT_CREATED,
            from_status=None,
            to_status=IncidentStatus.DETECTED,
            reason="Emergency SOS button activated",
            details={
                "source": "SOS",
                "severity": "CRITICAL",
                "has_coordinates": latitude is not None and longitude is not None,
                "location_freshness": freshness.value,
            },
        )
        self.incident_repo.create_event(event)

        self.audit_repo.create_event(
            event_type=AuditEventType.INCIDENT_CREATE,
            action="CREATE_SOS",
            resource_type="INCIDENT",
            resource_id=str(saved.id),
            actor_id=current_user.id,
            actor_email=current_user.email,
            actor_role=current_user.role.value,
            outcome=AuditOutcome.SUCCESS,
            details={
                "source": "SOS",
                "severity": "CRITICAL",
                "trip_id": str(trip_id) if trip_id else None,
                "idempotency_key": idempotency_key,
            },
        )

        # 6. Fault-tolerant Notifications & WebSocket Broadcast
        try:
            coord_str = f"({latitude:.4f}, {longitude:.4f})" if latitude and longitude else "(Location Unavailable)"
            await self.notification_service.notify_authorities(
                title="CRITICAL SOS ALERT",
                message=f"Tourist {current_user.full_name} triggered emergency SOS {coord_str}.",
                incident_id=saved.id,
                idempotency_prefix=f"sos_notif_{saved.id}",
                payload={"incident_id": str(saved.id), "source": "SOS", "severity": "CRITICAL"},
            )
            await ws_manager.broadcast_incident_event(
                "CREATED",
                {
                    "incident_id": str(saved.id),
                    "source": saved.source.value,
                    "severity": saved.severity.value,
                    "status": saved.status.value,
                    "tourist_id": str(current_user.id),
                    "tourist_name": current_user.full_name,
                    "latitude": saved.latitude,
                    "longitude": saved.longitude,
                    "created_at": saved.created_at.isoformat(),
                },
            )
        except Exception as e:
            logger.error(f"Post-SOS notification/broadcast error (incident safely saved): {e}")

        return saved

    async def create_from_risk(self, risk_assessment: RiskAssessment) -> Optional[Incident]:
        """
        Creates an incident signaled by the Risk Engine (Phase 15).
        Enters status DETECTED and requires human authority verification.
        """
        # Suppress duplicate risk incidents if an open one already exists for this trip
        existing = self.incident_repo.get_active_incident_for_tourist(
            tourist_id=risk_assessment.tourist_id,
            source=IncidentSource.RISK_ENGINE,
            trip_id=risk_assessment.trip_id,
        )
        if existing:
            return existing

        loc = risk_assessment.location_event
        lat = loc.latitude if loc else None
        lon = loc.longitude if loc else None
        acc = loc.accuracy if loc else None

        severity = IncidentSeverity.HIGH
        if risk_assessment.risk_score >= 0.85:
            severity = IncidentSeverity.CRITICAL

        incident = Incident(
            source=IncidentSource.RISK_ENGINE,
            severity=severity,
            status=IncidentStatus.DETECTED,
            tourist_id=risk_assessment.tourist_id,
            trip_id=risk_assessment.trip_id,
            latitude=lat,
            longitude=lon,
            accuracy=acc,
            location_freshness=LocationFreshness.LIVE if loc else LocationFreshness.UNKNOWN,
            description=f"Risk Engine Alert: {risk_assessment.explanation}",
            risk_assessment_id=risk_assessment.id,
        )
        saved = self.incident_repo.create(incident)

        event = IncidentEvent(
            incident_id=saved.id,
            actor_id=None,
            actor_role="SYSTEM",
            event_type=IncidentEventType.INCIDENT_CREATED,
            from_status=None,
            to_status=IncidentStatus.DETECTED,
            reason=f"Risk score {risk_assessment.risk_score:.2f} exceeded threshold ({risk_assessment.recommended_action.value})",
            details={
                "risk_score": risk_assessment.risk_score,
                "risk_level": risk_assessment.risk_level.value,
                "model_version": risk_assessment.model_version,
            },
        )
        self.incident_repo.create_event(event)

        try:
            await self.notification_service.notify_authorities(
                title="HIGH RISK INCIDENT DETECTED",
                message=f"Risk Engine flagged potential safety hazard for Tourist: {risk_assessment.explanation}",
                incident_id=saved.id,
                idempotency_prefix=f"risk_notif_{saved.id}",
                payload={"incident_id": str(saved.id), "source": "RISK_ENGINE", "severity": severity.value},
            )
            await ws_manager.broadcast_incident_event(
                "CREATED",
                {
                    "incident_id": str(saved.id),
                    "source": saved.source.value,
                    "severity": saved.severity.value,
                    "status": saved.status.value,
                    "tourist_id": str(risk_assessment.tourist_id),
                    "created_at": saved.created_at.isoformat(),
                },
            )
        except Exception as e:
            logger.error(f"Error during risk notification/broadcast: {e}")

        return saved

    async def transition_incident(
        self,
        incident_id: uuid.UUID,
        to_status: IncidentStatus,
        actor: User,
        reason: Optional[str] = None,
        resolution_notes: Optional[str] = None,
    ) -> Incident:
        """
        Authoritatively validates and performs a state machine transition.
        Records an append-only audit event and notifies participants.
        """
        incident = self.incident_repo.get(incident_id)
        if not incident:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Incident not found.")

        # 1. State Machine Validation
        IncidentStateMachine.validate_transition(
            incident=incident,
            to_state=to_status,
            actor=actor,
            notes=reason,
        )

        from_status = incident.status
        now = datetime.now(timezone.utc)

        # 2. Update Incident Fields based on target state
        incident.status = to_status
        if to_status == IncidentStatus.RESOLVED:
            incident.resolved_at = now
            if resolution_notes:
                incident.resolution_notes = resolution_notes
            elif reason:
                incident.resolution_notes = reason
        elif to_status == IncidentStatus.CLOSED:
            incident.closed_at = now
            # Restore trip emergency status if trip exists and no other active SOS
            if incident.trip and incident.trip.emergency_status == EmergencyStatus.SOS:
                other_sos = self.incident_repo.get_active_incident_for_tourist(
                    tourist_id=incident.tourist_id,
                    source=IncidentSource.SOS,
                    trip_id=incident.trip_id,
                )
                if not other_sos:
                    incident.trip.emergency_status = EmergencyStatus.NORMAL
                    self.db.add(incident.trip)

        saved = self.incident_repo.update(incident)

        # 3. Determine Event Type
        event_type = IncidentEventType.STATUS_CHANGED
        if to_status == IncidentStatus.VERIFIED:
            event_type = IncidentEventType.INCIDENT_VERIFIED
        elif to_status == IncidentStatus.ESCALATED:
            event_type = IncidentEventType.INCIDENT_ESCALATED
        elif to_status == IncidentStatus.ASSIGNED:
            event_type = IncidentEventType.INCIDENT_ASSIGNED
        elif to_status == IncidentStatus.RESPONDING:
            event_type = IncidentEventType.RESPONSE_STARTED
        elif to_status == IncidentStatus.RESOLVED:
            event_type = IncidentEventType.INCIDENT_RESOLVED
        elif to_status == IncidentStatus.CLOSED:
            event_type = IncidentEventType.INCIDENT_CLOSED
        elif to_status == IncidentStatus.DISMISSED:
            event_type = IncidentEventType.INCIDENT_DISMISSED

        # 4. Append-Only Incident Event and Cryptographic Audit Record
        audit_event = IncidentEvent(
            incident_id=saved.id,
            actor_id=actor.id,
            actor_role=actor.role.value,
            event_type=event_type,
            from_status=from_status,
            to_status=to_status,
            reason=reason or f"Transitioned from {from_status.value} to {to_status.value}",
            details={"resolution_notes": resolution_notes} if resolution_notes else {},
        )
        self.incident_repo.create_event(audit_event)

        self.audit_repo.create_event(
            event_type=AuditEventType.INCIDENT_STATE_TRANSITION,
            action=f"TRANSITION_{to_status.value}",
            resource_type="INCIDENT",
            resource_id=str(saved.id),
            actor_id=actor.id,
            actor_email=actor.email,
            actor_role=actor.role.value,
            outcome=AuditOutcome.SUCCESS,
            details={
                "from_status": from_status.value,
                "to_status": to_status.value,
                "reason": reason,
                "resolution_notes": resolution_notes,
            },
        )

        # 5. Notify Relevant Parties & WebSocket Broadcast
        try:
            # Notify Assigned Responder
            if incident.assigned_responder_id and incident.assigned_responder_id != actor.id:
                await self.notification_service.notify_user(
                    recipient_id=incident.assigned_responder_id,
                    title=f"Incident Status: {to_status.value}",
                    message=f"Incident {incident.id} status changed to {to_status.value}.",
                    incident_id=incident.id,
                )
            # Notify Tourist on Resolution/Closure
            if to_status in [IncidentStatus.RESOLVED, IncidentStatus.CLOSED]:
                await self.notification_service.notify_user(
                    recipient_id=incident.tourist_id,
                    title="Incident Resolved",
                    message=f"Your safety incident has been marked {to_status.value} by response authorities.",
                    incident_id=incident.id,
                )

            await ws_manager.broadcast_incident_event(
                "STATUS_CHANGED",
                {
                    "incident_id": str(saved.id),
                    "from_status": from_status.value,
                    "to_status": to_status.value,
                    "actor_id": str(actor.id),
                    "actor_name": actor.full_name,
                    "reason": reason,
                    "timestamp": now.isoformat(),
                },
            )
        except Exception as e:
            logger.error(f"Error broadcasting state transition: {e}")

        return saved

    async def assign_responder(
        self,
        incident_id: uuid.UUID,
        responder_id: uuid.UUID,
        assigned_by: User,
        notes: Optional[str] = None,
    ) -> Incident:
        """
        Assigns or re-assigns a responder to an incident.
        Preserves complete assignment history.
        """
        if assigned_by.role not in [UserRole.AUTHORITY, UserRole.ADMIN]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only authorities and administrators can assign responders to incidents.",
            )

        incident = self.incident_repo.get(incident_id)
        if not incident:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Incident not found.")

        if incident.status in [IncidentStatus.CLOSED, IncidentStatus.DISMISSED]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot assign responder to incident in terminal state '{incident.status.value}'.",
            )

        responder = self.user_repo.get(responder_id)
        if not responder or responder.role != UserRole.RESPONDER:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Target user is not a valid responder.",
            )

        now = datetime.now(timezone.utc)

        # 1. Deactivate existing active assignment if re-assigning
        active_assignment = self.incident_repo.get_active_assignment(incident_id)
        if active_assignment:
            active_assignment.status = AssignmentStatus.REASSIGNED
            active_assignment.unassigned_at = now
            self.db.add(active_assignment)

        # 2. Create new IncidentAssignment
        new_assignment = IncidentAssignment(
            incident_id=incident.id,
            responder_id=responder.id,
            assigned_by_id=assigned_by.id,
            assigned_at=now,
            status=AssignmentStatus.ACTIVE,
            notes=notes,
        )
        self.incident_repo.create_assignment(new_assignment)

        # 3. Update Incident responder reference
        incident.assigned_responder_id = responder.id

        # If incident was in VERIFIED or ESCALATED, advance state to ASSIGNED
        if incident.status in [IncidentStatus.VERIFIED, IncidentStatus.ESCALATED]:
            incident.status = IncidentStatus.ASSIGNED

        saved = self.incident_repo.update(incident)

        # 4. Audit Event & Cryptographic Audit Log
        event = IncidentEvent(
            incident_id=incident.id,
            actor_id=assigned_by.id,
            actor_role=assigned_by.role.value,
            event_type=IncidentEventType.INCIDENT_ASSIGNED,
            from_status=None,
            to_status=incident.status,
            reason=f"Assigned to responder {responder.full_name}",
            details={"responder_id": str(responder.id), "notes": notes},
        )
        self.incident_repo.create_event(event)

        self.audit_repo.create_event(
            event_type=AuditEventType.INCIDENT_ASSIGNMENT,
            action="ASSIGN_RESPONDER",
            resource_type="INCIDENT",
            resource_id=str(incident.id),
            actor_id=assigned_by.id,
            actor_email=assigned_by.email,
            actor_role=assigned_by.role.value,
            outcome=AuditOutcome.SUCCESS,
            details={
                "responder_id": str(responder.id),
                "responder_name": responder.full_name,
                "notes": notes,
            },
        )

        # 5. Notify Assigned Responder & Broadcast
        try:
            await self.notification_service.notify_user(
                recipient_id=responder.id,
                title="NEW EMERGENCY ASSIGNMENT",
                message=f"You have been assigned to Incident {incident.id}. Location: ({incident.latitude}, {incident.longitude}).",
                incident_id=incident.id,
                idempotency_key=f"assign_{incident.id}_{responder.id}",
                payload={"incident_id": str(incident.id), "action": "ASSIGNED"},
            )
            await ws_manager.broadcast_incident_event(
                "ASSIGNED",
                {
                    "incident_id": str(saved.id),
                    "responder_id": str(responder.id),
                    "responder_name": responder.full_name,
                    "assigned_by": assigned_by.full_name,
                    "status": saved.status.value,
                    "timestamp": now.isoformat(),
                },
            )
        except Exception as e:
            logger.error(f"Error during assignment notification/broadcast: {e}")

        return saved

    def get_incident(self, incident_id: uuid.UUID, current_user: User) -> Incident:
        incident = self.incident_repo.get(incident_id)
        if not incident:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Incident not found.")

        # RBAC Check
        if current_user.role in [UserRole.AUTHORITY, UserRole.ADMIN]:
            return incident
        if current_user.role == UserRole.RESPONDER:
            if incident.assigned_responder_id != current_user.id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Responders can only access incidents assigned to them.",
                )
            return incident
        if current_user.role == UserRole.TOURIST:
            if incident.tourist_id != current_user.id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Tourists can only view their own incidents.",
                )
            return incident

        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied.")

    def list_incidents(
        self,
        current_user: User,
        status_filter: Optional[IncidentStatus] = None,
        severity_filter: Optional[IncidentSeverity] = None,
        source_filter: Optional[IncidentSource] = None,
        exclude_terminal: bool = False,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Incident]:
        if current_user.role in [UserRole.AUTHORITY, UserRole.ADMIN]:
            return self.incident_repo.list_incidents(
                status=status_filter,
                severity=severity_filter,
                source=source_filter,
                exclude_terminal=exclude_terminal,
                limit=limit,
                offset=offset,
            )
        elif current_user.role == UserRole.RESPONDER:
            return self.incident_repo.list_incidents(
                status=status_filter,
                severity=severity_filter,
                source=source_filter,
                responder_id=current_user.id,
                exclude_terminal=exclude_terminal,
                limit=limit,
                offset=offset,
            )
        elif current_user.role == UserRole.TOURIST:
            return self.incident_repo.list_incidents(
                status=status_filter,
                severity=severity_filter,
                source=source_filter,
                tourist_id=current_user.id,
                exclude_terminal=exclude_terminal,
                limit=limit,
                offset=offset,
            )
        return []

    def get_timeline(self, incident_id: uuid.UUID, current_user: User) -> List[IncidentEvent]:
        # Verify access to the parent incident first
        self.get_incident(incident_id, current_user)
        return self.incident_repo.get_timeline(incident_id)

    def list_available_responders(self, current_user: User) -> List[User]:
        if current_user.role not in [UserRole.AUTHORITY, UserRole.ADMIN]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only authorities and administrators can list responders.",
            )
        return self.incident_repo.list_available_responders()
