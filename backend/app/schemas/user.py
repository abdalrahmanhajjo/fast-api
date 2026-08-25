"""User schemas: validation rules live here, not in the route handlers."""

import re
from datetime import datetime
from typing import Annotated, List, Optional

from pydantic import (
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    field_validator,
    model_validator,
)

from app.models.user import UserType

# --------------------------------------------------------------------------- #
# Validation constants
# --------------------------------------------------------------------------- #
MIN_AGE = 13
MAX_AGE = 120
MIN_PASSWORD_LENGTH = 8
MAX_PASSWORD_LENGTH = 128

# E.164-ish: optional leading +, 8-15 digits, optional single spaces/dashes.
PHONE_REGEX = re.compile(r"^\+?[1-9]\d{0,3}[\s-]?\d{6,12}$")

NAME_REGEX = re.compile(r"^[A-Za-zÀ-ɏ؀-ۿ][A-Za-zÀ-ɏ؀-ۿ'\-\s.]*$")

NonEmptyStr = Annotated[str, Field(min_length=1, max_length=50)]


# --------------------------------------------------------------------------- #
# Reusable validators
# --------------------------------------------------------------------------- #
def validate_name(value: str, field_label: str) -> str:
    cleaned = value.strip()
    if not cleaned:
        raise ValueError(f"{field_label} must not be empty or whitespace only")
    if len(cleaned) < 2:
        raise ValueError(f"{field_label} must be at least 2 characters long")
    if not NAME_REGEX.match(cleaned):
        raise ValueError(f"{field_label} may only contain letters, spaces, apostrophes and hyphens")
    return cleaned


def validate_phone_value(value: str) -> str:
    cleaned = re.sub(r"[()\s-]", "", value.strip())
    if not cleaned:
        raise ValueError("Phone number must not be empty")
    if not PHONE_REGEX.match(cleaned):
        raise ValueError(
            "Phone number must be a valid international number, e.g. +96170123456"
        )
    return cleaned


def validate_password_value(value: str) -> str:
    if len(value) < MIN_PASSWORD_LENGTH:
        raise ValueError(f"Password must be at least {MIN_PASSWORD_LENGTH} characters long")
    if len(value) > MAX_PASSWORD_LENGTH:
        raise ValueError(f"Password must be at most {MAX_PASSWORD_LENGTH} characters long")
    if not re.search(r"[A-Z]", value):
        raise ValueError("Password must contain at least one uppercase letter")
    if not re.search(r"[a-z]", value):
        raise ValueError("Password must contain at least one lowercase letter")
    if not re.search(r"\d", value):
        raise ValueError("Password must contain at least one digit")
    if re.search(r"\s", value):
        raise ValueError("Password must not contain whitespace")
    return value


def validate_city_value(value: str) -> str:
    cleaned = value.strip()
    if not cleaned:
        raise ValueError("City must not be empty or whitespace only")
    if len(cleaned) < 2:
        raise ValueError("City must be at least 2 characters long")
    return cleaned


# --------------------------------------------------------------------------- #
# Base with the shared user fields
# --------------------------------------------------------------------------- #
class UserBase(BaseModel):
    first_name: NonEmptyStr
    last_name: NonEmptyStr
    email: EmailStr
    phone: str = Field(..., min_length=6, max_length=20)
    city: NonEmptyStr
    age: int = Field(..., ge=MIN_AGE, le=MAX_AGE)

    @field_validator("first_name")
    @classmethod
    def _first_name(cls, v: str) -> str:
        return validate_name(v, "First name")

    @field_validator("last_name")
    @classmethod
    def _last_name(cls, v: str) -> str:
        return validate_name(v, "Last name")

    @field_validator("city")
    @classmethod
    def _city(cls, v: str) -> str:
        return validate_city_value(v)

    @field_validator("phone")
    @classmethod
    def _phone(cls, v: str) -> str:
        return validate_phone_value(v)

    @field_validator("email")
    @classmethod
    def _email(cls, v: str) -> str:
        return v.strip().lower()


# --------------------------------------------------------------------------- #
# Public registration  -  POST /register
# --------------------------------------------------------------------------- #
class UserRegister(UserBase):
    """Body accepted by the PUBLIC registration endpoint.

    SECURITY: `extra="forbid"` means a request carrying a `type` field is
    rejected outright with 422. A public user can never choose their own role -
    the service layer always writes `type = client`.
    """

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {
                "first_name": "John",
                "last_name": "Doe",
                "email": "john@example.com",
                "phone": "+96170123456",
                "city": "Tripoli",
                "age": 25,
                "password": "Password123",
            }
        },
    )

    password: str = Field(..., min_length=MIN_PASSWORD_LENGTH, max_length=MAX_PASSWORD_LENGTH)

    @field_validator("password")
    @classmethod
    def _password(cls, v: str) -> str:
        return validate_password_value(v)


