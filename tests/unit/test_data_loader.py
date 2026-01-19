"""Unit tests for data_loader module.

Story 9.2: Tests for unified data access with cascading lookup.
"""

from __future__ import annotations

from pathlib import Path

from resume_as_code.data_loader import (
    load_board_roles,
    load_certifications,
    load_education,
    load_highlights,
    load_profile,
    load_publications,
)
from resume_as_code.models.board_role import BoardRole
from resume_as_code.models.certification import Certification
from resume_as_code.models.education import Education
from resume_as_code.models.publication import Publication


class TestLoadProfile:
    """Tests for load_profile function."""

    def test_load_from_dedicated_file(self, tmp_path: Path) -> None:
        """Load profile from profile.yaml when it exists."""
        # Create profile.yaml
        profile_file = tmp_path / "profile.yaml"
        profile_file.write_text(
            """
name: "Jane Doe"
email: "jane@example.com"
phone: "555-1234"
location: "Austin, TX"
title: "Senior Engineer"
"""
        )

        # Create empty .resume.yaml
        config_file = tmp_path / ".resume.yaml"
        config_file.write_text("schema_version: '3.0.0'\n")

        profile = load_profile(tmp_path)

        assert profile is not None
        assert profile.name == "Jane Doe"
        assert profile.email == "jane@example.com"

    def test_fallback_to_resume_yaml(self, tmp_path: Path) -> None:
        """Fall back to .resume.yaml when profile.yaml doesn't exist."""
        # Create .resume.yaml with embedded profile
        config_file = tmp_path / ".resume.yaml"
        config_file.write_text(
            """
schema_version: '2.0.0'
profile:
  name: "John Smith"
  email: "john@example.com"
"""
        )

        profile = load_profile(tmp_path)

        assert profile is not None
        assert profile.name == "John Smith"

    def test_custom_path_via_data_paths(self, tmp_path: Path) -> None:
        """Use custom path from data_paths configuration."""
        # Create custom profile location
        data_dir = tmp_path / "data"
        data_dir.mkdir()
        custom_profile = data_dir / "my-profile.yaml"
        custom_profile.write_text(
            """
name: "Custom User"
email: "custom@example.com"
"""
        )

        # Create .resume.yaml with data_paths
        config_file = tmp_path / ".resume.yaml"
        config_file.write_text(
            """
schema_version: '3.0.0'
data_paths:
  profile: data/my-profile.yaml
"""
        )

        profile = load_profile(tmp_path)

        assert profile is not None
        assert profile.name == "Custom User"

    def test_returns_empty_profile_when_no_data(self, tmp_path: Path) -> None:
        """Return empty ProfileConfig when no profile data exists."""
        # Create minimal .resume.yaml
        config_file = tmp_path / ".resume.yaml"
        config_file.write_text("schema_version: '3.0.0'\n")

        profile = load_profile(tmp_path)

        assert profile is not None
        assert profile.name is None


class TestLoadCertifications:
    """Tests for load_certifications function."""

    def test_load_from_dedicated_file(self, tmp_path: Path) -> None:
        """Load certifications from certifications.yaml."""
        cert_file = tmp_path / "certifications.yaml"
        cert_file.write_text(
            """
- name: CISSP
  issuer: ISC2
  date: "2023-01"
- name: OSCP
  issuer: OffSec
  date: "2022-06"
"""
        )

        config_file = tmp_path / ".resume.yaml"
        config_file.write_text("schema_version: '3.0.0'\n")

        certs = load_certifications(tmp_path)

        assert len(certs) == 2
        assert certs[0].name == "CISSP"
        assert certs[1].name == "OSCP"
        assert all(isinstance(c, Certification) for c in certs)

    def test_fallback_to_resume_yaml(self, tmp_path: Path) -> None:
        """Fall back to .resume.yaml when certifications.yaml doesn't exist."""
        config_file = tmp_path / ".resume.yaml"
        config_file.write_text(
            """
schema_version: '2.0.0'
certifications:
  - name: CISM
    issuer: ISACA
"""
        )

        certs = load_certifications(tmp_path)

        assert len(certs) == 1
        assert certs[0].name == "CISM"

    def test_returns_empty_list_when_no_data(self, tmp_path: Path) -> None:
        """Return empty list when no certifications exist."""
        config_file = tmp_path / ".resume.yaml"
        config_file.write_text("schema_version: '3.0.0'\n")

        certs = load_certifications(tmp_path)

        assert certs == []


