from typing import Optional
from sqlalchemy.orm import Session
from backend.app.core.security import get_password_hash, verify_password, create_access_token
from backend.app.core.errors import DuplicateResourceError, AuthenticationError
from backend.app.domain.models.user import User
from backend.app.domain.models.tourist_profile import TouristProfile
from backend.app.domain.models.enums import UserRole
from backend.app.repositories.user_repository import UserRepository
from backend.app.schemas.auth import RegisterRequest, TokenResponse, UserResponse


class AuthService:
    def __init__(self, db: Session):
        self.db = db
        self.user_repo = UserRepository(db)

    def register(self, request: RegisterRequest) -> User:
        existing = self.user_repo.get_by_email(request.email)
        if existing:
            raise DuplicateResourceError(f"User with email '{request.email}' already exists")

        hashed_password = get_password_hash(request.password)
        user = User(
            email=request.email.lower().strip(),
            hashed_password=hashed_password,
            full_name=request.full_name.strip(),
            phone_number=request.phone_number.strip() if request.phone_number else None,
            role=request.role,
            is_active=True,
        )
        created_user = self.user_repo.create(user)

        # Auto-create empty profile for tourists
        if created_user.role == UserRole.TOURIST:
            profile = TouristProfile(user_id=created_user.id)
            self.db.add(profile)
            self.db.commit()

        return created_user

    def authenticate(self, email: str, password: str) -> TokenResponse:
        user = self.user_repo.get_by_email(email)
        if not user or not verify_password(password, user.hashed_password):
            raise AuthenticationError("Incorrect email or password")

        if not user.is_active:
            raise AuthenticationError("User account is inactive")

        token = create_access_token(
            subject=user.id,
            role=user.role.value,
        )
        return TokenResponse(
            access_token=token,
            token_type="bearer",
            user=UserResponse.model_validate(user),
        )
