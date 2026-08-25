"""JWT handling: missing, malformed, expired and revoked tokens."""

from datetime import timedelta

import pytest

from app.core.security import create_access_token
from app.services import user_service
from tests.conftest import auth_header

pytestmark = pytest.mark.asyncio

PROTECTED = "/users/me"


async def test_request_without_jwt(client, client_user):
    resp = await client.get(PROTECTED)
    assert resp.status_code == 401
    assert resp.headers.get("www-authenticate") == "Bearer"


async def test_invalid_jwt(client, client_user):
    resp = await client.get(PROTECTED, headers=auth_header("this.is.not.a.jwt"))
    assert resp.status_code == 401


async def test_jwt_signed_with_wrong_secret(client, client_user):
    from jose import jwt

    bad = jwt.encode({"sub": str(client_user.id), "type": "access"}, "wrong-secret")
    resp = await client.get(PROTECTED, headers=auth_header(bad))
    assert resp.status_code == 401


async def test_expired_jwt(client, client_user):
    token = create_access_token(
        subject=str(client_user.id),
        role="client",
        expires_delta=timedelta(seconds=-10),
    )
    resp = await client.get(PROTECTED, headers=auth_header(token))
    assert resp.status_code == 401


async def test_token_for_deleted_user_is_rejected(client, client_user, client_token):
    """Soft-deleting a user invalidates their already-issued tokens."""
    ok = await client.get(PROTECTED, headers=auth_header(client_token))
    assert ok.status_code == 200

    await user_service.soft_delete_user(client_user)

    resp = await client.get(PROTECTED, headers=auth_header(client_token))
    assert resp.status_code == 401


async def test_token_for_unknown_user_id(client, mongo_database):
    token = create_access_token(subject="507f1f77bcf86cd799439011", role="client")
    resp = await client.get(PROTECTED, headers=auth_header(token))
    assert resp.status_code == 401


async def test_role_claim_in_token_cannot_escalate(client, client_user):
    """The role is re-read from the database, so a forged `role` claim is inert."""
    token = create_access_token(subject=str(client_user.id), role="admin")
    resp = await client.get("/users", headers=auth_header(token))
    assert resp.status_code == 403


async def test_valid_token_grants_access(client, client_token):
    resp = await client.get(PROTECTED, headers=auth_header(client_token))
    assert resp.status_code == 200
