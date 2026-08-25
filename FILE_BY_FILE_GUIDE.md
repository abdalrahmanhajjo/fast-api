# Complete File-by-File Guide

This document explains what is inside every authored file in the project, what each file is responsible for, and how it connects to the rest of the application.

Generated directories are not documented file by file:

- `frontend/node_modules/` contains installed JavaScript packages.
- `frontend/dist/` contains the generated production frontend build.
- `backend/.venv/` contains the Python virtual environment.
- `__pycache__/` and `.pytest_cache/` contain temporary Python cache data.

Lock files are included below, but their thousands of generated dependency entries are not described individually.

---

## Root files

### `README.md`

This is the main quick-start and project reference document. It contains:

- The technology stack.
- Backend and frontend startup commands.
- Test commands.
- The project directory structure.
- A summary of all API routes.
- Security decisions such as role protection, password hashing, and JWT handling.
- Validation rules.
- Pagination and filtering behavior.
- Soft-delete behavior.
- Example requests and responses.

Use this file when someone wants to install, run, or quickly understand the application.

### `PROJECT_EXPLANATION.md`

This is the long-form explanation of what was built and how it works. It explains the application in first person and walks through:

- Architecture and request flow.
- MongoDB models.
- Authentication and authorization.
- Registration and login.
- Admin and client behavior.
- Statistics.
- React integration.
- Testing and security.

Use this file for a project presentation, report, or detailed technical explanation.

### `FILE_BY_FILE_GUIDE.md`

This is the document you are reading. Its purpose is to describe every important project file clearly.

---

# Backend

The backend is an asynchronous FastAPI application. It validates HTTP data with Pydantic, stores documents through Beanie and Motor, and uses MongoDB as its database.

## Backend environment and dependency files

### `backend/.env.example`

This is a safe configuration template. It shows the environment variables required by the backend:

- Application name and debug mode.
- MongoDB URI and database name.
- JWT secret, algorithm, and expiration time.
- Allowed CORS origins.
- Seeded administrator credentials.

It does not control the running application until it is copied to `.env`.

### `backend/.env`

This is the local environment configuration actually read by the backend. It should contain deployment-specific values and secrets. It must not be committed publicly.

Important current issue: `DEBUG` is set to `release`, but the application expects a boolean. It should be changed to `DEBUG=false` or `DEBUG=true`.

### `backend/requirements.txt`

This lists Python package requirements using compatible version ranges. It includes:

- FastAPI and Uvicorn.
- Pydantic and pydantic-settings.
- Motor and Beanie.
- Argon2 and python-jose.
- pytest, HTTPX, and the in-memory MongoDB test tools.

Use it with `pip install -r requirements.txt`.

### `backend/requirements-lock.txt`

This stores the exact dependency versions used for the tested environment. Unlike `requirements.txt`, it is intended to produce a repeatable installation.

### `backend/pytest.ini`

This configures pytest. It sets the asynchronous test behavior and tells pytest how to discover and run the backend tests.

### `backend/run.sh`

This is a small shell shortcut for starting the FastAPI application with Uvicorn in development mode.

### `backend/seed.py`

This script inserts initial data into MongoDB.

It contains:

- A list of demo cities and names.
- `seed_admin()`, which creates the first administrator if it does not exist.
- `seed_demo_clients()`, which creates 25 sample client accounts.
- `main()`, which connects to MongoDB, runs the requested seed operations, and closes the database connection.

Running `python seed.py` creates only the administrator. Running `python seed.py --demo` also creates the demo clients.

---

## Backend application entry point

### `backend/app/main.py`

This is the FastAPI entry point and application factory.

It contains:

- Logging configuration.
- A lifespan function that opens MongoDB during startup and closes it during shutdown.
- API title, description, version, and Swagger tag metadata.
- `create_app()`, which creates and configures the FastAPI instance.
- CORS middleware configuration.
- Registration of custom exception handlers.
- Inclusion of all API routers.
- The public `/` metadata endpoint.
- The public `/health` liveness endpoint.
- The final `app` object used by Uvicorn.

When the command `uvicorn app.main:app` runs, Uvicorn imports the `app` object from this file.

### `backend/app/__init__.py`

This marks `backend/app` as a Python package. It does not currently contain application logic.

---

## Backend API layer

### `backend/app/api/router.py`

This creates one central `APIRouter` and includes the authentication, user, and statistics routers. `main.py` includes this combined router once instead of importing every route file separately.

