"""POST /register - validation and the 'always a client' security rule."""

import pytest

from tests.conftest import register_payload

pytestmark = pytest.mark.asyncio


async def test_successful_registration(client):
    resp = await client.post("/register", json=register_payload())
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["email"] == "john@example.com"
    assert body["first_name"] == "John"
    assert body["type"] == "client"
    assert "id" in body


async def test_password_is_never_returned(client):
    resp = await client.post("/register", json=register_payload())
    body = resp.json()
    assert "password" not in body
    assert "password_hash" not in body


async def test_password_is_hashed_in_database(client):
    from app.models.user import User

    await client.post("/register", json=register_payload())
    user = await User.find_one({"email": "john@example.com"})
    assert user.password_hash != "ClientPass123"
    assert user.password_hash.startswith("$argon2")


async def test_invalid_email(client):
    resp = await client.post("/register", json=register_payload(email="not-an-email"))
    assert resp.status_code == 422


async def test_invalid_phone(client):
    resp = await client.post("/register", json=register_payload(phone="abc123"))
    assert resp.status_code == 422


@pytest.mark.parametrize("age", [-5, 0, 5, 200])
async def test_invalid_age(client, age):
    resp = await client.post("/register", json=register_payload(age=age))
    assert resp.status_code == 422


async def test_age_must_be_a_number(client):
    resp = await client.post("/register", json=register_payload(age="twenty"))
    assert resp.status_code == 422


async def test_empty_first_name(client):
    resp = await client.post("/register", json=register_payload(first_name=""))
    assert resp.status_code == 422


async def test_whitespace_first_name(client):
    resp = await client.post("/register", json=register_payload(first_name="   "))
    assert resp.status_code == 422


async def test_empty_last_name(client):
    resp = await client.post("/register", json=register_payload(last_name=""))
    assert resp.status_code == 422


async def test_empty_city(client):
    resp = await client.post("/register", json=register_payload(city=" "))
    assert resp.status_code == 422


@pytest.mark.parametrize(
    "password",
    ["short1A", "alllowercase1", "ALLUPPERCASE1", "NoDigitsHere", "with space1A"],
)
async def test_weak_password_rejected(client, password):
    resp = await client.post("/register", json=register_payload(password=password))
    assert resp.status_code == 422


async def test_missing_required_field(client):
    payload = register_payload()
    del payload["city"]
    resp = await client.post("/register", json=payload)
    assert resp.status_code == 422


async def test_duplicate_email_returns_409(client):
    await client.post("/register", json=register_payload())
    resp = await client.post("/register", json=register_payload(first_name="Jane"))
    assert resp.status_code == 409
    assert "already exists" in resp.json()["detail"].lower()


async def test_duplicate_email_is_case_insensitive(client):
    await client.post("/register", json=register_payload(email="john@example.com"))
    resp = await client.post("/register", json=register_payload(email="JOHN@EXAMPLE.COM"))
    assert resp.status_code == 409


async def test_register_with_type_admin_is_rejected(client):
    """The security rule: a public caller must not be able to pick their role."""
    resp = await client.post("/register", json=register_payload(type="admin"))
    assert resp.status_code == 422, resp.text


async def test_register_with_type_client_is_also_rejected(client):
    """`type` is not part of the public contract at all."""
    resp = await client.post("/register", json=register_payload(type="client"))
    assert resp.status_code == 422


async def test_registration_always_creates_a_client(client):
    from app.models.user import User

    for i in range(3):
        resp = await client.post(
            "/register", json=register_payload(email=f"user{i}@example.com")
        )
        assert resp.status_code == 201
        assert resp.json()["type"] == "client"

    admins = await User.find({"type": "admin"}).count()
    assert admins == 0


async def test_registration_trims_and_lowercases_email(client):
    resp = await client.post("/register", json=register_payload(email="John@Example.COM"))
    assert resp.status_code == 201
    assert resp.json()["email"] == "john@example.com"
