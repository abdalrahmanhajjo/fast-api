# Authentication & User Management System — FastAPI + MongoDB + React

A production-style REST API with JWT authentication, role-based authorization,
pagination, filtering, soft delete and public statistics — plus a React single-page
frontend that consumes it.

* **Backend:** FastAPI · MongoDB (Motor + Beanie ODM) · Argon2id · JWT (python-jose)
* **Frontend:** React 18 · React Router 6 · Vite
* **Tests:** 132 pytest cases, all passing

---

## 1. Quick start

### Prerequisites

* Python 3.11+
* Node.js 18+
* MongoDB running locally (`mongodb://localhost:27017`) — or a MongoDB Atlas URI

### Backend

```bash
cd backend
python -m venv .venv && source .venv/bin/activate     # Windows: .venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env                                   # then edit JWT_SECRET_KEY
python -c "import secrets; print(secrets.token_urlsafe(48))"   # generate a real secret

python seed.py --demo        # creates the first admin + 25 demo clients
uvicorn app.main:app --reload
```

* API: <http://localhost:8000>
* **Swagger UI: <http://localhost:8000/docs>**
* ReDoc: <http://localhost:8000/redoc>

Seeded admin: `admin@example.com` / `Admin1234` (change these in `.env`).
Demo clients: `user1@example.com` … `user25@example.com` / `Password123`.

### Frontend

```bash
cd frontend
npm install
cp .env.example .env
npm run dev
```

Open <http://localhost:5173>. The Vite dev server proxies `/api/*` to
`http://localhost:8000`, so there are no CORS issues in development.

### Tests

```bash
cd backend
pytest -v
```

The suite runs against an **in-memory MongoDB** (`mongomock-motor`), so no database
server is needed to run it.

---

## 2. Project structure

```
fastapi-auth-system/
├── backend/
│   ├── app/
│   │   ├── main.py                 # app factory, CORS, lifespan, Swagger metadata
│   │   ├── core/
│   │   │   ├── config.py           # env-driven settings (pydantic-settings)
│   │   │   ├── security.py         # Argon2 hashing + JWT encode/decode
│   │   │   └── exceptions.py       # domain errors -> HTTP responses
│   │   ├── db/
│   │   │   └── mongodb.py          # Motor client + Beanie init/teardown
│   │   ├── models/
│   │   │   └── user.py             # Beanie Document, indexes, soft-delete helpers
│   │   ├── schemas/
│   │   │   ├── user.py             # ALL Pydantic validation rules
│   │   │   ├── auth.py             # login request / token response
│   │   │   └── common.py           # generic pagination + message shapes
│   │   ├── services/
│   │   │   ├── user_service.py     # business logic: create/update/delete/list
│   │   │   └── stats_service.py    # aggregation pipelines
│   │   └── api/
│   │       ├── deps.py             # get_current_user / get_current_admin
│   │       ├── router.py           # aggregates all route modules
│   │       └── routes/
│   │           ├── auth.py         # POST /register, POST /login
│   │           ├── users.py        # /users, /users/me, /users/{id}
│   │           └── stats.py        # /stats/*
│   ├── tests/                      # 132 tests across 7 files
│   ├── seed.py                     # bootstrap admin + demo data
│   ├── requirements.txt
│   ├── requirements-lock.txt       # exact tested versions
│   └── .env.example
└── frontend/
    ├── src/
    │   ├── api/client.ts           # fetch wrapper, token handling, error mapping
    │   ├── context/AuthContext.tsx # session state, login/logout, refresh restore
    │   ├── components/             # Navbar, ProtectedRoute, Pagination, Modal, …
    │   ├── pages/                  # Home, Login, Register, Profile, Admin, Stats
    │   └── styles/index.css        # design tokens, light + dark
    └── vite.config.ts              # /api proxy to the backend
```

### What each folder is responsible for

| Folder | Responsibility |
| --- | --- |
| `core/` | Cross-cutting concerns with **no** FastAPI or database imports: settings, hashing, JWT, error types. Unit-testable in isolation. |
| `db/` | Owns the MongoDB connection lifecycle and the list of Beanie documents. Nothing else opens a client. |
| `models/` | The shape of data **as stored**. One `Document` per collection, plus indexes. |
| `schemas/` | The shape of data **as exchanged over HTTP**. Every validation rule lives here, so routes never validate by hand. |
| `services/` | Business rules — "emails are unique", "deleted users are invisible", "only an admin may change a role". Enforced regardless of which route calls in. |
| `api/routes/` | Thin HTTP layer: parse input → call a service → shape the response. |
| `api/deps.py` | Reusable `Depends(...)` functions for authentication and authorization. |

