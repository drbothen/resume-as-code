"""Tests for slug generation utility."""

from __future__ import annotations


class TestSlugify:
    """Tests for slugify function."""

    def test_basic_slugify(self) -> None:
        """Should convert text to lowercase with hyphens."""
        from resume_as_code.utils.slugify import slugify

        assert slugify("TechCorp Industries") == "techcorp-industries"
        assert slugify("Senior Platform Engineer") == "senior-platform-engineer"

    def test_special_characters_removed(self) -> None:
        """Should remove special characters."""
        from resume_as_code.utils.slugify import slugify

        assert slugify("O'Reilly & Associates") == "oreilly-associates"
        assert slugify("Test (Company)") == "test-company"

    def test_multiple_spaces_collapsed(self) -> None:
        """Should collapse multiple spaces to single hyphen."""
        from resume_as_code.utils.slugify import slugify

        assert slugify("Too   Many   Spaces") == "too-many-spaces"

    def test_leading_trailing_hyphens_removed(self) -> None:
        """Should remove leading and trailing hyphens."""
        from resume_as_code.utils.slugify import slugify

        assert slugify("  Test Company  ") == "test-company"
        assert slugify("---Test---") == "test"

    def test_unicode_normalization(self) -> None:
        """Should normalize unicode characters."""
        from resume_as_code.utils.slugify import slugify

        assert slugify("Café Company") == "cafe-company"
        assert slugify("Naïve Design") == "naive-design"

    def test_empty_string(self) -> None:
        """Should handle empty string."""
        from resume_as_code.utils.slugify import slugify

        assert slugify("") == ""

    def test_already_slugified(self) -> None:
        """Should handle already-slugified text."""
        from resume_as_code.utils.slugify import slugify

        assert slugify("already-slugified") == "already-slugified"


class TestGeneratePositionId:
    """Tests for position ID generation."""

    def test_basic_id_generation(self) -> None:
        """Should generate ID from employer and title."""
        from resume_as_code.utils.slugify import generate_position_id

        result = generate_position_id("TechCorp", "Senior Engineer")
        assert result == "pos-techcorp-senior-engineer"

    def test_long_names_truncated(self) -> None:
        """Should truncate very long employer/title names."""
        from resume_as_code.utils.slugify import generate_position_id

        result = generate_position_id(
            "Very Long Company Name That Goes On Forever",
            "Senior Principal Staff Software Engineer Level 5",
        )
        # Both parts should be truncated to 20 chars
        assert result.startswith("pos-")
        assert len(result) <= 45  # pos- + 20 + - + 20

    def test_special_characters_handled(self) -> None:
        """Should handle special characters in employer/title."""
        from resume_as_code.utils.slugify import generate_position_id

        result = generate_position_id("O'Reilly & Associates", "Sr. Engineer (Lead)")
        assert "pos-" in result
        assert "'" not in result
        assert "&" not in result


class TestGenerateUniquePositionId:
    """Tests for unique position ID generation with duplicate handling."""

    def test_no_conflict(self) -> None:
        """Should return base ID when no conflict."""
        from resume_as_code.utils.slugify import generate_unique_position_id

        existing: set[str] = set()
        result = generate_unique_position_id("TechCorp", "Engineer", existing)
        assert result == "pos-techcorp-engineer"

    def test_with_conflict_appends_number(self) -> None:
        """Should append number when ID already exists."""
        from resume_as_code.utils.slugify import generate_unique_position_id

        existing = {"pos-techcorp-engineer"}
        result = generate_unique_position_id("TechCorp", "Engineer", existing)
        assert result == "pos-techcorp-engineer-2"

    def test_multiple_conflicts(self) -> None:
        """Should increment number for multiple conflicts."""
        from resume_as_code.utils.slugify import generate_unique_position_id

        existing = {"pos-techcorp-engineer", "pos-techcorp-engineer-2"}
        result = generate_unique_position_id("TechCorp", "Engineer", existing)
        assert result == "pos-techcorp-engineer-3"
