import uuid
from datetime import datetime
from typing import TYPE_CHECKING, List, Optional
from sqlalchemy import String, Text, DateTime, ForeignKey, Uuid, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.domain.models.base import UUIDModel
from backend.app.domain.models.enums import TripStatus, EmergencyStatus

if TYPE_CHECKING:
    from backend.app.domain.models.user import User
    from backend.app.domain.models.itinerary import Itinerary


class Trip(UUIDModel):
    __tablename__ = "trips"

    tourist_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    start_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    end_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    status: Mapped[TripStatus] = mapped_column(
        SQLEnum(TripStatus, name="trip_status", native_enum=False),
        default=TripStatus.PLANNED,
        nullable=False,
        index=True,
    )
    emergency_status: Mapped[EmergencyStatus] = mapped_column(
        SQLEnum(EmergencyStatus, name="emergency_status", native_enum=False),
        default=EmergencyStatus.NORMAL,
        nullable=False,
        index=True,
    )

    # Relationships
    tourist: Mapped["User"] = relationship(
        "User",
        back_populates="trips",
    )
    itineraries: Mapped[List["Itinerary"]] = relationship(
        "Itinerary",
        back_populates="trip",
        cascade="all, delete-orphan",
        order_by="Itinerary.sequence_order",
    )
