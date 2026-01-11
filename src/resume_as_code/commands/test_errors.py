"""Test command for error verification (temporary).

This command is used to verify exit codes and error structure during development.
"""

from __future__ import annotations

import click

from resume_as_code.models.errors import (
    ConfigurationError,
    NotFoundError,
    RuntimeSystemError,
    UserError,
    ValidationError,
)
from resume_as_code.utils.errors import handle_errors


@click.command("test-errors")
@click.option(
    "--type",
    "error_type",
    type=click.Choice(["user", "config", "validation", "notfound", "system"]),
    required=True,
    help="Type of error to trigger",
)
@click.option(
    "--recoverable/--not-recoverable",
    "recoverable_override",
    default=None,
    help="Override the default recoverable flag",
)
@click.pass_context
@handle_errors
def test_errors(
    ctx: click.Context,
    error_type: str,
    recoverable_override: bool | None,
) -> None:
    """Trigger specific error types for testing exit codes and error structure.

    This is a temporary command for development and testing purposes.

    \b
    Examples:
        resume test-errors --type user         # Exit code 1
        resume test-errors --type config       # Exit code 2
        resume test-errors --type validation   # Exit code 3
        resume test-errors --type notfound     # Exit code 4
        resume test-errors --type system       # Exit code 5

        # With JSON output
        resume --json test-errors --type validation

        # Override recoverable flag
        resume --json test-errors --type system --recoverable
    """
    # Raise appropriate error based on type
    if error_type == "user":
        raise UserError(
            message="Invalid flag or argument provided",
            suggestion="Check the command syntax with --help",
            recoverable=recoverable_override if recoverable_override is not None else None,
        )
    elif error_type == "config":
        raise ConfigurationError(
            message="Configuration file is invalid",
            path=".resume/config.yaml",
            suggestion="Validate your YAML syntax",
            recoverable=recoverable_override if recoverable_override is not None else None,
        )
    elif error_type == "validation":
        raise ValidationError(
            message="Missing required field 'problem.statement'",
            path="work-units/wu-2024-03-15-api.yaml:12",
            suggestion="Add a problem statement describing the challenge",
            recoverable=recoverable_override if recoverable_override is not None else None,
        )
    elif error_type == "notfound":
        raise NotFoundError(
            message="Work unit file not found",
            path="work-units/nonexistent.yaml",
            suggestion="Check the file path or create the file",
            recoverable=recoverable_override if recoverable_override is not None else None,
        )
    else:  # system
        raise RuntimeSystemError(
            message="Failed to write output file",
            path="output/resume.pdf",
            suggestion="Check file permissions and disk space",
            recoverable=recoverable_override if recoverable_override is not None else None,
        )
