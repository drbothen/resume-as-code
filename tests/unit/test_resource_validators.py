"""Tests for resource validators.

Story 11.5: Tests for comprehensive resource validation.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from resume_as_code.services.validators import ValidationOrchestrator
from resume_as_code.services.validators.base import ResourceValidationResult
from resume_as_code.services.validators.board_role_validator import BoardRoleValidator
from resume_as_code.services.validators.certification_validator import (
    CertificationValidator,
)
from resume_as_code.services.validators.config_validator import ConfigValidator
from resume_as_code.services.validators.education_validator import EducationValidator
from resume_as_code.services.validators.highlight_validator import HighlightValidator
from resume_as_code.services.validators.orchestrator import AggregatedValidationResult
from resume_as_code.services.validators.position_validator import PositionValidator
from resume_as_code.services.validators.publication_validator import PublicationValidator

# =============================================================================
# Test Fixtures
# =============================================================================


VALID_POSITIONS = """\
positions:
  pos-techcorp-senior:
    employer: "TechCorp Industries"
    title: "Senior Platform Engineer"
    start_date: "2022-01"
  pos-techcorp-junior:
    employer: "TechCorp Industries"
    title: "Platform Engineer"
    start_date: "2020-01"
    end_date: "2021-12"
"""

INVALID_POSITIONS_DATE_RANGE = """\
positions:
  pos-invalid-dates:
    employer: "Some Corp"
    title: "Engineer"
    start_date: "2023-01"
    end_date: "2022-01"
"""

# Certifications are a root-level list (not wrapped in a key)
VALID_CERTIFICATIONS = """\
- name: "AWS Solutions Architect"
  issuer: "Amazon Web Services"
  date: "2023-01"
  expires: "2026-01"
- name: "CISSP"
  issuer: "ISC2"
  date: "2022-06"
"""

INVALID_CERTIFICATIONS_DATE = """\
- name: "Invalid Cert"
  issuer: "Test Issuer"
  date: "2025-01"
  expires: "2024-01"
"""

# Education is a root-level list
VALID_EDUCATION = """\
- degree: "Bachelor of Science in Computer Science"
  institution: "MIT"
  graduation_year: "2010"
"""

# Publications are a root-level list
VALID_PUBLICATIONS = """\
- title: "Zero Trust Architecture"
  type: "conference"
  venue: "RSA Conference"
  date: "2022-06"
  topics:
    - "security"
    - "zero-trust"
"""

# Board roles are a root-level list
VALID_BOARD_ROLES = """\
- organization: "TechStartup Inc"
  role: "Technical Advisor"
  type: "advisory"
  start_date: "2021-01"
  focus: "AI/ML Strategy"
"""

INVALID_BOARD_ROLES_DATE = """\
- organization: "BadDates Corp"
  role: "Director"
  type: "director"
  start_date: "2024-01"
  end_date: "2023-01"
