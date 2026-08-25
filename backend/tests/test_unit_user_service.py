"""Unit tests for pure user-service query and pagination helpers."""

import re

import pytest

from app.core.exceptions import NotFoundError
from app.models.user import UserType
from app.services.user_service import build_filter_query, parse_object_id, total_pages


def test_default_filter_excludes_soft_deleted_users():
    assert build_filter_query() == {"is_deleted": False}


def test_include_deleted_removes_active_only_filter():
    assert build_filter_query(include_deleted=True) == {}


def test_exact_age_takes_precedence_over_age_range():
    query = build_filter_query(age=30, min_age=18, max_age=40)

    assert query["age"] == 30


def test_age_range_builds_inclusive_mongodb_operators():
    query = build_filter_query(min_age=18, max_age=40)

    assert query["age"] == {"$gte": 18, "$lte": 40}


def test_role_is_stored_as_enum_value():
    query = build_filter_query(user_type=UserType.ADMIN)

    assert query["type"] == "admin"


def test_partial_text_filter_is_trimmed_case_insensitive_and_regex_escaped():
    query = build_filter_query(city="  Bei.*  ")

    assert query["city"] == {"$regex": re.escape("Bei.*"), "$options": "i"}


def test_global_search_targets_all_supported_fields():
    query = build_filter_query(search="  layla+admin  ")
    pattern = {"$regex": re.escape("layla+admin"), "$options": "i"}

    assert query["$or"] == [
        {"first_name": pattern},
        {"last_name": pattern},
        {"email": pattern},
        {"city": pattern},
    ]


@pytest.mark.parametrize(
    ("total", "limit", "expected"),
    [(0, 10, 0), (1, 10, 1), (10, 10, 1), (11, 10, 2), (25, 10, 3), (5, 0, 0)],
)
def test_total_pages_handles_boundaries(total, limit, expected):
    assert total_pages(total, limit) == expected


def test_parse_object_id_accepts_valid_mongodb_id():
    raw_id = "507f1f77bcf86cd799439011"

    assert str(parse_object_id(raw_id)) == raw_id


def test_parse_object_id_converts_invalid_value_to_domain_404():
    with pytest.raises(NotFoundError, match="User not found"):
        parse_object_id("not-a-mongodb-id")
