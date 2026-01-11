"""Error handling utilities for Resume as Code CLI."""

from __future__ import annotations

import sys
from collections.abc import Callable
from functools import wraps
from typing import TYPE_CHECKING, Any, TypeVar

import click

from resume_as_code.models.errors import ResumeError, RuntimeSystemError
from resume_as_code.models.output import JSONResponse
from resume_as_code.utils.console import err_console
from resume_as_code.utils.console import error as print_error

if TYPE_CHECKING:
    from resume_as_code.context import Context

F = TypeVar("F", bound=Callable[..., Any])


def handle_errors(func: F) -> F:
    """Decorator to handle ResumeError exceptions at CLI level.

    Catches all ResumeError exceptions and:
    - Outputs error in appropriate format (Rich/JSON/quiet)
    - Exits with correct exit code

    Unexpected exceptions are wrapped as RuntimeSystemError (exit code 5).
    """

    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        ctx = click.get_current_context(silent=True)
        try:
            return func(*args, **kwargs)
        except ResumeError as e:
            _handle_resume_error(e, ctx)
        except Exception as e:
            # Unexpected error - wrap as RuntimeSystemError
            sys_error = RuntimeSystemError(
                message=f"Unexpected error: {e}",
                suggestion="Please report this issue",
                recoverable=False,
            )
            _handle_resume_error(sys_error, ctx)

    return wrapper  # type: ignore[return-value]


def _get_context_obj(ctx: click.Context | None) -> Context | None:
    """Get the Context object from click context, handling None safely."""
    if ctx is None:
        return None
    obj = ctx.obj
    if obj is None:
        return None
    # Import Context from context module to avoid circular imports
    from resume_as_code.context import Context

    if isinstance(obj, Context):
        return obj
    return None


def _handle_resume_error(e: ResumeError, ctx: click.Context | None) -> None:
    """Handle a ResumeError and exit with correct code.

    Output precedence: quiet > json > rich (consistent with cli.py warning).
    """
    structured = e.to_structured()

    # Get context object safely
    context_obj = _get_context_obj(ctx)
    json_output = context_obj.json_output if context_obj else False
    quiet = context_obj.quiet if context_obj else False

    # Quiet mode takes precedence - no output at all
    if quiet:
        pass  # Silent exit with just the exit code
    elif json_output:
        command_name = ctx.info_name if ctx and ctx.info_name else "unknown"
        response = JSONResponse(
            status="error",
            command=command_name,
            errors=[structured.to_dict()],
        )
        click.echo(response.to_json())
    else:
        # Rich formatted error
        print_error(e.message)
        if e.path:
            err_console.print(f"  [dim]Path:[/dim] {e.path}")
        if e.suggestion:
            err_console.print(f"  [dim]Suggestion:[/dim] {e.suggestion}")

    sys.exit(e.exit_code)
