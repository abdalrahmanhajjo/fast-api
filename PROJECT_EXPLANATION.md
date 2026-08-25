# What I Built: FastAPI Authentication and User Management System

## 1. Project overview

I built a full-stack authentication and user-management application. The backend is a REST API made with FastAPI, MongoDB, Motor, and Beanie. The frontend is a React single-page application made with Vite and React Router.

The system supports:

- Public user registration
- Secure login with JSON Web Tokens (JWTs)
- Two roles: `client` and `admin`
- Protected routes and role-based authorization
- A user profile that can be viewed and updated
- Admin creation, viewing, filtering, updating, deletion, and restoration of users
- Pagination, searching, filtering, and sorting
- Soft deletion instead of permanent deletion
- Public statistics about active users
- Consistent validation and error responses
- Automated backend tests using an in-memory MongoDB database
- A React frontend that consumes the API

The main idea is separation of responsibilities. Routes deal with HTTP, schemas validate data, services enforce business rules, models represent stored data, dependencies handle authentication and authorization, and the database module owns the MongoDB connection.

---

## 2. Technologies I used

### Backend

- **FastAPI** creates the REST API, dependency injection, validation integration, and interactive API documentation.
- **Pydantic** defines request and response schemas and validates all incoming data.
- **pydantic-settings** loads configuration from environment variables and the `.env` file.
- **MongoDB** stores user documents.
- **Motor** is the asynchronous MongoDB driver.
- **Beanie** is the asynchronous ODM that maps Python classes to MongoDB documents.
- **Argon2id** securely hashes passwords.
- **python-jose** creates and verifies JWT access tokens.
- **Uvicorn** runs the ASGI application.
- **pytest**, **pytest-asyncio**, **HTTPX**, and **mongomock-motor** test the asynchronous API without requiring a real MongoDB server.

### Frontend

- **React 18** builds the user interface.
- **React Router 6** controls public, authenticated, and admin pages.
- **Vite** provides the development server, build system, and `/api` development proxy.
- The browser's **Fetch API** sends HTTP requests to FastAPI.
- **localStorage** keeps the JWT between page refreshes.

---

## 3. Project structure and responsibility of each layer

```text
fastapi-auth-system/
├── backend/
│   ├── app/
│   │   ├── main.py                 Application creation, CORS, lifespan, docs
│   │   ├── api/
│   │   │   ├── deps.py             Authentication and admin dependencies
│   │   │   ├── router.py           Combines all API routers
│   │   │   └── routes/
│   │   │       ├── auth.py         Registration and login
│   │   │       ├── users.py        Profile and admin user operations
│   │   │       └── stats.py        Public statistics
│   │   ├── core/
│   │   │   ├── config.py           Environment-based settings
│   │   │   ├── security.py         Password hashing and JWT functions
│   │   │   └── exceptions.py       Application errors and HTTP handlers
│   │   ├── db/mongodb.py           MongoDB startup and shutdown
│   │   ├── models/user.py          Stored user document and indexes
│   │   ├── schemas/                Request and response validation
│   │   └── services/               User rules and database operations
│   ├── tests/                       Automated backend tests
│   ├── seed.py                      Creates an admin and demo clients
│   └── requirements.txt            Python dependencies
├── frontend/
│   ├── src/api/client.ts            API client and JWT attachment
│   ├── src/context/AuthContext.tsx  Global authentication state
│   ├── src/components/              Reusable UI and route protection
│   ├── src/pages/                   Application pages
│   └── vite.config.ts               Development server and API proxy
├── README.md                        Quick-start and reference guide
└── PROJECT_EXPLANATION.md           This complete explanation
```

### Why the layers are separated

A route should not contain every part of the application logic. For example, the registration route receives a validated request and calls `user_service.create_user()`. The service checks email uniqueness, hashes the password through the security module, creates the model, and writes it to MongoDB. This makes the same rules reusable and keeps route functions easy to read.

The request moves through the application like this:

```text
Browser or API client
        |
        v
FastAPI route
        |
        +--> Pydantic request validation
        |
        +--> authentication/authorization dependency (when required)
        |
        v
Service business logic
        |
        v
Beanie model -> Motor -> MongoDB
        |
        v
Pydantic response model -> JSON response
```

---

## 4. How the application starts

`backend/app/main.py` is the application entry point. It creates the FastAPI application, registers CORS middleware and exception handlers, includes all routers, and exposes `/` and `/health`.

