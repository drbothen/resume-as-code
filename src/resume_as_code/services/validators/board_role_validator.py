"""Board role validator for validating board and advisory roles.

Story 11.5: Validates board role data including Pydantic schema
validation and cross-field validation (start_date <= end_date).
"""

from __future__ import annotations

from pathlib import Path

from pydantic import ValidationError as PydanticValidationError
from pydantic_core import ErrorDetails

from resume_as_code.data_loader import get_storage_mode, load_board_roles
from resume_as_code.models.board_role import BoardRole
from resume_as_code.models.errors import StructuredError
from resume_as_code.services.validators.base import (
    ResourceValidationResult,
    ResourceValidator,
)


class BoardRoleValidator(ResourceValidator):
    """Validator for board and advisory roles."""

    @property
    def resource_type(self) -> str:
        return "Board Roles"

    @property
    def resource_key(self) -> str:
        return "board_roles"

    def validate(self, project_path: Path) -> ResourceValidationResult:
        """Validate all board roles.

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
        mode, source_path = get_storage_mode(project_path, "board_roles")

        try:
            board_roles = load_board_roles(project_path)
        except PydanticValidationError as e:
            # Convert Pydantic validation errors
            for err in e.errors():
                field_path = ".".join(str(loc) for loc in err["loc"])
                errors.append(
                    StructuredError(
                        code="SCHEMA_VALIDATION_ERROR",
                        message=f"board_roles.{field_path}: {err['msg']}",
                        path=str(source_path) if source_path else "board-roles",
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
                        message=f"Failed to load board roles: {e}",
                        path=str(source_path) if source_path else "board-roles",
                        suggestion="Check YAML syntax and field types",
                        recoverable=True,
                    )
                ],
            )

        if not board_roles:
            return ResourceValidationResult(
                resource_type=self.resource_type,
                source_path=source_path,
                valid_count=0,
                invalid_count=0,
            )

        # Validate each board role
        for i, role in enumerate(board_roles):
            role_errors = self._validate_board_role(role, i, source_path)

            if role_errors:
                invalid_count += 1
                errors.extend(role_errors)
            else:
                valid_count += 1

        return ResourceValidationResult(
            resource_type=self.resource_type,
            source_path=source_path,
            valid_count=valid_count,
            invalid_count=invalid_count,
            warning_count=len(warnings),
            errors=errors,
            warnings=warnings,
        )

    def _validate_board_role(
        self,
        role: BoardRole,
        index: int,
        source_path: Path | None,
    ) -> list[StructuredError]:
        """Validate cross-field rules for a board role.

        Args:
            role: BoardRole to validate.
            index: Index in board roles list.
            source_path: Path to source file for error reporting.

        Returns:
            List of errors (empty if valid).
        """
        errors: list[StructuredError] = []

        # Check start_date <= end_date (if end_date present) - AC4
        if role.end_date and role.start_date > role.end_date:
            errors.append(
                StructuredError(
                    code="INVALID_DATE_RANGE",
                    message=(
                        f"Board role at '{role.organization}' has start_date "
                        f"({role.start_date}) after end_date ({role.end_date})"
                    ),
                    path=f"board_roles[{index}]",
                    suggestion="Ensure start_date is before or equal to end_date",
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

        if "date" in error_type.lower():
            return "Use YYYY-MM format for dates (e.g., '2024-01')"

        if "type" in str(error["loc"]):
            return "Use one of: director, advisory, committee"

        return "Check the field value against the schema requirements"
