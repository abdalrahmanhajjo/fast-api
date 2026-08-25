"""Authentication request / response schemas."""

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.schemas.user import UserPublic


class LoginRequest(BaseModel):
    """Credentials for POST /login."""

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {"email": "john@example.com", "password": "Password123"}
        },
    )

    email: EmailStr
    password: str = Field(..., min_length=1, max_length=128)


class Token(BaseModel):
    """OAuth2-style bearer token response."""

    access_token: str
    token_type: str = "bearer"
    expires_in: int = Field(..., description="Token lifetime in seconds")
    user: UserPublic