class TestLoadEducation:
    """Tests for load_education function."""

    def test_load_from_dedicated_file(self, tmp_path: Path) -> None:
        """Load education from education.yaml."""
        edu_file = tmp_path / "education.yaml"
        edu_file.write_text(
            """
- degree: "BS Computer Science"
  institution: "MIT"
  graduation_year: "2015"
"""
        )

        config_file = tmp_path / ".resume.yaml"
        config_file.write_text("schema_version: '3.0.0'\n")

        education = load_education(tmp_path)

        assert len(education) == 1
        assert education[0].degree == "BS Computer Science"
        assert isinstance(education[0], Education)

    def test_fallback_to_resume_yaml(self, tmp_path: Path) -> None:
        """Fall back to .resume.yaml when education.yaml doesn't exist."""
        config_file = tmp_path / ".resume.yaml"
        config_file.write_text(
            """
schema_version: '2.0.0'
education:
  - degree: "MS Engineering"
    institution: "Stanford"
"""
        )

        education = load_education(tmp_path)

        assert len(education) == 1
        assert education[0].institution == "Stanford"


class TestLoadHighlights:
    """Tests for load_highlights function."""

    def test_load_from_dedicated_file(self, tmp_path: Path) -> None:
        """Load highlights from highlights.yaml."""
        highlights_file = tmp_path / "highlights.yaml"
        highlights_file.write_text(
            """
- "Led digital transformation saving $10M annually"
- "Built team of 50 engineers from scratch"
"""
        )

        config_file = tmp_path / ".resume.yaml"
        config_file.write_text("schema_version: '3.0.0'\n")

        highlights = load_highlights(tmp_path)

        assert len(highlights) == 2
        assert "digital transformation" in highlights[0]

    def test_fallback_to_resume_yaml(self, tmp_path: Path) -> None:
        """Fall back to .resume.yaml when highlights.yaml doesn't exist."""
        config_file = tmp_path / ".resume.yaml"
        config_file.write_text(
            """
schema_version: '2.0.0'
career_highlights:
  - "Grew revenue 300%"
"""
        )

        highlights = load_highlights(tmp_path)

        assert len(highlights) == 1
        assert "revenue" in highlights[0]


class TestLoadPublications:
    """Tests for load_publications function."""

    def test_load_from_dedicated_file(self, tmp_path: Path) -> None:
        """Load publications from publications.yaml."""
        pub_file = tmp_path / "publications.yaml"
        pub_file.write_text(
            """
- title: "Zero Trust Architecture"
  type: conference
  venue: "RSA Conference"
  date: "2023-06"
  topics: ["security", "architecture"]
  abstract: "Deep dive into zero trust."
"""
        )

        config_file = tmp_path / ".resume.yaml"
        config_file.write_text("schema_version: '3.0.0'\n")

        pubs = load_publications(tmp_path)

        assert len(pubs) == 1
        assert pubs[0].title == "Zero Trust Architecture"
        assert isinstance(pubs[0], Publication)
        assert pubs[0].topics == ["security", "architecture"]

    def test_fallback_to_resume_yaml(self, tmp_path: Path) -> None:
        """Fall back to .resume.yaml when publications.yaml doesn't exist."""
        config_file = tmp_path / ".resume.yaml"
        config_file.write_text(
            """
schema_version: '2.0.0'
publications:
  - title: "API Security"
    type: article
    venue: "Tech Blog"
    date: "2022-01"
"""
        )

        pubs = load_publications(tmp_path)

        assert len(pubs) == 1
        assert pubs[0].title == "API Security"