### `backend/app/api/deps.py`

This contains reusable FastAPI dependencies for authentication and authorization.

It defines:

- `bearer_scheme`, which reads the Bearer token from the `Authorization` header.
- `get_current_user()`, which validates the JWT, loads the user from MongoDB, and rejects missing, expired, invalid, unknown, or deleted accounts.
- `get_current_admin()`, which requires the authenticated database user to have the `admin` role.
- `get_optional_user()`, which returns a user when a valid token exists but allows an anonymous request otherwise.

The important security decision is that the current role is read from MongoDB. The API does not trust the role stored in the JWT by itself.

### `backend/app/api/routes/auth.py`

This contains the public authentication endpoints.

`POST /register`:

- Accepts `UserRegister` data.
- Always supplies the `client` role.
- Calls `user_service.create_user()`.
- Returns a safe `UserPublic` response with status 201.

`POST /login`:

- Looks up the normalized email.
- Verifies the submitted password against the Argon2 hash.
- Rejects deleted accounts.
- Creates a signed JWT.
- Returns the token, expiration time, and safe user data.

### `backend/app/api/routes/users.py`

This contains profile and administrator user-management endpoints.

It includes:

- `POST /users`: admin creation of a client or administrator.
- `GET /users`: admin pagination, filtering, searching, and sorting.
- `GET /users/me`: returns the authenticated user's profile.
- `PUT /users/me`: updates the authenticated user's allowed fields.
- `GET /users/{user_id}`: admin retrieval of one user.
- `PUT /users/{user_id}`: admin update of any user, including role changes.
- `DELETE /users/{user_id}`: admin soft deletion.
- `POST /users/{user_id}/restore`: admin restoration.
- `_is_last_admin()`: prevents the final active administrator from demoting themselves.

The literal `/users/me` routes are defined before `/{user_id}` so FastAPI does not interpret `me` as an ID.

### `backend/app/api/routes/stats.py`

This contains three public statistics endpoints:

- `/stats/count` returns the active-user total.
- `/stats/average-age` returns the active-user average age.
- `/stats/top-cities` returns the top three cities.

The routes remain small because the database calculations are performed by `stats_service.py`.

### `backend/app/api/__init__.py`

This marks the API directory as a Python package. It has no runtime logic.

### `backend/app/api/routes/__init__.py`

This marks the route directory as a Python package. It has no runtime logic.

---

## Backend core layer

### `backend/app/core/config.py`

This defines application settings with `pydantic-settings`.

The `Settings` class contains:

- Project name, version, and debug mode.
- MongoDB configuration.
- JWT configuration.
- CORS origins.
- First-administrator seed values.
- Pagination defaults and limits.

`CORS_ORIGINS` converts the comma-separated environment value into a Python list. `get_settings()` is cached so settings are loaded only once per process. The module-level `settings` object is imported throughout the backend.

### `backend/app/core/security.py`

This contains all password and JWT security functions.

Password functions:

- `hash_password()` creates an Argon2id hash.
- `verify_password()` safely checks a password against a stored hash.
- `password_needs_rehash()` detects hashes created with older parameters.

JWT functions:

- `create_access_token()` creates a signed token with `sub`, `role`, `iat`, `exp`, `jti`, and `type` claims.
- `decode_access_token()` verifies the signature and expiration, checks the token type, and returns the payload or `None`.

This module intentionally contains no FastAPI-specific code.

### `backend/app/core/exceptions.py`

This defines expected application errors and maps them to consistent JSON responses.

Error classes:

- `BadRequestError` → 400.
- `UnauthorizedError` → 401.
- `ForbiddenError` → 403.
- `NotFoundError` → 404.
- `ConflictError` → 409.

`register_exception_handlers()` adds handlers for application errors, normal Starlette HTTP errors, and Pydantic validation errors. Validation failures are converted to a compact list containing `field` and `message`.

### `backend/app/core/__init__.py`

This marks the core directory as a Python package. It has no runtime logic.

---

## Backend database layer

### `backend/app/db/mongodb.py`

This owns the MongoDB connection lifecycle.

It contains:

- `DOCUMENT_MODELS`, the list of Beanie document classes.
- `_client`, the active Motor client.
- `init_models()`, which binds Beanie models to a database.
- `connect_to_mongo()`, which creates the Motor client and initializes Beanie.
- `close_mongo_connection()`, which closes the client.
- `get_client()`, which exposes the current client when needed.

