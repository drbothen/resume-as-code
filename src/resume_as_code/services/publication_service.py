"""Publication service for managing publications and speaking engagements.

Handles loading, saving, and querying publications from .resume.yaml config.
"""

from __future__ import annotations

from pathlib import Path

from ruamel.yaml import YAML

from resume_as_code.models.publication import Publication


class PublicationService:
    """Service for managing publications and speaking engagements."""

    def __init__(self, config_path: Path | None = None) -> None:
        """Initialize the publication service.

        Args:
            config_path: Path to .resume.yaml config file. Defaults to .resume.yaml
                        in current directory.
        """
        self.config_path = config_path or Path(".resume.yaml")
        self._publications: list[Publication] | None = None

    def load_publications(self) -> list[Publication]:
        """Load publications from config file.

        Returns:
            List of Publication objects.
            Returns empty list if file doesn't exist or has no publications.
        """
        if self._publications is not None:
            return self._publications

        if not self.config_path.exists():
            self._publications = []
            return self._publications

        yaml = YAML()
        with open(self.config_path) as f:
            data = yaml.load(f)

        if not data:
            self._publications = []
            return self._publications

        pubs_data = data.get("publications", [])
        self._publications = []

        for pub_data in pubs_data:
            # Convert to dict if needed (ruamel returns CommentedMap)
            pub_dict = dict(pub_data) if hasattr(pub_data, "items") else pub_data
            self._publications.append(Publication.model_validate(pub_dict))

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

    def save_publication(self, publication: Publication) -> None:
        """Save a publication to the config file.

        Creates the file if it doesn't exist, or adds to existing file.

        Args:
            publication: The Publication to save.
        """
        yaml = YAML()
        yaml.default_flow_style = False

        # Load existing data
        if self.config_path.exists():
            with open(self.config_path) as f:
                data = yaml.load(f) or {}
        else:
            data = {}

        if "publications" not in data:
            data["publications"] = []

        # Add publication (exclude None values)
        pub_data = publication.model_dump(exclude_none=True)
        # Remove 'display' if it's True (default)
        if pub_data.get("display") is True:
            del pub_data["display"]
        # Convert HttpUrl to string for YAML serialization
        if "url" in pub_data and pub_data["url"] is not None:
            pub_data["url"] = str(pub_data["url"])
        data["publications"].append(pub_data)

        # Save
        with open(self.config_path, "w") as f:
            yaml.dump(data, f)

        # Clear cache
        self._publications = None

    def remove_publication(self, title: str) -> bool:
        """Remove a publication by title (case-insensitive partial match).

        Args:
            title: Full or partial publication title to match.

        Returns:
            True if publication was removed, False if not found.

        Note:
            Uses case-insensitive partial matching. If multiple publications
            match, the first match is removed.
        """
        yaml = YAML()
        yaml.default_flow_style = False

        # Load existing data
        if not self.config_path.exists():
            return False

        with open(self.config_path) as f:
            data = yaml.load(f) or {}

        if "publications" not in data or not data["publications"]:
            return False

        # Find matching publication index
        title_lower = title.lower().strip()
        remove_idx = None
        for idx, pub_data in enumerate(data["publications"]):
            pub_title = pub_data.get("title", "")
            if title_lower in pub_title.lower():
                remove_idx = idx
                break

        if remove_idx is None:
            return False

        # Remove the publication
        del data["publications"][remove_idx]

        # Save
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