FastAPI's lifespan function runs around the life of the server:

1. Before requests are accepted, `connect_to_mongo()` creates a Motor client.
2. `init_beanie()` connects the `User` document model to the selected database.
3. The application processes requests.
4. During shutdown, `close_mongo_connection()` closes the MongoDB client.

The application object used by Uvicorn is:

```python
app = create_app()
```

Therefore, the backend is started with:

```bash
cd backend
uvicorn app.main:app --reload
```

FastAPI automatically generates documentation from the routes and Pydantic schemas:

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`
- Health check: `http://localhost:8000/health`

---

## 5. Configuration

`backend/app/core/config.py` defines a `Settings` class. Values are loaded from environment variables or `backend/.env`, while safe development defaults are available in the code.

Important settings are:

| Setting | Purpose |
| --- | --- |
| `MONGODB_URI` | MongoDB server connection string |
| `MONGODB_DB_NAME` | Database name |
| `JWT_SECRET_KEY` | Secret used to sign and verify JWTs |
| `JWT_ALGORITHM` | JWT algorithm; the default is `HS256` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Access-token lifetime |
| `CORS_ORIGINS_RAW` | Browser origins allowed to call the backend |
| `FIRST_ADMIN_EMAIL` | Email used by the seed script |
| `FIRST_ADMIN_PASSWORD` | Initial admin password used by the seed script |
| `DEFAULT_PAGE_SIZE` | Default number of users in a page |
| `MAX_PAGE_SIZE` | Maximum allowed page size |

`get_settings()` is cached, so the `.env` file is parsed only once for each backend process.

The development secret must be replaced before deployment. A secure value can be generated with:

