import uuid
from typing import Optional, Dict, Any, TYPE_CHECKING
from sqlalchemy import Uuid, ForeignKey, String, Text, JSON, Enum as SAEnum, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.domain.models.base import UUIDModel
from backend.app.domain.models.enums import IncidentEventType, IncidentStatus

if TYPE_CHECKING:
    from backend.app.domain.models.incident import Incident
    from backend.app.domain.models.user import User


class IncidentEvent(UUIDModel):
    __tablename__ = "incident_events"

    incident_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("incidents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    actor_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    actor_role: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    event_type: Mapped[IncidentEventType] = mapped_column(
        SAEnum(IncidentEventType, native_enum=False),
        nullable=False,
        index=True,
    )
    from_status: Mapped[Optional[IncidentStatus]] = mapped_column(
        SAEnum(IncidentStatus, native_enum=False),
        nullable=True,
    )
    to_status: Mapped[Optional[IncidentStatus]] = mapped_column(
        SAEnum(IncidentStatus, native_enum=False),
        nullable=True,
    )

    reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    details: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True, default=dict)

    # Relationships
    incident: Mapped["Incident"] = relationship("Incident", back_populates="events")
    actor: Mapped[Optional["User"]] = relationship("User", foreign_keys=[actor_id])

    __table_args__ = (
        Index("ix_incident_events_incident_created", "incident_id", "created_at"),
    )
