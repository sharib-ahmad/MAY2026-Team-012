"""Safe classification of database integrity failures.

This module translates PostgreSQL integrity metadata into the small set of
public API errors supported by Verdeza. It never exposes SQL statements,
parameters, constraint details, or driver messages to API clients.
"""

from dataclasses import dataclass

from sqlalchemy.exc import IntegrityError

UNIQUE_VIOLATION = "23505"
FOREIGN_KEY_VIOLATION = "23503"
NOT_NULL_VIOLATION = "23502"
CHECK_VIOLATION = "23514"

PUBLIC_VALIDATION_CONSTRAINTS = frozenset(
    {
        "ck_zones_name_not_blank",
        "ck_zones_code_not_blank",
        "ck_zones_code_is_canonical",
    }
)


@dataclass(frozen=True, slots=True)
class IntegrityErrorResult:
    """Public response selected for an integrity failure."""

    status_code: int
    code: str
    message: str


def extract_sqlstate(exc: IntegrityError) -> str | None:
    """Return the PostgreSQL SQLSTATE without relying on error text."""

    original = getattr(exc, "orig", None)
    diagnostics = getattr(original, "diag", None)

    return getattr(original, "sqlstate", None) or getattr(
        diagnostics,
        "sqlstate",
        None,
    )


def extract_constraint_name(exc: IntegrityError) -> str | None:
    """Return the database constraint name when the driver provides it."""

    original = getattr(exc, "orig", None)
    diagnostics = getattr(original, "diag", None)

    return getattr(diagnostics, "constraint_name", None)


def classify_integrity_error(exc: IntegrityError) -> IntegrityErrorResult:
    """Classify an integrity error into a safe public API response.

    Unknown database invariants fail closed as INTERNAL_ERROR. Only explicitly
    allow-listed check constraints are treated as client validation failures.
    """

    sqlstate = extract_sqlstate(exc)
    constraint_name = extract_constraint_name(exc)

    if sqlstate == UNIQUE_VIOLATION:
        return IntegrityErrorResult(
            status_code=409,
            code="DUPLICATE_RESOURCE",
            message="A resource with the same unique value already exists.",
        )

    if sqlstate == FOREIGN_KEY_VIOLATION:
        return IntegrityErrorResult(
            status_code=409,
            code="CONFLICT",
            message="The request conflicts with the current resource state.",
        )

    if sqlstate == CHECK_VIOLATION and constraint_name in PUBLIC_VALIDATION_CONSTRAINTS:
        return IntegrityErrorResult(
            status_code=422,
            code="VALIDATION_ERROR",
            message="The request contains invalid data.",
        )

    # Includes:
    # - NOT_NULL_VIOLATION
    # - unknown check constraints
    # - missing SQLSTATE
    # - all unknown integrity failures
    return IntegrityErrorResult(
        status_code=500,
        code="INTERNAL_ERROR",
        message="An unexpected error occurred.",
    )