---

## 3. Route summary

| Method | Endpoint | Access | Purpose |
| --- | --- | --- | --- |
| POST | `/register` | Public | Register — always creates a **client** |
| POST | `/login` | Public | Log in, receive a JWT |
| POST | `/users` | Admin | Create a client **or** an admin |
| GET | `/users/me` | Authenticated | Get own information |
| PUT | `/users/me` | Authenticated | Update own information |
| GET | `/users` | Admin | List users — pagination + filtering + search |
| GET | `/users/{id}` | Admin | Get one user |
| PUT | `/users/{id}` | Admin | Update any user, including their role |
| DELETE | `/users/{id}` | Admin | **Soft**-delete a user |
| POST | `/users/{id}/restore` | Admin | Undo a soft delete *(optional extra)* |
| GET | `/stats/count` | Public | Number of active users |
| GET | `/stats/average-age` | Public | Average age of active users |
| GET | `/stats/top-cities` | Public | Three most common cities |
| GET | `/health` | Public | Liveness probe |

---

## 4. Security design

### Role assignment — the core rule

Public registration **cannot** set a role. `UserRegister` is declared with
`extra="forbid"`, so a request like

```json
{ "first_name": "John", "email": "john@example.com", "type": "admin", "password": "Password123" }
```

is rejected with **422** — the request never reaches the service layer, and the
service hard-codes `UserType.CLIENT` regardless of what was sent:

```python
user = await user_service.create_user(payload.model_dump(), user_type=UserType.CLIENT)
```

Only `POST /users`, behind `Depends(get_current_admin)`, accepts a `type` field.

### Self-promotion is impossible

`PUT /users/me` uses `UserUpdateMe`, which has no `type` field and forbids extras.
A client sending `{"type": "admin"}` — alone or mixed with valid fields — gets a
422 and **nothing** is written. As a second line of defence,
`user_service.update_user()` drops the `type` key unless `allow_role_change=True`,
which only the admin route passes.

### Passwords

