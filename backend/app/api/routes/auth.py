"""Public authentication routes: registration and login."""

from fastapi import APIRouter, status

from app.core.config import settings
from app.core.exceptions import UnauthorizedError
from app.core.security import create_access_token, verify_password
from app.models.user import UserType
from app.schemas.auth import LoginRequest, Token
from app.schemas.user import UserPublic, UserRegister
from app.services import user_service

router = APIRouter(tags=["Authentication"])


@router.post(
    "/register",
    response_model=UserPublic,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new account (public)",
    responses={
        409: {"description": "Email already registered"},
        422: {"description": "Validation failed (this includes sending a `type` field)"},
    },
)
async def register(payload: UserRegister) -> UserPublic:
    """Create a new account.

    The role is **not** part of the request body. Every account created here is
    a `client`; sending a `type` field is rejected with 422 so a public caller
    can never grant themselves admin privileges.
    """
    user = await user_service.create_user(
        payload.model_dump(), user_type=UserType.CLIENT
    )
    return UserPublic.from_user(user)


@router.post(
    "/login",
    response_model=Token,
    summary="Log in and receive a JWT (public)",
    responses={401: {"description": "Invalid credentials or deactivated account"}},
)
async def login(payload: LoginRequest) -> Token:
    """Exchange email + password for a signed access token.

    A single generic 401 is returned for "no such email", "wrong password" and
    "account deleted" so the endpoint cannot be used to enumerate users.
    """
    user = await user_service.get_by_email(payload.email, include_deleted=True)
    if user is None or not verify_password(payload.password, user.password_hash):
        raise UnauthorizedError("Incorrect email or password.")

    if user.is_deleted:
        raise UnauthorizedError("Incorrect email or password.")

    token = create_access_token(subject=str(user.id), role=user.type.value)
    return Token(
        access_token=token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=UserPublic.from_user(user),
    )
