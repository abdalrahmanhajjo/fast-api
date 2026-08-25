"""Unit tests for Pydantic validation and normalization rules."""

import pytest
from pydantic import ValidationError

from app.models.user import UserType
from app.schemas.user import UserCreate, UserRegister, UserUpdateAdmin, UserUpdateMe


def valid_registration(**overrides):
    data = {
        "first_name": "  Layla  ",
        "last_name": "Khoury",
        "email": "  LAYLA@EXAMPLE.COM  ",
        "phone": "+961 70 123-456",
        "city": "  Beirut  ",
        "age": 27,
        "password": "StrongPass123",
    }
    data.update(overrides)
    return data


def test_registration_normalizes_user_input():
    user = UserRegister(**valid_registration())

    assert user.first_name == "Layla"
    assert user.email == "layla@example.com"
    assert user.phone == "+96170123456"
    assert user.city == "Beirut"


@pytest.mark.parametrize(
    "password",
    [
        "Short1",
        "nouppercase123",
        "NOLOWERCASE123",
        "NoNumberPassword",
        "Has Space123",
    ],
)
def test_registration_rejects_each_weak_password_category(password):
    with pytest.raises(ValidationError):
        UserRegister(**valid_registration(password=password))


@pytest.mark.parametrize("age", [12, 121])
def test_registration_rejects_age_outside_business_range(age):
    with pytest.raises(ValidationError):
        UserRegister(**valid_registration(age=age))


def test_public_registration_forbids_role_field():
    with pytest.raises(ValidationError) as exc_info:
        UserRegister(**valid_registration(type="admin"))

    assert any(error["type"] == "extra_forbidden" for error in exc_info.value.errors())


def test_admin_creation_defaults_to_client_role():
    user = UserCreate(**valid_registration())

    assert user.type == UserType.CLIENT


def test_admin_creation_accepts_admin_role():
    user = UserCreate(**valid_registration(type="admin"))

    assert user.type == UserType.ADMIN


def test_self_update_requires_at_least_one_field():
    with pytest.raises(ValidationError):
        UserUpdateMe()


def test_self_update_forbids_role_change():
    with pytest.raises(ValidationError):
        UserUpdateMe(type="admin")


def test_admin_update_accepts_role_only():
    update = UserUpdateAdmin(type="admin")

    assert update.type == UserType.ADMIN
    assert update.model_dump(exclude_unset=True) == {"type": UserType.ADMIN}
