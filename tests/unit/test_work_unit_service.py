"""Tests for Work Unit service."""

from __future__ import annotations

from datetime import date

from resume_as_code.services.work_unit_service import (
    generate_id,
    generate_slug,
)


class TestGenerateSlug:
    """Tests for slug generation."""

    def test_lowercase_conversion(self) -> None:
        """Should convert title to lowercase."""
        assert generate_slug("Hello World") == "hello-world"

    def test_special_chars_replaced(self) -> None:
        """Should replace special characters with hyphens."""
        assert generate_slug("ML Pipeline (v2)") == "ml-pipeline-v2"

    def test_multiple_spaces_collapsed(self) -> None:
        """Should collapse multiple spaces into single hyphen."""
        assert generate_slug("hello   world") == "hello-world"

    def test_leading_trailing_hyphens_removed(self) -> None:
        """Should remove leading and trailing hyphens."""
        assert generate_slug("--hello--") == "hello"

    def test_long_titles_truncated(self) -> None:
        """Should truncate very long titles."""
        long_title = "a" * 100
        slug = generate_slug(long_title)
        assert len(slug) <= 50

    def test_numbers_preserved(self) -> None:
        """Should preserve numbers in slug."""
        assert generate_slug("P1 Incident") == "p1-incident"

    def test_empty_title_returns_empty(self) -> None:
        """Should handle empty title."""
        assert generate_slug("") == ""

    def test_unicode_handled(self) -> None:
        """Should handle unicode characters."""
        assert generate_slug("Café Migration") == "caf-migration"


class TestGenerateId:
    """Tests for Work Unit ID generation."""

    def test_format_correct(self) -> None:
        """Should generate ID in format wu-YYYY-MM-DD-slug."""
        result = generate_id("Database Migration", date(2024, 3, 15))
        assert result == "wu-2024-03-15-database-migration"

    def test_slug_included(self) -> None:
        """Should include slugified title in ID."""
        result = generate_id("P1 Incident Response", date(2024, 1, 1))
        assert "p1-incident-response" in result

    def test_date_formatted_correctly(self) -> None:
        """Should format date with zero-padded month and day."""
        result = generate_id("Test", date(2024, 1, 5))
        assert "2024-01-05" in result
