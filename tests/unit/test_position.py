"""Unit tests for Position model."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from resume_as_code.models.position import Position


class TestPositionModel:
    """Tests for Position model."""

    def test_minimal_position(self) -> None:
        """Should create position with required fields only."""
        pos = Position(
            id="pos-test",
            employer="Test Corp",
            title="Engineer",
            start_date="2022-01",
        )
        assert pos.id == "pos-test"
        assert pos.employer == "Test Corp"
        assert pos.title == "Engineer"
        assert pos.start_date == "2022-01"
        assert pos.end_date is None
        assert pos.location is None
        assert pos.employment_type is None
        assert pos.promoted_from is None
        assert pos.description is None

    def test_full_position(self) -> None:
        """Should create position with all fields."""
        pos = Position(
            id="pos-test-senior",
            employer="Test Corp",
            title="Senior Engineer",
            location="Austin, TX",
            start_date="2022-01",
            end_date="2024-01",
            employment_type="full-time",
            promoted_from="pos-test-junior",
            description="Lead platform engineering efforts",
        )
        assert pos.id == "pos-test-senior"
        assert pos.employer == "Test Corp"
        assert pos.title == "Senior Engineer"
        assert pos.location == "Austin, TX"
        assert pos.start_date == "2022-01"
        assert pos.end_date == "2024-01"
        assert pos.employment_type == "full-time"
        assert pos.promoted_from == "pos-test-junior"
        assert pos.description == "Lead platform engineering efforts"

    def test_is_current_true_when_no_end_date(self) -> None:
        """Should return True for current positions (no end_date)."""
        pos = Position(
            id="pos-current",
            employer="Current Corp",
            title="Engineer",
            start_date="2023-01",
        )
        assert pos.is_current is True

    def test_is_current_false_when_has_end_date(self) -> None:
        """Should return False for past positions (has end_date)."""
        pos = Position(
            id="pos-past",
            employer="Past Corp",
            title="Engineer",
            start_date="2020-01",
            end_date="2022-12",
        )
        assert pos.is_current is False

    def test_format_date_range_current(self) -> None:
        """Should format date range with 'Present' for current positions."""
        pos = Position(
            id="pos-current",
            employer="Current Corp",
            title="Engineer",
            start_date="2023-01",
        )
        assert pos.format_date_range() == "2023 - Present"

    def test_format_date_range_past(self) -> None:
        """Should format date range with both years for past positions."""
        pos = Position(
            id="pos-past",
            employer="Past Corp",
            title="Engineer",
            start_date="2020-06",
            end_date="2022-12",
        )
        assert pos.format_date_range() == "2020 - 2022"

    def test_date_validation_valid_format(self) -> None:
        """Should accept valid YYYY-MM date format."""
        pos = Position(
            id="pos-test",
            employer="Test Corp",
            title="Engineer",
            start_date="2022-01",
            end_date="2024-12",
        )
        assert pos.start_date == "2022-01"
        assert pos.end_date == "2024-12"

    def test_date_validation_invalid_start_date(self) -> None:
        """Should reject invalid start_date format."""
        with pytest.raises(ValidationError) as exc_info:
            Position(
                id="pos-test",
                employer="Test Corp",
                title="Engineer",
                start_date="invalid",
            )
        assert "Date must be in YYYY-MM format" in str(exc_info.value)

    def test_date_validation_invalid_end_date(self) -> None:
        """Should reject invalid end_date format."""
        with pytest.raises(ValidationError) as exc_info:
            Position(
                id="pos-test",
                employer="Test Corp",
                title="Engineer",
                start_date="2022-01",
                end_date="2024",  # Missing month
            )
        assert "Date must be in YYYY-MM format" in str(exc_info.value)

    def test_date_validation_full_date_normalized(self) -> None:
        """YYYY-MM-DD format should be normalized to YYYY-MM."""
        pos = Position(
            id="pos-test",
            employer="Test Corp",
            title="Engineer",
            start_date="2022-01-15",
        )
        assert pos.start_date == "2022-01"

    def test_employment_type_valid_values(self) -> None:
        """Should accept all valid employment types."""
        valid_types = ["full-time", "part-time", "contract", "consulting", "freelance"]
        for emp_type in valid_types:
            pos = Position(
                id=f"pos-{emp_type}",
                employer="Test Corp",
                title="Engineer",
                start_date="2022-01",
                employment_type=emp_type,  # type: ignore[arg-type]
            )
            assert pos.employment_type == emp_type

    def test_employment_type_invalid_value(self) -> None:
        """Should reject invalid employment type."""
        with pytest.raises(ValidationError):
            Position(
                id="pos-test",
                employer="Test Corp",
                title="Engineer",
                start_date="2022-01",
                employment_type="invalid-type",  # type: ignore[arg-type]
            )

    def test_missing_required_field_employer(self) -> None:
        """Should reject position without employer."""
        with pytest.raises(ValidationError):
            Position(
                id="pos-test",
                title="Engineer",
                start_date="2022-01",
            )  # type: ignore[call-arg]

    def test_missing_required_field_title(self) -> None:
        """Should reject position without title."""
        with pytest.raises(ValidationError):
            Position(
                id="pos-test",
                employer="Test Corp",
                start_date="2022-01",
            )  # type: ignore[call-arg]

    def test_missing_required_field_start_date(self) -> None:
        """Should reject position without start_date."""
        with pytest.raises(ValidationError):
            Position(
                id="pos-test",
                employer="Test Corp",
                title="Engineer",
            )  # type: ignore[call-arg]

    def test_missing_required_field_id(self) -> None:
        """Should reject position without id."""
        with pytest.raises(ValidationError):
            Position(
                employer="Test Corp",
                title="Engineer",
                start_date="2022-01",
            )  # type: ignore[call-arg]

    def test_date_range_validation_valid(self) -> None:
        """Should accept end_date after start_date."""
        pos = Position(
            id="pos-test",
            employer="Test Corp",
            title="Engineer",
            start_date="2020-01",
            end_date="2022-12",
        )
        assert pos.start_date == "2020-01"
        assert pos.end_date == "2022-12"

    def test_date_range_validation_same_month(self) -> None:
        """Should accept end_date same as start_date."""
        pos = Position(
            id="pos-test",
            employer="Test Corp",
            title="Consultant",
            start_date="2022-06",
            end_date="2022-06",
        )
        assert pos.start_date == "2022-06"
        assert pos.end_date == "2022-06"

    def test_date_range_validation_end_before_start(self) -> None:
        """Should reject end_date before start_date."""
        with pytest.raises(ValidationError) as exc_info:
            Position(
                id="pos-test",
                employer="Test Corp",
                title="Engineer",
                start_date="2024-01",
                end_date="2020-12",
            )
        assert "end_date" in str(exc_info.value)
        assert "start_date" in str(exc_info.value)

    def test_extra_fields_forbidden(self) -> None:
        """Should reject extra fields not in schema."""
        with pytest.raises(ValidationError) as exc_info:
            Position(
                id="pos-test",
                employer="Test Corp",
                title="Engineer",
                start_date="2022-01",
                unknown_field="should not be allowed",  # type: ignore[call-arg]
            )
        errors = exc_info.value.errors()
        assert errors[0]["type"] == "extra_forbidden"
