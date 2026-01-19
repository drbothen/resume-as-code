"""Education validator for validating education entries.

Story 11.5: Validates education data via Pydantic model validation.
"""

from __future__ import annotations

from pathlib import Path

from pydantic import ValidationError as PydanticValidationError
from pydantic_core import ErrorDetails

from resume_as_code.data_loader import get_storage_mode, load_education
from resume_as_code.models.errors import StructuredError
from resume_as_code.services.validators.base import (
    ResourceValidationResult,
    ResourceValidator,
)


class EducationValidator(ResourceValidator):
    """Validator for education entries."""

    @property
    def resource_type(self) -> str:
        return "Education"

    @property
    def resource_key(self) -> str:
        return "education"

    def validate(self, project_path: Path) -> ResourceValidationResult:
        """Validate all education entries.

        Args:
            project_path: Project root directory.

        Returns:
            Validation result with counts and errors.
        """
        errors: list[StructuredError] = []
        warnings: list[StructuredError] = []

        # Determine source path
        mode, source_path = get_storage_mode(project_path, "education")

        try:
            education = load_education(project_path)
        except PydanticValidationError as e:
            # Convert Pydantic validation errors
            for err in e.errors():
                field_path = ".".join(str(loc) for loc in err["loc"])
                errors.append(
                    StructuredError(
                        code="SCHEMA_VALIDATION_ERROR",
                        message=f"education.{field_path}: {err['msg']}",
                        path=str(source_path) if source_path else "education",
                        suggestion=self._get_suggestion_for_error(err),
                        recoverable=True,
                    )
                )
            return ResourceValidationResult(
                resource_type=self.resource_type,
                source_path=source_path,
                valid_count=0,
                invalid_count=1,
                errors=errors,
            )
        except Exception as e:
            return ResourceValidationResult(
                resource_type=self.resource_type,
                source_path=source_path,
                valid_count=0,
                invalid_count=1,
                errors=[
                    StructuredError(
                        code="LOAD_ERROR",
                        message=f"Failed to load education: {e}",
                        path=str(source_path) if source_path else "education",
                        suggestion="Check YAML syntax and field types",
                        recoverable=True,
                    )
                ],
            )

        if not education:
            return ResourceValidationResult(
                resource_type=self.resource_type,
                source_path=source_path,
                valid_count=0,
                invalid_count=0,
            )

        # All entries passed Pydantic validation on load
        # Education model has no cross-field validation rules
        return ResourceValidationResult(
            resource_type=self.resource_type,
            source_path=source_path,
            valid_count=len(education),
            invalid_count=0,
            warning_count=len(warnings),
            errors=errors,
            warnings=warnings,
        )

    def _get_suggestion_for_error(self, error: ErrorDetails) -> str:
        """Generate a suggestion for a validation error.

        Args:
            error: Pydantic error dict.

        Returns:
            Helpful suggestion string.
        """
        error_type = error.get("type", "")

        if "missing" in error_type:
            field = error["loc"][-1] if error["loc"] else "field"
            return f"Add the required '{field}' field"

        if "string_type" in error_type:
            return "Value must be a string"

        if "empty" in str(error.get("msg", "")).lower():
            return "Field cannot be empty"

        return "Check the field value against the schema requirements"
