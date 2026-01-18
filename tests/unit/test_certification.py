"""Tests for Certification model."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest
from pydantic import ValidationError

from resume_as_code.models.certification import Certification


class TestCertificationModel:
    """Tests for Certification model."""

    def test_minimal_certification(self) -> None:
        """Should create cert with only name."""
        cert = Certification(name="AWS SAP")
        assert cert.name == "AWS SAP"
        assert cert.issuer is None
        assert cert.date is None
        assert cert.expires is None
        assert cert.credential_id is None
        assert cert.url is None
        assert cert.display is True

    def test_full_certification(self) -> None:
        """Should create cert with all fields."""
        cert = Certification(
            name="AWS Solutions Architect - Professional",
            issuer="Amazon Web Services",
            date="2024-06",
            expires="2027-06",
            credential_id="ABC123XYZ",
            url="https://aws.amazon.com/verification/ABC123XYZ",
            display=True,
        )
        assert cert.name == "AWS Solutions Architect - Professional"
        assert cert.issuer == "Amazon Web Services"
        assert cert.date == "2024-06"
        assert cert.expires == "2027-06"
        assert cert.credential_id == "ABC123XYZ"
        assert str(cert.url) == "https://aws.amazon.com/verification/ABC123XYZ"
        assert cert.display is True

    def test_date_format_validation_valid_yyyy_mm(self) -> None:
        """Should accept YYYY-MM date format."""
        cert = Certification(name="Test", date="2024-06")
        assert cert.date == "2024-06"

    def test_date_format_validation_normalizes_yyyy_mm_dd(self) -> None:
        """Should normalize YYYY-MM-DD to YYYY-MM."""
        cert = Certification(name="Test", date="2024-06-15")
        assert cert.date == "2024-06"

    def test_date_format_validation_invalid(self) -> None:
        """Should reject invalid date format."""
        with pytest.raises(ValidationError):
            Certification(name="Test", date="invalid")

    def test_date_format_validation_invalid_partial(self) -> None:
        """Should reject invalid partial date format."""
        with pytest.raises(ValidationError):
            Certification(name="Test", date="2024")

    def test_expires_format_validation_valid(self) -> None:
        """Should accept valid expires date format."""
        cert = Certification(name="Test", expires="2026-12")
        assert cert.expires == "2026-12"

    def test_expires_format_validation_normalizes(self) -> None:
        """Should normalize expires YYYY-MM-DD to YYYY-MM."""
        cert = Certification(name="Test", expires="2026-12-31")
        assert cert.expires == "2026-12"

    def test_expires_format_validation_invalid(self) -> None:
        """Should reject invalid expires format."""
        with pytest.raises(ValidationError):
            Certification(name="Test", expires="never")

    def test_url_validation_valid(self) -> None:
        """Should accept valid URL."""
        cert = Certification(name="Test", url="https://example.com/cert/123")
        assert str(cert.url) == "https://example.com/cert/123"

    def test_url_validation_invalid(self) -> None:
        """Should reject invalid URL."""
        with pytest.raises(ValidationError):
            Certification(name="Test", url="not-a-url")

    def test_display_default_true(self) -> None:
        """Display should default to True."""
        cert = Certification(name="Test")
        assert cert.display is True

    def test_display_can_be_false(self) -> None:
        """Display can be set to False."""
        cert = Certification(name="Test", display=False)
        assert cert.display is False


class TestCertificationStatus:
    """Tests for certification status calculation."""

    def test_status_active_no_expiration(self) -> None:
        """Should return active when no expiration date."""
        cert = Certification(name="Test")
        assert cert.get_status() == "active"

    def test_status_expired(self) -> None:
        """Should return expired for past expiration date."""
        cert = Certification(name="Test", expires="2020-01")
        assert cert.get_status() == "expired"

    def test_status_active_future_expiration(self) -> None:
        """Should return active for far-future expiration."""
        cert = Certification(name="Test", expires="2099-12")
        assert cert.get_status() == "active"

    def test_status_expires_soon(self) -> None:
        """Should return expires_soon within 90 days of expiration."""
        # Mock date.today() to test expires_soon logic
        from datetime import date as date_module

        # Create a cert that expires in 60 days from a fixed date
        with patch("resume_as_code.models.certification.date") as mock_date:
            mock_date.today.return_value = date_module(2024, 6, 1)
            cert = Certification(name="Test", expires="2024-07")  # ~60 days away
            assert cert.get_status() == "expires_soon"


class TestCertificationFormatDisplay:
    """Tests for certification display formatting."""

    def test_format_display_name_only(self) -> None:
        """Should format with just name."""
        cert = Certification(name="CISSP")
        display = cert.format_display()
        assert display == "CISSP"

    def test_format_display_with_issuer(self) -> None:
        """Should format with issuer."""
        cert = Certification(name="CISSP", issuer="ISC2")
        display = cert.format_display()
        assert "CISSP" in display
        assert "ISC2" in display

    def test_format_display_with_issuer_and_date(self) -> None:
        """Should format with issuer and date."""
        cert = Certification(name="CISSP", issuer="ISC2", date="2023-01")
        display = cert.format_display()
        assert "CISSP" in display
        assert "ISC2" in display
        assert "2023" in display

    def test_format_display_with_expiration(self) -> None:
        """Should format with expiration."""
        cert = Certification(
            name="CISSP",
            issuer="ISC2",
            date="2023-01",
            expires="2026-01",
        )
        display = cert.format_display()
        assert "CISSP" in display
        assert "ISC2" in display
        assert "2023" in display
        assert "expires" in display.lower()
        assert "2026" in display

    def test_format_display_date_without_issuer(self) -> None:
        """Should format with date when no issuer."""
        cert = Certification(name="CISSP", date="2023-01")
        display = cert.format_display()
        assert "CISSP" in display
        assert "2023" in display


class TestResumeConfigCertifications:
    """Tests for certifications in ResumeConfig."""

    def test_certifications_default_empty(self) -> None:
        """ResumeConfig should default to None for certifications (Story 9.2).

        Note: Access certifications via data_loader for actual usage.
        """
        from resume_as_code.models.config import ResumeConfig

        config = ResumeConfig()
        assert config.certifications is None

    def test_certifications_list(self) -> None:
        """ResumeConfig should accept certifications list."""
        from resume_as_code.models.config import ResumeConfig

        config = ResumeConfig(
            certifications=[
                Certification(name="AWS SAP", issuer="Amazon Web Services"),
                Certification(name="CISSP", issuer="ISC2"),
            ]
        )
        assert len(config.certifications) == 2
        assert config.certifications[0].name == "AWS SAP"
        assert config.certifications[1].name == "CISSP"

    def test_certifications_from_dict(self) -> None:
        """ResumeConfig should parse certifications from dict."""
        from resume_as_code.models.config import ResumeConfig

        config = ResumeConfig(
            certifications=[
                {"name": "AWS SAP", "issuer": "Amazon Web Services"},
                {"name": "CISSP", "issuer": "ISC2", "date": "2023-01"},
            ]
        )
        assert len(config.certifications) == 2
        assert config.certifications[0].name == "AWS SAP"
        assert config.certifications[1].date == "2023-01"


class TestCertificationsLoadingFromConfig:
    """Tests for certifications loading from config files."""

    def test_certifications_load_from_yaml(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Certifications should load from .resume.yaml file."""
        from resume_as_code.config import get_config, reset_config

        reset_config()
        config_file = tmp_path / ".resume.yaml"
        config_file.write_text(
            """
certifications:
  - name: "AWS Solutions Architect - Professional"
    issuer: "Amazon Web Services"
    date: "2024-06"
    credential_id: "ABC123XYZ"
    url: "https://aws.amazon.com/verification/ABC123XYZ"
  - name: "CISSP"
    issuer: "ISC2"
    date: "2023-01"
    expires: "2026-01"
"""
        )
        monkeypatch.chdir(tmp_path)
        with patch.dict("os.environ", {}, clear=True):
            config = get_config()
            assert len(config.certifications) == 2
            assert config.certifications[0].name == "AWS Solutions Architect - Professional"
            assert config.certifications[0].issuer == "Amazon Web Services"
            assert config.certifications[1].name == "CISSP"
            assert config.certifications[1].expires == "2026-01"

    def test_certifications_empty_when_not_in_config(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Certifications should be empty when not in config file."""
        from resume_as_code.config import get_config, reset_config

        reset_config()
        config_file = tmp_path / ".resume.yaml"
        config_file.write_text("output_dir: ./dist\n")
        monkeypatch.chdir(tmp_path)
        with patch.dict("os.environ", {}, clear=True):
            config = get_config()
            # Story 9.2: config.certifications is None when not in config
            # Use data_loader for actual access
            assert config.certifications is None

    def test_certifications_with_display_false(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Certifications with display: false should load correctly."""
        from resume_as_code.config import get_config, reset_config

        reset_config()
        config_file = tmp_path / ".resume.yaml"
        config_file.write_text(
            """
certifications:
  - name: "Old Cert"
    issuer: "Old Issuer"
    display: false
  - name: "Current Cert"
    issuer: "Current Issuer"
    display: true
"""
        )
        monkeypatch.chdir(tmp_path)
        with patch.dict("os.environ", {}, clear=True):
            config = get_config()
            assert len(config.certifications) == 2
            assert config.certifications[0].display is False
            assert config.certifications[1].display is True