Production startup uses `connect_to_mongo()`. Tests call `init_models()` with an in-memory database.

### `backend/app/db/__init__.py`

This marks the database directory as a Python package. It has no runtime logic.

---

## Backend model layer

### `backend/app/models/user.py`

This defines the MongoDB user document.

It contains:

- `utcnow()`, which creates timezone-aware UTC timestamps.
- `UserType`, the `admin` and `client` role enum.
- `User`, the Beanie document stored in the `users` collection.

The user document stores profile fields, role, password hash, deletion state, and timestamps. It defines database indexes for unique email, deletion status, city, and role.

Model helpers include:

- `is_admin`.
- `full_name`.
- `mark_deleted()`.
- `touch()`.

The plain password is never part of this model.

### `backend/app/models/__init__.py`

This marks the model directory as a Python package. It has no runtime logic.

---

## Backend schema layer

### `backend/app/schemas/auth.py`

This defines authentication HTTP schemas:

- `LoginRequest` accepts email and password and forbids unexpected fields.
- `Token` describes the login response: access token, token type, expiration seconds, and safe user information.

### `backend/app/schemas/user.py`

This is the main user validation file.

It contains:

- Age, password-length, phone, and name validation constants.
- Reusable validators for names, phones, passwords, cities, and normalized emails.
- `UserBase`, containing shared profile fields.
- `UserRegister`, which accepts public registration and explicitly does not accept a role.
- `UserCreate`, which allows an administrator to choose a role.
- `_UserUpdateFields`, containing optional partial-update fields.
- `UserUpdateMe`, which cannot change a role.
- `UserUpdateAdmin`, which can change a role.
- `UserPublic`, the safe public response without password information.
- `UserAdminView`, which adds deletion information.
- `UserListResponse`, the paginated admin response.
- Statistics response schemas for count, average age, and city rankings.

### `backend/app/schemas/common.py`

This contains reusable generic response shapes:

- `Message` for a simple detail response.
- `PageMeta` for page, limit, total, and total pages.
- Generic `Page[T]` for paginated items.

The current user list uses its more specific `UserListResponse`, but these common schemas are available for other resources.

### `backend/app/schemas/__init__.py`

This marks the schemas directory as a Python package. It has no runtime logic.

---

## Backend service layer

### `backend/app/services/user_service.py`

This contains user business logic and database operations.

Important helpers:

- `_icontains()` builds an escaped, case-insensitive MongoDB regular expression.
- `parse_object_id()` converts an ID string and returns a clean 404 for malformed values.

Read operations:

- Find by ID.
- Find by ID or raise 404.
- Find by email.
- Check whether an email is already taken.

Write operations:

- Create a user with an explicitly supplied role.
- Update allowed user fields.
- Hash a changed password.
- Prevent role changes when `allow_role_change` is false.
- Soft-delete a user.
- Restore a user.

Listing operations:

- Build MongoDB filters from query parameters.
- Combine exact filters, ranges, partial matching, and free-text search.
- Count filtered results before pagination.
- Sort, skip, and limit results.
- Calculate total pages.

### `backend/app/services/stats_service.py`

This contains MongoDB statistics queries.

- `count_active_users()` counts non-deleted users.
- `average_age_of_active_users()` uses an aggregation pipeline and rounds the result.
- `top_cities()` groups active users by city, sorts by count, and returns the leading cities.

Every query applies the shared active-user filter.

### `backend/app/services/__init__.py`

This marks the services directory as a Python package. It has no runtime logic.

---

## Backend test files

### `backend/tests/conftest.py`

This is the shared pytest setup file.

It creates:

- An in-memory MongoDB client using `mongomock-motor`.
- Beanie initialization for the test database.
- An HTTPX client connected directly to the FastAPI ASGI application.
- Factories and fixtures for clients, administrators, tokens, headers, and test populations.
- Automatic database cleanup so tests do not affect each other.

### `backend/tests/test_registration.py`

Tests public registration, including valid creation, password hashing, safe responses, every major validation rule, duplicate emails, normalization, and rejection of caller-supplied roles.

### `backend/tests/test_login.py`

Tests successful login, case-insensitive emails, wrong passwords, unknown emails, non-enumerating error messages, deleted accounts, administrator login, and required fields.

### `backend/tests/test_authentication.py`

Tests protected requests with missing, invalid, incorrectly signed, expired, deleted-user, and unknown-user tokens. It also verifies that a forged role claim cannot create administrator access.

