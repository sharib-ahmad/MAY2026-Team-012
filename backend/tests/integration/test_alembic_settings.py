"""Regression test for Alembic database-only configuration."""

import os
import subprocess
import sys
from pathlib import Path

import pytest

from app.core.config import get_database_settings

BACKEND_ROOT = Path(__file__).resolve().parents[2]


@pytest.mark.integration
def test_alembic_check_does_not_require_secret_key(engine):
    """Alembic must work without loading application-secret validation.

    The engine fixture first applies the real migrations to the disposable
    pytest database. The subprocess then runs Alembic with APP_ENV=local and an
    explicitly empty SECRET_KEY while retaining the same test DATABASE_URL.
    """

    environment = os.environ.copy()
    environment.update(
        {
            "APP_ENV": "local",
            "SECRET_KEY": "",
            "DATABASE_URL": (get_database_settings().DATABASE_URL),
        }
    )

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "alembic",
            "check",
        ],
        cwd=BACKEND_ROOT,
        env=environment,
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )

    output = "\n".join(
        part
        for part in (
            result.stdout.strip(),
            result.stderr.strip(),
        )
        if part
    )

    assert result.returncode == 0, f"Alembic check failed while SECRET_KEY was empty.\n{output}"
