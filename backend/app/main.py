"""FastAPI application factory + ASGI entry point.

Run locally with:
    uvicorn app.main:app --reload
Swagger UI:  http://localhost:8000/docs
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.core.config import settings
from app.core.exceptions import register_exception_handlers
from app.db.mongodb import close_mongo_connection, connect_to_mongo

logging.basicConfig(
    level=logging.DEBUG if settings.DEBUG else logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_: FastAPI):
    """Open the database on startup, close it on shutdown."""
    await connect_to_mongo()
    yield
    await close_mongo_connection()


DESCRIPTION = """
A production-style authentication and user-management REST API.

### Roles
* **client** - the role every public registration receives
* **admin**  - can create, list, filter, update and soft-delete users

### How to authorise in this page
1. `POST /login` with your email + password.
2. Copy the `access_token` from the response.
3. Click **Authorize** (top right) and paste the token.
"""

TAGS_METADATA = [
    {"name": "Authentication", "description": "Public registration and login."},
    {"name": "Users", "description": "Profile self-service and admin user management."},
    {"name": "Statistics", "description": "Public aggregates over active users."},
    {"name": "Health", "description": "Service liveness."},
]


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.PROJECT_NAME,
        version=settings.VERSION,
        description=DESCRIPTION,
        openapi_tags=TAGS_METADATA,
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    register_exception_handlers(app)
    app.include_router(api_router)

    @app.get("/", tags=["Health"], summary="Service metadata")
    async def root():
        return {
            "name": settings.PROJECT_NAME,
            "version": settings.VERSION,
            "docs": "/docs",
        }

    @app.get("/health", tags=["Health"], summary="Liveness probe")
    async def health():
        return {"status": "ok"}

    return app


app = create_app()
