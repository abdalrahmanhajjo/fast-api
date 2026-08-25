"""Public statistics endpoints - no authentication required.

All figures count ACTIVE users only; soft-deleted accounts are excluded.
"""

from fastapi import APIRouter

from app.schemas.user import AverageAgeStats, CityCount, CountStats, TopCitiesStats
from app.services import stats_service

router = APIRouter(prefix="/stats", tags=["Statistics"])


@router.get("/count", response_model=CountStats, summary="Total active users (public)")
async def get_count() -> CountStats:
    """Number of users that have not been soft-deleted."""
    return CountStats(total_users=await stats_service.count_active_users())


@router.get(
    "/average-age",
    response_model=AverageAgeStats,
    summary="Average age of active users (public)",
)
async def get_average_age() -> AverageAgeStats:
    """Mean age across active users, rounded to one decimal (0.0 when empty)."""
    return AverageAgeStats(average_age=await stats_service.average_age_of_active_users())


@router.get(
    "/top-cities",
    response_model=TopCitiesStats,
    summary="Three most common cities among active users (public)",
)
async def get_top_cities() -> TopCitiesStats:
    """Cities ranked by active-user count, highest first, capped at 3."""
    rows = await stats_service.top_cities(limit=3)
    return TopCitiesStats(cities=[CityCount(**row) for row in rows])
