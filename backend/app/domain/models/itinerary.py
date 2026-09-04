import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Optional
from sqlalchemy import String, Integer, Float, DateTime, ForeignKey, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.domain.models.base import UUIDModel

if TYPE_CHECKING:
    from backend.app.domain.models.trip import Trip


class Itinerary(UUIDModel):
    __tablename__ = "itineraries"

    trip_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("trips.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    destination_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    planned_arrival: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    planned_departure: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    latitude: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )
    longitude: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )
    sequence_order: Mapped[int] = mapped_column(
        Integer,
        default=1,
        nullable=False,
    )

    # Relationships
    trip: Mapped["Trip"] = relationship(
        "Trip",
        back_populates="itineraries",
    )
