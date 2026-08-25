"""Fast unit tests for password and JWT helpers.

These tests intentionally avoid FastAPI, HTTP, and MongoDB.  They exercise the
security boundary directly, which makes failures quick to diagnose in CI.
"""

from datetime import timedelta

from jose import jwt

from app.core.config import settings
from app.core.security import (
    TOKEN_TYPE,
    create_access_token,
    decode_access_token,
    hash_password,
    password_needs_rehash,
    verify_password,
)


def test_hash_password_never_returns_plain_text():
    password = "UnitTest123"

    password_hash = hash_password(password)

    assert password_hash != password
    assert password_hash.startswith("$argon2id$")


def test_argon_hash_uses_a_unique_salt_each_time():
    password = "UnitTest123"

    first_hash = hash_password(password)
    second_hash = hash_password(password)

    assert first_hash != second_hash
    assert verify_password(password, first_hash)
    assert verify_password(password, second_hash)


def test_verify_password_rejects_wrong_password_and_invalid_hash():
    password_hash = hash_password("CorrectPass123")

    assert verify_password("WrongPass123", password_hash) is False
    assert verify_password("CorrectPass123", "not-an-argon-hash") is False


def test_current_argon_hash_does_not_need_rehash():
    assert password_needs_rehash(hash_password("CurrentPass123")) is False


def test_invalid_argon_hash_needs_rehash():
    assert password_needs_rehash("invalid-hash") is True


def test_access_token_contains_required_claims():
    token = create_access_token(subject="user-123", role="client")

    payload = decode_access_token(token)

    assert payload is not None
    assert payload["sub"] == "user-123"
    assert payload["role"] == "client"
    assert payload["type"] == TOKEN_TYPE
    assert payload["iat"] < payload["exp"]
    assert isinstance(payload["jti"], str) and payload["jti"]


def test_each_access_token_has_a_unique_identifier():
    first = decode_access_token(create_access_token("user-123", "client"))
    second = decode_access_token(create_access_token("user-123", "client"))

    assert first is not None and second is not None
    assert first["jti"] != second["jti"]


def test_expired_access_token_is_rejected():
    token = create_access_token(
        subject="user-123",
        role="client",
        expires_delta=timedelta(seconds=-1),
    )

    assert decode_access_token(token) is None


def test_token_with_wrong_type_is_rejected():
    token = jwt.encode(
        {"sub": "user-123", "type": "refresh"},
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )

    assert decode_access_token(token) is None


def test_token_without_subject_is_rejected():
    token = jwt.encode(
        {"type": TOKEN_TYPE},
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )

    assert decode_access_token(token) is None


def test_malformed_token_is_rejected_without_raising():
    assert decode_access_token("not.a.valid.jwt") is None
