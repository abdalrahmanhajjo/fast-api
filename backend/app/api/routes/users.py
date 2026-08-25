"""User routes.

Route access map
----------------
  POST   /users        admin only
  GET    /users        admin only  (pagination + filtering + search)
  GET    /users/me     any authenticated user
  PUT    /users/me     any authenticated user
  GET    /users/{id}   admin only
  PUT    /users/{id}   admin only
  DELETE /users/{id}   admin only  (soft delete)
  POST   /users/{id}/restore   admin only (optional convenience)

NOTE ON ROUTE ORDER: `/users/me` is declared *before* `/users/{user_id}` so the
literal path wins over the parameterised one.
"""

from typing import Optional

from fastapi import APIRouter, Depends, Path, Query, status

from app.api.deps import get_current_admin, get_current_user
from app.core.config import settings
from app.core.exceptions import BadRequestError
from app.models.user import User, UserType
from app.schemas.common import Message
from app.schemas.user import (
    UserAdminView,
    UserCreate,
    UserListResponse,
    UserPublic,
    UserUpdateAdmin,
    UserUpdateMe,
)
from app.services import user_service

router = APIRouter(prefix="/users", tags=["Users"])


# --------------------------------------------------------------------------- #
# Admin - create
# --------------------------------------------------------------------------- #
@router.post(
    "",
    response_model=UserAdminView,
    status_code=status.HTTP_201_CREATED,
    summary="Create a user (admin only)",
    responses={
        401: {"description": "Missing / invalid token"},
        403: {"description": "Caller is not an admin"},
        409: {"description": "Email already registered"},
    },
)
async def create_user(
    payload: UserCreate,
    _admin: User = Depends(get_current_admin),
) -> UserAdminView:
    """An admin may create either a `client` or another `admin`."""
    data = payload.model_dump()
    user_type = UserType(data.pop("type", UserType.CLIENT))
    user = await user_service.create_user(data, user_type=user_type)
    return UserAdminView.from_user(user)


# --------------------------------------------------------------------------- #
# Admin - list with pagination + filtering + search
# --------------------------------------------------------------------------- #
@router.get(
    "",
    response_model=UserListResponse,
    summary="List users with pagination, filtering and search (admin only)",
    responses={401: {"description": "Missing / invalid token"}, 403: {"description": "Not an admin"}},
)
async def list_users(
    _admin: User = Depends(get_current_admin),
    page: int = Query(1, ge=1, description="1-based page number"),
    limit: int = Query(
        settings.DEFAULT_PAGE_SIZE,
        ge=1,
        le=settings.MAX_PAGE_SIZE,
        description=f"Items per page (max {settings.MAX_PAGE_SIZE})",
    ),
    age: Optional[int] = Query(None, ge=0, le=150, description="Exact age"),
    min_age: Optional[int] = Query(None, ge=0, le=150),
    max_age: Optional[int] = Query(None, ge=0, le=150),
    city: Optional[str] = Query(None, description="Case-insensitive partial match"),
    type: Optional[UserType] = Query(None, description="admin | client"),
    first_name: Optional[str] = Query(None, description="Case-insensitive partial match"),
    last_name: Optional[str] = Query(None, description="Case-insensitive partial match"),
    email: Optional[str] = Query(None, description="Case-insensitive partial match"),
    search: Optional[str] = Query(None, description="Free text over name, email and city"),
    include_deleted: bool = Query(False, description="Admin-only view of soft-deleted users"),
    sort_by: str = Query("created_at", description="created_at | first_name | age | ..."),
    order: str = Query("desc", pattern="^(asc|desc)$"),
) -> UserListResponse:
    """Soft-deleted users are excluded unless `include_deleted=true`.

    Filters are applied first, the total is computed over the filtered set, and
    pagination is applied last - so filtering and pagination compose correctly.
    """
    if min_age is not None and max_age is not None and min_age > max_age:
        raise BadRequestError("min_age cannot be greater than max_age.")

    query = user_service.build_filter_query(
        include_deleted=include_deleted,
        age=age,
        min_age=min_age,
        max_age=max_age,
        city=city,
        user_type=type,
        first_name=first_name,
        last_name=last_name,
        email=email,
        search=search,
    )

    users, total = await user_service.list_users(
        query, page=page, limit=limit, sort_by=sort_by, order=order
    )

    return UserListResponse(
        page=page,
        limit=limit,
        total=total,
        total_pages=user_service.total_pages(total, limit),
        users=[UserAdminView.from_user(u) for u in users],
    )