class TestLoadBoardRoles:
    """Tests for load_board_roles function."""

    def test_load_from_dedicated_file(self, tmp_path: Path) -> None:
        """Load board roles from board-roles.yaml."""
        roles_file = tmp_path / "board-roles.yaml"
        roles_file.write_text(
            """
- organization: "TechStartup Inc"
  role: "Technical Advisor"
  type: advisory
  start_date: "2023-01"
"""
        )

        config_file = tmp_path / ".resume.yaml"
        config_file.write_text("schema_version: '3.0.0'\n")

        roles = load_board_roles(tmp_path)

        assert len(roles) == 1
        assert roles[0].organization == "TechStartup Inc"
        assert isinstance(roles[0], BoardRole)

    def test_fallback_to_resume_yaml(self, tmp_path: Path) -> None:
        """Fall back to .resume.yaml when board-roles.yaml doesn't exist."""
        config_file = tmp_path / ".resume.yaml"
        config_file.write_text(
            """
schema_version: '2.0.0'
board_roles:
  - organization: "Nonprofit"
    role: "Board Member"
    type: director
    start_date: "2020-06"
"""
        )

        roles = load_board_roles(tmp_path)

        assert len(roles) == 1
        assert roles[0].organization == "Nonprofit"


class TestDirectoryMode:
    """Tests for directory mode (Story 11.2)."""

    def test_load_certifications_from_directory(self, tmp_path: Path) -> None:
        """Load certifications from directory when it exists."""
        certs_dir = tmp_path / "certifications"
        certs_dir.mkdir()

        (certs_dir / "cert-2023-01-cissp.yaml").write_text(
            "name: CISSP\nissuer: ISC2\ndate: '2023-01'\n"
        )
        (certs_dir / "cert-2022-06-oscp.yaml").write_text(
            "name: OSCP\nissuer: OffSec\ndate: '2022-06'\n"
        )

        config_file = tmp_path / ".resume.yaml"
        config_file.write_text("schema_version: '3.0.0'\n")

        certs = load_certifications(tmp_path)

        assert len(certs) == 2
        # Sorted alphabetically by filename: cert-2022 comes before cert-2023
        assert certs[0].name == "OSCP"  # 2022 < 2023
        assert certs[1].name == "CISSP"
        assert all(isinstance(c, Certification) for c in certs)

    def test_directory_takes_precedence_over_file(self, tmp_path: Path, caplog: object) -> None:
        """Directory mode takes precedence when both exist."""
        import logging

        # Create both directory and file
        certs_dir = tmp_path / "certifications"
        certs_dir.mkdir()
        (certs_dir / "cert-dir.yaml").write_text("name: Dir Cert\n")

        cert_file = tmp_path / "certifications.yaml"
        cert_file.write_text("- name: File Cert\n")

        config_file = tmp_path / ".resume.yaml"
        config_file.write_text("schema_version: '3.0.0'\n")

        with caplog.at_level(logging.WARNING):  # type: ignore[attr-defined]
            certs = load_certifications(tmp_path)

        # Directory wins
        assert len(certs) == 1
        assert certs[0].name == "Dir Cert"
        # Warning logged
        assert "using directory mode" in caplog.text

    def test_configured_dir_overrides_default(self, tmp_path: Path) -> None:
        """Configured *_dir path takes highest priority."""
        # Create default directory
        default_dir = tmp_path / "certifications"
        default_dir.mkdir()
        (default_dir / "cert.yaml").write_text("name: Default Dir Cert\n")

        # Create custom directory
        custom_dir = tmp_path / "custom-certs"
        custom_dir.mkdir()
        (custom_dir / "cert.yaml").write_text("name: Custom Dir Cert\n")

        config_file = tmp_path / ".resume.yaml"
        config_file.write_text(
            """
schema_version: '3.0.0'
data_paths:
  certifications_dir: custom-certs
"""
        )

        certs = load_certifications(tmp_path)

        assert len(certs) == 1
        assert certs[0].name == "Custom Dir Cert"

    def test_load_education_from_directory(self, tmp_path: Path) -> None:
        """Load education from directory."""
        edu_dir = tmp_path / "education"
        edu_dir.mkdir()

        (edu_dir / "edu-mit.yaml").write_text(
            "degree: BS Computer Science\ninstitution: MIT\ngraduation_year: '2015'\n"
        )

        config_file = tmp_path / ".resume.yaml"
        config_file.write_text("schema_version: '3.0.0'\n")

        education = load_education(tmp_path)

        assert len(education) == 1
        assert education[0].institution == "MIT"
        assert isinstance(education[0], Education)

    def test_load_publications_from_directory(self, tmp_path: Path) -> None:
        """Load publications from directory."""
        pub_dir = tmp_path / "publications"
        pub_dir.mkdir()

        (pub_dir / "pub-2023-06-talk.yaml").write_text(
            "title: My Talk\ntype: conference\nvenue: RSA\ndate: '2023-06'\n"
        )

        config_file = tmp_path / ".resume.yaml"
        config_file.write_text("schema_version: '3.0.0'\n")

        pubs = load_publications(tmp_path)

        assert len(pubs) == 1
        assert pubs[0].title == "My Talk"
        assert isinstance(pubs[0], Publication)

    def test_load_board_roles_from_directory(self, tmp_path: Path) -> None:
        """Load board roles from directory."""
        roles_dir = tmp_path / "board-roles"
        roles_dir.mkdir()

        (roles_dir / "board-acme.yaml").write_text(
            "organization: Acme Corp\nrole: Advisor\ntype: advisory\nstart_date: '2023-01'\n"
        )

        config_file = tmp_path / ".resume.yaml"
        config_file.write_text("schema_version: '3.0.0'\n")

        roles = load_board_roles(tmp_path)

        assert len(roles) == 1
        assert roles[0].organization == "Acme Corp"
        assert isinstance(roles[0], BoardRole)

    def test_load_highlights_from_directory(self, tmp_path: Path) -> None:
        """Load highlights from directory with text field."""
        highlights_dir = tmp_path / "highlights"
        highlights_dir.mkdir()

        (highlights_dir / "hl-001.yaml").write_text("text: First highlight\n")
        (highlights_dir / "hl-002.yaml").write_text("text: Second highlight\n")

        config_file = tmp_path / ".resume.yaml"
        config_file.write_text("schema_version: '3.0.0'\n")

        highlights = load_highlights(tmp_path)

        assert len(highlights) == 2
        assert "First highlight" in highlights[0]
        assert "Second highlight" in highlights[1]

    def test_skip_hidden_files_in_directory(self, tmp_path: Path) -> None:
        """Directory mode should skip hidden files."""
        certs_dir = tmp_path / "certifications"
        certs_dir.mkdir()

        (certs_dir / "cert-visible.yaml").write_text("name: Visible\n")
        (certs_dir / ".hidden.yaml").write_text("name: Hidden\n")

        config_file = tmp_path / ".resume.yaml"
        config_file.write_text("schema_version: '3.0.0'\n")

        certs = load_certifications(tmp_path)

        assert len(certs) == 1
        assert certs[0].name == "Visible"


