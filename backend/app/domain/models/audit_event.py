from __future__ import annotations

import uuid
from typing import Optional, Dict, Any, TYPE_CHECKING
from sqlalchemy import Uuid, ForeignKey, String, Integer, Text, JSON, Enum as SAEnum, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.domain.models.base import UUIDModel
from backend.app.domain.models.enums import AuditEventType, AuditOutcome

if TYPE_CHECKING:
    from backend.app.domain.models.user import User


class AuditEvent(UUIDModel):
    __tablename__ = "audit_events"

    # Monotonic sequence counter per chain
    sequence_number: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        unique=True,
        index=True,
    )

    event_type: Mapped[AuditEventType] = mapped_column(
        SAEnum(AuditEventType, native_enum=False),
        nullable=False,
        index=True,
    )

    # Actor metadata (denormalized to survive user deletion)
    actor_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    actor_email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    actor_role: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    client_ip: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    user_agent: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Targeted resource
    resource_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    resource_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)
    action: Mapped[str] = mapped_column(String(50), nullable=False)
    outcome: Mapped[AuditOutcome] = mapped_column(
        SAEnum(AuditOutcome, native_enum=False),
        nullable=False,
        default=AuditOutcome.SUCCESS,
        index=True,
    )

    # Structured metadata / state difference (Never contains raw passwords or raw PII)
    details: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)

    # Cryptographic Hash Chaining
    previous_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    event_hash: Mapped[str] = mapped_column(String(64), nullable=False, unique=True, index=True)

    # Optional relationship
    actor: Mapped[Optional["User"]] = relationship("User", foreign_keys=[actor_id])

    __table_args__ = (
        Index("ix_audit_events_created", "created_at"),
        Index("ix_audit_events_type_outcome", "event_type", "outcome"),
        Index("ix_audit_events_resource_lookup", "resource_type", "resource_id"),
    )
