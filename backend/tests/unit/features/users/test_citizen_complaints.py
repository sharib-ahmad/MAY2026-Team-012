"""
SCRUM-97 — Regression tests: complaint description strip-then-validate.

Bug: Pydantic validated raw string length (including whitespace) before
     .strip() was applied in the router. A payload like "  12345    "
     (11 chars) passed min_length=10 validation but stored only "12345"
     (5 chars) in the database.

Fix verified: field_validator in TicketCreate strips first, then checks
              that stripped length >= 10, rejecting short padded strings
              with a 422 ValidationError.
"""

import pytest
from pydantic import ValidationError

from app.features.complaints.schemas import TicketCreate

VALID_ISSUE_TYPE = "OVERFLOW"


class TestCitizenComplaints:
    """SCRUM-97: description must have >=10 non-whitespace chars after stripping."""

    # ── Cases that MUST be rejected (422) ────────────────────────────────

    def test_description_strip_bypasses_min_length(self):
        """Core Jira case: '  12345    ' strips to 5 chars — must raise ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            TicketCreate(issue_type=VALID_ISSUE_TYPE, description="  12345    ")
        errors = exc_info.value.errors()
        assert any("10 non-whitespace" in str(e["msg"]) for e in errors), (
            f"Expected 'non-whitespace' error, got: {errors}"
        )

    def test_empty_string_rejected(self):
        """Empty string must be rejected."""
        with pytest.raises(ValidationError):
            TicketCreate(issue_type=VALID_ISSUE_TYPE, description="")

    def test_only_whitespace_rejected(self):
        """String of only spaces/tabs must be rejected."""
        with pytest.raises(ValidationError):
            TicketCreate(issue_type=VALID_ISSUE_TYPE, description="          ")

    def test_nine_real_chars_padded_rejected(self):
        """9 real chars padded to look longer must be rejected."""
        with pytest.raises(ValidationError):
            TicketCreate(issue_type=VALID_ISSUE_TYPE, description="   123456789   ")

    def test_exactly_nine_chars_rejected(self):
        """Exactly 9 non-whitespace chars (no padding) must be rejected."""
        with pytest.raises(ValidationError):
            TicketCreate(issue_type=VALID_ISSUE_TYPE, description="123456789")

    # ── Cases that MUST be accepted ───────────────────────────────────────

    def test_valid_description_accepted(self):
        """10+ real chars with no padding must pass."""
        ticket = TicketCreate(
            issue_type=VALID_ISSUE_TYPE, description="Overflow near the main gate"
        )
        assert ticket.description == "Overflow near the main gate"

    def test_padded_valid_description_stripped_and_accepted(self):
        """10+ real chars with leading/trailing whitespace must pass and be stripped."""
        ticket = TicketCreate(
            issue_type=VALID_ISSUE_TYPE, description="   Overflow near the main gate   "
        )
        # Schema must strip the value before returning
        assert ticket.description == "Overflow near the main gate"
        assert not ticket.description.startswith(" ")
        assert not ticket.description.endswith(" ")

    def test_exactly_ten_chars_accepted(self):
        """Exactly 10 non-whitespace chars must pass."""
        ticket = TicketCreate(issue_type=VALID_ISSUE_TYPE, description="1234567890")
        assert len(ticket.description) == 10

    def test_exactly_ten_chars_padded_accepted(self):
        """10 real chars surrounded by spaces must pass and be stripped."""
        ticket = TicketCreate(issue_type=VALID_ISSUE_TYPE, description="  1234567890  ")
        assert ticket.description == "1234567890"

    def test_description_at_max_length_accepted(self):
        """500 chars must be accepted."""
        ticket = TicketCreate(issue_type=VALID_ISSUE_TYPE, description="A" * 500)
        assert len(ticket.description) == 500

    def test_description_exceeds_max_length_rejected(self):
        """501 chars must be rejected."""
        with pytest.raises(ValidationError):
            TicketCreate(issue_type=VALID_ISSUE_TYPE, description="A" * 501)
