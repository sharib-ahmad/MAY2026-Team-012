"""Configuration validation and settings-separation tests."""

import pytest
from pydantic import ValidationError

from app.core.config import (
    DatabaseSettings,
    Settings,
    get_database_settings,
    get_settings,
)

PG = "postgresql+psycopg://user:pass@localhost:5432/verdeza"
PG_TEST = "postgresql+psycopg://user:pass@localhost:5432/verdeza_test"


def _make_settings(**kwargs):
    values = {"DATABASE_URL": PG}
    values.update(kwargs)
    return Settings(**values)


@pytest.mark.unit
def test_database_settings_do_not_require_secret_key():
    """Database tooling must load its URL without an application secret."""

    settings = DatabaseSettings(
        APP_ENV="local",
        DATABASE_URL=PG,
    )

    assert settings.APP_ENV == "local"
    assert settings.DATABASE_URL == PG
    assert not hasattr(settings, "SECRET_KEY")


@pytest.mark.unit
def test_cached_database_settings_are_independent_of_secret_validation(
    monkeypatch,
):
    """The database accessor succeeds while the application accessor fails."""

    get_database_settings.cache_clear()
    get_settings.cache_clear()

    monkeypatch.setenv("APP_ENV", "local")
    monkeypatch.setenv("DATABASE_URL", PG)
    monkeypatch.setenv("SECRET_KEY", "")

    try:
        database_settings = get_database_settings()

        assert database_settings.DATABASE_URL == PG

        with pytest.raises(ValidationError):
            get_settings()
    finally:
        get_database_settings.cache_clear()
        get_settings.cache_clear()


@pytest.mark.unit
@pytest.mark.parametrize("environment", ["local", "staging", "production"])
def test_placeholder_secret_rejected_outside_tests(environment):
    with pytest.raises(ValidationError):
        _make_settings(
            APP_ENV=environment,
            SECRET_KEY="change-me-locally",
        )


@pytest.mark.unit
@pytest.mark.parametrize("environment", ["local", "staging", "production"])
def test_short_nonplaceholder_secret_rejected(environment):
    with pytest.raises(ValidationError):
        _make_settings(
            APP_ENV=environment,
            SECRET_KEY="abc123",
        )


@pytest.mark.unit
def test_whitespace_padded_secret_rejected():
    """Whitespace must not count as secret entropy."""

    with pytest.raises(ValidationError):
        _make_settings(
            APP_ENV="production",
            SECRET_KEY="shorttext" + " " * 40,
        )


@pytest.mark.unit
def test_valid_secret_accepted():
    settings = _make_settings(
        APP_ENV="production",
        SECRET_KEY="x" * 40,
    )

    assert len(settings.SECRET_KEY) == 40


@pytest.mark.unit
def test_test_env_allows_fixed_key():
    settings = Settings(
        APP_ENV="test",
        SECRET_KEY="",
        DATABASE_URL=PG_TEST,
    )

    assert settings.is_test
    assert settings.SECRET_KEY


@pytest.mark.unit
@pytest.mark.parametrize(
    "kwargs",
    [
        {"ACCESS_TOKEN_EXPIRE_MINUTES": -10},
        {"ACCESS_TOKEN_EXPIRE_MINUTES": 99999},
        {"BULK_PICKUP_MIN_LEAD_HOURS": -5},
        {"CREDIT_ROUNDING_DP": -2},
        {
            "COMPLAINT_DESC_MIN": 900,
            "COMPLAINT_DESC_MAX": 10,
        },
        {"PILOT_TIMEZONE": "Not/A-Timezone"},
    ],
)
def test_out_of_range_config_rejected(kwargs):
    with pytest.raises(ValidationError):
        _make_settings(
            APP_ENV="test",
            SECRET_KEY="",
            **kwargs,
        )


@pytest.mark.unit
def test_unsupported_algorithm_rejected():
    with pytest.raises(ValidationError):
        _make_settings(
            APP_ENV="test",
            SECRET_KEY="",
            ALGORITHM="none",
        )


@pytest.mark.unit
def test_unsupported_app_env_rejected():
    with pytest.raises(ValidationError):
        _make_settings(
            APP_ENV="prod",
            SECRET_KEY="x" * 40,
        )


@pytest.mark.unit
@pytest.mark.parametrize("environment", ["staging", "production"])
def test_malformed_postgres_scheme_rejected(environment):
    with pytest.raises(ValidationError):
        Settings(
            APP_ENV=environment,
            SECRET_KEY="x" * 40,
            DATABASE_URL="postgresqlfake://user:pass@localhost/database",
        )


@pytest.mark.unit
@pytest.mark.parametrize("environment", ["staging", "production"])
def test_non_postgres_backend_rejected(environment):
    with pytest.raises(ValidationError):
        Settings(
            APP_ENV=environment,
            SECRET_KEY="x" * 40,
            DATABASE_URL="sqlite:///./x.db",
        )


@pytest.mark.unit
@pytest.mark.parametrize("environment", ["staging", "production"])
def test_database_settings_reject_non_postgres_deployment_url(environment):
    """Database-only settings retain deployment database validation."""

    with pytest.raises(ValidationError):
        DatabaseSettings(
            APP_ENV=environment,
            DATABASE_URL="sqlite:///./x.db",
        )
