import uuid
from datetime import datetime, timezone
from typing import Optional, TYPE_CHECKING
from sqlalchemy import Uuid, ForeignKey, Float, DateTime, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from geoalchemy2 import Geometry

from backend.app.core.database import Base
from backend.app.domain.models.base import TimestampMixin, UUIDModel, utc_now

if TYPE_CHECKING:
    from backend.app.domain.models.user import User
    from backend.app.domain.models.trip import Trip


class LocationEvent(UUIDModel):
    __tablename__ = "location_events"

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

    latitude: Mapped[float] = mapped_column(Float, nullable=False)
    longitude: Mapped[float] = mapped_column(Float, nullable=False)
    accuracy: Mapped[float] = mapped_column(Float, nullable=False)  # in meters
    altitude: Mapped[Optional[float]] = mapped_column(Float, nullable=True)  # in meters
    speed: Mapped[Optional[float]] = mapped_column(Float, nullable=True)  # in m/s
    heading: Mapped[Optional[float]] = mapped_column(Float, nullable=True)  # in degrees [0, 360)

    # PostGIS Spatial Point (WGS 84, SRID 4326)
    geom = mapped_column(
        Geometry(geometry_type="POINT", srid=4326, spatial_index=True),
        nullable=True,
    )

    recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
        doc="Timestamp recorded by client GPS hardware",
    )
    received_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        nullable=False,
        doc="Timestamp ingested by backend server",
    )

    # Relationships
    tourist: Mapped["User"] = relationship("User", foreign_keys=[tourist_id])
    trip: Mapped["Trip"] = relationship("Trip", foreign_keys=[trip_id])

    __table_args__ = (
        Index("ix_location_events_tourist_recorded", "tourist_id", "recorded_at"),
        Index("ix_location_events_trip_recorded", "trip_id", "recorded_at"),
    )
