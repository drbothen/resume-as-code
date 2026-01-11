"""Shared pytest fixtures for Resume as Code tests."""

from __future__ import annotations

import pytest
from click.testing import CliRunner


@pytest.fixture
def cli_runner() -> CliRunner:
    """Provide a Click CLI test runner."""
    return CliRunner()