### `backend/tests/test_authorization.py`

Tests the difference between authentication and authorization. It confirms that clients cannot call administrator routes, modify other users, create accounts, or promote themselves.

### `backend/tests/test_profile.py`

Tests reading and updating the current profile, partial updates, password changes, password hashing, email changes, duplicate prevention, validation, empty updates, timestamps, and administrator use of profile endpoints.

### `backend/tests/test_admin_users.py`

This is the largest test module. It tests administrator creation and management of users, pagination, page boundaries, filters, search, sorting-related data behavior, updates, password changes, promotion, demotion, invalid IDs, duplicate emails, and last-administrator protection.

### `backend/tests/test_soft_delete.py`

Tests that deletion preserves the database record while disabling the account. It verifies login rejection, immediate token rejection, exclusion from lists and statistics, administrator self-deletion protection, explicit deleted-user views, restoration, and reserved deleted emails.

### `backend/tests/test_stats.py`

Tests public statistics, empty-database results, active-user counts, average age, top-city ordering, the three-city limit, and exclusion of deleted accounts.

### `backend/tests/__init__.py`

This marks the tests directory as a Python package. It contains no test logic.

---

# Frontend

The frontend is a React 18 TypeScript single-page application built by Vite. Tailwind provides utility styling, and official shadcn/ui components generated by the shadcn CLI provide the interface foundation on top of Radix primitives.

## Frontend package and build files

### `frontend/package.json`

This defines the frontend package, scripts, and dependencies.

Scripts:

- `npm run dev` starts Vite.
- `npm run build` creates the production bundle.
- `npm run preview` serves the production bundle locally.

Dependencies include React, React Router, Radix UI primitives, Lucide icons, Sonner toasts, Tailwind utilities, class utilities, and visualization support.

### `frontend/package-lock.json`

This generated file records the exact installed JavaScript dependency tree. It makes `npm install` reproducible. It should normally be updated only through npm commands.

### `frontend/vite.config.ts`

This configures Vite and the React plugin. The development server runs on port 5173 and proxies `/api` requests to FastAPI on port 8000. It removes the `/api` prefix before forwarding the request.

### `frontend/tailwind.config.js`

This configures Tailwind CSS.

It contains:

- Class-based dark mode.
- Source-file paths Tailwind scans for classes.
- Color tokens connected to CSS variables.
- Radius, font, and shadow tokens.
- The page-entry animation.

### `frontend/postcss.config.js`

This tells PostCSS to process CSS through Tailwind and Autoprefixer. Vite must be restarted after this file is first added or significantly changed.

### `frontend/.env.example`

This shows the frontend environment variable for the API base URL. The default `/api` value uses the Vite development proxy.

### `frontend/.env`

This is the local frontend configuration actually used by Vite. It should normally keep `VITE_API_BASE_URL=/api` during local development.

### `frontend/index.html`

This is the browser HTML shell. It contains:

- Character encoding and responsive viewport metadata.
- Theme color and description metadata.
- The Authdesk page title.
- The `#root` element where React renders.
- The script that loads `src/main.tsx`.

---

## Frontend entry and routing

### `frontend/src/main.tsx`

This is the React entry point.

It renders the application inside:

- `React.StrictMode` for development checks.
- `ThemeProvider` for light, dark, and system appearance.
- `BrowserRouter` for client-side routing.
- `AuthProvider` for session state.
- `Toaster` for action notifications.

It also imports the global Tailwind stylesheet.

### `frontend/src/App.tsx`

This defines all client-side routes inside the shared `AppShell`.

Routes include:

- `/` → overview.
- `/login` → login.
- `/register` → registration.
- `/stats` → public statistics.
- `/profile` → authenticated profile.
- `/admin` → administrator-only operations.
- `/forbidden` → 403 page.
- `/404` → not-found page.

Unknown routes redirect to `/404`. The pathname is used as a key so each page receives the entry animation when navigation changes.

---

## Frontend API and shared logic

### `frontend/src/api/client.ts`

This is the only low-level HTTP client used by the frontend.

It contains:

- `ApiError`, a normalized frontend error class.
- An unauthorized callback used to log out invalid sessions.
- `tokenStore`, which gets, saves, and removes the JWT from local storage.
- Error-message extraction for backend error formats.
- The shared `request()` function that builds URLs, query parameters, JSON bodies, and authorization headers.
- API methods for registration, login, profile operations, admin CRUD, restoration, and statistics.