# --------------------------------------------------------------------------- #
# Self service  (declared before /{user_id})
# --------------------------------------------------------------------------- #
@router.get(
    "/me",
    response_model=UserPublic,
    summary="Get my own profile",
    responses={401: {"description": "Missing / invalid token"}},
)
async def read_me(current_user: User = Depends(get_current_user)) -> UserPublic:
    """Returns the caller's own record. The password hash is never included."""
    return UserPublic.from_user(current_user)


@router.put(
    "/me",
    response_model=UserPublic,
    summary="Update my own profile",
    responses={
        401: {"description": "Missing / invalid token"},
        409: {"description": "Email already registered"},
        422: {"description": "Validation failed (this includes sending a `type` field)"},
    },
)
async def update_me(
    payload: UserUpdateMe,
    current_user: User = Depends(get_current_user),
) -> UserPublic:
    """Partial update of the caller's own record.

    `type` is not an accepted field, so a client cannot promote themselves;
    the request is rejected with 422. A new password is re-hashed before it is
    stored.
    """
    changes = payload.model_dump(exclude_unset=True)
    user = await user_service.update_user(current_user, changes, allow_role_change=False)
    return UserPublic.from_user(user)


# --------------------------------------------------------------------------- #
# Admin - single user operations
# --------------------------------------------------------------------------- #
@router.get(
    "/{user_id}",
    response_model=UserAdminView,
    summary="Get a single user (admin only)",
    responses={403: {"description": "Not an admin"}, 404: {"description": "User not found"}},
)
async def get_user(
    user_id: str = Path(..., description="MongoDB ObjectId"),
    _admin: User = Depends(get_current_admin),
) -> UserAdminView:
    user = await user_service.get_by_id_or_404(user_id, include_deleted=True)
    return UserAdminView.from_user(user)


@router.put(
    "/{user_id}",
    response_model=UserAdminView,
    summary="Update any user (admin only)",
    responses={
        403: {"description": "Not an admin"},
        404: {"description": "User not found"},
        409: {"description": "Email already registered"},
    },
)
async def update_user(
    payload: UserUpdateAdmin,
    user_id: str = Path(..., description="MongoDB ObjectId"),
    admin: User = Depends(get_current_admin),
) -> UserAdminView:
    """An admin may edit any field, including promoting/demoting the role."""
    user = await user_service.get_by_id_or_404(user_id)

    changes = payload.model_dump(exclude_unset=True)

    # Guard-rail: don't let the last admin demote themselves out of the system.
    if (
        str(user.id) == str(admin.id)
        and changes.get("type") == UserType.CLIENT
        and await _is_last_admin(admin)
    ):
        raise BadRequestError("You are the last admin; promote another admin first.")

    user = await user_service.update_user(user, changes, allow_role_change=True)
    return UserAdminView.from_user(user)


@router.delete(
    "/{user_id}",
    response_model=Message,
    summary="Soft-delete a user (admin only)",
    responses={
        400: {"description": "Admins cannot delete their own account"},
        403: {"description": "Not an admin"},
        404: {"description": "User not found"},
    },
)
async def delete_user(
    user_id: str = Path(..., description="MongoDB ObjectId"),
    admin: User = Depends(get_current_admin),
) -> Message:
    """Marks the user as deleted; the document itself is preserved.

    Afterwards the user cannot log in, does not appear in `GET /users`, and is
    excluded from every public statistic.
    """
    user = await user_service.get_by_id_or_404(user_id)

    if str(user.id) == str(admin.id):
        raise BadRequestError("You cannot delete your own account.")

    await user_service.soft_delete_user(user)
    return Message(detail="User deleted successfully.")


@router.post(
    "/{user_id}/restore",
    response_model=UserAdminView,
    summary="Restore a soft-deleted user (admin only, optional extra)",
    responses={403: {"description": "Not an admin"}, 404: {"description": "User not found"}},
)
async def restore_user(
    user_id: str = Path(..., description="MongoDB ObjectId"),
    _admin: User = Depends(get_current_admin),
) -> UserAdminView:
    user = await user_service.get_by_id_or_404(user_id, include_deleted=True)
    user = await user_service.restore_user(user)
    return UserAdminView.from_user(user)


# --------------------------------------------------------------------------- #
# helpers
# --------------------------------------------------------------------------- #
async def _is_last_admin(admin: User) -> bool:
    admins = await User.find(
        {"type": UserType.ADMIN.value, "is_deleted": False}
    ).count()
    return admins <= 1
