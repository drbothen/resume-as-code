"""Highlight service for managing career highlights.

Handles loading, saving, and querying career highlights.
Story 9.2: Uses data_loader for cascading lookup (separate file or embedded).
Story 6.13: Career Highlights Section (CTO/Hybrid Format)
Story 11.2: Added directory mode support.
"""

from __future__ import annotations

import re
from pathlib import Path

from ruamel.yaml import YAML

from resume_as_code.data_loader import get_storage_mode
from resume_as_code.data_loader import load_highlights as dl_load_highlights

# Default filename for separated data structure (Story 9.2)
DEFAULT_HIGHLIGHTS_FILE = "highlights.yaml"
DEFAULT_HIGHLIGHTS_DIR = "highlights"


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

    def _slugify(self, text: str) -> str:
        """Convert text to URL-safe slug."""
        slug = text.lower()
        slug = re.sub(r"[^a-z0-9]+", "-", slug)
        slug = slug.strip("-")
        slug = re.sub(r"-+", "-", slug)
        # Truncate to reasonable length
        return slug[:40]

    def _get_next_highlight_number(self, dir_path: Path) -> int:
        """Get the next available highlight number for directory mode."""
        if not dir_path.exists():
            return 1
        max_num = 0
        for yaml_file in dir_path.glob("hl-*.yaml"):
            match = re.match(r"hl-(\d+)-", yaml_file.name)
            if match:
                num = int(match.group(1))
                if num > max_num:
                    max_num = num
        return max_num + 1

    def save_highlight(self, highlight: str) -> Path | None:
        """Save a career highlight to the appropriate location.

        Story 9.2: Writes to highlights.yaml if it exists (v3 format),
        otherwise writes to .resume.yaml (v2 format).
        Story 11.2: Supports directory mode with per-item files.

        Args:
            highlight: The highlight text to save.

        Returns:
            Path to the saved file (directory mode), or None (file/embedded mode).
        """
        mode, path = get_storage_mode(self.project_path, "highlights")

        if mode == "dir":
            # Story 11.2: Directory mode - save to individual file
            dir_path = path or (self.project_path / DEFAULT_HIGHLIGHTS_DIR)
            dir_path.mkdir(parents=True, exist_ok=True)

            yaml = YAML()
            yaml.default_flow_style = False

            # Generate ID: hl-NNN-{slug}
            num = self._get_next_highlight_number(dir_path)
            slug = self._slugify(highlight)
            item_id = f"hl-{num:03d}-{slug}"
            file_path = dir_path / f"{item_id}.yaml"

            # Write highlight with 'text' field
            with open(file_path, "w") as f:
                yaml.dump({"text": highlight}, f)

            self._highlights = None
            return file_path

        # File or embedded mode - use existing logic
        yaml = YAML()
        yaml.default_flow_style = False

        if mode == "file":
            # v3 format: write to highlights.yaml (list format)
            data_path = path or (self.project_path / DEFAULT_HIGHLIGHTS_FILE)
            if data_path.exists():
                with open(data_path) as f:
                    highlights_list = yaml.load(f) or []
            else:
                highlights_list = []

            highlights_list.append(highlight)

            with open(data_path, "w") as f:
                yaml.dump(highlights_list, f)
        else:
            # Embedded mode: write to .resume.yaml
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
        return None

    def remove_highlight(self, index: int) -> bool:
        """Remove a career highlight by index (0-indexed).

        Story 9.2: Removes from highlights.yaml if it exists (v3 format),
        otherwise removes from .resume.yaml (v2 format).
        Story 11.2: Supports directory mode with per-item files.

        Args:
            index: Index of highlight to remove.

        Returns:
            True if highlight was removed, False if index out of bounds.
        """
        mode, path = get_storage_mode(self.project_path, "highlights")

        if mode == "dir":
            # Story 11.2: Directory mode - find and remove file by index
            dir_path = path or (self.project_path / DEFAULT_HIGHLIGHTS_DIR)
            if not dir_path.exists():
                return False

            # Get sorted list of highlight files
            highlight_files = sorted(
                f for f in dir_path.glob("*.yaml") if not f.name.startswith(".")
            )

            if not highlight_files:
                return False

            # Validate index
            if index < 0 or index >= len(highlight_files):
                return False

            # Remove the file at the given index
            highlight_files[index].unlink()
            self._highlights = None
            return True

        yaml = YAML()
        yaml.default_flow_style = False

        if mode == "file":
            # v3 format: remove from highlights.yaml
            data_path = path or (self.project_path / DEFAULT_HIGHLIGHTS_FILE)
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
            # Embedded mode: remove from .resume.yaml
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