When an authenticated request returns 401, it notifies the authentication context.

### `frontend/src/lib/utils.ts`

This contains small shared UI helpers:

- `cn()` merges conditional Tailwind classes safely using `clsx` and `tailwind-merge`.
- `initials()` produces two-letter initials for user avatars.

---

## Frontend contexts

### `frontend/src/context/AuthContext.tsx`

This controls authentication state for the entire React application.

It stores:

- The current user.
- Whether initial session restoration is loading.

It provides:

- `login()`, which calls the backend, stores the JWT, and saves the returned user.
- `logout()`, which removes the JWT and current user.
- `setUser()` for profile updates.
- `isAuthenticated`.
- `isAdmin`.

On page refresh, it calls `/users/me` when a stored token exists. Invalid tokens are removed automatically.

### `frontend/src/context/ThemeContext.tsx`

This controls appearance mode.

It:

- Reads the saved `light`, `dark`, or `system` preference.
- Detects the operating-system preference in system mode.
- Adds or removes the `dark` class on the HTML element.
- Saves changes to local storage.

---

## Frontend design system and global layout

### `frontend/src/styles/index.css`

This is the global stylesheet and Tailwind entry file.

It contains:

- Tailwind base, component, and utility directives.
- Light theme CSS variables.
- Intentionally designed dark theme variables.
- Global typography and background behavior.
- Selection styling and smooth scrolling.
- Reusable semantic Tailwind component classes such as `eyebrow`, `page-title`, `page-copy`, `menu-item`, `skip-link`, and `data-number`.

The frontend will look unstyled if this file is not processed by PostCSS and Tailwind.

### `frontend/components.json`

This is the official shadcn/ui registry configuration. It records the New York style, Radix base, TypeScript mode, Lucide icon library, Tailwind files, and `@/*` aliases used by the shadcn CLI.

### `frontend/src/components/ui/`

This directory contains actual shadcn source files generated by `npx shadcn add`. Each component has its own TypeScript file: Alert, Avatar, Badge, Button, Command, Dialog, Dropdown Menu, Input, Label, Select, Separator, Sheet, Skeleton, and Tooltip.

The source belongs to the application, so it can be customized. The Button adds a typed loading state and the Badge adds project-specific role and lifecycle variants while retaining the generated shadcn structure.

### `frontend/src/components/AppDialog.tsx`, `FeedbackAlert.tsx`, `FormField.tsx`, and `SimpleSelect.tsx`

These are small application-level composition wrappers. They do not replace shadcn: they combine the generated Dialog, Alert, Label, and Select primitives into consistent APIs used by the product screens.

### `frontend/src/components/AppShell.tsx`

This creates the full application frame.

It contains:

- The Authdesk brand.
- Role-aware desktop navigation.
- A responsive mobile navigation drawer.
- The user menu.
- Account settings and logout actions.
- Appearance selection.
- A button for the command palette.
- The global `Cmd/Ctrl + K` keyboard listener.
- A skip-to-content link.
- The main content container.
- The footer.

Navigation items are filtered according to whether the visitor is anonymous, authenticated, or an administrator.

### `frontend/src/components/CommandPalette.tsx`

This implements the global quick-navigation interface.

It uses the generated shadcn Command and CommandDialog components and provides:

- Search input.
- Filtering of available destinations.
- Role-aware navigation results supplied by `AppShell`.
- Keyboard-focused opening through `Cmd/Ctrl + K`.
- Navigation and automatic closing when an item is selected.

---

## Active reusable frontend components

### `frontend/src/components/ProtectedRoute.tsx`

This protects authenticated and administrator pages.

It:

- Shows a loading state while the session is being restored.
- Redirects anonymous visitors to login while remembering their requested page.
- Redirects non-admin users away from administrator pages.
- Renders the protected content when permission is valid.

This improves routing UX, but FastAPI remains the real security boundary.

### `frontend/src/components/Spinner.tsx`

Despite its historical name, this now renders content-shaped skeleton blocks instead of a spinning circle. Screen-reader text announces the loading label.

### `frontend/src/components/Pagination.tsx`

This renders the admin table pagination footer.

It shows:

- Total matching identities.
- Current page and total pages.
- Page-size selection.
- Previous and next buttons with correct disabled states.

### `frontend/src/components/UserFormModal.tsx`

This is the shared administrator form for creating and editing users.

It:

