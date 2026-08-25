"""Pytest fixtures.

The suite runs against an **in-memory MongoDB** (``mongomock_motor``) so it needs
no running database server. Swap ``mongo_database`` for a real Motor client
pointing at a throwaway database if you want to exercise real MongoDB.
"""

import os
import sys
from pathlib import Path
from typing import AsyncIterator

import pytest
import pytest_asyncio

BACKEND_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_ROOT))

# Deterministic settings before app modules import.
os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key-for-pytest-only")
os.environ.setdefault("ACCESS_TOKEN_EXPIRE_MINUTES", "60")
# Tests must not depend on a developer's local .env value.  In particular,
# pydantic-settings requires DEBUG to be a real boolean string.
os.environ["DEBUG"] = "false"

from httpx import ASGITransport, AsyncClient  # noqa: E402
from mongomock_motor import AsyncMongoMockClient  # noqa: E402

from app.db.mongodb import init_models  # noqa: E402
from app.main import create_app  # noqa: E402
from app.models.user import UserType  # noqa: E402
from app.services import user_service  # noqa: E402

ADMIN_PASSWORD = "AdminPass123"
CLIENT_PASSWORD = "ClientPass123"


# --------------------------------------------------------------------------- #
# Database / client
# --------------------------------------------------------------------------- #
@pytest_asyncio.fixture
async def mongo_database():
    """A fresh, isolated in-memory database per test."""
    client = AsyncMongoMockClient()
    database = client["test_auth_system"]
    await init_models(database)
    yield database


@pytest_asyncio.fixture
async def client(mongo_database) -> AsyncIterator[AsyncClient]:
    """HTTP client bound to the ASGI app (no network, no lifespan)."""
    app = create_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


# --------------------------------------------------------------------------- #
# Data factories
# --------------------------------------------------------------------------- #
def register_payload(**overrides) -> dict:
    payload = {
        "first_name": "John",
        "last_name": "Doe",
        "email": "john@example.com",
        "phone": "+96170123456",
        "city": "Tripoli",
        "age": 25,
        "password": CLIENT_PASSWORD,
    }
    payload.update(overrides)
    return payload


@pytest_asyncio.fixture
async def admin_user(mongo_database):
    """An admin created directly in the database (bypassing the API)."""
    return await user_service.create_user(
        {
            "first_name": "Root",
            "last_name": "Admin",
            "email": "admin@example.com",
            "phone": "+96170000000",
            "city": "Beirut",
            "age": 35,
            "password": ADMIN_PASSWORD,
        },
        user_type=UserType.ADMIN,
    )


@pytest_asyncio.fixture
async def client_user(mongo_database):
    return await user_service.create_user(
        register_payload(email="client@example.com"),
        user_type=UserType.CLIENT,
    )


async def login(ac: AsyncClient, email: str, password: str) -> str:
    resp = await ac.post("/login", json={"email": email, "password": password})
    assert resp.status_code == 200, resp.text
    return resp.json()["access_token"]


def auth_header(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


@pytest_asyncio.fixture
async def admin_token(client, admin_user) -> str:
    return await login(client, admin_user.email, ADMIN_PASSWORD)


@pytest_asyncio.fixture
async def client_token(client, client_user) -> str:
    return await login(client, client_user.email, CLIENT_PASSWORD)


@pytest_asyncio.fixture
def admin_headers(admin_token) -> dict:
    return auth_header(admin_token)


@pytest_asyncio.fixture
def client_headers(client_token) -> dict:
    return auth_header(client_token)


@pytest.fixture
def make_user(mongo_database):
    """Factory that creates users with arbitrary attributes."""

    async def _make(**overrides):
        user_type = overrides.pop("type", UserType.CLIENT)
        return await user_service.create_user(
            register_payload(**overrides), user_type=UserType(user_type)
        )

    return _make
