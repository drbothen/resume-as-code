"""Education service for managing academic credentials.

Handles loading, saving, and querying education records from .resume.yaml config.
"""

from __future__ import annotations

from pathlib import Path

from ruamel.yaml import YAML

from resume_as_code.models.education import Education


class EducationService:
    """Service for managing education records."""

    def __init__(self, config_path: Path | None = None) -> None:
        """Initialize the education service.

        Args:
            config_path: Path to .resume.yaml config file. Defaults to .resume.yaml
                        in current directory.
        """
        self.config_path = config_path or Path(".resume.yaml")
        self._education: list[Education] | None = None

    def load_education(self) -> list[Education]:
        """Load education records from config file.

        Returns:
            List of Education objects.
            Returns empty list if file doesn't exist or has no education records.
        """
        if self._education is not None:
            return self._education

        if not self.config_path.exists():
            self._education = []
            return self._education

        yaml = YAML()
        with open(self.config_path) as f:
            data = yaml.load(f)

        if not data:
            self._education = []
            return self._education

        edu_data = data.get("education", [])
        self._education = []

        for edu_item in edu_data:
            # Convert to dict if needed (ruamel returns CommentedMap)
            edu_dict = dict(edu_item) if hasattr(edu_item, "items") else edu_item
            self._education.append(Education.model_validate(edu_dict))

        return self._education

    def find_education(self, degree: str, institution: str) -> Education | None:
        """Find existing education by degree and institution.

        Case-insensitive, whitespace-normalized matching.

        Args:
            degree: Degree name to search for.
            institution: Institution name to match.

        Returns:
            Matching Education if found, None otherwise.
        """
        education = self.load_education()
        degree_lower = degree.lower().strip()
        institution_lower = institution.lower().strip()

        for edu in education:
            if (
                edu.degree.lower().strip() == degree_lower
                and edu.institution.lower().strip() == institution_lower
            ):
                return edu

        return None

    def save_education(self, education: Education) -> None:
        """Save an education record to the config file.

        Creates the file if it doesn't exist, or adds to existing file.

        Args:
            education: The Education record to save.
        """
        yaml = YAML()
        yaml.default_flow_style = False

        # Load existing data
        if self.config_path.exists():
            with open(self.config_path) as f:
                data = yaml.load(f) or {}
        else:
            data = {}

        if "education" not in data:
            data["education"] = []

        # Add education (exclude None values)
        edu_data = education.model_dump(exclude_none=True)
        # Remove 'display' if it's True (default)
        if edu_data.get("display") is True:
            del edu_data["display"]
        data["education"].append(edu_data)

        # Save
        with open(self.config_path, "w") as f:
            yaml.dump(data, f)

        # Clear cache
        self._education = None

    def find_educations_by_degree(self, query: str) -> list[Education]:
        """Find education records matching degree name.

        Case-insensitive partial matching on degree name.

        Args:
            query: Search string to match against degree names.

        Returns:
            List of matching Education records.
        """
        education = self.load_education()
        query_lower = query.lower().strip()

        return [edu for edu in education if query_lower in edu.degree.lower()]

    def remove_education(self, degree: str) -> bool:
        """Remove an education record by degree name.

        Performs exact match (case-insensitive) on degree name.

        Args:
            degree: The exact degree name to remove.

        Returns:
            True if education was removed, False if not found.
        """
        yaml = YAML()
        yaml.default_flow_style = False

        if not self.config_path.exists():
            return False

        with open(self.config_path) as f:
            data = yaml.load(f) or {}

        if "education" not in data or not data["education"]:
            return False

        original_count = len(data["education"])
        degree_lower = degree.lower().strip()

        data["education"] = [
            e for e in data["education"] if e.get("degree", "").lower().strip() != degree_lower
        ]

        if len(data["education"]) == original_count:
            return False

        # Save
        with open(self.config_path, "w") as f:
            yaml.dump(data, f)

        # Clear cache
        self._education = None
        return True
