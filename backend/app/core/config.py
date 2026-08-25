"""Application configuration.

All settings are read from environment variables (or a local `.env` file) so the
same image can be promoted from dev -> staging -> prod without code changes.
"""

from functools import lru_cache
from typing import List

from pydantic import computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ---- Application ----
    PROJECT_NAME: str = "FastAPI Auth & User Management"
    VERSION: str = "1.0.0"
    DEBUG: bool = False

    # ---- MongoDB ----
    MONGODB_URI: str = "mongodb://localhost:27017"
    MONGODB_DB_NAME: str = "auth_system"

    # ---- JWT ----
    JWT_SECRET_KEY: str = "CHANGE_ME_super_secret_key_for_local_dev_only"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # ---- CORS ----
    # Comma-separated in the environment, exposed as a list via `CORS_ORIGINS`.
    CORS_ORIGINS_RAW: str = "http://localhost:5173,http://127.0.0.1:5173"

    # ---- Bootstrap admin (seed.py only) ----
    FIRST_ADMIN_EMAIL: str = "admin@example.com"
    FIRST_ADMIN_PASSWORD: str = "Admin1234"

    # ---- Pagination guard-rails ----
    DEFAULT_PAGE_SIZE: int = 10
    MAX_PAGE_SIZE: int = 100

    @computed_field  # type: ignore[prop-decorator]
    @property
    def CORS_ORIGINS(self) -> List[str]:
        """Parsed list of allowed browser origins."""
        return [o.strip() for o in self.CORS_ORIGINS_RAW.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    """Cached so the .env file is parsed exactly once per process."""
    return Settings()


settings = get_settings()
