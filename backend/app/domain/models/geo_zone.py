import uuid
from typing import Optional, List
from sqlalchemy import String, Boolean, Enum as SQLEnum, Text
from sqlalchemy.orm import Mapped, mapped_column
from geoalchemy2 import Geometry

from backend.app.domain.models.base import UUIDModel
from backend.app.domain.models.enums import GeoZoneType


class GeoZone(UUIDModel):
    __tablename__ = "geo_zones"

    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True, index=True)
    description: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    zone_type: Mapped[GeoZoneType] = mapped_column(
        SQLEnum(GeoZoneType, name="geozonetype"),
        nullable=False,
        default=GeoZoneType.SAFE,
        index=True,
    )

    # PostGIS Spatial Polygon (WGS 84, SRID 4326)
    geom = mapped_column(
        Geometry(geometry_type="POLYGON", srid=4326, spatial_index=True),
        nullable=True,
    )

    # GeoJSON coordinates serialized as JSON string: [[[lng, lat], [lng, lat], ...]]
    coordinates_json: Mapped[str] = mapped_column(Text, nullable=False)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, index=True)