```bash
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

---

## 6. MongoDB user document

`backend/app/models/user.py` defines the `User` Beanie document stored in the `users` collection.

Each document contains:

| Field | Meaning |
| --- | --- |
| `first_name`, `last_name` | User's name |
| `email` | Normalized login email |
| `phone`, `city`, `age` | Profile information |
| `type` | Either `client` or `admin` |
| `password_hash` | Argon2id hash; never the plain password |
| `is_deleted` | Whether the account is soft-deleted |
| `deleted_at` | When the account was soft-deleted |
| `created_at`, `updated_at` | UTC audit timestamps |

The model creates these indexes:

- A unique index on `email` prevents duplicate accounts at the database level.
- An index on `is_deleted` helps active-user queries.
- Indexes on `city` and `type` help common filtering and statistics operations.

The model also has helper methods for getting a full name, checking whether a user is an admin, updating the modification time, and marking an account as deleted.

---

## 7. Input validation and safe responses

The schemas in `backend/app/schemas/` separate HTTP data from database documents.

### Validation rules

| Field | Rule |
| --- | --- |
| First and last name | Trimmed, 2-50 characters, supported letters and common name punctuation |
| Email | Valid email address, trimmed, and converted to lowercase |
| Phone | Normalized and checked as an international-style number |
| City | Trimmed, non-empty, and at least 2 characters |
| Age | Integer from 13 through 120 |
| Password | 8-128 characters, uppercase, lowercase, digit, and no whitespace |
| Role | Only the `admin` or `client` enum values |

Schemas use `extra="forbid"`. Unexpected request fields cause a `422 Unprocessable Entity` response instead of being silently ignored.

There are different schemas for different permissions:

- `UserRegister` accepts public registration fields but does not contain `type`.
- `UserCreate` is used by an admin and allows `type`.
- `UserUpdateMe` allows a user to update personal fields but not `type`.
- `UserUpdateAdmin` permits an admin to change a user's role.
- `UserPublic` returns safe profile data and never contains `password_hash`.
- `UserAdminView` adds soft-deletion fields for administrators.
- `UserListResponse` wraps a user list with pagination metadata.

The update endpoints behave like partial updates even though they use `PUT`: only fields actually sent by the caller are changed. An empty update is rejected.

---

## 8. Password security

Passwords are handled in `backend/app/core/security.py`.

When an account is created or a password is changed:

1. The plain password passes the Pydantic password rules.
2. `hash_password()` sends it to Argon2id.
3. Argon2 generates a random salt and creates a one-way hash.
4. Only the resulting hash is stored in `password_hash`.

During login, `verify_password()` compares the submitted password with the stored hash. A plain password cannot be recovered from the stored value. Invalid or damaged hashes safely return `False` instead of crashing the API.

The configured Argon2 parameters use two iterations, 64 MiB of memory, parallelism of two, a 32-byte hash, and a 16-byte salt.

---

## 9. JWT authentication

After a successful login, `create_access_token()` creates a signed JWT containing:

| Claim | Meaning |
| --- | --- |
| `sub` | MongoDB user ID |
| `role` | Role at the time the token was created |
| `iat` | Issued-at time |
| `exp` | Expiration time |
| `jti` | Unique token identifier |
| `type` | Token marker, currently `access` |

The client sends the token on protected requests:

```http
Authorization: Bearer <access_token>
```

`get_current_user()` performs authentication:

1. It reads the Bearer token with FastAPI's `HTTPBearer` dependency.
2. It verifies the token signature and expiration.
3. It checks the token type and `sub` claim.
4. It uses `sub` to load the latest user from MongoDB.
5. It rejects missing, invalid, expired, unknown, or soft-deleted users with `401`.

The database is intentionally checked on every protected request. The JWT's role is only a hint: authorization uses the current role stored in MongoDB. Consequently, demoting or soft-deleting a user affects their existing token immediately.

`get_current_admin()` first runs `get_current_user()` and then checks that the current database role is `admin`. A valid client receives `403 Forbidden`, while a missing or invalid login receives `401 Unauthorized`.

---

## 10. Registration flow

The public endpoint is `POST /register`.

Example request:

```json
{
  "first_name": "John",
  "last_name": "Doe",
  "email": "john@example.com",
  "phone": "+96170123456",
  "city": "Tripoli",
  "age": 25,
  "password": "Password123"
}
```

The complete flow is:

1. FastAPI parses the JSON body as `UserRegister`.
2. Pydantic validates and normalizes every field.
3. The route explicitly calls `create_user(..., user_type=UserType.CLIENT)`.
4. The service checks the email across active and deleted users.
5. The password is converted to an Argon2id hash.
6. Beanie inserts the new user into MongoDB.
7. The route returns `UserPublic` with status `201`, without the password or its hash.

A public caller cannot create an admin. The registration schema rejects a `type` property, and the route explicitly supplies the `client` role. These are two separate layers of protection.

---

## 11. Login flow

The public endpoint is `POST /login`.

```json
{
  "email": "john@example.com",
  "password": "Password123"
}
```

The flow is:

1. The email and password are validated.
2. The service finds the normalized email, including soft-deleted records.
3. Argon2 verifies the password hash.
4. A deleted account is rejected.
5. A signed access token is created with the configured expiration.
6. The API returns the token, token type, lifetime in seconds, and safe user data.

Example response:

```json
{
  "access_token": "eyJ...",
  "token_type": "bearer",
  "expires_in": 3600,
  "user": {
    "id": "66c...",
    "first_name": "John",
    "last_name": "Doe",
    "email": "john@example.com",
    "phone": "+96170123456",
    "city": "Tripoli",
    "age": 25,
    "type": "client",
    "created_at": "2026-08-24T10:00:00Z",
    "updated_at": "2026-08-24T10:00:00Z"
  }
}
```

The same `401` message is returned for an unknown email, a wrong password, and a deleted account. This avoids revealing whether a particular email is registered.

---

## 12. User profile flow

Any authenticated user can call:

- `GET /users/me` to read their profile.
- `PUT /users/me` to change one or more profile fields or their password.

Both endpoints use `get_current_user()`. The update route passes `allow_role_change=False` to the service. In addition, `UserUpdateMe` has no role field and forbids extra properties. Therefore, a client cannot promote themselves by sending `{"type": "admin"}`.

When the email changes, its uniqueness is checked. When the password changes, it is hashed before saving. `updated_at` is refreshed after every successful update.

---

## 13. Administrator flow

Admin endpoints depend on `get_current_admin()`.

An administrator can:

- Create a client or another administrator.
- List and search users.
- Read one user, including soft-delete information.
- Update any user and change their role.
- Soft-delete another user.
- Restore a soft-deleted user.

There are two important safeguards:

- An admin cannot delete their own account.
- The last active admin cannot demote themselves. Another admin must be promoted first.

These rules help prevent accidentally losing all administrative access.

---

## 14. Pagination, filtering, searching, and sorting

`GET /users` is admin-only and supports:

| Parameter | Behavior |
| --- | --- |
| `page` | One-based page number; minimum 1 |
| `limit` | Page size, restricted by `MAX_PAGE_SIZE` |
| `age` | Exact age; takes precedence over an age range |
| `min_age`, `max_age` | Inclusive age range |
| `city` | Case-insensitive partial match |
| `type` | Exact `admin` or `client` role |
| `first_name`, `last_name`, `email` | Case-insensitive partial match |
| `search` | Searches first name, last name, email, and city |
| `include_deleted` | Includes soft-deleted users when true |
| `sort_by` | Selects an allowed field for sorting |
| `order` | `asc` or `desc` |

Example:

```http
GET /users?search=ali&city=Tripoli&type=client&page=2&limit=10&sort_by=age&order=asc
Authorization: Bearer <admin-token>
```

User-supplied text is passed through `re.escape()` before being used in MongoDB regular expressions. This prevents the search text from becoming unintended regular-expression syntax.

The service applies operations in this order:

1. Build the MongoDB filter.
2. Count every document matching that filter.
3. Calculate `skip = (page - 1) * limit`.
4. Sort the matching documents.
5. Apply `skip` and `limit`.
6. Return users and pagination metadata.

This means `total` describes the filtered result, not all users in the database.

---

## 15. Soft deletion and restoration

`DELETE /users/{user_id}` does not permanently remove a MongoDB document. It changes:

```text
is_deleted = true
deleted_at = current UTC time
updated_at = current UTC time
```

After soft deletion, the account:

- Cannot log in.
- Cannot use an already issued token.
- Is excluded from normal user lists.
- Is excluded from all public statistics.
- Still owns its email address, preventing an ambiguous duplicate account.

An admin can inspect deleted records with `include_deleted=true` and restore one with `POST /users/{user_id}/restore`. Restoration clears `deleted_at`, changes `is_deleted` to `false`, and updates the modification timestamp.

---

## 16. Public statistics

The statistics endpoints do not require authentication:

- `GET /stats/count` returns the number of active users.
- `GET /stats/average-age` returns the mean active-user age, rounded to one decimal. It returns `0.0` when there are no active users.
- `GET /stats/top-cities` returns the three cities with the most active users.

The service applies `{"is_deleted": false}` to every calculation. Average age and city rankings use MongoDB aggregation pipelines, so MongoDB performs the calculation instead of loading every user into Python.

---

## 17. Complete API reference

| Method | Endpoint | Access | Successful result |
| --- | --- | --- | --- |
| `GET` | `/` | Public | Application name, version, and docs path |
| `GET` | `/health` | Public | `{"status": "ok"}` |
| `POST` | `/register` | Public | Creates a client; `201` |
| `POST` | `/login` | Public | Returns an access token and user |
| `GET` | `/users/me` | Authenticated | Returns the current profile |
| `PUT` | `/users/me` | Authenticated | Updates the current profile |
| `POST` | `/users` | Admin | Creates a client or admin; `201` |
| `GET` | `/users` | Admin | Returns filtered and paginated users |
| `GET` | `/users/{user_id}` | Admin | Returns one user |
| `PUT` | `/users/{user_id}` | Admin | Updates any user, including role |
| `DELETE` | `/users/{user_id}` | Admin | Soft-deletes a user |
| `POST` | `/users/{user_id}/restore` | Admin | Restores a soft-deleted user |
| `GET` | `/stats/count` | Public | Active-user count |
| `GET` | `/stats/average-age` | Public | Active-user average age |
| `GET` | `/stats/top-cities` | Public | Three most common cities |

Common error status codes are:

| Code | Meaning in this project |
| --- | --- |
| `400` | Invalid business operation, such as an invalid age range or self-deletion |
| `401` | Missing, invalid, expired token, bad credentials, or deactivated account |
| `403` | Authenticated user does not have the required admin role |
| `404` | Requested user does not exist; malformed MongoDB IDs also become a clean 404 |
| `409` | Email already exists |
| `422` | Request data failed Pydantic validation |

Validation errors use a frontend-friendly format:

```json
{
  "detail": "Validation failed.",
  "errors": [
    {
      "field": "password",
      "message": "Value error, Password must contain at least one uppercase letter"
    }
  ]
}
```

---

## 18. How the React frontend works with FastAPI

`frontend/src/api/client.ts` is a small wrapper around `fetch()`.

For each request it:

1. Builds the URL and query parameters.
2. Reads the JWT from `localStorage` when authentication is needed.
3. Adds `Authorization: Bearer <token>`.
4. Converts the request body to JSON.
5. Parses the JSON response.
6. Converts backend failures into one `ApiError` shape.
7. Notifies the authentication layer when an authenticated request returns `401`.

`AuthContext.tsx` stores the current user and exposes `login`, `logout`, `isAuthenticated`, and `isAdmin` to the whole React application.

The browser session works as follows:

```text
Login page -> POST /login -> receive JWT -> save JWT in localStorage
     -> store returned user in AuthContext -> open protected pages
