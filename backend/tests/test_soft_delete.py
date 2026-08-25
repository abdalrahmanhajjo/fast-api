"""DELETE /users/{id} - the record survives, the account does not."""

import pytest

from app.models.user import User
from tests.conftest import CLIENT_PASSWORD

pytestmark = pytest.mark.asyncio


async def test_admin_soft_deletes_a_user(client, admin_headers, client_user):
    resp = await client.delete(f"/users/{client_user.id}", headers=admin_headers)
    assert resp.status_code == 200, resp.text


async def test_record_still_exists_in_the_database(client, admin_headers, client_user):
    await client.delete(f"/users/{client_user.id}", headers=admin_headers)
    raw = await User.get(client_user.id)
    assert raw is not None
    assert raw.is_deleted is True
    assert raw.deleted_at is not None
    assert raw.email == client_user.email


async def test_deleted_user_disappears_from_listing(client, admin_headers, client_user):
    before = (await client.get("/users?limit=100", headers=admin_headers)).json()
    assert str(client_user.id) in {u["id"] for u in before["users"]}

    await client.delete(f"/users/{client_user.id}", headers=admin_headers)

    after = (await client.get("/users?limit=100", headers=admin_headers)).json()
    assert str(client_user.id) not in {u["id"] for u in after["users"]}
    assert after["total"] == before["total"] - 1


async def test_deleted_user_cannot_login(client, admin_headers, client_user):
    await client.delete(f"/users/{client_user.id}", headers=admin_headers)
    resp = await client.post(
        "/login", json={"email": client_user.email, "password": CLIENT_PASSWORD}
    )
    assert resp.status_code == 401


async def test_deleted_users_existing_token_stops_working(
    client, admin_headers, client_user, client_headers
):
    assert (await client.get("/users/me", headers=client_headers)).status_code == 200
    await client.delete(f"/users/{client_user.id}", headers=admin_headers)
    assert (await client.get("/users/me", headers=client_headers)).status_code == 401


async def test_deleted_user_excluded_from_statistics(client, admin_headers, client_user):
    before = (await client.get("/stats/count")).json()["total_users"]
    await client.delete(f"/users/{client_user.id}", headers=admin_headers)
    after = (await client.get("/stats/count")).json()["total_users"]
    assert after == before - 1


async def test_delete_unknown_user_returns_404(client, admin_headers):
    resp = await client.delete("/users/507f1f77bcf86cd799439011", headers=admin_headers)
    assert resp.status_code == 404


async def test_deleting_twice_returns_404_the_second_time(client, admin_headers, client_user):
    assert (await client.delete(f"/users/{client_user.id}", headers=admin_headers)).status_code == 200
    assert (await client.delete(f"/users/{client_user.id}", headers=admin_headers)).status_code == 404


async def test_admin_cannot_delete_themselves(client, admin_headers, admin_user):
    resp = await client.delete(f"/users/{admin_user.id}", headers=admin_headers)
    assert resp.status_code == 400


async def test_client_cannot_delete(client, client_headers, admin_user):
    resp = await client.delete(f"/users/{admin_user.id}", headers=client_headers)
    assert resp.status_code == 403


async def test_admin_can_view_deleted_users_explicitly(client, admin_headers, client_user):
    await client.delete(f"/users/{client_user.id}", headers=admin_headers)
    body = (await client.get("/users?include_deleted=true&limit=100", headers=admin_headers)).json()
    ids = {u["id"] for u in body["users"]}
    assert str(client_user.id) in ids
    deleted = next(u for u in body["users"] if u["id"] == str(client_user.id))
    assert deleted["is_deleted"] is True


async def test_admin_can_restore_a_deleted_user(client, admin_headers, client_user):
    await client.delete(f"/users/{client_user.id}", headers=admin_headers)
    resp = await client.post(f"/users/{client_user.id}/restore", headers=admin_headers)
    assert resp.status_code == 200
    assert resp.json()["is_deleted"] is False

    login = await client.post(
        "/login", json={"email": client_user.email, "password": CLIENT_PASSWORD}
    )
    assert login.status_code == 200


async def test_deleted_email_cannot_be_reused_by_registration(client, admin_headers, client_user):
    """Keeps restore safe: the address stays reserved by the soft-deleted row."""
    await client.delete(f"/users/{client_user.id}", headers=admin_headers)
    resp = await client.post(
        "/register",
        json={
            "first_name": "Someone",
            "last_name": "Else",
            "email": client_user.email,
            "phone": "+96170999888",
            "city": "Beirut",
            "age": 30,
            "password": "AnotherPass123",
        },
    )
    assert resp.status_code == 409
