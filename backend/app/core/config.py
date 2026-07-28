"""Application and database configuration.

DatabaseSettings contains only the configuration required by database tooling,
including Alembic. It intentionally does not validate application secrets.

Settings extends DatabaseSettings with the complete application configuration.
Application startup remains fail-closed outside APP_ENV=test when SECRET_KEY is
missing, weak, or a known placeholder.
"""

from functools import lru_cache
from pathlib import Path
from typing import Literal
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from pydantic import Field, ValidationInfo, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.engine import make_url
from sqlalchemy.exc import ArgumentError

Environment = Literal["local", "test", "staging", "production"]

BACKEND_ROOT = Path(__file__).resolve().parents[2]
ENV_FILE = BACKEND_ROOT / ".env"

SETTINGS_CONFIG = SettingsConfigDict(
    env_file=ENV_FILE,
    env_file_encoding="utf-8",
    extra="ignore",
)

_PLACEHOLDER_SECRETS = {
    "",
    "change-me-locally",
    "changeme",
    "replace-me",
    "secret",
}


class DatabaseSettings(BaseSettings):
    """Configuration required by database tooling and migrations."""

    model_config = SETTINGS_CONFIG

    APP_ENV: Environment = "local"
    DATABASE_URL: str = "postgresql+psycopg://verdeza:verdeza@localhost:5432/verdeza"

    @property
    def is_test(self) -> bool:
        return self.APP_ENV == "test"

    @model_validator(mode="after")
    def _validate_database_configuration(self) -> "DatabaseSettings":
        """Require PostgreSQL in deployment environments.

        Local and test environments retain their existing flexibility. The
        destructive pytest database-name guard remains in tests/conftest.py,
        where destructive test setup is performed.
        """

        if self.APP_ENV not in ("staging", "production"):
            return self

        try:
            url = make_url(self.DATABASE_URL)
        except ArgumentError as exc:
            raise ValueError(f"DATABASE_URL is not a valid URL: {exc}") from exc

        if url.get_backend_name() != "postgresql":
            raise ValueError(
                f"DATABASE_URL backend must be postgresql in {self.APP_ENV}; "
                f"got {url.get_backend_name()!r}."
            )

        return self


class Settings(DatabaseSettings):
    """Complete FastAPI application configuration."""

    SECRET_KEY: str = Field(default="")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=480, ge=5, le=1440)
    ALGORITHM: Literal["HS256", "HS384", "HS512"] = "HS256"

    PILOT_TIMEZONE: str = "Asia/Kolkata"

    BULK_PICKUP_MIN_LEAD_HOURS: int = Field(default=24, ge=1, le=720)
    COMPLAINT_REOPEN_WINDOW_HOURS: int = Field(default=48, ge=1, le=720)
    COMPLAINT_AGING_THRESHOLD_DAYS: int = Field(default=3, ge=1, le=90)
    COMPLAINT_DESC_MIN: int = Field(default=10, ge=1, le=1000)
    COMPLAINT_DESC_MAX: int = Field(default=500, ge=10, le=5000)

    CREDIT_ROUNDING_DP: int = Field(default=2, ge=0, le=6)
    CO2_ROUNDING_DP: int = Field(default=3, ge=0, le=6)

    @field_validator("SECRET_KEY")
    @classmethod
    def _secret_strong_outside_tests(
        cls,
        value: str,
        info: ValidationInfo,
    ) -> str:
        """Fail closed for application startup outside the test environment."""

        environment = info.data.get("APP_ENV", "local")

        if environment == "test":
            return value or "test-only-key-not-used-anywhere-real"

        stripped = value.strip()

        if stripped.lower() in _PLACEHOLDER_SECRETS:
            raise ValueError(
                "SECRET_KEY is missing or a placeholder while "
                f"APP_ENV={environment!r}. "
                "Set a real secret; the app fails closed."
            )

        if len(stripped) < 32:
            raise ValueError(
                f"SECRET_KEY is too short ({len(stripped)} non-space chars) "
                f"for APP_ENV={environment!r}; use at least 32 characters "
                "of real entropy."
            )

        return value

    @model_validator(mode="after")
    def _validate_application_configuration(self) -> "Settings":
        """Validate application-specific cross-field configuration."""

        if self.COMPLAINT_DESC_MIN >= self.COMPLAINT_DESC_MAX:
            raise ValueError(
                "COMPLAINT_DESC_MIN must be < COMPLAINT_DESC_MAX "
                f"(got {self.COMPLAINT_DESC_MIN} >= "
                f"{self.COMPLAINT_DESC_MAX})."
            )

        try:
            ZoneInfo(self.PILOT_TIMEZONE)
        except ZoneInfoNotFoundError as exc:
            raise ValueError(
                f"PILOT_TIMEZONE {self.PILOT_TIMEZONE!r} " "is not a valid timezone."
            ) from exc

        return self


@lru_cache
def get_database_settings() -> DatabaseSettings:
    """Return cached database-only configuration."""

    return DatabaseSettings()


@lru_cache
def get_settings() -> Settings:
    """Return cached complete application configuration."""

    return Settings()
