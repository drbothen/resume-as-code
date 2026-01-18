"""YAML handling with comment preservation for migrations.

This module provides functions for loading and saving YAML files
while preserving comments, formatting, and structure using ruamel.yaml.
"""

from __future__ import annotations

from pathlib import Path

from ruamel.yaml import YAML
from ruamel.yaml.comments import CommentedMap


def load_yaml_preserve(path: Path) -> CommentedMap:
    """Load YAML file preserving comments and formatting.

    Uses ruamel.yaml to maintain comments, quotes, and structure
    for round-trip editing.

    Args:
        path: Path to YAML file.

    Returns:
        CommentedMap with preserved structure. Returns empty
        CommentedMap if file is empty.

    Example:
        >>> data = load_yaml_preserve(Path(".resume.yaml"))
        >>> data["new_field"] = "value"  # Add field
        >>> save_yaml_preserve(Path(".resume.yaml"), data)  # Comments preserved
    """
    yaml = YAML()
    yaml.preserve_quotes = True

    with path.open() as f:
        result = yaml.load(f)
        if result is None:
            return CommentedMap()
        return result  # type: ignore[no-any-return]


def save_yaml_preserve(path: Path, data: CommentedMap) -> None:
    """Save YAML file preserving comments and formatting.

    Uses ruamel.yaml to maintain comments, quotes, and structure.
    Configures consistent indentation for readability.

    Args:
        path: Path to save to.
        data: CommentedMap data to save.

    Example:
        >>> data = load_yaml_preserve(Path("config.yaml"))
        >>> data["updated"] = True
        >>> save_yaml_preserve(Path("config.yaml"), data)
    """
    yaml = YAML()
    yaml.preserve_quotes = True
    yaml.indent(mapping=2, sequence=4, offset=2)

    with path.open("w") as f:
        yaml.dump(data, f)
