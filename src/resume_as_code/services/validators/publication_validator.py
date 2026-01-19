"""Publication validator for validating publications.

Story 11.5: Validates publication data including Pydantic schema
validation and date format validation.
"""

from __future__ import annotations

from pathlib import Path

from pydantic import ValidationError as PydanticValidationError
from pydantic_core import ErrorDetails

from resume_as_code.data_loader import get_storage_mode, load_publications
from resume_as_code.models.errors import StructuredError
from resume_as_code.services.validators.base import (
    ResourceValidationResult,
    ResourceValidator,
)


class PublicationValidator(ResourceValidator):
    """Validator for publications."""

    @property
    def resource_type(self) -> str:
        return "Publications"

    @property
    def resource_key(self) -> str:
        return "publications"

    def validate(self, project_path: Path) -> ResourceValidationResult:
        """Validate all publications.

        Args:
            project_path: Project root directory.

        Returns:
            Validation result with counts and errors.
        """
        errors: list[StructuredError] = []
        warnings: list[StructuredError] = []

        # Determine source path
        mode, source_path = get_storage_mode(project_path, "publications")

        try:
            publications = load_publications(project_path)
        except PydanticValidationError as e:
            # Convert Pydantic validation errors
            for err in e.errors():
                field_path = ".".join(str(loc) for loc in err["loc"])
                errors.append(
                    StructuredError(
                        code="SCHEMA_VALIDATION_ERROR",
                        message=f"publications.{field_path}: {err['msg']}",
                        path=str(source_path) if source_path else "publications",
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
                        message=f"Failed to load publications: {e}",
                        path=str(source_path) if source_path else "publications",
                        suggestion="Check YAML syntax and field types",
                        recoverable=True,
                    )
                ],
            )

        if not publications:
            return ResourceValidationResult(
                resource_type=self.resource_type,
                source_path=source_path,
                valid_count=0,
                invalid_count=0,
            )

        # All entries passed Pydantic validation on load
        # Date format is validated by YearMonth type
        return ResourceValidationResult(
            resource_type=self.resource_type,
            source_path=source_path,
            valid_count=len(publications),
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
        msg = str(error.get("msg", ""))

        if "missing" in error_type:
            field = error["loc"][-1] if error["loc"] else "field"
            return f"Add the required '{field}' field"

        if "string_type" in error_type:
            return "Value must be a string"

        if "date" in error_type.lower() or "format" in msg.lower():
            return "Use YYYY-MM format for dates (e.g., '2024-01')"

        if "type" in str(error["loc"]):
            return "Use one of: conference, article, whitepaper, book, podcast, webinar"

        return "Check the field value against the schema requirements"
