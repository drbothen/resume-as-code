"""Highlight service for managing career highlights.

Handles loading, saving, and querying career highlights from .resume.yaml config.
Story 6.13: Career Highlights Section (CTO/Hybrid Format)
"""

from __future__ import annotations

from pathlib import Path

from ruamel.yaml import YAML


class HighlightService:
    """Service for managing career highlights."""

    def __init__(self, config_path: Path | None = None) -> None:
        """Initialize the highlight service.

        Args:
            config_path: Path to .resume.yaml config file. Defaults to .resume.yaml
                        in current directory.
        """
        self.config_path = config_path or Path(".resume.yaml")
        self._highlights: list[str] | None = None

    def load_highlights(self) -> list[str]:
        """Load career highlights from config file.

        Returns:
            List of highlight strings.
            Returns empty list if file doesn't exist or has no highlights.
        """
        if self._highlights is not None:
            return self._highlights

        if not self.config_path.exists():
            self._highlights = []
            return self._highlights

        yaml = YAML()
        with self.config_path.open() as f:
            data = yaml.load(f)

        if not data:
            self._highlights = []
            return self._highlights

        highlights_data = data.get("career_highlights", [])
        self._highlights = list(highlights_data) if highlights_data else []

        return self._highlights

    def save_highlight(self, highlight: str) -> None:
        """Save a career highlight to the config file.

        Creates the file if it doesn't exist, or adds to existing file.

        Args:
            highlight: The highlight text to save.
        """
        yaml = YAML()
        yaml.default_flow_style = False

        # Load existing data
        if self.config_path.exists():
            with self.config_path.open() as f:
                data = yaml.load(f) or {}
        else:
            data = {}

        if "career_highlights" not in data:
            data["career_highlights"] = []

        # Add highlight
        data["career_highlights"].append(highlight)

        # Save
        with self.config_path.open("w") as f:
            yaml.dump(data, f)

        # Clear cache
        self._highlights = None

    def remove_highlight(self, index: int) -> bool:
        """Remove a career highlight by index (0-indexed).

        Args:
            index: Index of highlight to remove.

        Returns:
            True if highlight was removed, False if index out of bounds.
        """
        yaml = YAML()
        yaml.default_flow_style = False

        # Load existing data
        if not self.config_path.exists():
            return False

        with self.config_path.open() as f:
            data = yaml.load(f) or {}

        if "career_highlights" not in data or not data["career_highlights"]:
            return False

        # Validate index
        if index < 0 or index >= len(data["career_highlights"]):
            return False

        # Remove the highlight
        del data["career_highlights"][index]

        # Save
        with self.config_path.open("w") as f:
            yaml.dump(data, f)

        # Clear cache
        self._highlights = None
        return True
