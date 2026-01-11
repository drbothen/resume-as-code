"""Tests for console utilities."""

from __future__ import annotations

from pathlib import Path

import pytest

from resume_as_code.utils.console import (
    console,
    err_console,
    error,
    info,
    reset_output_mode,
    set_verbose_enabled,
    success,
    verbose,
    verbose_path,
    warning,
)


@pytest.fixture(autouse=True)
def _reset_output_mode():  # type: ignore[misc]
    """Reset module-level output mode before and after each test."""
    reset_output_mode()
    yield
    reset_output_mode()


class TestConsoleSingletons:
    """Test console singleton instances."""

    def test_console_exists(self) -> None:
        """Console instance should exist."""
        assert console is not None

    def test_err_console_exists(self) -> None:
        """Error console instance should exist."""
        assert err_console is not None

    def test_console_writes_to_stdout(self) -> None:
        """Main console should write to stdout (not stderr)."""
        assert console.stderr is False

    def test_err_console_writes_to_stderr(self) -> None:
        """Error console should write to stderr."""
        assert err_console.stderr is True


class TestSuccessFunction:
    """Test success message formatting."""

    def test_success_captures_message(self) -> None:
        """Success should include the provided message."""
        # Use Rich's built-in capture mechanism
        with console.capture() as capture:
            success("test message")
        output = capture.get()
        assert "test message" in output

    def test_success_includes_checkmark(self) -> None:
        """Success messages should include checkmark symbol."""
        with console.capture() as capture:
            success("task complete")
        output = capture.get()
        assert "✓" in output


class TestErrorFunction:
    """Test error message formatting."""

    def test_error_goes_to_stderr(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Error messages should go to stderr."""
        error("test error message")
        captured = capsys.readouterr()
        assert "test error message" in captured.err

    def test_error_includes_x_symbol(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Error messages should include X symbol."""
        error("test error")
        captured = capsys.readouterr()
        assert "test error" in captured.err
        # Verify the X symbol is present (✗ or similar)
        assert "✗" in captured.err or "X" in captured.err or "×" in captured.err


class TestWarningFunction:
    """Test warning message formatting."""

    def test_warning_goes_to_stderr(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Warning messages should go to stderr."""
        warning("test warning message")
        captured = capsys.readouterr()
        assert "test warning message" in captured.err

    def test_warning_includes_symbol(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Warning messages should include warning symbol."""
        warning("caution")
        captured = capsys.readouterr()
        assert "caution" in captured.err


class TestInfoFunction:
    """Test info message formatting."""

    def test_info_captures_message(self) -> None:
        """Info messages should include the provided message."""
        with console.capture() as capture:
            info("test info message")
        output = capture.get()
        assert "test info message" in output

    def test_info_includes_symbol(self) -> None:
        """Info messages should include info symbol."""
        with console.capture() as capture:
            info("informational")
        output = capture.get()
        assert "ℹ" in output


class TestVerboseFunction:
    """Test verbose message formatting."""

    def test_verbose_goes_to_stderr_when_enabled(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Verbose messages should go to stderr when verbose is enabled."""
        set_verbose_enabled(True)
        verbose("debug info")
        captured = capsys.readouterr()
        assert "debug info" in captured.err

    def test_verbose_suppressed_when_disabled(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Verbose messages should be suppressed when verbose is disabled."""
        set_verbose_enabled(False)
        verbose("debug info")
        captured = capsys.readouterr()
        assert captured.err == ""


class TestVerbosePathFunction:
    """Test verbose_path for file path logging (AC #3)."""

    def test_verbose_path_shows_path_when_enabled(self, capsys: pytest.CaptureFixture[str]) -> None:
        """verbose_path should show file paths when verbose is enabled."""
        set_verbose_enabled(True)
        verbose_path("/some/file/path.yaml", action="Reading")
        captured = capsys.readouterr()
        assert "/some/file/path.yaml" in captured.err
        assert "Reading" in captured.err

    def test_verbose_path_accepts_pathlib_path(self, capsys: pytest.CaptureFixture[str]) -> None:
        """verbose_path should accept pathlib.Path objects."""
        set_verbose_enabled(True)
        verbose_path(Path("/another/path.json"), action="Writing")
        captured = capsys.readouterr()
        assert "/another/path.json" in captured.err
        assert "Writing" in captured.err

    def test_verbose_path_default_action(self, capsys: pytest.CaptureFixture[str]) -> None:
        """verbose_path should use 'Accessing' as default action."""
        set_verbose_enabled(True)
        verbose_path("/test/path")
        captured = capsys.readouterr()
        assert "Accessing" in captured.err

    def test_verbose_path_suppressed_when_disabled(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """verbose_path should be suppressed when verbose is disabled."""
        set_verbose_enabled(False)
        verbose_path("/some/path")
        captured = capsys.readouterr()
        assert captured.err == ""
