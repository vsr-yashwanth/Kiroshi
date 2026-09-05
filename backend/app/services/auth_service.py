from typing import Optional
from sqlalchemy.orm import Session
from backend.app.core.security import get_password_hash, verify_password, create_access_token
from backend.app.core.errors import DuplicateResourceError, AuthenticationError
from backend.app.domain.models.user import User
from backend.app.domain.models.tourist_profile import TouristProfile
from backend.app.domain.models.enums import UserRole, AuditEventType, AuditOutcome
from backend.app.repositories.user_repository import UserRepository
from backend.app.repositories.audit_repository import AuditRepository
from backend.app.schemas.auth import RegisterRequest, TokenResponse, UserResponse


class AuthService:
    def __init__(self, db: Session):
        self.db = db
        self.user_repo = UserRepository(db)
        self.audit_repo = AuditRepository(db)

    def register(self, request: RegisterRequest) -> User:
        existing = self.user_repo.get_by_email(request.email)
        if existing:
            self.audit_repo.create_event(
                event_type=AuditEventType.AUTH_REGISTER,
                action="REGISTER",
                resource_type="USER",
                resource_id=request.email,
                outcome=AuditOutcome.FAILURE,
                details={"reason": "Email already exists"},
            )
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

        self.audit_repo.create_event(
            event_type=AuditEventType.AUTH_REGISTER,
            action="REGISTER",
            resource_type="USER",
            resource_id=str(created_user.id),
            actor_id=created_user.id,
            actor_email=created_user.email,
            actor_role=created_user.role.value,
            outcome=AuditOutcome.SUCCESS,
            details={"role": created_user.role.value},
        )

        return created_user

    def authenticate(self, email: str, password: str, client_ip: Optional[str] = None, user_agent: Optional[str] = None) -> TokenResponse:
        user = self.user_repo.get_by_email(email)
        if not user or not verify_password(password, user.hashed_password):
            self.audit_repo.create_event(
                event_type=AuditEventType.AUTH_LOGIN_FAILURE,
                action="LOGIN",
                resource_type="USER",
                resource_id=email,
                client_ip=client_ip,
                user_agent=user_agent,
                outcome=AuditOutcome.DENIED,
                details={"reason": "Invalid credentials", "email_attempted": email},
            )
            raise AuthenticationError("Incorrect email or password")

        if not user.is_active:
            self.audit_repo.create_event(
                event_type=AuditEventType.AUTH_LOGIN_FAILURE,
                action="LOGIN",
                resource_type="USER",
                resource_id=str(user.id),
                actor_id=user.id,
                actor_email=user.email,
                actor_role=user.role.value,
                client_ip=client_ip,
                user_agent=user_agent,
                outcome=AuditOutcome.DENIED,
                details={"reason": "Inactive account"},
            )
            raise AuthenticationError("User account is inactive")

        token = create_access_token(
            subject=user.id,
            role=user.role.value,
        )

        self.audit_repo.create_event(
            event_type=AuditEventType.AUTH_LOGIN_SUCCESS,
            action="LOGIN",
            resource_type="USER",
            resource_id=str(user.id),
            actor_id=user.id,
            actor_email=user.email,
            actor_role=user.role.value,
            client_ip=client_ip,
            user_agent=user_agent,
            outcome=AuditOutcome.SUCCESS,
            details={"role": user.role.value},
        )

        return TokenResponse(
            access_token=token,
            token_type="bearer",
            user=UserResponse.model_validate(user),
        )
