import uuid
from datetime import datetime
from typing import Optional, TYPE_CHECKING
from sqlalchemy import Uuid, ForeignKey, DateTime, Enum as SQLEnum, UniqueConstraint, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.domain.models.base import UUIDModel, TimestampMixin, utc_now
from backend.app.domain.models.enums import ZoneEventType

if TYPE_CHECKING:
    from backend.app.domain.models.user import User
    from backend.app.domain.models.trip import Trip
    from backend.app.domain.models.geo_zone import GeoZone
    from backend.app.domain.models.location_event import LocationEvent


class TouristZoneState(UUIDModel):
    """Tracks the current occupancy state of a tourist inside active GeoZones."""
    __tablename__ = "tourist_zone_states"

    tourist_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    zone_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("geo_zones.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    entered_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        nullable=False,
    )
    last_seen_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        onupdate=utc_now,
        nullable=False,
    )

    tourist: Mapped["User"] = relationship("User")
    zone: Mapped["GeoZone"] = relationship("GeoZone")

    __table_args__ = (
        UniqueConstraint("tourist_id", "zone_id", name="uq_tourist_zone_occupancy"),
    )


class ZoneEvent(UUIDModel):
    """Historical audit log of geofence ENTER and EXIT transitions."""
    __tablename__ = "zone_events"

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
    zone_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("geo_zones.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    event_type: Mapped[ZoneEventType] = mapped_column(
        SQLEnum(ZoneEventType, name="zoneeventtype"),
        nullable=False,
        index=True,
    )
    location_event_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("location_events.id", ondelete="SET NULL"),
        nullable=True,
    )
    occurred_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        nullable=False,
        index=True,
    )

    tourist: Mapped["User"] = relationship("User")
    trip: Mapped["Trip"] = relationship("Trip")
    zone: Mapped["GeoZone"] = relationship("GeoZone")
    location_event: Mapped[Optional["LocationEvent"]] = relationship("LocationEvent")

    __table_args__ = (
        Index("ix_zone_events_tourist_occurred", "tourist_id", "occurred_at"),
        Index("ix_zone_events_zone_occurred", "zone_id", "occurred_at"),
    )
