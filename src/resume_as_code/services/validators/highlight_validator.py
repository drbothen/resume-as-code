"""Highlight validator for validating career highlights.

Story 11.5: Validates highlight data - non-empty strings,
warns on highlights > 150 characters.
"""

from __future__ import annotations

from pathlib import Path

from resume_as_code.data_loader import get_storage_mode, load_highlights
from resume_as_code.models.errors import StructuredError
from resume_as_code.services.validators.base import (
    ResourceValidationResult,
    ResourceValidator,
)


class HighlightValidator(ResourceValidator):
    """Validator for career highlights."""

    # Maximum recommended highlight length
    MAX_HIGHLIGHT_LENGTH = 150

    @property
    def resource_type(self) -> str:
        return "Highlights"

    @property
    def resource_key(self) -> str:
        return "highlights"

    def validate(self, project_path: Path) -> ResourceValidationResult:
        """Validate all career highlights.

        Args:
            project_path: Project root directory.

        Returns:
            Validation result with counts and errors.
        """
        errors: list[StructuredError] = []
        warnings: list[StructuredError] = []
        valid_count = 0
        invalid_count = 0

        # Determine source path
        mode, source_path = get_storage_mode(project_path, "highlights")

        try:
            highlights = load_highlights(project_path)
        except Exception as e:
            return ResourceValidationResult(
                resource_type=self.resource_type,
                source_path=source_path,
                valid_count=0,
                invalid_count=1,
                errors=[
                    StructuredError(
                        code="LOAD_ERROR",
                        message=f"Failed to load highlights: {e}",
                        path=str(source_path) if source_path else "highlights",
                        suggestion="Check YAML syntax and ensure all entries are strings",
                        recoverable=True,
                    )
                ],
            )

        if not highlights:
            return ResourceValidationResult(
                resource_type=self.resource_type,
                source_path=source_path,
                valid_count=0,
                invalid_count=0,
            )

        # Validate each highlight
        for i, highlight in enumerate(highlights):
            highlight_errors = self._validate_highlight(highlight, i, source_path)
            highlight_warnings = self._check_warnings(highlight, i, source_path)

            if highlight_errors:
                invalid_count += 1
                errors.extend(highlight_errors)
            else:
                valid_count += 1

            warnings.extend(highlight_warnings)

        return ResourceValidationResult(
            resource_type=self.resource_type,
            source_path=source_path,
            valid_count=valid_count,
            invalid_count=invalid_count,
            warning_count=len(warnings),
            errors=errors,
            warnings=warnings,
        )

    def _validate_highlight(
        self,
        highlight: str,
        index: int,
        source_path: Path | None,
    ) -> list[StructuredError]:
        """Validate a single highlight.

        Args:
            highlight: Highlight text to validate.
            index: Index in highlights list.
            source_path: Path to source file for error reporting.

        Returns:
            List of errors (empty if valid).
        """
        errors: list[StructuredError] = []

        # Check non-empty
        if not highlight or not highlight.strip():
            errors.append(
                StructuredError(
                    code="EMPTY_HIGHLIGHT",
                    message=f"Highlight at index {index} is empty",
                    path=f"highlights[{index}]",
                    suggestion="Provide a non-empty highlight text",
                    recoverable=True,
                )
            )

        return errors

    def _check_warnings(
        self,
        highlight: str,
        index: int,
        source_path: Path | None,
    ) -> list[StructuredError]:
        """Check for warning conditions.

        Args:
            highlight: Highlight text to check.
            index: Index in highlights list.
            source_path: Path to source file for warning reporting.

        Returns:
            List of warnings.
        """
        warnings: list[StructuredError] = []

        # Warn on long highlights
        if len(highlight) > self.MAX_HIGHLIGHT_LENGTH:
            warnings.append(
                StructuredError(
                    code="HIGHLIGHT_TOO_LONG",
                    message=(
                        f"Highlight at index {index} is {len(highlight)} characters "
                        f"(recommended max: {self.MAX_HIGHLIGHT_LENGTH})"
                    ),
                    path=f"highlights[{index}]",
                    suggestion="Consider shortening for better resume readability",
                    recoverable=True,
                )
            )

        return warnings
