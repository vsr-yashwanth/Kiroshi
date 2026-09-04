import uuid
from datetime import datetime
from typing import Optional, Dict, Any, TYPE_CHECKING
from sqlalchemy import Uuid, ForeignKey, String, Text, Boolean, Integer, JSON, DateTime, Enum as SAEnum, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.domain.models.base import UUIDModel
from backend.app.domain.models.enums import NotificationChannel, NotificationDeliveryStatus

if TYPE_CHECKING:
    from backend.app.domain.models.user import User
    from backend.app.domain.models.incident import Incident


class Notification(UUIDModel):
    __tablename__ = "notifications"

    recipient_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    incident_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("incidents.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)

    channel: Mapped[NotificationChannel] = mapped_column(
        SAEnum(NotificationChannel, native_enum=False),
        default=NotificationChannel.IN_APP,
        nullable=False,
        index=True,
    )
    status: Mapped[NotificationDeliveryStatus] = mapped_column(
        SAEnum(NotificationDeliveryStatus, native_enum=False),
        default=NotificationDeliveryStatus.PENDING,
        nullable=False,
        index=True,
    )

    is_read: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)
    retry_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    idempotency_key: Mapped[Optional[str]] = mapped_column(
        String(128),
        unique=True,
        nullable=True,
        index=True,
    )
    payload: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True, default=dict)
    sent_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    recipient: Mapped["User"] = relationship("User", foreign_keys=[recipient_id])
    incident: Mapped[Optional["Incident"]] = relationship("Incident", foreign_keys=[incident_id])

    __table_args__ = (
        Index("ix_notifications_recipient_status", "recipient_id", "status"),
        Index("ix_notifications_recipient_created", "recipient_id", "created_at"),
    )
