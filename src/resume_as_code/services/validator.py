"""Validator service for JSON Schema validation of Work Units."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

import jsonschema  # type: ignore[import-untyped]
from ruamel.yaml import YAML

from resume_as_code.models.errors import StructuredError


@dataclass
class ValidationResult:
    """Result of validating a single Work Unit."""

    file_path: Path
    valid: bool
    errors: list[StructuredError] = field(default_factory=list)


@dataclass
class ValidationSummary:
    """Summary of validation across multiple files."""

    results: list[ValidationResult]

    @property
    def valid_count(self) -> int:
        """Count of valid files."""
        return sum(1 for r in self.results if r.valid)

    @property
    def invalid_count(self) -> int:
        """Count of invalid files."""
        return sum(1 for r in self.results if not r.valid)

    @property
    def total_count(self) -> int:
        """Total number of files validated."""
        return len(self.results)


# Cached schema for performance
_schema: dict[str, object] | None = None


def load_schema() -> dict[str, object]:
    """Load the Work Unit JSON Schema.

    Returns:
        The JSON Schema as a dictionary.
    """
    global _schema
    if _schema is None:
        schema_path = (
            Path(__file__).parent.parent.parent.parent / "schemas" / "work-unit.schema.json"
        )
        with schema_path.open() as f:
            _schema = json.load(f)
    return _schema


def validate_file(path: Path) -> ValidationResult:
    """Validate a single Work Unit file against the JSON Schema.

    Args:
        path: Path to the YAML file.

    Returns:
        ValidationResult with file path, validity, and any errors.
    """
    yaml = YAML()
    yaml.preserve_quotes = True

    try:
        with path.open() as f:
            data = yaml.load(f)
    except Exception as e:
        return ValidationResult(
            file_path=path,
            valid=False,
            errors=[
                StructuredError(
                    code="YAML_PARSE_ERROR",
                    message=f"Failed to parse YAML: {e}",
                    path=str(path),
                    suggestion="Check YAML syntax - ensure proper indentation and formatting",
                    recoverable=True,
                )
            ],
        )

    schema = load_schema()
    # Use Draft202012Validator since schema uses draft/2020-12/schema
    validator = jsonschema.Draft202012Validator(schema)
    errors = list(validator.iter_errors(data))

    if not errors:
        return ValidationResult(file_path=path, valid=True)

    structured_errors = [_convert_schema_error(err, path) for err in errors]

    return ValidationResult(
        file_path=path,
        valid=False,
        errors=structured_errors,
    )


def validate_directory(path: Path) -> list[ValidationResult]:
    """Validate all YAML files in a directory.

    Args:
        path: Path to directory containing Work Units.

    Returns:
        List of ValidationResults for each file.
    """
    results: list[ValidationResult] = []
    for yaml_file in sorted(path.glob("*.yaml")):
        results.append(validate_file(yaml_file))
    return results


def validate_path(path: Path) -> ValidationSummary:
    """Validate a file or directory.

    Args:
        path: Path to file or directory.

    Returns:
        ValidationSummary with all results.
    """
    results = [validate_file(path)] if path.is_file() else validate_directory(path)
    return ValidationSummary(results=results)


def _convert_schema_error(
    error: jsonschema.ValidationError,
    file_path: Path,
) -> StructuredError:
    """Convert jsonschema error to StructuredError."""
    path_str = ".".join(str(p) for p in error.absolute_path) or "(root)"

    # Generate helpful suggestions based on error type
    suggestion = _generate_suggestion(error)

    return StructuredError(
        code="SCHEMA_VALIDATION_ERROR",
        message=f"{path_str}: {error.message}",
        path=str(file_path),
        suggestion=suggestion,
        recoverable=True,
    )


def _generate_suggestion(error: jsonschema.ValidationError) -> str:
    """Generate a helpful suggestion for the error."""
    if error.validator == "required":
        # Extract missing field name from message
        try:
            missing = error.message.split("'")[1]
            return f"Add the required field '{missing}' to your Work Unit"
        except IndexError:
            return "Add the missing required field to your Work Unit"

    if error.validator == "enum":
        valid_values = ", ".join(str(v) for v in error.validator_value)
        return f"Use one of the valid values: {valid_values}"

    if error.validator == "type":
        expected = error.validator_value
        return f"Expected type '{expected}'"

    if error.validator == "minLength":
        return f"Value must be at least {error.validator_value} characters"

    if error.validator == "pattern":
        return f"Value must match pattern: {error.validator_value}"

    return "Check the field value against the schema requirements"
