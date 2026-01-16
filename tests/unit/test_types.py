"""Tests for reusable date types (YearMonth, Year)."""

from __future__ import annotations

import pytest
from pydantic import BaseModel, ValidationError

from resume_as_code.models.types import Year, YearMonth


class YearMonthModel(BaseModel):
    """Test model for YearMonth type."""

    date: YearMonth  # Required field
    optional_date: YearMonth | None = None  # Optional field


class YearModel(BaseModel):
    """Test model for Year type."""

    year: Year  # Required field
    optional_year: Year | None = None  # Optional field


class TestYearMonth:
    """Tests for YearMonth annotated type."""

    def test_valid_format_accepted(self) -> None:
        """YYYY-MM format is accepted."""
        model = YearMonthModel(date="2024-01")
        assert model.date == "2024-01"

    def test_extended_format_normalized(self) -> None:
        """YYYY-MM-DD is normalized to YYYY-MM."""
        model = YearMonthModel(date="2024-01-15")
        assert model.date == "2024-01"

    def test_invalid_format_rejected(self) -> None:
        """Invalid format raises ValidationError."""
        with pytest.raises(ValidationError, match="YYYY-MM"):
            YearMonthModel(date="01-2024")

    def test_required_field_rejects_none(self) -> None:
        """Required YearMonth field rejects None."""
        # BeforeValidator returns None, then type validation fails
        with pytest.raises(ValidationError):
            YearMonthModel(date=None)  # type: ignore[arg-type]

    def test_optional_accepts_none(self) -> None:
        """Optional YearMonth accepts None."""
        model = YearMonthModel(date="2024-01", optional_date=None)
        assert model.optional_date is None

    def test_optional_accepts_valid_value(self) -> None:
        """Optional YearMonth accepts valid value."""
        model = YearMonthModel(date="2024-01", optional_date="2025-06")
        assert model.optional_date == "2025-06"

    def test_whitespace_stripped(self) -> None:
        """Whitespace is stripped from input."""
        model = YearMonthModel(date="  2024-01  ")
        assert model.date == "2024-01"

    def test_invalid_month_format_valid(self) -> None:
        """Month outside 01-12 passes format validation (semantic validation separate)."""
        # BeforeValidator only checks format pattern, not semantic validity
        model = YearMonthModel(date="2024-99")
        assert model.date == "2024-99"  # Format valid, semantically invalid


class TestYear:
    """Tests for Year annotated type."""

    def test_string_year_accepted(self) -> None:
        """String year is accepted."""
        model = YearModel(year="2024")
        assert model.year == "2024"

    def test_int_year_coerced(self) -> None:
        """Integer year is coerced to string."""
        model = YearModel(year=2024)  # type: ignore[arg-type]
        assert model.year == "2024"

    def test_extended_format_normalized(self) -> None:
        """Extended format is normalized to YYYY."""
        model = YearModel(year="2024-01")
        assert model.year == "2024"

    def test_invalid_format_rejected(self) -> None:
        """Invalid format raises ValidationError."""
        with pytest.raises(ValidationError, match="YYYY"):
            YearModel(year="24")

    def test_required_field_rejects_none(self) -> None:
        """Required Year field rejects None."""
        with pytest.raises(ValidationError):
            YearModel(year=None)  # type: ignore[arg-type]

    def test_optional_accepts_none(self) -> None:
        """Optional Year accepts None."""
        model = YearModel(year="2024", optional_year=None)
        assert model.optional_year is None

    def test_whitespace_stripped(self) -> None:
        """Whitespace is stripped from input."""
        model = YearModel(year="  2024  ")
        assert model.year == "2024"


class TestJsonSchema:
    """Tests for JSON schema generation."""

    def test_year_month_schema_has_pattern(self) -> None:
        """YearMonth generates schema with pattern constraint."""
        schema = YearMonthModel.model_json_schema()
        # Check that pattern is present in the date field
        date_schema = schema["properties"]["date"]
        assert "pattern" in date_schema
        assert date_schema["pattern"] == r"^\d{4}-\d{2}$"

    def test_year_schema_has_pattern(self) -> None:
        """Year generates schema with pattern constraint."""
        schema = YearModel.model_json_schema()
        # Check that pattern is present in the year field
        year_schema = schema["properties"]["year"]
        assert "pattern" in year_schema
        assert year_schema["pattern"] == r"^\d{4}$"
