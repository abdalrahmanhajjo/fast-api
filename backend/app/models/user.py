"""The persisted user document (Beanie ODM on top of MongoDB)."""

from datetime import datetime, timezone
from enum import Enum
from typing import Optional

import pymongo
from beanie import Document
from pydantic import EmailStr, Field


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class UserType(str, Enum):
    """The only two roles the system knows about."""

    ADMIN = "admin"
    CLIENT = "client"


class User(Document):
    """A user account.

    Deletion is *soft*: the document is never removed, it is flagged with
    ``is_deleted`` and stamped with ``deleted_at``. Every read path filters on
    ``is_deleted == False`` unless it explicitly asks for deleted records.
    """

    first_name: str
    last_name: str
    email: EmailStr
    phone: str
    city: str
    age: int

    # Authorisation
    type: UserType = UserType.CLIENT

    # Never stores the plain password - Argon2id hash only.
    password_hash: str

    # Soft delete
    is_deleted: bool = False
    deleted_at: Optional[datetime] = None

    # Audit
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "users"
        indexes = [
            pymongo.IndexModel([("email", pymongo.ASCENDING)], unique=True, name="uniq_email"),
            pymongo.IndexModel([("is_deleted", pymongo.ASCENDING)], name="idx_is_deleted"),
            pymongo.IndexModel([("city", pymongo.ASCENDING)], name="idx_city"),
            pymongo.IndexModel([("type", pymongo.ASCENDING)], name="idx_type"),
        ]

    class Config:
        json_schema_extra = {
            "example": {
                "first_name": "John",
                "last_name": "Doe",
                "email": "john@example.com",
                "phone": "+96170123456",
                "city": "Tripoli",
                "age": 25,
                "type": "client",
            }
        }

    # --------------------------------------------------------------------- #
    # Helpers
    # --------------------------------------------------------------------- #
    @property
    def is_admin(self) -> bool:
        return self.type == UserType.ADMIN

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"

    def mark_deleted(self) -> None:
        self.is_deleted = True
        self.deleted_at = utcnow()
        self.updated_at = utcnow()

    def touch(self) -> None:
        self.updated_at = utcnow()
