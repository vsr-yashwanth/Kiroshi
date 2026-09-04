import uuid
from datetime import datetime
from typing import Optional, TYPE_CHECKING
from sqlalchemy import Uuid, ForeignKey, Text, DateTime, Enum as SAEnum, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.domain.models.base import UUIDModel, utc_now
from backend.app.domain.models.enums import AssignmentStatus

if TYPE_CHECKING:
    from backend.app.domain.models.incident import Incident
    from backend.app.domain.models.user import User


class IncidentAssignment(UUIDModel):
    __tablename__ = "incident_assignments"

    incident_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("incidents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    responder_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    assigned_by_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    assigned_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        nullable=False,
    )
    unassigned_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    status: Mapped[AssignmentStatus] = mapped_column(
        SAEnum(AssignmentStatus, native_enum=False),
        default=AssignmentStatus.ACTIVE,
        nullable=False,
        index=True,
    )
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    incident: Mapped["Incident"] = relationship("Incident", back_populates="assignments")
    responder: Mapped["User"] = relationship("User", foreign_keys=[responder_id])
    assigned_by: Mapped["User"] = relationship("User", foreign_keys=[assigned_by_id])

    __table_args__ = (
        Index("ix_incident_assignments_responder_status", "responder_id", "status"),
        Index("ix_incident_assignments_incident_assigned", "incident_id", "assigned_at"),
    )
