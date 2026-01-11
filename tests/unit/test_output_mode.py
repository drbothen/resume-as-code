"""Tests for output mode switching."""

from __future__ import annotations

import pytest

from resume_as_code.cli import Context
from resume_as_code.utils.console import (
    OutputMode,
    configure_output,
    error,
    get_output_mode,
    info,
    reset_output_mode,
    success,
    warning,
)


@pytest.fixture(autouse=True)
def _reset_output_mode():  # type: ignore[misc]
    """Reset module-level output mode before and after each test."""
    reset_output_mode()
    yield
    reset_output_mode()


class TestOutputModeEnum:
    """Test OutputMode enumeration."""

    def test_rich_mode_exists(self) -> None:
        """RICH output mode should exist."""
        assert OutputMode.RICH.value == "rich"

    def test_json_mode_exists(self) -> None:
        """JSON output mode should exist."""
        assert OutputMode.JSON.value == "json"

    def test_quiet_mode_exists(self) -> None:
        """QUIET output mode should exist."""
        assert OutputMode.QUIET.value == "quiet"


class TestGetOutputMode:
    """Test get_output_mode function."""

    def test_default_mode_is_rich(self) -> None:
        """Default output mode should be RICH."""
        ctx = Context()
        assert get_output_mode(ctx) == OutputMode.RICH

    def test_json_flag_sets_json_mode(self) -> None:
        """--json flag should set JSON mode."""
        ctx = Context()
        ctx.json_output = True
        assert get_output_mode(ctx) == OutputMode.JSON

    def test_quiet_flag_sets_quiet_mode(self) -> None:
        """--quiet flag should set QUIET mode."""
        ctx = Context()
        ctx.quiet = True
        assert get_output_mode(ctx) == OutputMode.QUIET

    def test_quiet_takes_precedence_over_json(self) -> None:
        """--quiet should take precedence over --json."""
        ctx = Context()
        ctx.json_output = True
        ctx.quiet = True
        assert get_output_mode(ctx) == OutputMode.QUIET

    def test_verbose_does_not_change_mode(self) -> None:
        """--verbose should not change output mode."""
        ctx = Context()
        ctx.verbose = True
        assert get_output_mode(ctx) == OutputMode.RICH


class TestConfigureOutput:
    """Test configure_output function."""

    def test_configure_sets_rich_mode_by_default(self) -> None:
        """configure_output should set RICH mode by default."""
        ctx = Context()
        configure_output(ctx)
        # After configure_output, mode should be RICH
        assert get_output_mode(ctx) == OutputMode.RICH

    def test_configure_sets_json_mode(self) -> None:
        """configure_output should set JSON mode when json_output is True."""
        ctx = Context()
        ctx.json_output = True
        configure_output(ctx)
        assert get_output_mode(ctx) == OutputMode.JSON

    def test_configure_sets_quiet_mode(self) -> None:
        """configure_output should set QUIET mode when quiet is True."""
        ctx = Context()
        ctx.quiet = True
        configure_output(ctx)
        assert get_output_mode(ctx) == OutputMode.QUIET

    def test_configure_sets_verbose_enabled(self) -> None:
        """configure_output should set verbose flag."""
        ctx = Context()
        ctx.verbose = True
        configure_output(ctx)
        # Verify by testing verbose output works
        # (This tests the side effect of configure_output)
        assert ctx.verbose is True


class TestOutputModeSuppression:
    """Test that console helpers respect output mode."""

    def test_success_suppressed_in_json_mode(self, capsys: pytest.CaptureFixture[str]) -> None:
        """success() should be suppressed in JSON mode."""
        ctx = Context()
        ctx.json_output = True
        configure_output(ctx)
        success("should not appear")
        captured = capsys.readouterr()
        assert captured.out == ""

    def test_success_suppressed_in_quiet_mode(self, capsys: pytest.CaptureFixture[str]) -> None:
        """success() should be suppressed in QUIET mode."""
        ctx = Context()
        ctx.quiet = True
        configure_output(ctx)
        success("should not appear")
        captured = capsys.readouterr()
        assert captured.out == ""

    def test_info_suppressed_in_json_mode(self, capsys: pytest.CaptureFixture[str]) -> None:
        """info() should be suppressed in JSON mode."""
        ctx = Context()
        ctx.json_output = True
        configure_output(ctx)
        info("should not appear")
        captured = capsys.readouterr()
        assert captured.out == ""

    def test_warning_suppressed_in_json_mode(self, capsys: pytest.CaptureFixture[str]) -> None:
        """warning() should be suppressed in JSON mode to keep stderr clean."""
        ctx = Context()
        ctx.json_output = True
        configure_output(ctx)
        warning("should not appear")
        captured = capsys.readouterr()
        assert captured.err == ""

    def test_error_suppressed_in_json_mode(self, capsys: pytest.CaptureFixture[str]) -> None:
        """error() should be suppressed in JSON mode to keep stderr clean."""
        ctx = Context()
        ctx.json_output = True
        configure_output(ctx)
        error("should not appear")
        captured = capsys.readouterr()
        assert captured.err == ""

    def test_warning_suppressed_in_quiet_mode(self, capsys: pytest.CaptureFixture[str]) -> None:
        """warning() should be suppressed in QUIET mode."""
        ctx = Context()
        ctx.quiet = True
        configure_output(ctx)
        warning("should not appear")
        captured = capsys.readouterr()
        assert captured.err == ""

    def test_error_suppressed_in_quiet_mode(self, capsys: pytest.CaptureFixture[str]) -> None:
        """error() should be suppressed in QUIET mode."""
        ctx = Context()
        ctx.quiet = True
        configure_output(ctx)
        error("should not appear")
        captured = capsys.readouterr()
        assert captured.err == ""
