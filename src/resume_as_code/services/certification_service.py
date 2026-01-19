"""Certification service for managing professional certifications.

Handles loading, saving, and querying certifications.
Story 9.2: Uses data_loader for cascading lookup (separate file or embedded).
Story 11.2: Added directory mode support via ShardedLoader.
"""

from __future__ import annotations

from pathlib import Path

from ruamel.yaml import YAML

from resume_as_code.data_loader import get_storage_mode
from resume_as_code.data_loader import load_certifications as dl_load_certifications
from resume_as_code.models.certification import Certification
from resume_as_code.services.sharded_loader import ShardedLoader

# Default filename for separated data structure (Story 9.2)
DEFAULT_CERTIFICATIONS_FILE = "certifications.yaml"
DEFAULT_CERTIFICATIONS_DIR = "certifications"


class CertificationService:
    """Service for managing professional certifications."""

    def __init__(self, config_path: Path | None = None) -> None:
        """Initialize the certification service.

        Args:
            config_path: Path to .resume.yaml config file. Defaults to .resume.yaml
                        in current directory. Used to determine project root.
        """
        self.config_path = config_path or Path(".resume.yaml")
        self.project_path = self.config_path.parent
        self._certifications: list[Certification] | None = None

    def load_certifications(self) -> list[Certification]:
        """Load certifications using data_loader cascading lookup.

        Story 9.2: Supports both separated files and embedded data.

        Returns:
            List of Certification objects.
            Returns empty list if no certifications found.
        """
        if self._certifications is not None:
            return self._certifications

        # Use data_loader for cascading lookup (Story 9.2)
        self._certifications = dl_load_certifications(self.project_path)
        return self._certifications

    def find_certification(self, name: str, issuer: str | None = None) -> Certification | None:
        """Find existing certification by name and optional issuer.

        Case-insensitive, whitespace-normalized matching.

        Args:
            name: Certification name to search for.
            issuer: Optional issuer to match.

        Returns:
            Matching Certification if found, None otherwise.
        """
        certifications = self.load_certifications()
        name_lower = name.lower().strip()
        issuer_lower = issuer.lower().strip() if issuer else None

        for cert in certifications:
            if cert.name.lower().strip() == name_lower and (
                issuer_lower is None
                or (cert.issuer and cert.issuer.lower().strip() == issuer_lower)
            ):
                return cert

        return None

    def _get_data_file_path(self) -> Path:
        """Get the path to the certifications data file.

        Story 9.2: Prefers separated file, falls back to .resume.yaml.

        Returns:
            Path to certifications.yaml if it exists, otherwise .resume.yaml.
        """
        separated_path = self.project_path / DEFAULT_CERTIFICATIONS_FILE
        if separated_path.exists():
            return separated_path
        return self.config_path

    def _uses_separated_format(self) -> bool:
        """Check if project uses separated data files (v3 format).

        Returns:
            True if certifications.yaml exists, False otherwise.
        """
        return (self.project_path / DEFAULT_CERTIFICATIONS_FILE).exists()

    def save_certification(self, certification: Certification) -> Path | None:
        """Save a certification to the appropriate location.

        Story 9.2: Writes to certifications.yaml if it exists (v3 format),
        otherwise writes to .resume.yaml (v2 format).
        Story 11.2: Supports directory mode with per-item files.

        Args:
            certification: The Certification to save.

        Returns:
            Path to the saved file (directory mode), or None (file/embedded mode).
        """
        mode, path = get_storage_mode(self.project_path, "certifications")

        if mode == "dir":
            # Story 11.2: Directory mode - save to individual file
            dir_path = path or (self.project_path / DEFAULT_CERTIFICATIONS_DIR)
            loader = ShardedLoader(dir_path, Certification)
            item_id = loader.generate_id(certification)
            saved_path = loader.save(certification, item_id)
            self._certifications = None
            return saved_path

        # File or embedded mode - use existing logic
        yaml = YAML()
        yaml.default_flow_style = False

        # Prepare certification data
        cert_data = certification.model_dump(exclude_none=True)
        # Remove 'display' if it's True (default)
        if cert_data.get("display") is True:
            del cert_data["display"]
        # Convert HttpUrl to string for YAML serialization
        if "url" in cert_data and cert_data["url"] is not None:
            cert_data["url"] = str(cert_data["url"])

        if mode == "file":
            # v3 format: write to certifications.yaml (list format)
            data_path = path or (self.project_path / DEFAULT_CERTIFICATIONS_FILE)
            if data_path.exists():
                with open(data_path) as f:
                    certs_list = yaml.load(f) or []
            else:
                certs_list = []

            certs_list.append(cert_data)

            with open(data_path, "w") as f:
                yaml.dump(certs_list, f)
        else:
            # Embedded mode: write to .resume.yaml
            if self.config_path.exists():
                with open(self.config_path) as f:
                    data = yaml.load(f) or {}
            else:
                data = {}

            if "certifications" not in data:
                data["certifications"] = []

            data["certifications"].append(cert_data)

            with open(self.config_path, "w") as f:
                yaml.dump(data, f)

        # Clear cache
        self._certifications = None
        return None

    def remove_certification(self, name: str) -> bool:
        """Remove a certification by name (case-insensitive partial match).

        Story 9.2: Removes from certifications.yaml if it exists (v3 format),
        otherwise removes from .resume.yaml (v2 format).
        Story 11.2: Supports directory mode with per-item files.

        Args:
            name: Full or partial certification name to match.

        Returns:
            True if certification was removed, False if not found.

        Note:
            Uses case-insensitive partial matching. If multiple certifications
            match, the first match is removed.
        """
        mode, path = get_storage_mode(self.project_path, "certifications")
        name_lower = name.lower().strip()

        if mode == "dir":
            # Story 11.2: Directory mode - find and remove file
            dir_path = path or (self.project_path / DEFAULT_CERTIFICATIONS_DIR)
            loader = ShardedLoader(dir_path, Certification)
            certs = loader.load_all()

            # Find matching certification with its source file
            for cert in certs:
                if name_lower in cert.name.lower():
                    source_file = getattr(cert, "_source_file", None)
                    if source_file:
                        # Extract item_id from filename (without .yaml)
                        item_id = source_file.stem
                        if loader.remove(item_id):
                            self._certifications = None
                            return True
                    return False
            return False

        yaml = YAML()
        yaml.default_flow_style = False

        if mode == "file":
            # v3 format: remove from certifications.yaml
            data_path = path or (self.project_path / DEFAULT_CERTIFICATIONS_FILE)
            if not data_path.exists():
                return False

            with open(data_path) as f:
                certs_list = yaml.load(f) or []

            if not certs_list:
                return False

            # Find matching certification index
            remove_idx = None
            for idx, cert_data in enumerate(certs_list):
                cert_name = cert_data.get("name", "")
                if name_lower in cert_name.lower():
                    remove_idx = idx
                    break

            if remove_idx is None:
                return False

            del certs_list[remove_idx]

            with open(data_path, "w") as f:
                yaml.dump(certs_list, f)
        else:
            # Embedded mode: remove from .resume.yaml
            if not self.config_path.exists():
                return False

            with open(self.config_path) as f:
                data = yaml.load(f) or {}

            if "certifications" not in data or not data["certifications"]:
                return False

            # Find matching certification index
            remove_idx = None
            for idx, cert_data in enumerate(data["certifications"]):
                cert_name = cert_data.get("name", "")
                if name_lower in cert_name.lower():
                    remove_idx = idx
                    break

            if remove_idx is None:
                return False

            del data["certifications"][remove_idx]

            with open(self.config_path, "w") as f:
                yaml.dump(data, f)

        # Clear cache
        self._certifications = None
        return True

    def find_certifications_by_name(self, name: str) -> list[Certification]:
        """Find all certifications matching a partial name.

        Case-insensitive partial matching.

        Args:
            name: Partial name to search for.

        Returns:
            List of matching Certification objects.
        """
        certifications = self.load_certifications()
        name_lower = name.lower().strip()

        return [cert for cert in certifications if name_lower in cert.name.lower()]
