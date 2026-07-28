"""Configuration validation — env-independent.

Every Settings(...) call passes DATABASE_URL explicitly so the result never
depends on the developer's shell or .env (the auditor reproduced a failure when
the ambient URL was sqlite).
"""

import pytest
from pydantic import ValidationError

from app.core.config import Settings

PG = "postgresql+psycopg://user:pass@localhost:5432/verdeza"


def _mk(**kw):
    base = {"DATABASE_URL": PG}
    base.update(kw)
    return Settings(**base)


@pytest.mark.unit
@pytest.mark.parametrize("env", ["local", "staging", "production"])
def test_placeholder_secret_rejected_outside_tests(env):
    with pytest.raises(ValidationError):
        _mk(APP_ENV=env, SECRET_KEY="change-me-locally")


@pytest.mark.unit
@pytest.mark.parametrize("env", ["local", "staging", "production"])
def test_short_nonplaceholder_secret_rejected(env):
    with pytest.raises(ValidationError):
        _mk(APP_ENV=env, SECRET_KEY="abc123")


@pytest.mark.unit
def test_whitespace_padded_secret_rejected():
    """Spaces are not entropy: 'short' + 30 spaces must fail."""
    with pytest.raises(ValidationError):
        _mk(APP_ENV="production", SECRET_KEY="shorttext" + " " * 40)


@pytest.mark.unit
def test_valid_secret_accepted():
    s = _mk(APP_ENV="production", SECRET_KEY="x" * 40)
    assert len(s.SECRET_KEY) == 40


@pytest.mark.unit
def test_test_env_allows_fixed_key():
    s = Settings(
        APP_ENV="test", SECRET_KEY="", DATABASE_URL="postgresql+psycopg://u:p@h/verdeza_test"
    )
    assert s.is_test and s.SECRET_KEY


@pytest.mark.unit
@pytest.mark.parametrize(
    "kwargs",
    [
        {"ACCESS_TOKEN_EXPIRE_MINUTES": -10},
        {"ACCESS_TOKEN_EXPIRE_MINUTES": 99999},
        {"BULK_PICKUP_MIN_LEAD_HOURS": -5},
        {"CREDIT_ROUNDING_DP": -2},
        {"COMPLAINT_DESC_MIN": 900, "COMPLAINT_DESC_MAX": 10},
        {"PILOT_TIMEZONE": "Not/A-Timezone"},
    ],
)
def test_out_of_range_config_rejected(kwargs):
    with pytest.raises(ValidationError):
        _mk(APP_ENV="test", SECRET_KEY="", **kwargs)


@pytest.mark.unit
def test_unsupported_algorithm_rejected():
    with pytest.raises(ValidationError):
        _mk(APP_ENV="test", SECRET_KEY="", ALGORITHM="none")


@pytest.mark.unit
def test_unsupported_app_env_rejected():
    with pytest.raises(ValidationError):
        _mk(APP_ENV="prod", SECRET_KEY="x" * 40)  # not in the Literal set


@pytest.mark.unit
@pytest.mark.parametrize("env", ["staging", "production"])
def test_malformed_postgres_scheme_rejected(env):
    """postgresqlfake:// must be rejected by make_url backend check."""
    with pytest.raises(ValidationError):
        Settings(APP_ENV=env, SECRET_KEY="x" * 40, DATABASE_URL="postgresqlfake://u:p@h/d")


@pytest.mark.unit
@pytest.mark.parametrize("env", ["staging", "production"])
def test_non_postgres_backend_rejected(env):
    with pytest.raises(ValidationError):
        Settings(APP_ENV=env, SECRET_KEY="x" * 40, DATABASE_URL="sqlite:///./x.db")
