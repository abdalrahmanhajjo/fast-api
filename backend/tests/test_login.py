"""POST /login."""

import pytest

from app.services import user_service
from tests.conftest import ADMIN_PASSWORD, CLIENT_PASSWORD

pytestmark = pytest.mark.asyncio


async def test_successful_login(client, client_user):
    resp = await client.post(
        "/login", json={"email": client_user.email, "password": CLIENT_PASSWORD}
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["token_type"] == "bearer"
    assert body["access_token"]
    assert body["user"]["email"] == client_user.email
    assert "password_hash" not in body["user"]


async def test_login_is_case_insensitive_on_email(client, client_user):
    resp = await client.post(
        "/login", json={"email": client_user.email.upper(), "password": CLIENT_PASSWORD}
    )
    assert resp.status_code == 200


async def test_incorrect_password(client, client_user):
    resp = await client.post(
        "/login", json={"email": client_user.email, "password": "WrongPass123"}
    )
    assert resp.status_code == 401


async def test_nonexistent_email(client, mongo_database):
    resp = await client.post(
        "/login", json={"email": "ghost@example.com", "password": CLIENT_PASSWORD}
    )
    assert resp.status_code == 401


async def test_error_message_does_not_leak_which_field_was_wrong(client, client_user):
    wrong_pw = await client.post(
        "/login", json={"email": client_user.email, "password": "WrongPass123"}
    )
    no_user = await client.post(
        "/login", json={"email": "ghost@example.com", "password": "WrongPass123"}
    )
    assert wrong_pw.json()["detail"] == no_user.json()["detail"]


async def test_soft_deleted_user_cannot_login(client, client_user):
    await user_service.soft_delete_user(client_user)
    resp = await client.post(
        "/login", json={"email": client_user.email, "password": CLIENT_PASSWORD}
    )
    assert resp.status_code == 401


async def test_admin_login_returns_admin_type(client, admin_user):
    resp = await client.post(
        "/login", json={"email": admin_user.email, "password": ADMIN_PASSWORD}
    )
    assert resp.status_code == 200
    assert resp.json()["user"]["type"] == "admin"


async def test_login_requires_both_fields(client):
    resp = await client.post("/login", json={"email": "john@example.com"})
    assert resp.status_code == 422
