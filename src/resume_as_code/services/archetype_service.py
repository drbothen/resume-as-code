"""Archetype service for loading Work Unit templates."""

from __future__ import annotations

import importlib.resources
from importlib.abc import Traversable
from typing import Any

import yaml

# Package data location for archetypes
_ARCHETYPES_PACKAGE = "resume_as_code.data.archetypes"


def _get_archetypes_traversable() -> Traversable:
    """Get traversable for archetypes package data."""
    return importlib.resources.files(_ARCHETYPES_PACKAGE)


def list_archetypes() -> list[str]:
    """List available archetype names.

    Returns:
        List of archetype names (without .yaml extension).
    """
    try:
        archetypes_dir = _get_archetypes_traversable()
        return sorted(
            [
                f.name.removesuffix(".yaml")
                for f in archetypes_dir.iterdir()
                if f.name.endswith(".yaml")
            ]
        )
    except (ModuleNotFoundError, FileNotFoundError):
        return []


def load_archetype(name: str) -> str:
    """Load archetype file content as string (preserving comments).

    Args:
        name: The archetype name (without .yaml extension).

    Returns:
        The raw YAML content as a string.

    Raises:
        FileNotFoundError: If the archetype does not exist.
    """
    try:
        archetypes_dir = _get_archetypes_traversable()
        archetype_file = archetypes_dir / f"{name}.yaml"
        content: str = archetype_file.read_text()
        return content
    except (ModuleNotFoundError, FileNotFoundError) as e:
        msg = f"Archetype '{name}' not found"
        raise FileNotFoundError(msg) from e


def load_archetype_data(name: str) -> dict[str, Any]:
    """Load archetype as parsed YAML data (loses comments).

    Args:
        name: The archetype name (without .yaml extension).

    Returns:
        Parsed YAML data as a dictionary.

    Raises:
        FileNotFoundError: If the archetype does not exist.
    """
    content = load_archetype(name)
    data: dict[str, Any] = yaml.safe_load(content)
    return data
