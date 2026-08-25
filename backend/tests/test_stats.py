"""Public statistics endpoints."""

import pytest

pytestmark = pytest.mark.asyncio


@pytest.fixture
async def city_population(make_user):
    """Tripoli x4, Beirut x3, Saida x2, Tyre x1 - ages 20..29."""
    plan = ["Tripoli"] * 4 + ["Beirut"] * 3 + ["Saida"] * 2 + ["Tyre"]
    users = []
    for i, city in enumerate(plan):
        users.append(await make_user(email=f"u{i}@example.com", city=city, age=20 + i))
    return users


# --------------------------------------------------------------------------- #
# Public access
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("path", ["/stats/count", "/stats/average-age", "/stats/top-cities"])
async def test_stats_are_public(client, mongo_database, path):
    resp = await client.get(path)
    assert resp.status_code == 200


# --------------------------------------------------------------------------- #
# Count
# --------------------------------------------------------------------------- #
async def test_count_on_empty_database(client, mongo_database):
    assert (await client.get("/stats/count")).json() == {"total_users": 0}


async def test_total_active_users(client, city_population):
    assert (await client.get("/stats/count")).json()["total_users"] == 10


async def test_count_excludes_soft_deleted(client, admin_headers, city_population):
    await client.delete(f"/users/{city_population[0].id}", headers=admin_headers)
    # 10 clients + 1 admin fixture - 1 deleted
    assert (await client.get("/stats/count")).json()["total_users"] == 10


# --------------------------------------------------------------------------- #
# Average age
# --------------------------------------------------------------------------- #
async def test_average_age_on_empty_database(client, mongo_database):
    assert (await client.get("/stats/average-age")).json() == {"average_age": 0.0}


async def test_average_age(client, city_population):
    # ages 20..29 -> mean 24.5
    assert (await client.get("/stats/average-age")).json()["average_age"] == 24.5


async def test_average_age_excludes_soft_deleted(client, admin_headers, make_user):
    a = await make_user(email="a@example.com", age=20)
    await make_user(email="b@example.com", age=30)
    await client.delete(f"/users/{a.id}", headers=admin_headers)
    # remaining: b(30) + admin fixture(35) -> 32.5
    assert (await client.get("/stats/average-age")).json()["average_age"] == 32.5


# --------------------------------------------------------------------------- #
# Top cities
# --------------------------------------------------------------------------- #
async def test_top_cities_on_empty_database(client, mongo_database):
    assert (await client.get("/stats/top-cities")).json() == {"cities": []}


async def test_top_cities_returns_at_most_three(client, city_population):
    cities = (await client.get("/stats/top-cities")).json()["cities"]
    assert len(cities) == 3


async def test_top_cities_are_ordered_by_count(client, city_population):
    cities = (await client.get("/stats/top-cities")).json()["cities"]
    assert [c["city"] for c in cities] == ["Tripoli", "Beirut", "Saida"]
    assert [c["count"] for c in cities] == [4, 3, 2]


async def test_top_cities_excludes_soft_deleted(client, admin_headers, city_population):
    # remove 3 of the 4 Tripoli users -> Tripoli drops to 1
    for user in city_population[:3]:
        await client.delete(f"/users/{user.id}", headers=admin_headers)
    cities = (await client.get("/stats/top-cities")).json()["cities"]
    counts = {c["city"]: c["count"] for c in cities}
    assert counts.get("Beirut") == 4  # 3 from the fixture + the admin (Beirut)
    assert counts.get("Tripoli", 0) <= 1