# --------------------------------------------------------------------------- #
# Admin user creation  -  POST /users
# --------------------------------------------------------------------------- #
class UserCreate(UserRegister):
    """Body accepted by the ADMIN-only create endpoint - `type` IS allowed."""

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {
                "first_name": "Jane",
                "last_name": "Smith",
                "email": "jane@example.com",
                "phone": "+96170123456",
                "city": "Beirut",
                "age": 30,
                "type": "admin",
                "password": "SecurePassword123",
            }
        },
    )

    type: UserType = UserType.CLIENT


# --------------------------------------------------------------------------- #
# Updates
# --------------------------------------------------------------------------- #
class _UserUpdateFields(BaseModel):
    """Every field optional; only what is sent gets changed (PATCH semantics)."""

    first_name: Optional[NonEmptyStr] = None
    last_name: Optional[NonEmptyStr] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(default=None, min_length=6, max_length=20)
    city: Optional[NonEmptyStr] = None
    age: Optional[int] = Field(default=None, ge=MIN_AGE, le=MAX_AGE)
    password: Optional[str] = Field(
        default=None, min_length=MIN_PASSWORD_LENGTH, max_length=MAX_PASSWORD_LENGTH
    )

    @field_validator("first_name")
    @classmethod
    def _first_name(cls, v):
        return validate_name(v, "First name") if v is not None else v

    @field_validator("last_name")
    @classmethod
    def _last_name(cls, v):
        return validate_name(v, "Last name") if v is not None else v

    @field_validator("city")
    @classmethod
    def _city(cls, v):
        return validate_city_value(v) if v is not None else v

    @field_validator("phone")
    @classmethod
    def _phone(cls, v):
        return validate_phone_value(v) if v is not None else v

    @field_validator("password")
    @classmethod
    def _password(cls, v):
        return validate_password_value(v) if v is not None else v

    @field_validator("email")
    @classmethod
    def _email(cls, v):
        return v.strip().lower() if v is not None else v

    @model_validator(mode="after")
    def _at_least_one_field(self):
        if not self.model_fields_set:
            raise ValueError("At least one field must be provided")
        return self


class UserUpdateMe(_UserUpdateFields):
    """Body for PUT /users/me.

    SECURITY: `type` is NOT a field here and `extra="forbid"` is set, so a
    client sending {"type": "admin"} is rejected with 422 and can never
    self-promote. Role changes are exclusively an admin operation.
    """

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={"example": {"city": "Beirut", "age": 26}},
    )


class UserUpdateAdmin(_UserUpdateFields):
    """Body for PUT /users/{id} - an admin MAY change the role."""

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={"example": {"city": "Beirut", "type": "admin"}},
    )

    type: Optional[UserType] = None


# --------------------------------------------------------------------------- #
# Responses
# --------------------------------------------------------------------------- #
class UserPublic(BaseModel):
    """Safe user representation - never contains the password hash."""

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: str
    first_name: str
    last_name: str
    email: EmailStr
    phone: str
    city: str
    age: int
    type: UserType
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    @classmethod
    def from_user(cls, user) -> "UserPublic":
        return cls(
            id=str(user.id),
            first_name=user.first_name,
            last_name=user.last_name,
            email=user.email,
            phone=user.phone,
            city=user.city,
            age=user.age,
            type=user.type,
            created_at=user.created_at,
            updated_at=user.updated_at,
        )


class UserAdminView(UserPublic):
    """What an admin sees - adds soft-delete bookkeeping."""

    is_deleted: bool = False
    deleted_at: Optional[datetime] = None

    @classmethod
    def from_user(cls, user) -> "UserAdminView":
        base = UserPublic.from_user(user).model_dump()
        return cls(**base, is_deleted=user.is_deleted, deleted_at=user.deleted_at)


class UserListResponse(BaseModel):
    """Paginated list shape required by the spec."""

    page: int
    limit: int
    total: int
    total_pages: int
    users: List[UserAdminView]


# --------------------------------------------------------------------------- #
# Statistics
# --------------------------------------------------------------------------- #
class CountStats(BaseModel):
    total_users: int


class AverageAgeStats(BaseModel):
    average_age: float


class CityCount(BaseModel):
    city: str
    count: int


class TopCitiesStats(BaseModel):
    cities: List[CityCount]
