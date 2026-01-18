"""Education service for managing academic credentials.

Handles loading, saving, and querying education records.
Story 9.2: Uses data_loader for cascading lookup (separate file or embedded).
"""

from __future__ import annotations

from pathlib import Path

from ruamel.yaml import YAML

from resume_as_code.data_loader import load_education as dl_load_education
from resume_as_code.models.education import Education

# Default filename for separated data structure (Story 9.2)
DEFAULT_EDUCATION_FILE = "education.yaml"


class EducationService:
    """Service for managing education records."""

    def __init__(self, config_path: Path | None = None) -> None:
        """Initialize the education service.

        Args:
            config_path: Path to .resume.yaml config file. Defaults to .resume.yaml
                        in current directory. Used to determine project root.
        """
        self.config_path = config_path or Path(".resume.yaml")
        self.project_path = self.config_path.parent
        self._education: list[Education] | None = None

    def load_education(self) -> list[Education]:
        """Load education records using data_loader cascading lookup.

        Story 9.2: Supports both separated files and embedded data.

        Returns:
            List of Education objects.
            Returns empty list if no education records found.
        """
        if self._education is not None:
            return self._education

        # Use data_loader for cascading lookup (Story 9.2)
        self._education = dl_load_education(self.project_path)
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

    def _uses_separated_format(self) -> bool:
        """Check if project uses separated data files (v3 format).

        Returns:
            True if education.yaml exists, False otherwise.
        """
        return (self.project_path / DEFAULT_EDUCATION_FILE).exists()

    def save_education(self, education: Education) -> None:
        """Save an education record to the appropriate file.

        Story 9.2: Writes to education.yaml if it exists (v3 format),
        otherwise writes to .resume.yaml (v2 format).

        Args:
            education: The Education record to save.
        """
        yaml = YAML()
        yaml.default_flow_style = False

        # Prepare education data
        edu_data = education.model_dump(exclude_none=True)
        # Remove 'display' if it's True (default)
        if edu_data.get("display") is True:
            del edu_data["display"]

        if self._uses_separated_format():
            # v3 format: write to education.yaml (list format)
            data_path = self.project_path / DEFAULT_EDUCATION_FILE
            if data_path.exists():
                with open(data_path) as f:
                    edu_list = yaml.load(f) or []
            else:
                edu_list = []

            edu_list.append(edu_data)

            with open(data_path, "w") as f:
                yaml.dump(edu_list, f)
        else:
            # v2 format: write to .resume.yaml (embedded)
            if self.config_path.exists():
                with open(self.config_path) as f:
                    data = yaml.load(f) or {}
            else:
                data = {}

            if "education" not in data:
                data["education"] = []

            data["education"].append(edu_data)

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

        Story 9.2: Removes from education.yaml if it exists (v3 format),
        otherwise removes from .resume.yaml (v2 format).

        Args:
            degree: The exact degree name to remove.

        Returns:
            True if education was removed, False if not found.
        """
        yaml = YAML()
        yaml.default_flow_style = False

        degree_lower = degree.lower().strip()

        if self._uses_separated_format():
            # v3 format: remove from education.yaml
            data_path = self.project_path / DEFAULT_EDUCATION_FILE
            if not data_path.exists():
                return False

            with open(data_path) as f:
                edu_list = yaml.load(f) or []

            if not edu_list:
                return False

            original_count = len(edu_list)
            edu_list = [e for e in edu_list if e.get("degree", "").lower().strip() != degree_lower]

            if len(edu_list) == original_count:
                return False

            with open(data_path, "w") as f:
                yaml.dump(edu_list, f)
        else:
            # v2 format: remove from .resume.yaml
            if not self.config_path.exists():
                return False

            with open(self.config_path) as f:
                data = yaml.load(f) or {}

            if "education" not in data or not data["education"]:
                return False

            original_count = len(data["education"])
            data["education"] = [
                e for e in data["education"] if e.get("degree", "").lower().strip() != degree_lower
            ]

            if len(data["education"]) == original_count:
                return False

            with open(self.config_path, "w") as f:
                yaml.dump(data, f)

        # Clear cache
        self._education = None
        return True
