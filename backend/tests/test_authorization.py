"""Role-based access control."""

import pytest

pytestmark = pytest.mark.asyncio

ADMIN_ONLY = [
    ("get", "/users"),
    ("post", "/users"),
]


@pytest.mark.parametrize("method,path", ADMIN_ONLY)
async def test_client_is_forbidden_from_admin_routes(client, client_headers, method, path):
    resp = await client.request(method.upper(), path, headers=client_headers, json={})
    assert resp.status_code == 403, f"{method.upper()} {path} -> {resp.status_code}"


@pytest.mark.parametrize("method,path", ADMIN_ONLY)
async def test_anonymous_gets_401_not_403(client, mongo_database, method, path):
    resp = await client.request(method.upper(), path, json={})
    assert resp.status_code == 401


async def test_admin_can_access_admin_routes(client, admin_headers):
    resp = await client.get("/users", headers=admin_headers)
    assert resp.status_code == 200


async def test_client_cannot_update_another_user(client, client_headers, admin_user):
    resp = await client.put(
        f"/users/{admin_user.id}", headers=client_headers, json={"city": "Hacked"}
    )
    assert resp.status_code == 403


async def test_client_cannot_delete_another_user(client, client_headers, admin_user):
    resp = await client.delete(f"/users/{admin_user.id}", headers=client_headers)
    assert resp.status_code == 403


async def test_client_cannot_read_another_user_by_id(client, client_headers, admin_user):
    resp = await client.get(f"/users/{admin_user.id}", headers=client_headers)
    assert resp.status_code == 403


async def test_client_cannot_change_own_role(client, client_headers, client_user):
    resp = await client.put("/users/me", headers=client_headers, json={"type": "admin"})
    assert resp.status_code == 422

    me = await client.get("/users/me", headers=client_headers)
    assert me.json()["type"] == "client"


async def test_client_cannot_sneak_role_alongside_valid_fields(client, client_headers):
    resp = await client.put(
        "/users/me", headers=client_headers, json={"city": "Beirut", "type": "admin"}
    )
    assert resp.status_code == 422

    me = await client.get("/users/me", headers=client_headers)
    assert me.json()["type"] == "client"
    assert me.json()["city"] == "Tripoli", "the whole request must be rejected atomically"


async def test_client_cannot_create_users(client, client_headers):
    payload = {
        "first_name": "New",
        "last_name": "Admin",
        "email": "new@example.com",
        "phone": "+96170111222",
        "city": "Beirut",
        "age": 30,
        "type": "admin",
        "password": "SecurePass123",
    }
    resp = await client.post("/users", headers=client_headers, json=payload)
    assert resp.status_code == 403
