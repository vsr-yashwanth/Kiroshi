import uuid
from datetime import datetime, timezone
from typing import Optional, List
from sqlalchemy import select, and_, func
from sqlalchemy.orm import Session, joinedload

from backend.app.domain.models.incident import Incident
from backend.app.domain.models.incident_event import IncidentEvent
from backend.app.domain.models.incident_assignment import IncidentAssignment
from backend.app.domain.models.user import User
from backend.app.domain.models.enums import (
    IncidentStatus,
    IncidentSeverity,
    IncidentSource,
    AssignmentStatus,
    UserRole,
)


class IncidentRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, incident: Incident) -> Incident:
        self.db.add(incident)
        self.db.commit()
        self.db.refresh(incident)
        return incident

    def update(self, incident: Incident) -> Incident:
        self.db.add(incident)
        self.db.commit()
        self.db.refresh(incident)
        return incident

    def get(self, incident_id: uuid.UUID) -> Optional[Incident]:
        stmt = (
            select(Incident)
            .where(Incident.id == incident_id)
            .options(
                joinedload(Incident.tourist),
                joinedload(Incident.trip),
                joinedload(Incident.assigned_responder),
                joinedload(Incident.risk_assessment),
            )
        )
        return self.db.execute(stmt).unique().scalar_one_or_none()

    def get_by_idempotency_key(self, idempotency_key: str) -> Optional[Incident]:
        stmt = (
            select(Incident)
            .where(Incident.idempotency_key == idempotency_key)
            .options(
                joinedload(Incident.tourist),
                joinedload(Incident.trip),
            )
        )
        return self.db.execute(stmt).unique().scalar_one_or_none()

    def get_active_incident_for_tourist(
        self,
        tourist_id: uuid.UUID,
        source: Optional[IncidentSource] = None,
        trip_id: Optional[uuid.UUID] = None,
    ) -> Optional[Incident]:
        """Finds any ongoing (non-closed, non-dismissed) incident for a tourist."""
        filters = [
            Incident.tourist_id == tourist_id,
            Incident.status.notin_([IncidentStatus.CLOSED, IncidentStatus.DISMISSED]),
        ]
        if source:
            filters.append(Incident.source == source)
        if trip_id:
            filters.append(Incident.trip_id == trip_id)

        stmt = select(Incident).where(and_(*filters)).order_by(Incident.created_at.desc()).limit(1)
        return self.db.execute(stmt).scalar_one_or_none()

    def list_incidents(
        self,
        status: Optional[IncidentStatus] = None,
        severity: Optional[IncidentSeverity] = None,
        source: Optional[IncidentSource] = None,
        tourist_id: Optional[uuid.UUID] = None,
        responder_id: Optional[uuid.UUID] = None,
        exclude_terminal: bool = False,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Incident]:
        filters = []
        if status:
            filters.append(Incident.status == status)
        elif exclude_terminal:
            filters.append(Incident.status.notin_([IncidentStatus.CLOSED, IncidentStatus.DISMISSED]))

        if severity:
            filters.append(Incident.severity == severity)
        if source:
            filters.append(Incident.source == source)
        if tourist_id:
            filters.append(Incident.tourist_id == tourist_id)
        if responder_id:
            filters.append(Incident.assigned_responder_id == responder_id)

        stmt = (
            select(Incident)
            .where(and_(*filters) if filters else True)
            .options(
                joinedload(Incident.tourist),
                joinedload(Incident.trip),
                joinedload(Incident.assigned_responder),
            )
            .order_by(Incident.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        return list(self.db.execute(stmt).unique().scalars().all())

    def count_incidents(
        self,
        status: Optional[IncidentStatus] = None,
        severity: Optional[IncidentSeverity] = None,
        exclude_terminal: bool = False,
    ) -> int:
        filters = []
        if status:
            filters.append(Incident.status == status)
        elif exclude_terminal:
            filters.append(Incident.status.notin_([IncidentStatus.CLOSED, IncidentStatus.DISMISSED]))
        if severity:
            filters.append(Incident.severity == severity)

        stmt = select(func.count(Incident.id)).where(and_(*filters) if filters else True)
        return self.db.execute(stmt).scalar() or 0

    # Incident Events / Timeline
    def create_event(self, event: IncidentEvent) -> IncidentEvent:
        self.db.add(event)
        self.db.commit()
        self.db.refresh(event)
        return event

    def get_timeline(self, incident_id: uuid.UUID) -> List[IncidentEvent]:
        stmt = (
            select(IncidentEvent)
            .where(IncidentEvent.incident_id == incident_id)
            .options(joinedload(IncidentEvent.actor))
            .order_by(IncidentEvent.created_at.asc())
        )
        return list(self.db.execute(stmt).unique().scalars().all())

    # Incident Assignments
    def create_assignment(self, assignment: IncidentAssignment) -> IncidentAssignment:
        self.db.add(assignment)
        self.db.commit()
        self.db.refresh(assignment)
        return assignment

    def get_active_assignment(self, incident_id: uuid.UUID) -> Optional[IncidentAssignment]:
        stmt = (
            select(IncidentAssignment)
            .where(
                and_(
                    IncidentAssignment.incident_id == incident_id,
                    IncidentAssignment.status == AssignmentStatus.ACTIVE,
                )
            )
            .order_by(IncidentAssignment.assigned_at.desc())
            .limit(1)
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def get_assignment_history(self, incident_id: uuid.UUID) -> List[IncidentAssignment]:
        stmt = (
            select(IncidentAssignment)
            .where(IncidentAssignment.incident_id == incident_id)
            .options(
                joinedload(IncidentAssignment.responder),
                joinedload(IncidentAssignment.assigned_by),
            )
            .order_by(IncidentAssignment.assigned_at.asc())
        )
        return list(self.db.execute(stmt).unique().scalars().all())

    def list_available_responders(self) -> List[User]:
        stmt = (
            select(User)
            .where(and_(User.role == UserRole.RESPONDER, User.is_active == True))
            .order_by(User.full_name.asc())
        )
        return list(self.db.execute(stmt).scalars().all())
