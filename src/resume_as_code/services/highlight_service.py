"""Highlight service for managing career highlights.

Handles loading, saving, and querying career highlights.
Story 9.2: Uses data_loader for cascading lookup (separate file or embedded).
Story 6.13: Career Highlights Section (CTO/Hybrid Format)
"""

from __future__ import annotations

from pathlib import Path

from ruamel.yaml import YAML

from resume_as_code.data_loader import load_highlights as dl_load_highlights

# Default filename for separated data structure (Story 9.2)
DEFAULT_HIGHLIGHTS_FILE = "highlights.yaml"


class HighlightService:
    """Service for managing career highlights."""

    def __init__(self, config_path: Path | None = None) -> None:
        """Initialize the highlight service.

        Args:
            config_path: Path to .resume.yaml config file. Defaults to .resume.yaml
                        in current directory. Used to determine project root.
        """
        self.config_path = config_path or Path(".resume.yaml")
        self.project_path = self.config_path.parent
        self._highlights: list[str] | None = None

    def load_highlights(self) -> list[str]:
        """Load career highlights using data_loader cascading lookup.

        Story 9.2: Supports both separated files and embedded data.

        Returns:
            List of highlight strings.
            Returns empty list if no highlights found.
        """
        if self._highlights is not None:
            return self._highlights

        # Use data_loader for cascading lookup (Story 9.2)
        self._highlights = dl_load_highlights(self.project_path)
        return self._highlights

    def _uses_separated_format(self) -> bool:
        """Check if project uses separated data files (v3 format).

        Returns:
            True if highlights.yaml exists, False otherwise.
        """
        return (self.project_path / DEFAULT_HIGHLIGHTS_FILE).exists()

    def save_highlight(self, highlight: str) -> None:
        """Save a career highlight to the appropriate file.

        Story 9.2: Writes to highlights.yaml if it exists (v3 format),
        otherwise writes to .resume.yaml (v2 format).

        Args:
            highlight: The highlight text to save.
        """
        yaml = YAML()
        yaml.default_flow_style = False

        if self._uses_separated_format():
            # v3 format: write to highlights.yaml (list format)
            data_path = self.project_path / DEFAULT_HIGHLIGHTS_FILE
            if data_path.exists():
                with open(data_path) as f:
                    highlights_list = yaml.load(f) or []
            else:
                highlights_list = []

            highlights_list.append(highlight)

            with open(data_path, "w") as f:
                yaml.dump(highlights_list, f)
        else:
            # v2 format: write to .resume.yaml (embedded)
            if self.config_path.exists():
                with open(self.config_path) as f:
                    data = yaml.load(f) or {}
            else:
                data = {}

            if "career_highlights" not in data:
                data["career_highlights"] = []

            data["career_highlights"].append(highlight)

            with open(self.config_path, "w") as f:
                yaml.dump(data, f)

        # Clear cache
        self._highlights = None

    def remove_highlight(self, index: int) -> bool:
        """Remove a career highlight by index (0-indexed).

        Story 9.2: Removes from highlights.yaml if it exists (v3 format),
        otherwise removes from .resume.yaml (v2 format).

        Args:
            index: Index of highlight to remove.

        Returns:
            True if highlight was removed, False if index out of bounds.
        """
        yaml = YAML()
        yaml.default_flow_style = False

        if self._uses_separated_format():
            # v3 format: remove from highlights.yaml
            data_path = self.project_path / DEFAULT_HIGHLIGHTS_FILE
            if not data_path.exists():
                return False

            with open(data_path) as f:
                highlights_list = yaml.load(f) or []

            if not highlights_list:
                return False

            # Validate index
            if index < 0 or index >= len(highlights_list):
                return False

            del highlights_list[index]

            with open(data_path, "w") as f:
                yaml.dump(highlights_list, f)
        else:
            # v2 format: remove from .resume.yaml
            if not self.config_path.exists():
                return False

            with open(self.config_path) as f:
                data = yaml.load(f) or {}

            if "career_highlights" not in data or not data["career_highlights"]:
                return False

            # Validate index
            if index < 0 or index >= len(data["career_highlights"]):
                return False

            del data["career_highlights"][index]

            with open(self.config_path, "w") as f:
                yaml.dump(data, f)

        # Clear cache
        self._highlights = None
        return True