"""

# Highlights are a root-level list
VALID_HIGHLIGHTS = """\
- "Led digital transformation generating $50M revenue"
- "Built platform serving 10M users daily"
"""

VALID_CONFIG = """\
schema_version: "2.0.0"
work_units_dir: "work-units"
"""

INVALID_CONFIG_VERSION = """\
schema_version: "invalid"
work_units_dir: "work-units"
"""


# =============================================================================
# Position Validator Tests
# =============================================================================


class TestPositionValidator:
    """Tests for PositionValidator."""

    def test_resource_type(self) -> None:
        """Should return correct resource type."""
        validator = PositionValidator()
        assert validator.resource_type == "Positions"
        assert validator.resource_key == "positions"

    def test_valid_positions(self, tmp_path: Path) -> None:
        """Should validate positions correctly."""
        (tmp_path / "positions.yaml").write_text(VALID_POSITIONS)

        validator = PositionValidator()
        result = validator.validate(tmp_path)

        assert result.is_valid
        assert result.valid_count == 2
        assert result.invalid_count == 0

    def test_missing_positions_file(self, tmp_path: Path) -> None:
        """Should handle missing positions.yaml gracefully."""
        validator = PositionValidator()
        result = validator.validate(tmp_path)

        assert result.is_valid
        assert result.valid_count == 0
        assert result.invalid_count == 0

    def test_invalid_date_range(self, tmp_path: Path) -> None:
        """Should detect start_date > end_date (AC4)."""
        (tmp_path / "positions.yaml").write_text(INVALID_POSITIONS_DATE_RANGE)

        validator = PositionValidator()
        result = validator.validate(tmp_path)

        assert not result.is_valid
        assert result.invalid_count == 1
        # Pydantic model_validator raises ValueError, captured as SCHEMA_VALIDATION_ERROR
        # The error message contains the date range validation failure
        assert any(
            "SCHEMA_VALIDATION_ERROR" in e.code and "end_date" in e.message.lower()
            for e in result.errors
        )


# =============================================================================
# Certification Validator Tests
# =============================================================================


class TestCertificationValidator:
    """Tests for CertificationValidator."""

    def test_resource_type(self) -> None:
        """Should return correct resource type."""
        validator = CertificationValidator()
        assert validator.resource_type == "Certifications"
        assert validator.resource_key == "certifications"

    def test_valid_certifications(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Should validate certifications correctly."""
        (tmp_path / "certifications.yaml").write_text(VALID_CERTIFICATIONS)
        monkeypatch.chdir(tmp_path)

        validator = CertificationValidator()
        result = validator.validate(tmp_path)

        assert result.is_valid
        assert result.valid_count == 2
        assert result.invalid_count == 0

    def test_invalid_date_range(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Should detect date > expires (AC4)."""
        (tmp_path / "certifications.yaml").write_text(INVALID_CERTIFICATIONS_DATE)
        monkeypatch.chdir(tmp_path)

        validator = CertificationValidator()
        result = validator.validate(tmp_path)

        assert not result.is_valid
        assert result.invalid_count == 1
        assert any("INVALID_DATE_RANGE" in e.code for e in result.errors)

    def test_expired_certification_warning(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should warn on expired certifications (Task 3.4)."""
        expired_cert = """\
- name: "Expired Cert"
  issuer: "Test Issuer"
  date: "2020-01"
  expires: "2022-01"
"""
        (tmp_path / "certifications.yaml").write_text(expired_cert)
        monkeypatch.chdir(tmp_path)

        validator = CertificationValidator()
        result = validator.validate(tmp_path)

        # Expired cert is valid but generates warning
        assert result.is_valid
        assert result.valid_count == 1
        assert result.warning_count == 1
        assert any("CERTIFICATION_EXPIRED" in w.code for w in result.warnings)

    def test_expires_soon_certification_warning(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should warn on certifications expiring within 90 days (Task 3.4)."""
        from datetime import date, timedelta

        # Calculate date 30 days from now
        soon_date = date.today() + timedelta(days=30)
        soon_str = soon_date.strftime("%Y-%m")

        expires_soon_cert = f"""\
- name: "Expiring Soon Cert"
  issuer: "Test Issuer"
  date: "2020-01"
  expires: "{soon_str}"
"""
        (tmp_path / "certifications.yaml").write_text(expires_soon_cert)
        monkeypatch.chdir(tmp_path)

        validator = CertificationValidator()
        result = validator.validate(tmp_path)

        # Cert expiring soon is valid but generates warning
        assert result.is_valid
        assert result.valid_count == 1
        assert result.warning_count == 1
        assert any("CERTIFICATION_EXPIRES_SOON" in w.code for w in result.warnings)


# =============================================================================
# Education Validator Tests
# =============================================================================


class TestEducationValidator:
    """Tests for EducationValidator."""

    def test_resource_type(self) -> None:
        """Should return correct resource type."""
        validator = EducationValidator()
        assert validator.resource_type == "Education"
        assert validator.resource_key == "education"

    def test_valid_education(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Should validate education correctly."""
        (tmp_path / "education.yaml").write_text(VALID_EDUCATION)
        monkeypatch.chdir(tmp_path)

        validator = EducationValidator()
        result = validator.validate(tmp_path)

        assert result.is_valid
        assert result.valid_count == 1
        assert result.invalid_count == 0


# =============================================================================
# Publication Validator Tests
# =============================================================================


class TestPublicationValidator:
    """Tests for PublicationValidator."""

    def test_resource_type(self) -> None:
        """Should return correct resource type."""
        validator = PublicationValidator()
        assert validator.resource_type == "Publications"
        assert validator.resource_key == "publications"

    def test_valid_publications(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Should validate publications correctly."""
        (tmp_path / "publications.yaml").write_text(VALID_PUBLICATIONS)
        monkeypatch.chdir(tmp_path)

        validator = PublicationValidator()
        result = validator.validate(tmp_path)

        assert result.is_valid
        assert result.valid_count == 1
        assert result.invalid_count == 0


# =============================================================================
# Board Role Validator Tests
# =============================================================================


class TestBoardRoleValidator:
    """Tests for BoardRoleValidator."""

    def test_resource_type(self) -> None:
        """Should return correct resource type."""
        validator = BoardRoleValidator()
        assert validator.resource_type == "Board Roles"
        assert validator.resource_key == "board_roles"

    def test_valid_board_roles(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Should validate board roles correctly."""
        (tmp_path / "board-roles.yaml").write_text(VALID_BOARD_ROLES)
        monkeypatch.chdir(tmp_path)

        validator = BoardRoleValidator()
        result = validator.validate(tmp_path)

        assert result.is_valid
        assert result.valid_count == 1
        assert result.invalid_count == 0

    def test_invalid_date_range(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Should detect start_date > end_date (AC4)."""
        (tmp_path / "board-roles.yaml").write_text(INVALID_BOARD_ROLES_DATE)
        monkeypatch.chdir(tmp_path)

        validator = BoardRoleValidator()
        result = validator.validate(tmp_path)

        assert not result.is_valid
        assert result.invalid_count == 1
        assert any("INVALID_DATE_RANGE" in e.code for e in result.errors)


# =============================================================================
# Highlight Validator Tests
# =============================================================================


class TestHighlightValidator:
    """Tests for HighlightValidator."""

    def test_resource_type(self) -> None:
        """Should return correct resource type."""
        validator = HighlightValidator()
        assert validator.resource_type == "Highlights"
        assert validator.resource_key == "highlights"

    def test_valid_highlights(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Should validate highlights correctly."""
        (tmp_path / "highlights.yaml").write_text(VALID_HIGHLIGHTS)
        monkeypatch.chdir(tmp_path)

        validator = HighlightValidator()
        result = validator.validate(tmp_path)

        assert result.is_valid
        assert result.valid_count == 2
        assert result.invalid_count == 0

    def test_highlight_too_long_warning(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should warn when highlight exceeds 150 characters (Task 7.3)."""
        long_highlight = "x" * 200  # Over 150 chars
        highlights_yaml = f"""\
- "{long_highlight}"
- "Short highlight"
"""
        (tmp_path / "highlights.yaml").write_text(highlights_yaml)
        monkeypatch.chdir(tmp_path)

        validator = HighlightValidator()
        result = validator.validate(tmp_path)

        # Long highlight is valid but generates warning
        assert result.is_valid
        assert result.valid_count == 2
        assert result.warning_count == 1
        assert any("HIGHLIGHT_TOO_LONG" in w.code for w in result.warnings)

    def test_empty_highlight_error(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Should error on empty highlight string."""
        highlights_yaml = """\
- ""
- "Valid highlight"
"""
        (tmp_path / "highlights.yaml").write_text(highlights_yaml)
        monkeypatch.chdir(tmp_path)

        validator = HighlightValidator()
        result = validator.validate(tmp_path)

        assert not result.is_valid
        assert result.invalid_count == 1
        assert any("EMPTY_HIGHLIGHT" in e.code for e in result.errors)


# =============================================================================
# Config Validator Tests
# =============================================================================


class TestConfigValidator:
    """Tests for ConfigValidator."""

    def test_resource_type(self) -> None:
        """Should return correct resource type."""
        validator = ConfigValidator()
        assert validator.resource_type == "Config"
        assert validator.resource_key == "config"

    def test_valid_config(self, tmp_path: Path) -> None:
        """Should validate config correctly."""
        (tmp_path / ".resume.yaml").write_text(VALID_CONFIG)
        (tmp_path / "work-units").mkdir()

        validator = ConfigValidator()
        result = validator.validate(tmp_path)

        assert result.is_valid
        assert result.valid_count == 1
        assert result.invalid_count == 0

    def test_invalid_schema_version(self, tmp_path: Path) -> None:
        """Should detect invalid schema_version format."""
        (tmp_path / ".resume.yaml").write_text(INVALID_CONFIG_VERSION)
        (tmp_path / "work-units").mkdir()

        validator = ConfigValidator()
        result = validator.validate(tmp_path)

        assert not result.is_valid
        assert result.invalid_count == 1
        assert any("INVALID_SCHEMA_VERSION" in e.code for e in result.errors)

    def test_missing_work_units_dir_warning(self, tmp_path: Path) -> None:
        """Should warn when work_units_dir does not exist (Task 8.4)."""
        config_yaml = """\
schema_version: "2.0.0"
work_units_dir: "nonexistent-work-units"
"""
        (tmp_path / ".resume.yaml").write_text(config_yaml)
        # Note: not creating the work-units directory

        validator = ConfigValidator()
        result = validator.validate(tmp_path)

        # Missing path is a warning, not an error
        assert result.is_valid
        assert result.warning_count >= 1
        assert any("PATH_NOT_FOUND" in w.code for w in result.warnings)

    def test_missing_templates_dir_warning(self, tmp_path: Path) -> None:
        """Should warn when templates_dir does not exist (Task 8.4)."""
        config_yaml = """\
schema_version: "2.0.0"
work_units_dir: "work-units"
templates_dir: "nonexistent-templates"
"""
        (tmp_path / ".resume.yaml").write_text(config_yaml)
        (tmp_path / "work-units").mkdir()
        # Note: not creating the templates directory

        validator = ConfigValidator()
        result = validator.validate(tmp_path)

        # Missing path is a warning, not an error
        assert result.is_valid
        assert result.warning_count >= 1
        assert any("PATH_NOT_FOUND" in w.code for w in result.warnings)


# =============================================================================
# Orchestrator Tests
# =============================================================================


class TestValidationOrchestrator:
    """Tests for ValidationOrchestrator."""

    def test_validate_all_returns_aggregated_result(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should run all validators and return aggregated result."""
        # Create minimal valid project
        (tmp_path / ".resume.yaml").write_text(VALID_CONFIG)
        (tmp_path / "work-units").mkdir()
        (tmp_path / "positions.yaml").write_text(VALID_POSITIONS)

        monkeypatch.chdir(tmp_path)

        orchestrator = ValidationOrchestrator()
        result = orchestrator.validate_all(tmp_path)

        assert isinstance(result, AggregatedValidationResult)
        assert len(result.results) > 0
        # At least positions should be valid
        positions_result = next((r for r in result.results if r.resource_type == "Positions"), None)
        assert positions_result is not None
        assert positions_result.is_valid

    def test_validate_single_positions(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should validate single resource type."""
        (tmp_path / "positions.yaml").write_text(VALID_POSITIONS)
        monkeypatch.chdir(tmp_path)

        orchestrator = ValidationOrchestrator()
        result = orchestrator.validate_single(tmp_path, "positions")

        assert result is not None
        assert isinstance(result, ResourceValidationResult)
        assert result.resource_type == "Positions"
        assert result.is_valid

    def test_validate_single_unknown_key(self, tmp_path: Path) -> None:
        """Should return None for unknown resource key."""
        orchestrator = ValidationOrchestrator()
        result = orchestrator.validate_single(tmp_path, "unknown_key")

        assert result is None

    def test_get_validator_keys(self) -> None:
        """Should return all validator keys."""
        orchestrator = ValidationOrchestrator()
        keys = orchestrator.get_validator_keys()

        assert "work_units" in keys
        assert "positions" in keys
        assert "certifications" in keys
        assert "education" in keys
        assert "publications" in keys
        assert "board_roles" in keys
        assert "highlights" in keys
        assert "config" in keys


class TestAggregatedValidationResult:
    """Tests for AggregatedValidationResult properties."""

    def test_is_valid_all_pass(self) -> None:
        """Should return True when all results are valid."""
        result = AggregatedValidationResult(
            results=[
                ResourceValidationResult(
                    resource_type="Test1", source_path=None, valid_count=1, invalid_count=0
                ),
                ResourceValidationResult(
                    resource_type="Test2", source_path=None, valid_count=2, invalid_count=0
                ),
            ]
        )
        assert result.is_valid

    def test_is_valid_some_fail(self) -> None:
        """Should return False when any result has errors."""
        result = AggregatedValidationResult(
            results=[
                ResourceValidationResult(
                    resource_type="Test1", source_path=None, valid_count=1, invalid_count=0
                ),
                ResourceValidationResult(
                    resource_type="Test2", source_path=None, valid_count=0, invalid_count=1
                ),
            ]
        )
        assert not result.is_valid

    def test_total_warnings(self) -> None:
        """Should sum all warnings across results."""
        result = AggregatedValidationResult(
            results=[
                ResourceValidationResult(
                    resource_type="Test1",
                    source_path=None,
                    valid_count=1,
                    invalid_count=0,
                    warning_count=2,
                ),
                ResourceValidationResult(
                    resource_type="Test2",
                    source_path=None,
                    valid_count=1,
                    invalid_count=0,
                    warning_count=3,
                ),
            ]
        )
        assert result.total_warnings == 5