```

After a hard refresh, the context finds the stored token and calls `GET /users/me`. If the backend accepts it, the session is restored. If it is expired, invalid, or belongs to a deleted account, the token is removed.

`ProtectedRoute` protects the profile page and can also require the admin role for the admin page. This improves the user experience, but the frontend is not the security boundary. FastAPI checks the JWT and database role again for every protected API request.

During development, the frontend calls `/api`. Vite proxies that path to `http://localhost:8000` and removes the `/api` prefix. For example:

```text
Browser request:  http://localhost:5173/api/login
Proxied request:  http://localhost:8000/login
```

---

## 19. Automated testing

The backend tests cover registration, authentication, login, authorization, profile updates, admin user operations, soft deletion, and statistics.

Tests use `mongomock-motor`, an in-memory MongoDB-compatible client. The test setup binds Beanie models to that temporary database. This makes tests isolated and allows them to run without a local MongoDB server.

Run the test suite with:

```bash
cd backend
pytest -v
```

The important behaviors tested include validation failures, duplicate emails, password hashing, invalid and expired authentication, role restrictions, self-promotion prevention, filtering and pagination, deletion effects, restoration, and active-user-only statistics.

---

## 20. How to run the complete project

### Requirements

- Python 3.11 or newer
- Node.js 18 or newer
- A local MongoDB server or MongoDB Atlas connection

