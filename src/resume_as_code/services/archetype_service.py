"""Archetype service for loading Work Unit templates."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

# Archetypes directory at project root level
# __file__ -> services/archetype_service.py
# parent -> services/
# parent.parent -> resume_as_code/
# parent.parent.parent -> src/
# parent.parent.parent.parent -> project root
ARCHETYPES_DIR = Path(__file__).parent.parent.parent.parent / "archetypes"


def list_archetypes() -> list[str]:
    """List available archetype names.

    Returns:
        List of archetype names (without .yaml extension).
    """
    if not ARCHETYPES_DIR.exists():
        return []
    return sorted([p.stem for p in ARCHETYPES_DIR.glob("*.yaml")])


def get_archetype_path(name: str) -> Path:
    """Get the path to an archetype file.

    Args:
        name: The archetype name (without .yaml extension).

    Returns:
        Path to the archetype file.

    Raises:
        FileNotFoundError: If the archetype does not exist.
    """
    path = ARCHETYPES_DIR / f"{name}.yaml"
    if not path.exists():
        msg = f"Archetype '{name}' not found"
        raise FileNotFoundError(msg)
    return path


def load_archetype(name: str) -> str:
    """Load archetype file content as string (preserving comments).

    Args:
        name: The archetype name (without .yaml extension).

    Returns:
        The raw YAML content as a string.

    Raises:
        FileNotFoundError: If the archetype does not exist.
    """
    path = get_archetype_path(name)
    return path.read_text()


def load_archetype_data(name: str) -> dict[str, Any]:
    """Load archetype as parsed YAML data (loses comments).

    Args:
        name: The archetype name (without .yaml extension).

    Returns:
        Parsed YAML data as a dictionary.

    Raises:
        FileNotFoundError: If the archetype does not exist.
    """
    path = get_archetype_path(name)
    with path.open() as f:
        data: dict[str, Any] = yaml.safe_load(f)
        return data
