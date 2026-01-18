"""Shared pytest fixtures for Resume as Code tests."""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path
from typing import Any

import pytest
from click.testing import CliRunner


def _configure_weasyprint_library_path() -> None:
    """Configure library path for WeasyPrint on macOS.

    WeasyPrint requires pango/cairo libraries. On macOS with Homebrew,
    these are installed but not on the default library path.
    This adds the Homebrew lib path to DYLD_LIBRARY_PATH.
    """
    import platform

    if platform.system() != "Darwin":
        return

    try:
        result = subprocess.run(
            ["brew", "--prefix"],
            capture_output=True,
            text=True,
            check=True,
        )
        brew_prefix = result.stdout.strip()
        lib_path = f"{brew_prefix}/lib"

        current_path = os.environ.get("DYLD_LIBRARY_PATH", "")
        if lib_path not in current_path:
            os.environ["DYLD_LIBRARY_PATH"] = (
                f"{lib_path}:{current_path}" if current_path else lib_path
            )
    except (subprocess.CalledProcessError, FileNotFoundError):
        # Homebrew not available - skip configuration
        pass


# Configure library path before tests import WeasyPrint
_configure_weasyprint_library_path()


@pytest.fixture(autouse=True)
def clear_onet_env_var(monkeypatch: pytest.MonkeyPatch) -> None:
    """Clear ONET_API_KEY env var for test isolation.

    Many tests assume O*NET is not configured. Without this fixture,
    tests can fail if ONET_API_KEY is set in the user's environment.

    Tests that need ONET_API_KEY can use monkeypatch.setenv() to set it.
    """
    monkeypatch.delenv("ONET_API_KEY", raising=False)


@pytest.fixture
def cli_runner() -> CliRunner:
    """Provide a Click CLI test runner."""
    return CliRunner()


@pytest.fixture
def work_unit_schema() -> dict[str, Any]:
    """Load the Work Unit JSON schema."""
    schema_path = (
        Path(__file__).parent.parent
        / "src"
        / "resume_as_code"
        / "schemas"
        / "work-unit.schema.json"
    )
    with schema_path.open() as f:
        return json.load(f)
