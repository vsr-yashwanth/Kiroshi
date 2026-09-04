import uuid
from typing import Optional, Dict, Any, List, TYPE_CHECKING
from sqlalchemy import Uuid, ForeignKey, Float, String, Text, JSON, Enum as SAEnum, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.domain.models.base import UUIDModel
from backend.app.domain.models.enums import RiskLevel, RecommendedAction

if TYPE_CHECKING:
    from backend.app.domain.models.user import User
    from backend.app.domain.models.trip import Trip
    from backend.app.domain.models.location_event import LocationEvent


class RiskAssessment(UUIDModel):
    __tablename__ = "risk_assessments"

    tourist_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    trip_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("trips.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    location_event_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("location_events.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    risk_score: Mapped[float] = mapped_column(Float, nullable=False, index=True)
    risk_level: Mapped[RiskLevel] = mapped_column(
        SAEnum(RiskLevel, native_enum=False),
        nullable=False,
        index=True,
    )
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    contributing_signals: Mapped[List[Dict[str, Any]]] = mapped_column(
        JSON,
        nullable=False,
        default=list,
    )
    explanation: Mapped[str] = mapped_column(Text, nullable=False)
    recommended_action: Mapped[RecommendedAction] = mapped_column(
        SAEnum(RecommendedAction, native_enum=False),
        nullable=False,
    )
    model_version: Mapped[str] = mapped_column(String(50), nullable=False)

    # Relationships
    tourist: Mapped["User"] = relationship("User")
    trip: Mapped["Trip"] = relationship("Trip")
    location_event: Mapped[Optional["LocationEvent"]] = relationship("LocationEvent")

    __table_args__ = (
        Index("ix_risk_assessments_created_at", "created_at"),
        Index("idx_risk_assessments_tourist_created", "tourist_id", "created_at"),
        Index("idx_risk_assessments_trip_created", "trip_id", "created_at"),
    )
