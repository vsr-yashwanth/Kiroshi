from sqlalchemy import Column, String, Float, Boolean, JSON
from geoalchemy2 import Geometry
from backend.app.domain.models.base import UUIDModel, TimestampMixin
from backend.app.domain.models.enums import CameraStatus


class Camera(UUIDModel, TimestampMixin):
    __tablename__ = "cameras"

    name = Column(String(100), nullable=False)
    description = Column(String(255), nullable=True)
    status = Column(String(30), default=CameraStatus.ACTIVE.value, nullable=False)
    
    # PostGIS Point location (WGS84 SRID 4326)
    location = Column(Geometry("POINT", srid=4326, spatial_index=True), nullable=False)
    coverage_radius_meters = Column(Float, default=50.0, nullable=False)
    
    # Simulated vs Real Provider
    is_simulated = Column(Boolean, default=True, nullable=False)
    stream_url = Column(String(500), nullable=True)
    camera_metadata = Column(JSON, default=dict, nullable=False)

    @property
    def latitude(self) -> float:
        # Helper for serialized responses
        return 0.0

    @property
    def longitude(self) -> float:
        return 0.0
