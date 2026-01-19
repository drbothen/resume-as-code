"""Publication service for managing publications and speaking engagements.

Handles loading, saving, and querying publications.
Story 9.2: Uses data_loader for cascading lookup (separate file or embedded).
Story 11.2: Added directory mode support via ShardedLoader.
"""

from __future__ import annotations

from pathlib import Path

from ruamel.yaml import YAML

from resume_as_code.data_loader import get_storage_mode
from resume_as_code.data_loader import load_publications as dl_load_publications
from resume_as_code.models.publication import Publication
from resume_as_code.services.sharded_loader import ShardedLoader

# Default filename for separated data structure (Story 9.2)
DEFAULT_PUBLICATIONS_FILE = "publications.yaml"
DEFAULT_PUBLICATIONS_DIR = "publications"


class PublicationService:
    """Service for managing publications and speaking engagements."""

    def __init__(self, config_path: Path | None = None) -> None:
        """Initialize the publication service.

        Args:
            config_path: Path to .resume.yaml config file. Defaults to .resume.yaml
                        in current directory. Used to determine project root.
        """
        self.config_path = config_path or Path(".resume.yaml")
        self.project_path = self.config_path.parent
        self._publications: list[Publication] | None = None

    def load_publications(self) -> list[Publication]:
        """Load publications using data_loader cascading lookup.

        Story 9.2: Supports both separated files and embedded data.

        Returns:
            List of Publication objects.
            Returns empty list if no publications found.
        """
        if self._publications is not None:
            return self._publications

        # Use data_loader for cascading lookup (Story 9.2)
        self._publications = dl_load_publications(self.project_path)
        return self._publications

    def find_publication(self, title: str) -> Publication | None:
        """Find existing publication by title.

        Case-insensitive, whitespace-normalized matching.

        Args:
            title: Publication title to search for.

        Returns:
            Matching Publication if found, None otherwise.
        """
        publications = self.load_publications()
        title_lower = title.lower().strip()

        for pub in publications:
            if pub.title.lower().strip() == title_lower:
                return pub

        return None

    def _uses_separated_format(self) -> bool:
        """Check if project uses separated data files (v3 format).

        Returns:
            True if publications.yaml exists, False otherwise.
        """
        return (self.project_path / DEFAULT_PUBLICATIONS_FILE).exists()

    def save_publication(self, publication: Publication) -> Path | None:
        """Save a publication to the appropriate location.

        Story 9.2: Writes to publications.yaml if it exists (v3 format),
        otherwise writes to .resume.yaml (v2 format).
        Story 11.2: Supports directory mode with per-item files.

        Args:
            publication: The Publication to save.

        Returns:
            Path to the saved file (directory mode), or None (file/embedded mode).
        """
        mode, path = get_storage_mode(self.project_path, "publications")

        if mode == "dir":
            # Story 11.2: Directory mode - save to individual file
            dir_path = path or (self.project_path / DEFAULT_PUBLICATIONS_DIR)
            loader = ShardedLoader(dir_path, Publication)
            item_id = loader.generate_id(publication)
            saved_path = loader.save(publication, item_id)
            self._publications = None
            return saved_path

        # File or embedded mode - use existing logic
        yaml = YAML()
        yaml.default_flow_style = False

        # Prepare publication data
        pub_data = publication.model_dump(exclude_none=True)
        # Remove 'display' if it's True (default)
        if pub_data.get("display") is True:
            del pub_data["display"]
        # Remove 'topics' if it's an empty list (default)
        if not pub_data.get("topics"):
            pub_data.pop("topics", None)
        # Convert HttpUrl to string for YAML serialization
        if "url" in pub_data and pub_data["url"] is not None:
            pub_data["url"] = str(pub_data["url"])

        if mode == "file":
            # v3 format: write to publications.yaml (list format)
            data_path = path or (self.project_path / DEFAULT_PUBLICATIONS_FILE)
            if data_path.exists():
                with open(data_path) as f:
                    pubs_list = yaml.load(f) or []
            else:
                pubs_list = []

            pubs_list.append(pub_data)

            with open(data_path, "w") as f:
                yaml.dump(pubs_list, f)
        else:
            # Embedded mode: write to .resume.yaml
            if self.config_path.exists():
                with open(self.config_path) as f:
                    data = yaml.load(f) or {}
            else:
                data = {}

            if "publications" not in data:
                data["publications"] = []

            data["publications"].append(pub_data)

            with open(self.config_path, "w") as f:
                yaml.dump(data, f)

        # Clear cache
        self._publications = None
        return None

    def remove_publication(self, title: str) -> bool:
        """Remove a publication by title (case-insensitive partial match).

        Story 9.2: Removes from publications.yaml if it exists (v3 format),
        otherwise removes from .resume.yaml (v2 format).
        Story 11.2: Supports directory mode with per-item files.

        Args:
            title: Full or partial publication title to match.

        Returns:
            True if publication was removed, False if not found.

        Note:
            Uses case-insensitive partial matching. If multiple publications
            match, the first match is removed.
        """
        mode, path = get_storage_mode(self.project_path, "publications")
        title_lower = title.lower().strip()

        if mode == "dir":
            # Story 11.2: Directory mode - find and remove file
            dir_path = path or (self.project_path / DEFAULT_PUBLICATIONS_DIR)
            loader = ShardedLoader(dir_path, Publication)
            pubs = loader.load_all()

            # Find matching publication with its source file
            for pub in pubs:
                if title_lower in pub.title.lower():
                    source_file = getattr(pub, "_source_file", None)
                    if source_file:
                        # Extract item_id from filename (without .yaml)
                        item_id = source_file.stem
                        if loader.remove(item_id):
                            self._publications = None
                            return True
                    return False
            return False

        yaml = YAML()
        yaml.default_flow_style = False

        if mode == "file":
            # v3 format: remove from publications.yaml
            data_path = path or (self.project_path / DEFAULT_PUBLICATIONS_FILE)
            if not data_path.exists():
                return False

            with open(data_path) as f:
                pubs_list = yaml.load(f) or []

            if not pubs_list:
                return False

            # Find matching publication index
            remove_idx = None
            for idx, pub_data in enumerate(pubs_list):
                pub_title = pub_data.get("title", "")
                if title_lower in pub_title.lower():
                    remove_idx = idx
                    break

            if remove_idx is None:
                return False

            del pubs_list[remove_idx]

            with open(data_path, "w") as f:
                yaml.dump(pubs_list, f)
        else:
            # Embedded mode: remove from .resume.yaml
            if not self.config_path.exists():
                return False

            with open(self.config_path) as f:
                data = yaml.load(f) or {}

            if "publications" not in data or not data["publications"]:
                return False

            # Find matching publication index
            remove_idx = None
            for idx, pub_data in enumerate(data["publications"]):
                pub_title = pub_data.get("title", "")
                if title_lower in pub_title.lower():
                    remove_idx = idx
                    break

            if remove_idx is None:
                return False

            del data["publications"][remove_idx]

            with open(self.config_path, "w") as f:
                yaml.dump(data, f)

        # Clear cache
        self._publications = None
        return True

    def find_publications_by_title(self, title: str) -> list[Publication]:
        """Find all publications matching a partial title.

        Case-insensitive partial matching.

        Args:
            title: Partial title to search for.

        Returns:
            List of matching Publication objects.
        """
        publications = self.load_publications()
        title_lower = title.lower().strip()

        return [pub for pub in publications if title_lower in pub.title.lower()]
