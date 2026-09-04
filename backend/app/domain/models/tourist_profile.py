import uuid
from typing import TYPE_CHECKING, Optional
from sqlalchemy import String, Text, Boolean, ForeignKey, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.domain.models.base import UUIDModel

if TYPE_CHECKING:
    from backend.app.domain.models.user import User


class TouristProfile(UUIDModel):
    __tablename__ = "tourist_profiles"

    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True,
    )
    nationality: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
    )
    passport_or_id_hash: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
    )
    emergency_contact_name: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
    )
    emergency_contact_phone: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
    )
    medical_notes: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    consent_given: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    # Relationships
    user: Mapped["User"] = relationship(
        "User",
        back_populates="tourist_profile",
    )
