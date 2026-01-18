"""Tests for ProfileConfig model."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest
from pydantic import ValidationError

from resume_as_code.config import get_config, reset_config
from resume_as_code.models.config import ProfileConfig, ResumeConfig


class TestProfileConfig:
    """Test ProfileConfig model."""

    def test_default_all_none(self) -> None:
        """ProfileConfig should have all fields default to None."""
        profile = ProfileConfig()
        assert profile.name is None
        assert profile.email is None
        assert profile.phone is None
        assert profile.location is None
        assert profile.linkedin is None
        assert profile.github is None
        assert profile.website is None
        assert profile.title is None
        assert profile.summary is None

    def test_accepts_all_string_fields(self) -> None:
        """ProfileConfig should accept all string fields."""
        profile = ProfileConfig(
            name="Joshua Magady",
            email="joshua@example.com",
            phone="555-123-4567",
            location="Austin, TX",
            title="Senior Platform Engineer",
            summary="Experienced platform engineer.",
        )
        assert profile.name == "Joshua Magady"
        assert profile.email == "joshua@example.com"
        assert profile.phone == "555-123-4567"
        assert profile.location == "Austin, TX"
        assert profile.title == "Senior Platform Engineer"
        assert profile.summary == "Experienced platform engineer."

    def test_linkedin_url_validation_valid(self) -> None:
        """ProfileConfig should accept valid LinkedIn URL."""
        profile = ProfileConfig(linkedin="https://linkedin.com/in/jmagady")
        assert str(profile.linkedin) == "https://linkedin.com/in/jmagady"

    def test_linkedin_url_validation_invalid(self) -> None:
        """ProfileConfig should reject invalid LinkedIn URL."""
        with pytest.raises(ValidationError):
            ProfileConfig(linkedin="not-a-url")

    def test_github_url_validation_valid(self) -> None:
        """ProfileConfig should accept valid GitHub URL."""
        profile = ProfileConfig(github="https://github.com/jmagady")
        assert str(profile.github) == "https://github.com/jmagady"

    def test_github_url_validation_invalid(self) -> None:
        """ProfileConfig should reject invalid GitHub URL."""
        with pytest.raises(ValidationError):
            ProfileConfig(github="not-a-url")

    def test_website_url_validation_valid(self) -> None:
        """ProfileConfig should accept valid website URL."""
        profile = ProfileConfig(website="https://example.com")
        # Note: Pydantic HttpUrl normalizes URLs by adding trailing slash
        assert str(profile.website) == "https://example.com/"

    def test_website_url_validation_invalid(self) -> None:
        """ProfileConfig should reject invalid website URL."""
        with pytest.raises(ValidationError):
            ProfileConfig(website="not-a-url")

    def test_complete_profile(self) -> None:
        """ProfileConfig should accept complete profile data."""
        profile = ProfileConfig(
            name="Joshua Magady",
            email="joshua@example.com",
            phone="555-123-4567",
            location="Austin, TX",
            linkedin="https://linkedin.com/in/jmagady",
            github="https://github.com/jmagady",
            website="https://jmagady.dev",
            title="Senior Platform Engineer",
            summary="Experienced platform engineer with 10+ years.",
        )
        assert profile.name == "Joshua Magady"
        assert profile.email == "joshua@example.com"
        assert str(profile.linkedin) == "https://linkedin.com/in/jmagady"
        assert str(profile.github) == "https://github.com/jmagady"


class TestResumeConfigProfile:
    """Test profile field on ResumeConfig."""

    def test_default_profile(self) -> None:
        """ResumeConfig should default to None for profile (Story 9.2).

        Note: Access profile via data_loader for actual usage.
        """
        config = ResumeConfig()
        assert config.profile is None

    def test_custom_profile(self) -> None:
        """ResumeConfig should accept custom profile."""
        config = ResumeConfig(
            profile=ProfileConfig(
                name="Test User",
                email="test@example.com",
            )
        )
        assert config.profile.name == "Test User"
        assert config.profile.email == "test@example.com"

    def test_profile_from_dict(self) -> None:
        """ResumeConfig should parse profile from dict."""
        config = ResumeConfig(
            profile={
                "name": "Dict User",
                "title": "Engineer",
            }
        )
        assert config.profile.name == "Dict User"
        assert config.profile.title == "Engineer"


class TestBuildCommandProfile:
    """Test build command uses profile from data_loader (Story 9.2)."""

    def test_load_contact_info_from_profile(self) -> None:
        """_load_contact_info should use profile from data_loader (Story 9.2)."""
        from resume_as_code.commands.build import _load_contact_info

        test_profile = ProfileConfig(
            name="Joshua Magady",
            title="Senior Platform Engineer",
            email="joshua@example.com",
            phone="555-123-4567",
            location="Austin, TX",
            linkedin="https://linkedin.com/in/jmagady",
            github="https://github.com/jmagady",
        )
        with patch("resume_as_code.commands.build.load_profile") as mock_load_profile:
            mock_load_profile.return_value = test_profile
            contact = _load_contact_info()
            assert contact.name == "Joshua Magady"
            assert contact.title == "Senior Platform Engineer"
            assert contact.email == "joshua@example.com"
            assert contact.phone == "555-123-4567"
            assert contact.location == "Austin, TX"
            assert contact.linkedin == "https://linkedin.com/in/jmagady"
            assert contact.github == "https://github.com/jmagady"

    def test_load_contact_info_title_is_optional(self) -> None:
        """_load_contact_info should handle missing title gracefully (Story 9.2)."""
        from resume_as_code.commands.build import _load_contact_info

        test_profile = ProfileConfig(
            name="Test User",
            # title is None
        )
        with patch("resume_as_code.commands.build.load_profile") as mock_load_profile:
            mock_load_profile.return_value = test_profile
            contact = _load_contact_info()
            assert contact.name == "Test User"
            assert contact.title is None

    def test_load_contact_info_fallback_when_no_name(self) -> None:
        """_load_contact_info should fall back to 'Your Name' and warn (Story 9.2)."""
        from resume_as_code.commands.build import _load_contact_info

        test_profile = ProfileConfig(
            email="test@example.com",
            # name is None
        )
        with (
            patch("resume_as_code.commands.build.load_profile") as mock_load_profile,
            patch("resume_as_code.commands.build.console") as mock_console,
        ):
            mock_load_profile.return_value = test_profile
            contact = _load_contact_info()
            # Should fall back to placeholder
            assert contact.name == "Your Name"
            # Email should still be populated
            assert contact.email == "test@example.com"
            # Should have printed warning (AC #3)
            mock_console.print.assert_called_once()
            warning_msg = mock_console.print.call_args[0][0]
            assert "No profile configured" in warning_msg
            assert "resume config profile.name" in warning_msg

    def test_load_contact_info_empty_profile(self) -> None:
        """_load_contact_info should handle empty profile (Story 9.2)."""
        from resume_as_code.commands.build import _load_contact_info

        test_profile = ProfileConfig()  # Empty profile
        with (
            patch("resume_as_code.commands.build.load_profile") as mock_load_profile,
            patch("resume_as_code.commands.build.console"),
        ):
            mock_load_profile.return_value = test_profile
            contact = _load_contact_info()
            assert contact.name == "Your Name"
            assert contact.email is None


class TestProfileSummaryIntegration:
    """Test profile.summary flows through to ResumeData."""

    def test_summary_passed_to_resume_data(self) -> None:
        """profile.summary should be passed to ResumeData via data_loader (Story 9.2)."""
        import tempfile
        from pathlib import Path as PathLib
        from unittest.mock import MagicMock, patch

        from click.testing import CliRunner

        from resume_as_code.cli import main

        test_profile = ProfileConfig(
            name="Test User",
            summary="Experienced engineer with 10+ years...",
        )
        config = MagicMock()
        config.work_units_dir = PathLib("work-units")
        config.output_dir = PathLib("dist")
        config.default_template = "modern"
        config.default_format = "both"
        config.tailored_notice = False
        config.tailored_notice_text = None
        config.employment_continuity = "minimum_bullet"

        # Mock get_config and data_loader functions (Story 9.2)
        with (
            patch("resume_as_code.commands.build.get_config") as mock_get_config,
            patch("resume_as_code.commands.build.SavedPlan") as mock_plan_cls,
            patch("resume_as_code.commands.build._load_work_units_from_plan") as mock_load_wus,
            patch("resume_as_code.commands.build._generate_outputs") as mock_gen,
            patch("resume_as_code.commands.build.load_profile") as mock_load_profile,
            patch("resume_as_code.commands.build.load_certifications") as mock_load_certs,
            patch("resume_as_code.commands.build.load_education") as mock_load_edu,
            patch("resume_as_code.commands.build.load_highlights") as mock_load_highlights,
            patch("resume_as_code.commands.build.load_publications") as mock_load_pubs,
            patch("resume_as_code.commands.build.load_board_roles") as mock_load_roles,
        ):
            mock_get_config.return_value = config
            mock_plan = MagicMock()
            mock_plan.selected_work_units = []
            mock_plan_cls.load.return_value = mock_plan
            mock_load_wus.return_value = []

            # Mock data_loader functions (Story 9.2)
            mock_load_profile.return_value = test_profile
            mock_load_certs.return_value = []
            mock_load_edu.return_value = []
            mock_load_highlights.return_value = []
            mock_load_pubs.return_value = []
            mock_load_roles.return_value = []

            with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
                f.write("version: '1.0.0'\njd_hash: abc\nselected_work_units: []\n")
                f.write("selection_count: 0\ntop_k: 8\nranker_version: test\n")
                f.write("created_at: '2024-01-01T00:00:00'\n")
                plan_path = f.name

            try:
                runner = CliRunner()
                runner.invoke(main, ["build", "--plan", plan_path])

                # Verify _generate_outputs was called with ResumeData containing summary
                assert mock_gen.called
                call_kwargs = mock_gen.call_args.kwargs
                resume_data = call_kwargs["resume"]
                assert resume_data.summary == "Experienced engineer with 10+ years..."
            finally:
                PathLib(plan_path).unlink()


class TestProfileLoadingFromConfig:
    """Test profile loading from config files."""

    def test_profile_loads_from_yaml(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Profile should load from .resume.yaml file."""
        reset_config()
        config_file = tmp_path / ".resume.yaml"
        config_file.write_text(
            """
profile:
  name: "Test User"
  email: "test@example.com"
  phone: "555-123-4567"
  location: "Austin, TX"
  title: "Senior Engineer"
"""
        )
        monkeypatch.chdir(tmp_path)
        with patch.dict("os.environ", {}, clear=True):
            config = get_config()
            assert config.profile.name == "Test User"
            assert config.profile.email == "test@example.com"
            assert config.profile.phone == "555-123-4567"
            assert config.profile.location == "Austin, TX"
            assert config.profile.title == "Senior Engineer"

    def test_profile_loads_url_fields_from_yaml(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Profile URL fields should load and validate from YAML."""
        reset_config()
        config_file = tmp_path / ".resume.yaml"
        config_file.write_text(
            """
profile:
  name: "Test User"
  linkedin: "https://linkedin.com/in/testuser"
  github: "https://github.com/testuser"
  website: "https://testuser.dev"
"""
        )
        monkeypatch.chdir(tmp_path)
        with patch.dict("os.environ", {}, clear=True):
            config = get_config()
            assert config.profile.name == "Test User"
            assert str(config.profile.linkedin) == "https://linkedin.com/in/testuser"
            assert str(config.profile.github) == "https://github.com/testuser"
            assert str(config.profile.website) == "https://testuser.dev/"

    def test_profile_defaults_when_not_in_config(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Profile should be None when not in config file (Story 9.2).

        Note: Access profile via data_loader for actual usage.
        """
        reset_config()
        config_file = tmp_path / ".resume.yaml"
        config_file.write_text("output_dir: ./dist\n")
        monkeypatch.chdir(tmp_path)
        with patch.dict("os.environ", {}, clear=True):
            config = get_config()
            # Story 9.2: config.profile is None when not in config
            # Use data_loader for actual access
            assert config.profile is None

    def test_profile_partial_config(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Profile should handle partial configuration."""
        reset_config()
        config_file = tmp_path / ".resume.yaml"
        config_file.write_text(
            """
profile:
  name: "Partial User"
  # Only name configured, rest defaults
"""
        )
        monkeypatch.chdir(tmp_path)
        with patch.dict("os.environ", {}, clear=True):
            config = get_config()
            assert config.profile.name == "Partial User"
            assert config.profile.email is None
            assert config.profile.linkedin is None
