"""Exception hierarchy and structured errors for Resume as Code.

Exit Code Reference:
    0 - Success
    1 - UserError (invalid user input)
    2 - ConfigurationError (invalid config file)
    3 - ValidationError (schema validation failed)
    4 - NotFoundError (resource not found)
    5 - RuntimeSystemError (system/runtime error)

Note: Click's built-in UsageError also uses exit code 2 for invalid CLI arguments.
When exit code 2 is returned, check the error message to distinguish between:
- Click usage errors (wrong flags, missing required args)
- ConfigurationError (invalid config file content)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class StructuredError:
    """Structured error for JSON output and AI agent consumption."""

    code: str  # "VALIDATION_ERROR", "CONFIG_ERROR", etc.
    message: str  # Human-readable description
    path: str | None = None  # File path with optional line number
    suggestion: str | None = None  # Actionable fix recommendation
    recoverable: bool = False  # Can agent retry after fixing?

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "code": self.code,
            "message": self.message,
            "path": self.path,
            "suggestion": self.suggestion,
            "recoverable": self.recoverable,
        }


class ResumeError(Exception):
    """Base exception for all resume-as-code errors.

    Args:
        message: Human-readable error description.
        path: Optional file path with optional line number (e.g., "config.yaml:10").
        suggestion: Actionable fix recommendation. Should always be provided for
            recoverable errors to help AI agents understand how to fix the issue.
        recoverable: Whether the error can be fixed and retried. If None, uses
            the class default. Recoverable errors should include a suggestion.

    Example:
        raise ValidationError(
            message="Missing required field 'title'",
            path="work-units/example.yaml:5",
            suggestion="Add a 'title' field to the work unit",
        )
    """

    exit_code: int = 1
    error_code: str = "RESUME_ERROR"
    recoverable: bool = False

    def __init__(
        self,
        message: str,
        path: str | None = None,
        suggestion: str | None = None,
        recoverable: bool | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.path = path
        self.suggestion = suggestion
        if recoverable is not None:
            self.recoverable = recoverable

    def to_structured(self) -> StructuredError:
        """Convert to structured error for JSON output."""
        return StructuredError(
            code=self.error_code,
            message=self.message,
            path=self.path,
            suggestion=self.suggestion,
            recoverable=self.recoverable,
        )


class UserError(ResumeError):
    """Invalid user input - correctable by user."""

    exit_code = 1
    error_code = "USER_ERROR"
    recoverable = True  # User can fix and retry


class ConfigurationError(ResumeError):
    """Configuration is invalid or missing."""

    exit_code = 2
    error_code = "CONFIG_ERROR"
    recoverable = True  # User can fix config and retry


class ValidationError(ResumeError):
    """Schema or content validation failed."""

    exit_code = 3
    error_code = "VALIDATION_ERROR"
    recoverable = True  # User can fix file and retry


class RenderError(ResumeError):
    """Output rendering failed (PDF, DOCX generation)."""

    exit_code = 1
    error_code = "RENDER_ERROR"
    recoverable = True  # User can fix template/data and retry


class NotFoundError(ResumeError):
    """Resource (file, work unit) not found."""

    exit_code = 4
    error_code = "NOT_FOUND_ERROR"
    recoverable = True  # User can create file and retry


class RuntimeSystemError(ResumeError):
    """System/runtime error (I/O, network, etc.)."""

    exit_code = 5
    error_code = "SYSTEM_ERROR"
    recoverable = False  # Usually requires investigation
