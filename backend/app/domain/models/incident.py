import uuid
from datetime import datetime
from typing import Optional, List, TYPE_CHECKING
from sqlalchemy import Uuid, ForeignKey, Float, String, Text, DateTime, Enum as SAEnum, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.domain.models.base import UUIDModel
from backend.app.domain.models.enums import (
    IncidentSource,
    IncidentSeverity,
    IncidentStatus,
    LocationFreshness,
)

if TYPE_CHECKING:
    from backend.app.domain.models.user import User
    from backend.app.domain.models.trip import Trip
    from backend.app.domain.models.risk_assessment import RiskAssessment
    from backend.app.domain.models.incident_event import IncidentEvent
    from backend.app.domain.models.incident_assignment import IncidentAssignment


class Incident(UUIDModel):
    __tablename__ = "incidents"

    source: Mapped[IncidentSource] = mapped_column(
        SAEnum(IncidentSource, native_enum=False),
        nullable=False,
        index=True,
    )
    severity: Mapped[IncidentSeverity] = mapped_column(
        SAEnum(IncidentSeverity, native_enum=False),
        nullable=False,
        index=True,
    )
    status: Mapped[IncidentStatus] = mapped_column(
        SAEnum(IncidentStatus, native_enum=False),
        default=IncidentStatus.DETECTED,
        nullable=False,
        index=True,
    )

    tourist_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    trip_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("trips.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    latitude: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    longitude: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    accuracy: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    location_freshness: Mapped[LocationFreshness] = mapped_column(
        SAEnum(LocationFreshness, native_enum=False),
        default=LocationFreshness.UNKNOWN,
        nullable=False,
    )

    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    risk_assessment_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("risk_assessments.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    assigned_responder_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    idempotency_key: Mapped[Optional[str]] = mapped_column(
        String(128),
        unique=True,
        nullable=True,
        index=True,
    )

    resolution_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    resolved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    closed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    tourist: Mapped["User"] = relationship("User", foreign_keys=[tourist_id])
    trip: Mapped[Optional["Trip"]] = relationship("Trip", foreign_keys=[trip_id])
    risk_assessment: Mapped[Optional["RiskAssessment"]] = relationship("RiskAssessment", foreign_keys=[risk_assessment_id])
    assigned_responder: Mapped[Optional["User"]] = relationship("User", foreign_keys=[assigned_responder_id])
    events: Mapped[List["IncidentEvent"]] = relationship(
        "IncidentEvent",
        back_populates="incident",
        cascade="all, delete-orphan",
        order_by="IncidentEvent.created_at",
    )
    assignments: Mapped[List["IncidentAssignment"]] = relationship(
        "IncidentAssignment",
        back_populates="incident",
        cascade="all, delete-orphan",
        order_by="IncidentAssignment.assigned_at",
    )

    __table_args__ = (
        Index("ix_incidents_status_created", "status", "created_at"),
        Index("ix_incidents_tourist_created", "tourist_id", "created_at"),
        Index("ix_incidents_assigned_status", "assigned_responder_id", "status"),
    )