Argon2id (OWASP's current recommendation) via `argon2-cffi`, 64 MiB memory cost.
Plain passwords are never stored, never logged and never returned — `UserPublic`
simply has no password field, so it cannot leak by accident.

### JWT

Claims: `sub` (user id), `role`, `iat`, `exp`, `jti`, `type`. The `role` claim is a
*hint only* — `get_current_user` re-reads the user from the database on every
request, so a forged or stale role claim cannot escalate privileges, and
soft-deleting a user invalidates their already-issued tokens immediately.

### Error semantics

| Code | When |
| --- | --- |
| 400 | Business-logic errors (`min_age > max_age`, deleting your own account) |
| 401 | No token, invalid token, expired token, wrong credentials, deactivated account |
| 403 | Authenticated, but the role is insufficient |
| 404 | User does not exist (a malformed ObjectId is also a 404, not a 500) |
| 409 | Duplicate email |
| 422 | Validation failure — returns `{"detail": ..., "errors": [{"field", "message"}]}` |

Login returns the *same* 401 message for "unknown email" and "wrong password", so
the endpoint cannot be used to enumerate registered users.

---

## 5. Validation rules

| Field | Rule |
| --- | --- |
| `first_name` / `last_name` | Required, non-empty after trimming, ≥ 2 chars, letters/spaces/apostrophes/hyphens only |
| `email` | Required, RFC-valid (`email-validator`), normalised to lowercase, unique |
| `phone` | Required, international format — `+96170123456`, `03 123456`, `+1-555-1234567` |
| `city` | Required, non-empty after trimming, ≥ 2 chars |
| `age` | Required, integer, 13–120 |
| `password` | ≥ 8 chars, at least one uppercase, one lowercase, one digit, no whitespace |
| `type` | `admin` or `client` — **never accepted from a public caller** |

---

## 6. Pagination, filtering and search

```
GET /users?city=Tripoli&type=client&page=2&limit=10
```

Response:

```json
{ "page": 2, "limit": 10, "total": 45, "total_pages": 5, "users": [ ... ] }
```

Order of operations: **filter → count the filtered set → skip/limit**. That is what
makes filtering and pagination compose correctly — `total` always describes the
filtered result, not the whole collection.

| Parameter | Behaviour |
| --- | --- |
| `page` | ≥ 1, default `1` |
| `limit` | 1–100, default `10` (max enforced by `MAX_PAGE_SIZE`) |
| `age` | Exact match |
| `min_age` / `max_age` | Inclusive range (ignored when `age` is given) |
| `city`, `first_name`, `last_name`, `email` | Case-insensitive *contains* (regex-escaped — user input cannot inject regex metacharacters) |
| `type` | Exact: `admin` or `client` |
| `search` | Free text across first name, last name, email and city |
| `include_deleted` | Admin-only view of soft-deleted records |
| `sort_by` / `order` | `created_at`, `first_name`, `age`, … / `asc` \| `desc` |

---

## 7. Soft delete

`DELETE /users/{id}` never removes the document. It sets:

```
is_deleted = true
deleted_at = <timestamp>
```

A soft-deleted user:

* cannot log in (401),
* has their existing JWTs rejected immediately,
* does not appear in `GET /users`,
* is excluded from every `/stats/*` figure,
* **still exists in MongoDB** and can be listed with `?include_deleted=true`
  or restored with `POST /users/{id}/restore`.

Their email stays reserved, so a restore can never collide with a newer account.

---

## 8. Frontend

| Route | Access | Contents |
| --- | --- | --- |
| `/` | Public | Landing page |
| `/stats` | Public | Live statistics with a top-cities bar chart |
| `/login`, `/register` | Public | Auth forms; registration never sends a `type` |
| `/profile` | Authenticated | View & edit own details, change password |
| `/admin` | Admin only | Table, filters, search, pagination, sortable columns, create/edit modals, soft delete + restore |
| `/forbidden`, `/404` | — | A client landing on `/admin` is redirected to `/forbidden` |

`<ProtectedRoute>` guards routes and remembers where the user was heading, so
logging in returns them to it. The JWT is kept in `localStorage`; any `401` from
any request drops the session automatically.

---

## 9. Test coverage

```
tests/test_registration.py    validation, duplicate email, "always a client"
tests/test_login.py           credentials, deleted users, no user enumeration
tests/test_authentication.py  missing / malformed / expired / revoked JWTs
tests/test_authorization.py   admin vs client vs anonymous, self-promotion attempts
tests/test_profile.py         GET/PUT /users/me, password change, duplicate email
tests/test_admin_users.py     create, list, paginate, filter, filter+paginate, role changes
tests/test_soft_delete.py     invisibility, login block, stats exclusion, record survival
tests/test_stats.py           count, average age, top cities, empty-database cases
```

```
132 passed
```

---

## 10. Configuration

All settings come from environment variables (see `backend/.env.example`).

| Variable | Default | Notes |
| --- | --- | --- |
| `MONGODB_URI` | `mongodb://localhost:27017` | Swap for an Atlas URI in production |
| `MONGODB_DB_NAME` | `auth_system` | |
| `JWT_SECRET_KEY` | dev placeholder | **Must** be changed before deploying |
| `JWT_ALGORITHM` | `HS256` | |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `60` | |
| `CORS_ORIGINS_RAW` | `http://localhost:5173,…` | Comma-separated |
| `FIRST_ADMIN_EMAIL` / `FIRST_ADMIN_PASSWORD` | `admin@example.com` / `Admin1234` | Used by `seed.py` only |
| `DEFAULT_PAGE_SIZE` / `MAX_PAGE_SIZE` | `10` / `100` | Pagination guard-rails |

---

## 11. Manual verification with curl

```bash
# public registration — always a client
curl -X POST localhost:8000/register -H 'Content-Type: application/json' \
  -d '{"first_name":"John","last_name":"Doe","email":"john@example.com",
       "phone":"+96170123456","city":"Tripoli","age":25,"password":"Password123"}'

# trying to self-assign admin -> 422
curl -X POST localhost:8000/register -H 'Content-Type: application/json' \
  -d '{"first_name":"Bad","last_name":"Actor","email":"bad@example.com",
       "phone":"+96170555000","city":"Tripoli","age":25,
       "type":"admin","password":"Password123"}'

# log in
TOKEN=$(curl -s -X POST localhost:8000/login -H 'Content-Type: application/json' \
  -d '{"email":"admin@example.com","password":"Admin1234"}' | jq -r .access_token)

# filtering + pagination together
curl "localhost:8000/users?city=Tripoli&type=client&page=2&limit=10" \
  -H "Authorization: Bearer $TOKEN"

# public statistics
curl localhost:8000/stats/count
curl localhost:8000/stats/average-age
curl localhost:8000/stats/top-cities
```
# fast-api
# fast-api
