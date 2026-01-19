"""Work unit validator for validating work units.

Story 11.5: Wraps existing validator.py logic to conform
to the ResourceValidator interface.
"""

from __future__ import annotations

from pathlib import Path

from resume_as_code.config import get_config
from resume_as_code.models.errors import StructuredError
from resume_as_code.services.validator import validate_path
from resume_as_code.services.validators.base import (
    ResourceValidationResult,
    ResourceValidator,
)


class WorkUnitValidator(ResourceValidator):
    """Validator for work units."""

    @property
    def resource_type(self) -> str:
        return "Work Units"

    @property
    def resource_key(self) -> str:
        return "work_units"

    def validate(self, project_path: Path) -> ResourceValidationResult:
        """Validate all work units.

        Args:
            project_path: Project root directory.

        Returns:
            Validation result with counts and errors.
        """
        config = get_config(project_config_path=project_path / ".resume.yaml")
        work_units_path = project_path / config.work_units_dir

        if not work_units_path.exists():
            return ResourceValidationResult(
                resource_type=self.resource_type,
                source_path=work_units_path,
                valid_count=0,
                invalid_count=0,
            )

        # Use existing validator
        summary = validate_path(work_units_path)

        # Convert to ResourceValidationResult
        errors: list[StructuredError] = []
        for result in summary.results:
            if not result.valid:
                errors.extend(result.errors)

        return ResourceValidationResult(
            resource_type=self.resource_type,
            source_path=work_units_path,
            valid_count=summary.valid_count,
            invalid_count=summary.invalid_count,
            errors=errors,
        )
