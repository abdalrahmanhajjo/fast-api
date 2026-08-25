"""Admin user management: create, list, paginate, filter, update, change role."""

import pytest

pytestmark = pytest.mark.asyncio


def payload(**overrides) -> dict:
    base = {
        "first_name": "Jane",
        "last_name": "Smith",
        "email": "jane@example.com",
        "phone": "+96170123456",
        "city": "Beirut",
        "age": 30,
        "password": "SecurePassword123",
    }
    base.update(overrides)
    return base


# --------------------------------------------------------------------------- #
# Create
# --------------------------------------------------------------------------- #
async def test_admin_creates_a_client(client, admin_headers):
    resp = await client.post("/users", headers=admin_headers, json=payload(type="client"))
    assert resp.status_code == 201, resp.text
    assert resp.json()["type"] == "client"


async def test_admin_creates_an_admin(client, admin_headers):
    resp = await client.post("/users", headers=admin_headers, json=payload(type="admin"))
    assert resp.status_code == 201, resp.text
    assert resp.json()["type"] == "admin"


async def test_created_admin_can_login_and_use_admin_routes(client, admin_headers):
    await client.post("/users", headers=admin_headers, json=payload(type="admin"))
    token = (
        await client.post(
            "/login", json={"email": "jane@example.com", "password": "SecurePassword123"}
        )
    ).json()["access_token"]
    resp = await client.get("/users", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200


async def test_type_defaults_to_client_when_omitted(client, admin_headers):
    resp = await client.post("/users", headers=admin_headers, json=payload())
    assert resp.status_code == 201
    assert resp.json()["type"] == "client"


async def test_admin_create_duplicate_email_returns_409(client, admin_headers, admin_user):
    resp = await client.post(
        "/users", headers=admin_headers, json=payload(email=admin_user.email)
    )
    assert resp.status_code == 409


async def test_admin_create_validates_input(client, admin_headers):
    resp = await client.post("/users", headers=admin_headers, json=payload(age=-1))
    assert resp.status_code == 422


async def test_admin_create_rejects_unknown_type(client, admin_headers):
    resp = await client.post("/users", headers=admin_headers, json=payload(type="superuser"))
    assert resp.status_code == 422


# --------------------------------------------------------------------------- #
# List / pagination
# --------------------------------------------------------------------------- #
@pytest.fixture
async def population(make_user):
    """25 users: mixed cities, types and ages (plus the admin fixture)."""
    cities = ["Tripoli", "Beirut", "Saida"]
    created = []
    for i in range(24):
        created.append(
            await make_user(
                email=f"user{i}@example.com",
                first_name=["John", "Jane", "Ali"][i % 3],
                last_name=["Doe", "Smith"][i % 2],
                city=cities[i % 3],
                age=20 + (i % 5),
                type="admin" if i % 6 == 0 else "client",
            )
        )
    return created


async def test_list_returns_pagination_envelope(client, admin_headers, population):
    resp = await client.get("/users", headers=admin_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert set(body) == {"page", "limit", "total", "total_pages", "users"}
    assert body["page"] == 1
    assert body["limit"] == 10
    assert body["total"] == 25  # 24 + admin fixture
    assert body["total_pages"] == 3
    assert len(body["users"]) == 10


async def test_list_never_exposes_password_hash(client, admin_headers, population):
    body = (await client.get("/users", headers=admin_headers)).json()
    for user in body["users"]:
        assert "password" not in user and "password_hash" not in user


async def test_pagination_second_page(client, admin_headers, population):
    body = (await client.get("/users?page=2&limit=10", headers=admin_headers)).json()
    assert body["page"] == 2
    assert len(body["users"]) == 10


async def test_pagination_last_page_is_partial(client, admin_headers, population):
    body = (await client.get("/users?page=3&limit=10", headers=admin_headers)).json()
    assert len(body["users"]) == 5


async def test_pages_do_not_overlap(client, admin_headers, population):
    p1 = (await client.get("/users?page=1&limit=10", headers=admin_headers)).json()["users"]
    p2 = (await client.get("/users?page=2&limit=10", headers=admin_headers)).json()["users"]
    assert {u["id"] for u in p1}.isdisjoint({u["id"] for u in p2})


async def test_page_beyond_the_end_is_empty(client, admin_headers, population):
    body = (await client.get("/users?page=99&limit=10", headers=admin_headers)).json()
    assert body["users"] == []
    assert body["total"] == 25


@pytest.mark.parametrize("qs", ["page=0", "page=-1", "limit=0", "limit=101", "limit=-5"])
async def test_invalid_pagination_params(client, admin_headers, population, qs):
    resp = await client.get(f"/users?{qs}", headers=admin_headers)
    assert resp.status_code == 422


async def test_max_limit_is_enforced(client, admin_headers, population):
    assert (await client.get("/users?limit=100", headers=admin_headers)).status_code == 200
    assert (await client.get("/users?limit=1000", headers=admin_headers)).status_code == 422


# --------------------------------------------------------------------------- #
# Filtering
# --------------------------------------------------------------------------- #
async def test_filter_by_city(client, admin_headers, population):
    body = (await client.get("/users?city=Tripoli&limit=100", headers=admin_headers)).json()
    assert body["total"] > 0
    assert all(u["city"] == "Tripoli" for u in body["users"])


async def test_filter_by_city_is_case_insensitive(client, admin_headers, population):
    a = (await client.get("/users?city=Tripoli&limit=100", headers=admin_headers)).json()
    b = (await client.get("/users?city=tripoli&limit=100", headers=admin_headers)).json()
    assert a["total"] == b["total"]


async def test_filter_by_type(client, admin_headers, population):
    body = (await client.get("/users?type=admin&limit=100", headers=admin_headers)).json()
    assert body["total"] > 0
    assert all(u["type"] == "admin" for u in body["users"])


async def test_filter_by_age(client, admin_headers, population):
    body = (await client.get("/users?age=22&limit=100", headers=admin_headers)).json()
    assert body["total"] > 0
    assert all(u["age"] == 22 for u in body["users"])


async def test_filter_by_first_name(client, admin_headers, population):
    body = (await client.get("/users?first_name=John&limit=100", headers=admin_headers)).json()
    assert body["total"] > 0
    assert all("john" in u["first_name"].lower() for u in body["users"])


async def test_filter_by_last_name(client, admin_headers, population):
    body = (await client.get("/users?last_name=Smith&limit=100", headers=admin_headers)).json()
    assert body["total"] > 0
    assert all(u["last_name"] == "Smith" for u in body["users"])


async def test_filter_by_email(client, admin_headers, population):
    body = (await client.get("/users?email=user1@&limit=100", headers=admin_headers)).json()
    assert body["total"] > 0
    assert all("user1@" in u["email"] for u in body["users"])


async def test_filter_with_no_matches(client, admin_headers, population):
    body = (await client.get("/users?city=Atlantis", headers=admin_headers)).json()
    assert body["total"] == 0
    assert body["total_pages"] == 0
    assert body["users"] == []


async def test_multiple_filters_combined(client, admin_headers, population):
    body = (
        await client.get("/users?city=Tripoli&type=client&limit=100", headers=admin_headers)
    ).json()
    assert all(u["city"] == "Tripoli" and u["type"] == "client" for u in body["users"])


async def test_search_across_fields(client, admin_headers, population):
    body = (await client.get("/users?search=Ali&limit=100", headers=admin_headers)).json()
    assert body["total"] > 0


async def test_age_range_filter(client, admin_headers, population):
    body = (await client.get("/users?min_age=22&max_age=24&limit=100", headers=admin_headers)).json()
    assert all(22 <= u["age"] <= 24 for u in body["users"])


async def test_inverted_age_range_is_a_400(client, admin_headers, population):
    resp = await client.get("/users?min_age=40&max_age=20", headers=admin_headers)
    assert resp.status_code == 400


# --------------------------------------------------------------------------- #
# Filtering + pagination together
# --------------------------------------------------------------------------- #
async def test_filtering_and_pagination_compose(client, admin_headers, population):
    all_tripoli = (
        await client.get("/users?city=Tripoli&type=client&limit=100", headers=admin_headers)
    ).json()
    total = all_tripoli["total"]
    assert total > 3

    page1 = (
        await client.get(
            "/users?city=Tripoli&type=client&page=1&limit=3", headers=admin_headers
        )
    ).json()
    page2 = (
        await client.get(
            "/users?city=Tripoli&type=client&page=2&limit=3", headers=admin_headers
        )
    ).json()

    assert page1["total"] == total, "total must reflect the FILTERED set, not everything"
    assert page1["limit"] == 3
    assert len(page1["users"]) == 3
    assert {u["id"] for u in page1["users"]}.isdisjoint({u["id"] for u in page2["users"]})
    assert all(u["city"] == "Tripoli" and u["type"] == "client" for u in page2["users"])


# --------------------------------------------------------------------------- #
# Update
# --------------------------------------------------------------------------- #
async def test_admin_updates_a_user(client, admin_headers, client_user):
    resp = await client.put(
        f"/users/{client_user.id}", headers=admin_headers, json={"city": "Zahle", "age": 40}
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["city"] == "Zahle"
    assert resp.json()["age"] == 40


async def test_admin_promotes_client_to_admin(client, admin_headers, client_user):
    resp = await client.put(
        f"/users/{client_user.id}", headers=admin_headers, json={"type": "admin"}
    )
    assert resp.status_code == 200
    assert resp.json()["type"] == "admin"


async def test_admin_demotes_admin_to_client(client, admin_headers, admin_user, make_user):
    other = await make_user(email="other@example.com", type="admin")
    resp = await client.put(f"/users/{other.id}", headers=admin_headers, json={"type": "client"})
    assert resp.status_code == 200
    assert resp.json()["type"] == "client"


async def test_admin_update_changes_password(client, admin_headers, client_user):
    resp = await client.put(
        f"/users/{client_user.id}", headers=admin_headers, json={"password": "ResetPass123"}
    )
    assert resp.status_code == 200
    login = await client.post(
        "/login", json={"email": client_user.email, "password": "ResetPass123"}
    )
    assert login.status_code == 200


async def test_admin_update_duplicate_email_returns_409(client, admin_headers, client_user, admin_user):
    resp = await client.put(
        f"/users/{client_user.id}", headers=admin_headers, json={"email": admin_user.email}
    )
    assert resp.status_code == 409


async def test_admin_update_unknown_user_returns_404(client, admin_headers):
    resp = await client.put(
        "/users/507f1f77bcf86cd799439011", headers=admin_headers, json={"city": "Beirut"}
    )
    assert resp.status_code == 404


async def test_malformed_id_returns_404(client, admin_headers):
    resp = await client.put(
        "/users/not-an-objectid", headers=admin_headers, json={"city": "Beirut"}
    )
    assert resp.status_code == 404


async def test_admin_update_validates_input(client, admin_headers, client_user):
    resp = await client.put(f"/users/{client_user.id}", headers=admin_headers, json={"age": 999})
    assert resp.status_code == 422


async def test_last_admin_cannot_demote_themselves(client, admin_headers, admin_user):
    resp = await client.put(
        f"/users/{admin_user.id}", headers=admin_headers, json={"type": "client"}
    )
    assert resp.status_code == 400
