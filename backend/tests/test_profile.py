"""GET /users/me and PUT /users/me."""

import pytest

from tests.conftest import CLIENT_PASSWORD

pytestmark = pytest.mark.asyncio


async def test_get_own_information(client, client_headers, client_user):
    resp = await client.get("/users/me", headers=client_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["email"] == client_user.email
    assert body["first_name"] == "John"
    assert body["city"] == "Tripoli"
    assert body["age"] == 25
    assert "password" not in body and "password_hash" not in body


async def test_update_own_information(client, client_headers):
    resp = await client.put(
        "/users/me",
        headers=client_headers,
        json={"first_name": "Johnny", "city": "Beirut", "age": 26},
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["first_name"] == "Johnny"
    assert body["city"] == "Beirut"
    assert body["age"] == 26
    assert body["last_name"] == "Doe", "untouched fields must be preserved"


async def test_partial_update_only_changes_sent_fields(client, client_headers):
    await client.put("/users/me", headers=client_headers, json={"city": "Saida"})
    me = (await client.get("/users/me", headers=client_headers)).json()
    assert me["city"] == "Saida"
    assert me["first_name"] == "John"


async def test_update_own_password_and_login_with_it(client, client_headers, client_user):
    resp = await client.put(
        "/users/me", headers=client_headers, json={"password": "BrandNewPass123"}
    )
    assert resp.status_code == 200

    old = await client.post(
        "/login", json={"email": client_user.email, "password": CLIENT_PASSWORD}
    )
    assert old.status_code == 401

    new = await client.post(
        "/login", json={"email": client_user.email, "password": "BrandNewPass123"}
    )
    assert new.status_code == 200


async def test_new_password_is_hashed(client, client_headers, client_user):
    from app.models.user import User

    await client.put("/users/me", headers=client_headers, json={"password": "BrandNewPass123"})
    fresh = await User.get(client_user.id)
    assert fresh.password_hash != "BrandNewPass123"
    assert fresh.password_hash.startswith("$argon2")


async def test_update_email(client, client_headers):
    resp = await client.put(
        "/users/me", headers=client_headers, json={"email": "newmail@example.com"}
    )
    assert resp.status_code == 200
    assert resp.json()["email"] == "newmail@example.com"


async def test_update_to_duplicate_email_returns_409(client, client_headers, admin_user):
    resp = await client.put(
        "/users/me", headers=client_headers, json={"email": admin_user.email}
    )
    assert resp.status_code == 409


async def test_update_to_own_email_is_allowed(client, client_headers, client_user):
    resp = await client.put(
        "/users/me", headers=client_headers, json={"email": client_user.email}
    )
    assert resp.status_code == 200


async def test_update_validates_new_values(client, client_headers):
    assert (await client.put("/users/me", headers=client_headers, json={"age": 300})).status_code == 422
    assert (await client.put("/users/me", headers=client_headers, json={"phone": "nope"})).status_code == 422
    assert (await client.put("/users/me", headers=client_headers, json={"first_name": ""})).status_code == 422
    assert (await client.put("/users/me", headers=client_headers, json={"password": "weak"})).status_code == 422


async def test_empty_update_body_is_rejected(client, client_headers):
    resp = await client.put("/users/me", headers=client_headers, json={})
    assert resp.status_code == 422


async def test_updated_at_changes(client, client_headers, client_user):
    before = (await client.get("/users/me", headers=client_headers)).json()["updated_at"]
    await client.put("/users/me", headers=client_headers, json={"city": "Tyre"})
    after = (await client.get("/users/me", headers=client_headers)).json()["updated_at"]
    assert after >= before


async def test_admin_can_also_use_me_endpoints(client, admin_headers):
    resp = await client.get("/users/me", headers=admin_headers)
    assert resp.status_code == 200
    assert resp.json()["type"] == "admin"
