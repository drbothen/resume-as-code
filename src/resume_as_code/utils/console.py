"""Rich console utilities for Resume as Code CLI output."""

from __future__ import annotations

from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING

from rich.console import Console

if TYPE_CHECKING:
    from resume_as_code.context import Context

# Singleton console instances
console = Console()  # stdout - for results only
err_console = Console(stderr=True)  # stderr - for progress/status/errors


# Module-level output mode tracking (set by CLI before command execution)
_current_mode: OutputMode | None = None
_verbose_enabled: bool = False


class OutputMode(Enum):
    """Output mode for CLI commands."""

    RICH = "rich"
    JSON = "json"
    QUIET = "quiet"


def configure_output(ctx: Context) -> None:
    """Configure output mode from CLI context. Call this before command execution."""
    global _current_mode, _verbose_enabled
    _current_mode = get_output_mode(ctx)
    _verbose_enabled = ctx.verbose


def reset_output_mode() -> None:
    """Reset output mode to defaults. Primarily for testing."""
    global _current_mode, _verbose_enabled
    _current_mode = None
    _verbose_enabled = False


def set_verbose_enabled(enabled: bool) -> None:
    """Set verbose mode. Primarily for testing."""
    global _verbose_enabled
    _verbose_enabled = enabled


def get_output_mode(ctx: Context) -> OutputMode:
    """Determine current output mode from context flags."""
    if ctx.quiet:
        return OutputMode.QUIET
    if ctx.json_output:
        return OutputMode.JSON
    return OutputMode.RICH


def _should_output_rich() -> bool:
    """Check if Rich output should be shown (not in JSON or QUIET mode)."""
    return _current_mode is None or _current_mode == OutputMode.RICH


def _should_output_stderr() -> bool:
    """Check if stderr output should be shown (not in JSON or QUIET mode)."""
    # In JSON mode, suppress stderr to keep output clean for parsing
    # In QUIET mode, suppress all output
    return _current_mode is None or _current_mode == OutputMode.RICH


def success(message: str) -> None:
    """Display a success message with green checkmark."""
    if _should_output_rich():
        console.print(f"[green]✓[/green] {message}")


def warning(message: str) -> None:
    """Display a warning message with yellow symbol."""
    if _should_output_stderr():
        err_console.print(f"[yellow]⚠[/yellow] {message}")


def error(message: str) -> None:
    """Display an error message with red X."""
    if _should_output_stderr():
        err_console.print(f"[red]✗[/red] {message}")


def info(message: str) -> None:
    """Display an informational message."""
    if _should_output_rich():
        console.print(f"[blue]ℹ[/blue] {message}")


def verbose(message: str) -> None:
    """Display verbose debug information (only when --verbose and RICH mode)."""
    if _verbose_enabled and _should_output_stderr():
        err_console.print(f"[dim]{message}[/dim]")


def verbose_path(path: str | Path, action: str = "Accessing") -> None:
    """Display file path being accessed in verbose mode (AC #3 requirement).

    Args:
        path: The file path being accessed.
        action: Description of what's happening (e.g., "Reading", "Writing", "Checking").
    """
    if _verbose_enabled and _should_output_stderr():
        err_console.print(f"[dim]{action}: {path}[/dim]")


def json_output(json_string: str) -> None:
    """Output raw JSON string without any formatting or wrapping.

    Use this for JSON mode output to ensure valid JSON that can be parsed
    by downstream tools. Bypasses Rich to avoid line wrapping issues.

    Args:
        json_string: A valid JSON string to output.
    """
    import click

    click.echo(json_string)
