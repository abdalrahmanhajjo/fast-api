"""Password hashing (Argon2) and JWT creation / verification.

This module is intentionally free of FastAPI imports so it can be unit-tested
and reused outside the web layer.
"""

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional
from uuid import uuid4

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError, VerifyMismatchError
from jose import JWTError, jwt

from app.core.config import settings

# Argon2id is the current OWASP recommendation for password storage.
_password_hasher = PasswordHasher(
    time_cost=2,
    memory_cost=64 * 1024,  # 64 MiB
    parallelism=2,
    hash_len=32,
    salt_len=16,
)

TOKEN_TYPE = "access"


# --------------------------------------------------------------------------- #
# Passwords
# --------------------------------------------------------------------------- #
def hash_password(plain_password: str) -> str:
    """Hash a plain-text password. The salt is generated and embedded by Argon2."""
    return _password_hasher.hash(plain_password)


def verify_password(plain_password: str, password_hash: str) -> bool:
    """Constant-time verification of a plain password against a stored hash."""
    try:
        return _password_hasher.verify(password_hash, plain_password)
    except (VerifyMismatchError, VerificationError, InvalidHashError):
        return False


def password_needs_rehash(password_hash: str) -> bool:
    """True when the stored hash used weaker parameters than the current policy."""
    try:
        return _password_hasher.check_needs_rehash(password_hash)
    except InvalidHashError:
        return True


# --------------------------------------------------------------------------- #
# JWT
# --------------------------------------------------------------------------- #
def create_access_token(
    subject: str,
    role: str,
    expires_delta: Optional[timedelta] = None,
) -> str:
    """Build a signed JWT.

    Claims:
        sub  - the user id (string)
        role - "admin" | "client" (a *hint*; the role is always re-read from the
               database before authorising, so a stale token cannot escalate)
        exp  - expiry
        iat  - issued at
        jti  - unique token id
        type - token type marker
    """
    now = datetime.now(timezone.utc)
    expire = now + (
        expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    payload: Dict[str, Any] = {
        "sub": str(subject),
        "role": role,
        "iat": now,
        "exp": expire,
        "jti": uuid4().hex,
        "type": TOKEN_TYPE,
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_access_token(token: str) -> Optional[Dict[str, Any]]:
    """Return the JWT payload, or ``None`` when the token is invalid/expired."""
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )
    except JWTError:
        return None

    if payload.get("type") != TOKEN_TYPE or not payload.get("sub"):
        return None
    return payload
