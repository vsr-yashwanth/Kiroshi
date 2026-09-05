from sqlalchemy import Column, String, Float, DateTime, JSON, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID
from backend.app.domain.models.base import UUIDModel, TimestampMixin
from backend.app.domain.models.enums import InvestigationStatus


class CCTVInvestigation(UUIDModel, TimestampMixin):
    __tablename__ = "cctv_investigations"

    incident_id = Column(UUID(as_uuid=True), ForeignKey("incidents.id", ondelete="CASCADE"), nullable=False, index=True)
    requested_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    
    status = Column(String(50), default=InvestigationStatus.REQUESTED.value, nullable=False, index=True)
    search_radius_meters = Column(Float, default=200.0, nullable=False)
    
    time_window_start = Column(DateTime(timezone=True), nullable=False)
    time_window_end = Column(DateTime(timezone=True), nullable=False)
    
    cameras_queried_count = Column(Float, default=0)
    cameras_queried = Column(JSON, default=list, nullable=False)  # List of camera UUIDs
    detection_results = Column(JSON, default=list, nullable=False)  # DetectionResult payloads
    
    summary = Column(String(500), nullable=True)
    investigation_metadata = Column(JSON, default=dict, nullable=False)
