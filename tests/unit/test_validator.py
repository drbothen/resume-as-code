"""Tests for validator service."""

from __future__ import annotations

from pathlib import Path

import pytest

from resume_as_code.services.validator import (
    ValidationResult,
    ValidationSummary,
    _generate_suggestion,
    load_schema,
    validate_directory,
    validate_file,
    validate_path,
)


@pytest.fixture
def valid_work_unit_content() -> str:
    """Valid Work Unit YAML content."""
    return """\
schema_version: "4.0.0"
id: "wu-2026-01-10-test-work-unit"
title: "Test Work Unit for Validation"

problem:
  statement: "A test problem statement that is long enough"

actions:
  - "Took an action that is long enough"

outcome:
  result: "Got a result that is long enough"

archetype: minimal
"""


@pytest.fixture
def invalid_work_unit_content() -> str:
    """Invalid Work Unit YAML content (missing required fields)."""
    return """\
schema_version: "4.0.0"
archetype: minimal
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


class TestGenerateSuggestion:
    """Tests for _generate_suggestion function."""

    def test_required_validator_suggestion(self) -> None:
        """Should generate suggestion for missing required field."""

        class MockError:
            validator = "required"
            message = "'title' is a required property"
            validator_value = None
            absolute_path: list[str] = []

        suggestion = _generate_suggestion(MockError())  # type: ignore[arg-type]
        assert "title" in suggestion.lower()
        # Should use contextual suggestion from validation_messages
        assert "accomplishment" in suggestion.lower() or "add" in suggestion.lower()

    def test_required_validator_problem_statement_contextual(self) -> None:
        """Should use contextual suggestion for problem.statement field (AC #1)."""

        class MockError:
            validator = "required"
            message = "'statement' is a required property"
            validator_value = None
            absolute_path = ["problem"]

        suggestion = _generate_suggestion(MockError())  # type: ignore[arg-type]
        # Should include helpful context about what to add
        assert len(suggestion) > 20  # Meaningful suggestion, not just generic

    def test_required_validator_malformed_message(self) -> None:
        """Should handle malformed required message gracefully."""

        class MockError:
            validator = "required"
            message = "malformed message without quotes"
            validator_value = None
            absolute_path: list[str] = []

        suggestion = _generate_suggestion(MockError())  # type: ignore[arg-type]
        # Should return some suggestion even for malformed messages
        assert len(suggestion) > 10

    def test_enum_validator_suggestion(self) -> None:
        """Should list valid enum values in suggestion."""

        class MockError:
            validator = "enum"
            message = "invalid is not one of ['a', 'b', 'c']"
            validator_value = ["a", "b", "c"]
            absolute_path: list[str] = []

        suggestion = _generate_suggestion(MockError())  # type: ignore[arg-type]
        assert "a, b, c" in suggestion
        assert "valid values" in suggestion.lower()

    def test_type_validator_suggestion_with_example(self) -> None:
        """Should show expected type with example (AC #2)."""

        class MockError:
            validator = "type"
            message = "123 is not of type 'string'"
            validator_value = "string"
            absolute_path: list[str] = []

        suggestion = _generate_suggestion(MockError())  # type: ignore[arg-type]
        assert "string" in suggestion.lower()
        # Should include example of correct format
        assert '"' in suggestion or "example" in suggestion.lower()

    def test_minlength_validator_suggestion(self) -> None:
        """Should show minimum length requirement in suggestion."""

        class MockError:
            validator = "minLength"
            message = "'ab' is too short"
            validator_value = 10
            absolute_path: list[str] = []

        suggestion = _generate_suggestion(MockError())  # type: ignore[arg-type]
        assert "10" in suggestion
        assert "at least" in suggestion

    def test_pattern_validator_suggestion(self) -> None:
        """Should show pattern in suggestion."""

        class MockError:
            validator = "pattern"
            message = "'invalid' does not match pattern"
            validator_value = "^wu-\\d{4}-\\d{2}-\\d{2}-[a-z0-9-]+$"
            absolute_path: list[str] = []

        suggestion = _generate_suggestion(MockError())  # type: ignore[arg-type]
        assert "pattern" in suggestion
        assert "wu-" in suggestion

    def test_unknown_validator_suggestion(self) -> None:
        """Should return generic suggestion for unknown validators."""

        class MockError:
            validator = "someUnknownValidator"
            message = "some error"
            validator_value = None
            absolute_path: list[str] = []

        suggestion = _generate_suggestion(MockError())  # type: ignore[arg-type]
        assert "schema" in suggestion.lower()

    def test_enum_validator_confidence_field(self) -> None:
        """Should show valid confidence values for enum error (AC #3)."""

        class MockError:
            validator = "enum"
            message = "'super-high' is not one of ['high', 'medium', 'low']"
            validator_value = ["high", "medium", "low"]
            absolute_path = ["confidence"]

        suggestion = _generate_suggestion(MockError())  # type: ignore[arg-type]
        assert "high" in suggestion
        assert "medium" in suggestion
        assert "low" in suggestion


class TestErrorCollection:
    """Tests for comprehensive error collection (AC #4)."""

    def test_collects_all_errors_not_just_first(self, tmp_path: Path) -> None:
        """Should report all errors, not just the first one (AC #4)."""
        # Create file with multiple errors
        file_path = tmp_path / "multi-error.yaml"
        file_path.write_text("""\
schema_version: "4.0.0"
archetype: minimal
# Missing: id, title, problem, actions, outcome
confidence: super-high
""")
        result = validate_file(file_path)

        # Should have multiple errors (at least 5 missing required + 1 enum)
        assert len(result.errors) >= 6
        assert not result.valid

    def test_errors_sorted_by_field_path(self, tmp_path: Path) -> None:
        """Should sort errors by field path for consistent output (AC #4)."""
        file_path = tmp_path / "unsorted.yaml"
        file_path.write_text("""\
schema_version: "4.0.0"
archetype: minimal
# Missing required fields, should be sorted
""")
        result = validate_file(file_path)

        # Extract field paths from error messages
        paths = [e.message.split(":")[0] for e in result.errors]
        assert paths == sorted(paths), "Errors should be sorted by field path"

    def test_max_errors_per_file_limit(self, tmp_path: Path) -> None:
        """Should limit errors to reasonable max per file."""
        from resume_as_code.services.validator import MAX_ERRORS_PER_FILE

        # This test verifies the constant exists and is reasonable
        assert MAX_ERRORS_PER_FILE >= 10
        assert MAX_ERRORS_PER_FILE <= 50
