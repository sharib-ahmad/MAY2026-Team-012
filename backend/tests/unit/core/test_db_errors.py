"""Unit tests for safe PostgreSQL integrity-error classification."""

from types import SimpleNamespace

import pytest
from sqlalchemy.exc import IntegrityError

from app.core.db_errors import (
    classify_integrity_error,
    extract_constraint_name,
    extract_sqlstate,
)


class FakeDriverError(Exception):
    """Minimal Psycopg-style driver error used by classifier unit tests."""

    def __init__(
        self,
        *,
        sqlstate: str | None = None,
        constraint_name: str | None = None,
        diagnostics_sqlstate: str | None = None,
    ) -> None:
        super().__init__("private database detail")

        self.sqlstate = sqlstate
        self.diag = SimpleNamespace(
            sqlstate=diagnostics_sqlstate,
            constraint_name=constraint_name,
        )


def make_integrity_error(
    *,
    sqlstate: str | None = None,
    constraint_name: str | None = None,
    diagnostics_sqlstate: str | None = None,
) -> IntegrityError:
    original = FakeDriverError(
        sqlstate=sqlstate,
        constraint_name=constraint_name,
        diagnostics_sqlstate=diagnostics_sqlstate,
    )

    return IntegrityError(
        "INSERT INTO private_table(secret_column) VALUES (%(value)s)",
        {"value": "private-value"},
        original,
    )


@pytest.mark.unit
@pytest.mark.parametrize(
    (
        "sqlstate",
        "constraint_name",
        "expected_status",
        "expected_code",
    ),
    [
        (
            "23505",
            "uq_zones_code_canonical",
            409,
            "DUPLICATE_RESOURCE",
        ),
        (
            "23503",
            "fk_private",
            409,
            "CONFLICT",
        ),
        (
            "23514",
            "ck_zones_name_not_blank",
            422,
            "VALIDATION_ERROR",
        ),
        (
            "23514",
            "ck_zones_code_not_blank",
            422,
            "VALIDATION_ERROR",
        ),
        (
            "23514",
            "ck_zones_code_is_canonical",
            422,
            "VALIDATION_ERROR",
        ),
        (
            "23514",
            "ck_unknown_internal_rule",
            500,
            "INTERNAL_ERROR",
        ),
        (
            "23502",
            "users_email_not_null",
            500,
            "INTERNAL_ERROR",
        ),
        (
            "99999",
            "unknown",
            500,
            "INTERNAL_ERROR",
        ),
        (
            None,
            None,
            500,
            "INTERNAL_ERROR",
        ),
    ],
)
def test_integrity_error_classification(
    sqlstate,
    constraint_name,
    expected_status,
    expected_code,
):
    error = make_integrity_error(
        sqlstate=sqlstate,
        constraint_name=constraint_name,
    )

    result = classify_integrity_error(error)

    assert result.status_code == expected_status
    assert result.code == expected_code


@pytest.mark.unit
def test_sqlstate_falls_back_to_driver_diagnostics():
    error = make_integrity_error(
        sqlstate=None,
        diagnostics_sqlstate="23505",
        constraint_name="uq_zones_code_canonical",
    )

    assert extract_sqlstate(error) == "23505"


@pytest.mark.unit
def test_constraint_name_is_read_from_driver_diagnostics():
    error = make_integrity_error(
        sqlstate="23514",
        constraint_name="ck_zones_code_not_blank",
    )

    assert extract_constraint_name(error) == "ck_zones_code_not_blank"


@pytest.mark.unit
def test_missing_driver_diagnostics_fail_closed():
    error = IntegrityError(
        "private SQL",
        {"private": "value"},
        Exception("private driver message"),
    )

    result = classify_integrity_error(error)

    assert extract_sqlstate(error) is None
    assert extract_constraint_name(error) is None
    assert result.status_code == 500
    assert result.code == "INTERNAL_ERROR"