### Start the backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Edit `.env`, especially `JWT_SECRET_KEY`. Then create the first admin and optional demo clients:

```bash
python seed.py --demo
```

Start FastAPI:

```bash
uvicorn app.main:app --reload
```

### Start the frontend

In another terminal:

```bash
cd frontend
npm install
cp .env.example .env
npm run dev
```

Open `http://localhost:5173`.

With the default seed configuration:

- Admin: `admin@example.com` / `Admin1234`
- Demo clients: `user1@example.com` through `user25@example.com` / `Password123`

Development credentials must be changed before a real deployment.

---

## 21. Example end-to-end use

### Register a client

```bash
curl -X POST http://localhost:8000/register \
  -H 'Content-Type: application/json' \
  -d '{
    "first_name": "John",
    "last_name": "Doe",
    "email": "john@example.com",
    "phone": "+96170123456",
    "city": "Tripoli",
    "age": 25,
    "password": "Password123"
  }'
```

### Log in

```bash
curl -X POST http://localhost:8000/login \
  -H 'Content-Type: application/json' \
  -d '{"email":"john@example.com","password":"Password123"}'
```

Copy `access_token` from the response.

### Read the authenticated profile

```bash
curl http://localhost:8000/users/me \
  -H 'Authorization: Bearer YOUR_ACCESS_TOKEN'
```

### Call an admin endpoint

Log in as the seeded administrator, copy its token, and run:

```bash
curl 'http://localhost:8000/users?page=1&limit=10&city=Tripoli' \
  -H 'Authorization: Bearer ADMIN_ACCESS_TOKEN'
```

---

## 22. Security decisions summarized

The most important security decisions in the project are:

- Plain passwords are never stored or returned.
- Argon2id hashes every password with a random salt.
- JWTs are signed, expire, and are validated on every protected request.
- The current user and role are loaded from MongoDB instead of trusting the JWT role claim.
- Public registration always creates a client.
- Self-service updates cannot change a role at either the schema or service layer.
- Admin access is enforced in backend dependencies, not only in React.
- Login uses one generic failure message to reduce account enumeration.
- Soft-deleting an account immediately stops its existing tokens.
- Response schemas prevent password hashes from leaking.
- Search input is escaped before being used as a regular expression.
- Duplicate emails are prevented by both service checks and a unique database index.
- The last active admin cannot demote themselves, and an admin cannot delete themselves.
- Configuration and secrets are supplied through environment variables.

In summary, I built the application as a layered asynchronous FastAPI system: Pydantic validates the API contract, dependencies identify and authorize callers, services enforce the rules, Beanie and Motor communicate with MongoDB, Argon2id protects passwords, JWTs carry authenticated sessions, and React provides the browser interface.
