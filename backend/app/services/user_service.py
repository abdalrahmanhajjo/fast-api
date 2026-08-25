"""Business logic for users.

Routes stay thin: they parse/validate input, call into here, and shape the
response. Everything that is a *rule* ("emails are unique", "deleted users are
invisible") lives in this module so it is enforced no matter which route runs.
"""

import math
import re
from typing import Any, Dict, List, Optional, Tuple

from beanie import PydanticObjectId

from app.core.exceptions import ConflictError, NotFoundError
from app.core.security import hash_password
from app.models.user import User, UserType, utcnow

SORTABLE_FIELDS = {
    "created_at",
    "updated_at",
    "first_name",
    "last_name",
    "email",
    "age",
    "city",
    "type",
}


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #
def _icontains(value: str) -> Dict[str, str]:
    """Case-insensitive 'contains' query, with the input escaped so a user can
    not inject regex metacharacters."""
    return {"$regex": re.escape(value.strip()), "$options": "i"}


def parse_object_id(raw_id: str) -> PydanticObjectId:
    """Turn a path parameter into an ObjectId or raise a clean 404."""
    try:
        return PydanticObjectId(raw_id)
    except Exception as exc:  # noqa: BLE001 - any malformed id is simply "not found"
        raise NotFoundError("User not found.") from exc


# --------------------------------------------------------------------------- #
# Reads
# --------------------------------------------------------------------------- #
async def get_by_id(user_id: str, include_deleted: bool = False) -> Optional[User]:
    oid = parse_object_id(user_id)
    query: Dict[str, Any] = {"_id": oid}
    if not include_deleted:
        query["is_deleted"] = False
    return await User.find_one(query)


async def get_by_id_or_404(user_id: str, include_deleted: bool = False) -> User:
    user = await get_by_id(user_id, include_deleted=include_deleted)
    if user is None:
        raise NotFoundError("User not found.")
    return user


async def get_by_email(email: str, include_deleted: bool = True) -> Optional[User]:
    query: Dict[str, Any] = {"email": email.strip().lower()}
    if not include_deleted:
        query["is_deleted"] = False
    return await User.find_one(query)


async def email_is_taken(email: str, exclude_user_id: Optional[Any] = None) -> bool:
    """Uniqueness check across ALL users, including soft-deleted ones, so a
    deleted account can still be restored without an email collision."""
    existing = await get_by_email(email)
    if existing is None:
        return False
    if exclude_user_id is not None and str(existing.id) == str(exclude_user_id):
        return False
    return True


# --------------------------------------------------------------------------- #
# Writes
# --------------------------------------------------------------------------- #
async def create_user(data: Dict[str, Any], user_type: UserType) -> User:
    """Create a user with an explicitly supplied role.

    The caller decides the role - public registration always passes
    ``UserType.CLIENT``; the admin endpoint passes whatever the admin chose.
    """
    email = data["email"].strip().lower()
    if await email_is_taken(email):
        raise ConflictError("A user with this email already exists.")

    user = User(
        first_name=data["first_name"],
        last_name=data["last_name"],
        email=email,
        phone=data["phone"],
        city=data["city"],
        age=data["age"],
        type=user_type,
        password_hash=hash_password(data["password"]),
    )
    await user.insert()
    return user


async def update_user(
    user: User,
    changes: Dict[str, Any],
    allow_role_change: bool = False,
) -> User:
    """Apply a partial update.

    ``allow_role_change`` is the single switch that separates "a client editing
    themselves" from "an admin editing anyone". When it is False the ``type``
    key is dropped even if it somehow reached this layer.
    """
    if not allow_role_change:
        changes.pop("type", None)

    new_email = changes.get("email")
    if new_email and new_email != user.email:
        if await email_is_taken(new_email, exclude_user_id=user.id):
            raise ConflictError("A user with this email already exists.")
        user.email = new_email

    if "password" in changes and changes["password"]:
        user.password_hash = hash_password(changes["password"])

    for field in ("first_name", "last_name", "phone", "city", "age"):
        if field in changes and changes[field] is not None:
            setattr(user, field, changes[field])

    if allow_role_change and changes.get("type") is not None:
        user.type = UserType(changes["type"])

    user.touch()
    await user.save()
    return user


async def soft_delete_user(user: User) -> User:
    """Flag the record as deleted - the document itself is kept forever."""
    if user.is_deleted:
        return user
    user.mark_deleted()
    await user.save()
    return user


async def restore_user(user: User) -> User:
    """Optional admin convenience: undo a soft delete."""
    user.is_deleted = False
    user.deleted_at = None
    user.updated_at = utcnow()
    await user.save()
    return user


# --------------------------------------------------------------------------- #
# Listing: filtering + searching + pagination
# --------------------------------------------------------------------------- #
def build_filter_query(
    *,
    include_deleted: bool = False,
    age: Optional[int] = None,
    min_age: Optional[int] = None,
    max_age: Optional[int] = None,
    city: Optional[str] = None,
    user_type: Optional[UserType] = None,
    first_name: Optional[str] = None,
    last_name: Optional[str] = None,
    email: Optional[str] = None,
    search: Optional[str] = None,
) -> Dict[str, Any]:
    """Translate query parameters into a MongoDB filter document."""
    query: Dict[str, Any] = {}

    if not include_deleted:
        query["is_deleted"] = False

    if age is not None:
        query["age"] = age
    else:
        age_range: Dict[str, int] = {}
        if min_age is not None:
            age_range["$gte"] = min_age
        if max_age is not None:
            age_range["$lte"] = max_age
        if age_range:
            query["age"] = age_range

    if city:
        query["city"] = _icontains(city)
    if user_type is not None:
        query["type"] = user_type.value
    if first_name:
        query["first_name"] = _icontains(first_name)
    if last_name:
        query["last_name"] = _icontains(last_name)
    if email:
        query["email"] = _icontains(email)

    if search:
        pattern = _icontains(search)
        query["$or"] = [
            {"first_name": pattern},
            {"last_name": pattern},
            {"email": pattern},
            {"city": pattern},
        ]

    return query


async def list_users(
    query: Dict[str, Any],
    page: int = 1,
    limit: int = 10,
    sort_by: str = "created_at",
    order: str = "desc",
) -> Tuple[List[User], int]:
    """Return ``(users_on_this_page, total_matching)``.

    Order of operations required by the spec:
      1. apply the filters
      2. count ALL matching documents
      3. apply skip/limit
    """
    if sort_by not in SORTABLE_FIELDS:
        sort_by = "created_at"
    direction = -1 if order.lower() == "desc" else 1

    total = await User.find(query).count()
    skip = (page - 1) * limit

    users = (
        await User.find(query)
        .sort([(sort_by, direction)])
        .skip(skip)
        .limit(limit)
        .to_list()
    )
    return users, total


def total_pages(total: int, limit: int) -> int:
    return math.ceil(total / limit) if limit > 0 and total > 0 else 0
