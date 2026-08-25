"""Aggregates every route module into a single router."""

from fastapi import APIRouter

from app.api.routes import auth, stats, users

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(stats.router)
