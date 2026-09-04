from typing import TYPE_CHECKING, List, Optional
from sqlalchemy import String, Boolean, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.domain.models.base import UUIDModel
from backend.app.domain.models.enums import UserRole

if TYPE_CHECKING:
    from backend.app.domain.models.tourist_profile import TouristProfile
    from backend.app.domain.models.trip import Trip


class User(UUIDModel):
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        index=True,
        nullable=False,
    )
    hashed_password: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    full_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    phone_number: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
    )
    role: Mapped[UserRole] = mapped_column(
        SQLEnum(UserRole, name="user_role", native_enum=False),
        default=UserRole.TOURIST,
        nullable=False,
        index=True,
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    # Relationships
    tourist_profile: Mapped[Optional["TouristProfile"]] = relationship(
        "TouristProfile",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
    )
    trips: Mapped[List["Trip"]] = relationship(
        "Trip",
        back_populates="tourist",
        cascade="all, delete-orphan",
    )
