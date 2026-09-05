import uuid
from typing import Optional, Dict, Any, TYPE_CHECKING
from sqlalchemy import Uuid, ForeignKey, String, JSON, Enum as SAEnum, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.domain.models.base import UUIDModel
from backend.app.domain.models.enums import SyncEventType, SyncEventStatus

if TYPE_CHECKING:
    from backend.app.domain.models.user import User


class SyncRecord(UUIDModel):
    __tablename__ = "sync_records"

    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    idempotency_key: Mapped[str] = mapped_column(
        String(128),
        nullable=False,
        unique=True,
        index=True,
        doc="Client-provided unique event or transaction idempotency key",
    )
    event_type: Mapped[SyncEventType] = mapped_column(
        SAEnum(SyncEventType, native_enum=False),
        nullable=False,
        index=True,
    )
    resource_type: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        doc="Target entity type: incidents, location_events, trips",
    )
    resource_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid(as_uuid=True),
        nullable=True,
        doc="Identifier of the resulting or existing entity",
    )
    status: Mapped[SyncEventStatus] = mapped_column(
        SAEnum(SyncEventStatus, native_enum=False),
        nullable=False,
        default=SyncEventStatus.SYNCED,
        index=True,
    )
    response_payload: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON,
        nullable=True,
        doc="Cached outcome or response details for idempotent replays",
    )

    # Relationships
    user: Mapped["User"] = relationship("User", foreign_keys=[user_id])

    __table_args__ = (
        Index("ix_sync_records_user_created", "user_id", "created_at"),
        Index("ix_sync_records_user_idempotency", "user_id", "idempotency_key"),
    )
