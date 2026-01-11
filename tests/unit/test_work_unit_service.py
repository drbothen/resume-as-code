"""Tests for Work Unit service."""

from __future__ import annotations

from datetime import date
from pathlib import Path

import pytest

from resume_as_code.services.work_unit_service import (
    _escape_yaml_string,
    create_work_unit_file,
    generate_id,
    generate_slug,
    get_work_units_dir,
)


class TestEscapeYamlString:
    """Tests for YAML string escaping."""

    def test_escapes_double_quotes(self) -> None:
        """Should escape double quotes."""
        assert _escape_yaml_string('hello "world"') == r"hello \"world\""

    def test_escapes_backslashes(self) -> None:
        """Should escape backslashes."""
        assert _escape_yaml_string(r"path\to\file") == r"path\\to\\file"

    def test_escapes_backslash_before_quote(self) -> None:
        """Should escape backslashes before quotes correctly."""
        assert _escape_yaml_string(r"test\"end") == r"test\\\"end"

    def test_no_change_for_simple_string(self) -> None:
        """Should not modify strings without special chars."""
        assert _escape_yaml_string("simple string") == "simple string"

    def test_preserves_single_quotes(self) -> None:
        """Should not escape single quotes."""
        assert _escape_yaml_string("it's fine") == "it's fine"


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


class TestGetWorkUnitsDir:
    """Tests for work units directory management."""

    def test_creates_directory_if_not_exists(self, tmp_path: Path) -> None:
        """Should create directory when it doesn't exist."""
        new_dir = tmp_path / "work-units"
        assert not new_dir.exists()

        result = get_work_units_dir(new_dir)

        assert result == new_dir
        assert new_dir.exists()

    def test_returns_existing_directory(self, tmp_path: Path) -> None:
        """Should return existing directory without modification."""
        existing_dir = tmp_path / "work-units"
        existing_dir.mkdir()

        result = get_work_units_dir(existing_dir)

        assert result == existing_dir

    def test_uses_cwd_when_base_dir_none(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should default to CWD/work-units when base_dir is None."""
        monkeypatch.chdir(tmp_path)

        result = get_work_units_dir(None)

        assert result == tmp_path / "work-units"
        assert result.exists()

    def test_creates_nested_directories(self, tmp_path: Path) -> None:
        """Should create nested parent directories."""
        nested_dir = tmp_path / "deep" / "nested" / "work-units"
        assert not nested_dir.exists()

        result = get_work_units_dir(nested_dir)

        assert result == nested_dir
        assert nested_dir.exists()


class TestCreateWorkUnitFile:
    """Tests for work unit file creation."""

    def test_creates_file_with_correct_id(self, tmp_path: Path) -> None:
        """Should create file with provided work unit ID in content."""
        work_units_dir = tmp_path / "work-units"

        file_path = create_work_unit_file(
            archetype="greenfield",
            work_unit_id="wu-2024-03-15-test-project",
            title="Test Project",
            work_units_dir=work_units_dir,
        )

        content = file_path.read_text()
        assert 'id: "wu-2024-03-15-test-project"' in content

    def test_creates_file_with_correct_title(self, tmp_path: Path) -> None:
        """Should create file with provided title in content."""
        work_units_dir = tmp_path / "work-units"

        file_path = create_work_unit_file(
            archetype="greenfield",
            work_unit_id="wu-2024-03-15-test",
            title="My Test Title",
            work_units_dir=work_units_dir,
        )

        content = file_path.read_text()
        assert 'title: "My Test Title"' in content

    def test_handles_title_with_single_quotes(self, tmp_path: Path) -> None:
        """Should handle titles containing single quote characters."""
        work_units_dir = tmp_path / "work-units"

        file_path = create_work_unit_file(
            archetype="greenfield",
            work_unit_id="wu-2024-03-15-test",
            title="Project's Big Launch",
            work_units_dir=work_units_dir,
        )

        content = file_path.read_text()
        assert "Project's Big Launch" in content

    def test_handles_title_with_double_quotes(self, tmp_path: Path) -> None:
        """Should escape double quotes in titles to produce valid YAML."""
        work_units_dir = tmp_path / "work-units"

        file_path = create_work_unit_file(
            archetype="greenfield",
            work_unit_id="wu-2024-03-15-test",
            title='My "Big" Project',
            work_units_dir=work_units_dir,
        )

        content = file_path.read_text()
        # Double quotes should be escaped
        assert r'title: "My \"Big\" Project"' in content

    def test_handles_title_with_backslash(self, tmp_path: Path) -> None:
        """Should escape backslashes in titles to produce valid YAML."""
        work_units_dir = tmp_path / "work-units"

        file_path = create_work_unit_file(
            archetype="greenfield",
            work_unit_id="wu-2024-03-15-test",
            title="Path\\to\\file",
            work_units_dir=work_units_dir,
        )

        content = file_path.read_text()
        # Backslashes should be escaped
        assert r'title: "Path\\to\\file"' in content

    def test_file_named_after_work_unit_id(self, tmp_path: Path) -> None:
        """Should name file using work unit ID."""
        work_units_dir = tmp_path / "work-units"

        file_path = create_work_unit_file(
            archetype="incident",
            work_unit_id="wu-2024-01-01-outage-fix",
            title="Outage Fix",
            work_units_dir=work_units_dir,
        )

        assert file_path.name == "wu-2024-01-01-outage-fix.yaml"
