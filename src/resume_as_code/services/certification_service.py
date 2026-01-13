"""Certification service for managing professional certifications.

Handles loading, saving, and querying certifications from .resume.yaml config.
"""

from __future__ import annotations

from pathlib import Path

from ruamel.yaml import YAML

from resume_as_code.models.certification import Certification


class CertificationService:
    """Service for managing professional certifications."""

    def __init__(self, config_path: Path | None = None) -> None:
        """Initialize the certification service.

        Args:
            config_path: Path to .resume.yaml config file. Defaults to .resume.yaml
                        in current directory.
        """
        self.config_path = config_path or Path(".resume.yaml")
        self._certifications: list[Certification] | None = None

    def load_certifications(self) -> list[Certification]:
        """Load certifications from config file.

        Returns:
            List of Certification objects.
            Returns empty list if file doesn't exist or has no certifications.
        """
        if self._certifications is not None:
            return self._certifications

        if not self.config_path.exists():
            self._certifications = []
            return self._certifications

        yaml = YAML()
        with open(self.config_path) as f:
            data = yaml.load(f)

        if not data:
            self._certifications = []
            return self._certifications

        certs_data = data.get("certifications", [])
        self._certifications = []

        for cert_data in certs_data:
            # Convert to dict if needed (ruamel returns CommentedMap)
            cert_dict = dict(cert_data) if hasattr(cert_data, "items") else cert_data
            self._certifications.append(Certification.model_validate(cert_dict))

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

    def save_certification(self, certification: Certification) -> None:
        """Save a certification to the config file.

        Creates the file if it doesn't exist, or adds to existing file.

        Args:
            certification: The Certification to save.
        """
        yaml = YAML()
        yaml.default_flow_style = False

        # Load existing data
        if self.config_path.exists():
            with open(self.config_path) as f:
                data = yaml.load(f) or {}
        else:
            data = {}

        if "certifications" not in data:
            data["certifications"] = []

        # Add certification (exclude None values)
        cert_data = certification.model_dump(exclude_none=True)
        # Remove 'display' if it's True (default)
        if cert_data.get("display") is True:
            del cert_data["display"]
        # Convert HttpUrl to string for YAML serialization
        if "url" in cert_data and cert_data["url"] is not None:
            cert_data["url"] = str(cert_data["url"])
        data["certifications"].append(cert_data)

        # Save
        with open(self.config_path, "w") as f:
            yaml.dump(data, f)

        # Clear cache
        self._certifications = None
