"""Application configuration.

Design rules:
  * Fail closed: outside APP_ENV=test, a missing/placeholder/short
    SECRET_KEY stops startup. Length is measured on the STRIPPED value so
    surrounding whitespace cannot pad a weak secret to length.
  * Every acceptance-criteria threshold is a bounded Field.
  * DATABASE_URL is parsed with SQLAlchemy make_url and the backend name must be
    exactly 'postgresql' in staging/production — 'postgresqlfake://'
    is rejected.
  * Domain precision (credit/CO2) lives here so services do not invent it.
"""

from functools import lru_cache
from typing import Literal
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from pydantic import Field, ValidationInfo, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.engine import make_url
from sqlalchemy.exc import ArgumentError

Environment = Literal["local", "test", "staging", "production"]

_PLACEHOLDER_SECRETS = {"change-me-locally", "changeme", "secret", "", "replace-me"}


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    APP_ENV: Environment = "local"

    DATABASE_URL: str = "postgresql+psycopg://verdeza:verdeza@localhost:5432/verdeza"
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

    @property
    def is_test(self) -> bool:
        return self.APP_ENV == "test"

    @field_validator("SECRET_KEY")
    @classmethod
    def _secret_strong_outside_tests(cls, v: str, info: ValidationInfo) -> str:
        env = info.data.get("APP_ENV", "local")
        if env == "test":
            return v or "test-only-key-not-used-anywhere-real"
        stripped = v.strip()
        if stripped.lower() in _PLACEHOLDER_SECRETS:
            raise ValueError(
                f"SECRET_KEY is missing or a placeholder while APP_ENV={env!r}. "
                "Set a real secret; the app fails closed."
            )
        # Length measured on the stripped value — whitespace is not entropy.
        if len(stripped) < 32:
            raise ValueError(
                f"SECRET_KEY is too short ({len(stripped)} non-space chars) for "
                f"APP_ENV={env!r}; use at least 32 characters of real entropy."
            )
        return v

    @model_validator(mode="after")
    def _cross_field(self) -> "Settings":
        if self.COMPLAINT_DESC_MIN >= self.COMPLAINT_DESC_MAX:
            raise ValueError(
                "COMPLAINT_DESC_MIN must be < COMPLAINT_DESC_MAX "
                f"(got {self.COMPLAINT_DESC_MIN} >= {self.COMPLAINT_DESC_MAX})."
            )
        try:
            ZoneInfo(self.PILOT_TIMEZONE)
        except ZoneInfoNotFoundError as exc:
            raise ValueError(
                f"PILOT_TIMEZONE {self.PILOT_TIMEZONE!r} is not a valid timezone."
            ) from exc
        # Parse the URL properly; require the postgresql backend in real envs.
        if self.APP_ENV in ("staging", "production"):
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


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
