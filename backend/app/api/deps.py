"""Reusable authentication & authorisation dependencies.

    JWT  ->  identify user  ->  check role  ->  allow / deny
"""

from typing import Optional

from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.exceptions import ForbiddenError, UnauthorizedError
from app.core.security import decode_access_token
from app.models.user import User, UserType
from app.services import user_service

# auto_error=False so we can raise our own uniform 401 payload.
bearer_scheme = HTTPBearer(auto_error=False, description="Paste the JWT returned by /login")


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
) -> User:
    """Resolve the caller from the `Authorization: Bearer <jwt>` header.

    401 is returned when the header is missing, the token is malformed,
    expired, points at a user that no longer exists, or points at a
    soft-deleted account.
    """
    if credentials is None or not credentials.credentials:
        raise UnauthorizedError("Not authenticated. A Bearer token is required.")

    payload = decode_access_token(credentials.credentials)
    if payload is None:
        raise UnauthorizedError("Invalid or expired token.")

    user = await user_service.get_by_id(payload["sub"], include_deleted=True)
    if user is None:
        raise UnauthorizedError("Invalid or expired token.")

    # A soft-deleted account is inactive: its old tokens stop working immediately.
    if user.is_deleted:
        raise UnauthorizedError("This account has been deactivated.")

    return user


async def get_current_admin(
    current_user: User = Depends(get_current_user),
) -> User:
    """Authenticated AND holding the admin role, otherwise 403."""
    if current_user.type != UserType.ADMIN:
        raise ForbiddenError("Admin privileges are required for this operation.")
    return current_user


async def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
) -> Optional[User]:
    """For endpoints that are public but behave differently when signed in."""
    if credentials is None or not credentials.credentials:
        return None
    payload = decode_access_token(credentials.credentials)
    if payload is None:
        return None
    user = await user_service.get_by_id(payload["sub"])
    return user
