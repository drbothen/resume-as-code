"""Position validator for validating positions.yaml.

Story 11.5: Validates position data including Pydantic schema
validation and cross-field validation (start_date <= end_date).
"""

from __future__ import annotations

from pathlib import Path

from pydantic import ValidationError as PydanticValidationError
from pydantic_core import ErrorDetails
from ruamel.yaml import YAML

from resume_as_code.models.errors import StructuredError
from resume_as_code.models.position import Position
from resume_as_code.services.validators.base import (
    ResourceValidationResult,
    ResourceValidator,
)

# Default positions path
DEFAULT_POSITIONS_PATH = Path("positions.yaml")


class PositionValidator(ResourceValidator):
    """Validator for positions.yaml."""

    @property
    def resource_type(self) -> str:
        return "Positions"

    @property
    def resource_key(self) -> str:
        return "positions"

    def validate(self, project_path: Path) -> ResourceValidationResult:
        """Validate all positions.

        Args:
            project_path: Project root directory.

        Returns:
            Validation result with counts and errors.
        """
        # Use default positions path - validators always use project_path as base
        positions_path = project_path / DEFAULT_POSITIONS_PATH

        if not positions_path.exists():
            return ResourceValidationResult(
                resource_type=self.resource_type,
                source_path=positions_path,
                valid_count=0,
                invalid_count=0,
            )

        errors: list[StructuredError] = []
        warnings: list[StructuredError] = []
        valid_count = 0
        invalid_count = 0

        # Load YAML
        yaml = YAML()
        try:
            with positions_path.open() as f:
                data = yaml.load(f)
        except Exception as e:
            return ResourceValidationResult(
                resource_type=self.resource_type,
                source_path=positions_path,
                valid_count=0,
                invalid_count=1,
                errors=[
                    StructuredError(
                        code="YAML_PARSE_ERROR",
                        message=f"Failed to parse positions.yaml: {e}",
                        path=str(positions_path),
                        suggestion="Check YAML syntax and formatting",
                        recoverable=True,
                    )
                ],
            )

        if not data or not isinstance(data, dict):
            return ResourceValidationResult(
                resource_type=self.resource_type,
                source_path=positions_path,
                valid_count=0,
                invalid_count=0,
            )

        positions_data = data.get("positions", {})
        if not positions_data:
            return ResourceValidationResult(
                resource_type=self.resource_type,
                source_path=positions_path,
                valid_count=0,
                invalid_count=0,
            )

        # Validate each position
        for pos_id, pos_data in positions_data.items():
            pos_errors = self._validate_position(pos_id, pos_data, positions_path)
            if pos_errors:
                invalid_count += 1
                errors.extend(pos_errors)
            else:
                valid_count += 1

        return ResourceValidationResult(
            resource_type=self.resource_type,
            source_path=positions_path,
            valid_count=valid_count,
            invalid_count=invalid_count,
            warning_count=len(warnings),
            errors=errors,
            warnings=warnings,
        )

    def _validate_position(
        self,
        pos_id: str,
        pos_data: dict,  # type: ignore[type-arg]
        source_path: Path,
    ) -> list[StructuredError]:
        """Validate a single position.

        Args:
            pos_id: Position ID.
            pos_data: Position data dictionary.
            source_path: Path to positions.yaml for error reporting.

        Returns:
            List of errors (empty if valid).
        """
        errors: list[StructuredError] = []

        # Add ID to data for model validation
        pos_dict = dict(pos_data)
        pos_dict["id"] = pos_id

        try:
            Position.model_validate(pos_dict)
        except PydanticValidationError as e:
            for err in e.errors():
                field_path = ".".join(str(loc) for loc in err["loc"])
                errors.append(
                    StructuredError(
                        code="SCHEMA_VALIDATION_ERROR",
                        message=f"positions.{pos_id}.{field_path}: {err['msg']}",
                        path=str(source_path),
                        suggestion=self._get_suggestion_for_error(err),
                        recoverable=True,
                    )
                )

        return errors

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

        if "date" in error_type.lower() or "format" in str(error.get("msg", "")).lower():
            return "Use YYYY-MM format for dates (e.g., '2024-01')"

        if "end_date" in str(error.get("loc", [])) and "before" in str(error.get("msg", "")):
            return "Ensure end_date is after or equal to start_date"

        return "Check the field value against the schema requirements"
