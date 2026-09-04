from typing import Callable, List
from uuid import UUID
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from backend.app.core.database import get_db
from backend.app.core.security import decode_access_token
from backend.app.core.errors import AuthenticationError, AuthorizationError
from backend.app.domain.models.user import User
from backend.app.domain.models.enums import UserRole
from backend.app.repositories.user_repository import UserRepository

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/api/v1/auth/login"
)


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    payload = decode_access_token(token)
    if not payload:
        raise AuthenticationError("Could not validate credentials")

    user_id_str: str = payload.get("sub")
    if not user_id_str:
        raise AuthenticationError("Malformed token subject")

    try:
        user_id = UUID(user_id_str)
    except ValueError:
        raise AuthenticationError("Invalid user ID in token")

    user_repo = UserRepository(db)
    user = user_repo.get(user_id)
    if not user:
        raise AuthenticationError("User not found")

    return user


def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user account",
        )
    return current_user


def require_role(*allowed_roles: UserRole) -> Callable[[User], User]:
    def role_checker(current_user: User = Depends(get_current_active_user)) -> User:
        if current_user.role not in allowed_roles:
            raise AuthorizationError(
                f"Role '{current_user.role.value}' does not have sufficient permissions"
            )
        return current_user

    return role_checker