- Uses one form for both modes.
- Pre-fills user data during editing.
- Collects profile data, age, role, and password.
- Makes the password optional during editing.
- Converts age to a number before sending it.
- Displays backend errors.
- Calls the `onSubmit` function supplied by the admin page.
- Uses the shared accessible dialog and UI controls.

---

## Frontend pages

### `frontend/src/pages/HomePage.tsx`

This is the public overview page.

It contains:

- The primary Authdesk product message.
- Different actions for anonymous users, clients, and administrators.
- The identity-signal visual showing token, role, and account checks.
- A three-stage explanation of authentication, authorization, and operations.

When a user is signed in, it displays real session information from `AuthContext`.

### `frontend/src/pages/LoginPage.tsx`

This provides the login experience.

It contains:

- Email and password state.
- Loading and backend error states.
- The call to `AuthContext.login()`.
- Return-to-requested-page navigation.
- Role-aware navigation after login.
- `AuthLayout`, the shared split-screen visual used by login and registration.

The decorative security panel becomes hidden on smaller screens so the form receives priority.

### `frontend/src/pages/RegisterPage.tsx`

This provides public account registration.

It:

- Collects name, email, phone, city, age, and password.
- Never sends a role.
- Maps backend validation errors to individual fields.
- Calls registration, then automatically logs in the new user.
- Navigates to the profile page after success.
- Reuses the `AuthLayout` from the login page.

### `frontend/src/pages/ProfilePage.tsx`

This is the authenticated account settings page.

It:

- Loads the latest profile from `/users/me`.
- Updates global authentication state.
- Displays avatar initials, role, and creation date.
- Separates personal details from contact and security details.
- Allows an optional password change.
- Sends updates to `/users/me`.
- Displays errors and a success toast.
- Explains that role changes are controlled by administrators.

### `frontend/src/pages/AdminPage.tsx`

This is the main identity command center and the most complex frontend file.

State includes:

- Draft and applied filters.
- Deleted-user visibility.
- Pagination.
- Sorting.
- Loaded data.
- Loading and error states.
- The active create, edit, or delete dialog.

Functionality includes:

- Loading the real paginated user API.
- Search and progressive filters.
- Role, city, age, email, and name filters.
- Server-side sorting.
- Identity, lifecycle, and filter summary signals.
- A responsive scrollable table.
- User initials, role badges, and lifecycle badges.
- Contextual row menus.
- User creation and editing.
- Soft deletion with confirmation.
- User restoration.
- Toast feedback.
- Protected self-deletion behavior reflected in the UI.

Small helper components inside the file render signals, sortable headers, and row menus.

### `frontend/src/pages/StatsPage.tsx`

This is the public network-health page.

It calls all three statistics endpoints in parallel and displays:

- Active identity count.
- Average age.
- Leading location count.
- A relative horizontal city distribution.
- Explanations for what each number means.
- Loading skeletons, API errors, and an empty state.

The visualization uses real MongoDB aggregate results and does not invent trend data that the backend cannot provide.

### `frontend/src/pages/ForbiddenPage.tsx`

This is the branded 403 screen. It explains that the user is authenticated but lacks administrator permission and provides a path back to the profile.

### `frontend/src/pages/NotFoundPage.tsx`

This is the branded 404 screen. It explains that the requested route does not exist and provides a path back to the overview.

---

# How the main files connect

The main runtime flow is:

```text
frontend/index.html
    -> frontend/src/main.tsx
        -> ThemeProvider
        -> BrowserRouter
        -> AuthProvider
        -> App.tsx
            -> AppShell.tsx
            -> selected page
                -> api/client.ts
                    -> Vite /api proxy
                        -> backend/app/main.py
                            -> api/router.py
                                -> route function
                                    -> dependency checks
                                    -> Pydantic schema
                                    -> service
                                        -> Beanie model
                                            -> MongoDB
```

For a protected request, the backend path is:

```text
Authorization header
    -> api/deps.py
        -> core/security.py decodes JWT
        -> services/user_service.py loads user
        -> role and deletion state checked
        -> route allowed or rejected
```

For a user creation request, the backend path is:

```text
JSON body
    -> schemas/user.py validates fields
    -> routes/auth.py or routes/users.py chooses role authority
    -> services/user_service.py checks unique email
    -> core/security.py hashes password
    -> models/user.py defines stored document
    -> db/mongodb.py provides the database connection
```

This separation keeps HTTP behavior, validation, security, business rules, database storage, and visual presentation independent and easier to maintain.