class TestDataPathsConfig:
    """Tests for data_paths configuration support."""

    def test_all_custom_paths(self, tmp_path: Path) -> None:
        """Support custom paths for all data files."""
        # Create custom directory structure
        data_dir = tmp_path / "custom-data"
        data_dir.mkdir()

        (data_dir / "profile.yaml").write_text("name: Custom\n")
        (data_dir / "certs.yaml").write_text("- name: CISSP\n  issuer: ISC2\n")
        (data_dir / "edu.yaml").write_text("- degree: BS\n  institution: MIT\n")
        (data_dir / "highlights.yaml").write_text("- First highlight\n")
        (data_dir / "pubs.yaml").write_text(
            "- title: Paper\n  type: article\n  venue: Journal\n  date: '2023-01'\n"
        )
        (data_dir / "boards.yaml").write_text(
            "- organization: Org\n  role: Advisor\n  type: advisory\n  start_date: '2023-01'\n"
        )

        config_file = tmp_path / ".resume.yaml"
        config_file.write_text(
            """
schema_version: '3.0.0'
data_paths:
  profile: custom-data/profile.yaml
  certifications: custom-data/certs.yaml
  education: custom-data/edu.yaml
  highlights: custom-data/highlights.yaml
  publications: custom-data/pubs.yaml
  board_roles: custom-data/boards.yaml
"""
        )

        # Verify all data loads from custom paths
        assert load_profile(tmp_path).name == "Custom"
        assert len(load_certifications(tmp_path)) == 1
        assert len(load_education(tmp_path)) == 1
        assert len(load_highlights(tmp_path)) == 1
        assert len(load_publications(tmp_path)) == 1
        assert len(load_board_roles(tmp_path)) == 1
