"""Shared pytest fixtures for Resume as Code tests."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
from click.testing import CliRunner


@pytest.fixture
def cli_runner() -> CliRunner:
    """Provide a Click CLI test runner."""
    return CliRunner()


@pytest.fixture
def work_unit_schema() -> dict[str, Any]:
    """Load the Work Unit JSON schema."""
    schema_path = Path(__file__).parent.parent / "schemas" / "work-unit.schema.json"
    with schema_path.open() as f:
        return json.load(f)
