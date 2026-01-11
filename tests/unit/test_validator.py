"""Tests for validator service."""

from __future__ import annotations

from pathlib import Path

import pytest

from resume_as_code.services.validator import (
    ValidationResult,
    ValidationSummary,
    load_schema,
    validate_directory,
    validate_file,
    validate_path,
)


@pytest.fixture
def valid_work_unit_content() -> str:
    """Valid Work Unit YAML content."""
    return """\
schema_version: "1.0.0"
id: "wu-2026-01-10-test-work-unit"
title: "Test Work Unit for Validation"

problem:
  statement: "A test problem statement that is long enough"

actions:
  - "Took an action that is long enough"

outcome:
  result: "Got a result that is long enough"
"""


@pytest.fixture
def invalid_work_unit_content() -> str:
    """Invalid Work Unit YAML content (missing required fields)."""
    return """\
schema_version: "1.0.0"
id: "wu-2026-01-10-test"
# Missing: title, problem, actions, outcome
"""


@pytest.fixture
def valid_work_unit(tmp_path: Path, valid_work_unit_content: str) -> Path:
    """Create a valid Work Unit file."""
    file_path = tmp_path / "wu-valid.yaml"
    file_path.write_text(valid_work_unit_content)
    return file_path


@pytest.fixture
def invalid_work_unit(tmp_path: Path, invalid_work_unit_content: str) -> Path:
    """Create an invalid Work Unit file."""
    file_path = tmp_path / "wu-invalid.yaml"
    file_path.write_text(invalid_work_unit_content)
    return file_path


class TestLoadSchema:
    """Tests for load_schema function."""

    def test_load_schema_returns_dict(self) -> None:
        """Should load the JSON schema and return a dict."""
        schema = load_schema()
        assert isinstance(schema, dict)
        assert "$schema" in schema
        assert "properties" in schema

    def test_load_schema_has_required_fields(self) -> None:
        """Schema should have expected required fields."""
        schema = load_schema()
        assert "required" in schema
        assert "id" in schema["required"]
        assert "title" in schema["required"]
        assert "problem" in schema["required"]
        assert "actions" in schema["required"]
        assert "outcome" in schema["required"]


class TestValidateFile:
    """Tests for validate_file function."""

    def test_valid_file_returns_valid_result(self, valid_work_unit: Path) -> None:
        """Should return valid=True for valid Work Unit."""
        result = validate_file(valid_work_unit)
        assert isinstance(result, ValidationResult)
        assert result.valid is True
        assert result.errors == []
        assert result.file_path == valid_work_unit

    def test_invalid_file_returns_invalid_result(self, invalid_work_unit: Path) -> None:
        """Should return valid=False with errors for invalid Work Unit."""
        result = validate_file(invalid_work_unit)
        assert result.valid is False
        assert len(result.errors) > 0
        assert result.file_path == invalid_work_unit

    def test_malformed_yaml_returns_parse_error(self, tmp_path: Path) -> None:
        """Should handle malformed YAML gracefully."""
        file_path = tmp_path / "malformed.yaml"
        file_path.write_text("invalid: yaml: content: [")

        result = validate_file(file_path)
        assert result.valid is False
        assert len(result.errors) == 1
        assert result.errors[0].code == "YAML_PARSE_ERROR"

    def test_error_includes_file_path(self, invalid_work_unit: Path) -> None:
        """Errors should include the file path."""
        result = validate_file(invalid_work_unit)
        for error in result.errors:
            assert error.path is not None


class TestValidateDirectory:
    """Tests for validate_directory function."""

    def test_validates_all_yaml_files(
        self,
        tmp_path: Path,
        valid_work_unit_content: str,
        invalid_work_unit_content: str,
    ) -> None:
        """Should validate all YAML files in directory."""
        (tmp_path / "wu-valid.yaml").write_text(valid_work_unit_content)
        (tmp_path / "wu-invalid.yaml").write_text(invalid_work_unit_content)

        results = validate_directory(tmp_path)
        assert len(results) == 2

    def test_empty_directory_returns_empty_list(self, tmp_path: Path) -> None:
        """Should return empty list for directory with no YAML files."""
        results = validate_directory(tmp_path)
        assert results == []

    def test_ignores_non_yaml_files(self, tmp_path: Path, valid_work_unit_content: str) -> None:
        """Should only validate .yaml files."""
        (tmp_path / "wu-valid.yaml").write_text(valid_work_unit_content)
        (tmp_path / "readme.md").write_text("# README")
        (tmp_path / "data.json").write_text("{}")

        results = validate_directory(tmp_path)
        assert len(results) == 1


class TestValidatePath:
    """Tests for validate_path function."""

    def test_file_path_validates_single_file(self, valid_work_unit: Path) -> None:
        """Should validate single file when path is a file."""
        summary = validate_path(valid_work_unit)
        assert isinstance(summary, ValidationSummary)
        assert summary.total_count == 1
        assert summary.valid_count == 1
        assert summary.invalid_count == 0

    def test_directory_path_validates_all_files(
        self, tmp_path: Path, valid_work_unit_content: str
    ) -> None:
        """Should validate all files when path is a directory."""
        (tmp_path / "wu-1.yaml").write_text(valid_work_unit_content)
        (tmp_path / "wu-2.yaml").write_text(valid_work_unit_content)

        summary = validate_path(tmp_path)
        assert summary.total_count == 2
        assert summary.valid_count == 2


class TestValidationSummary:
    """Tests for ValidationSummary class."""

    def test_counts_valid_and_invalid(self) -> None:
        """Should correctly count valid and invalid results."""
        results = [
            ValidationResult(file_path=Path("a.yaml"), valid=True),
            ValidationResult(file_path=Path("b.yaml"), valid=False, errors=[]),
            ValidationResult(file_path=Path("c.yaml"), valid=True),
        ]
        summary = ValidationSummary(results=results)

        assert summary.valid_count == 2
        assert summary.invalid_count == 1
        assert summary.total_count == 3
