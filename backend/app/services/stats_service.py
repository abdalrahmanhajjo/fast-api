"""Public statistics.

Every aggregation is scoped to ACTIVE users only (``is_deleted == False``);
soft-deleted accounts must never influence a public number.
"""

from typing import Any, Dict, List

from app.models.user import User

ACTIVE_FILTER: Dict[str, Any] = {"is_deleted": False}


async def count_active_users() -> int:
    return await User.find(ACTIVE_FILTER).count()


async def average_age_of_active_users() -> float:
    """Mean age of active users, rounded to 1 decimal. 0.0 when there are none."""
    pipeline: List[Dict[str, Any]] = [
        {"$match": ACTIVE_FILTER},
        {"$group": {"_id": None, "average_age": {"$avg": "$age"}}},
    ]
    result = await User.aggregate(pipeline).to_list()
    if not result or result[0].get("average_age") is None:
        return 0.0
    return round(float(result[0]["average_age"]), 1)


async def top_cities(limit: int = 3) -> List[Dict[str, Any]]:
    """The N most common cities among active users, most common first."""
    pipeline: List[Dict[str, Any]] = [
        {"$match": ACTIVE_FILTER},
        {"$group": {"_id": "$city", "count": {"$sum": 1}}},
        {"$sort": {"count": -1, "_id": 1}},
        {"$limit": limit},
    ]
    result = await User.aggregate(pipeline).to_list()
    return [{"city": row["_id"], "count": row["count"]} for row in result]
