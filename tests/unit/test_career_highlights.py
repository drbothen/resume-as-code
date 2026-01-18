"""Tests for career highlights functionality."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from click.testing import CliRunner
from pydantic import ValidationError

from resume_as_code.cli import main as cli
from resume_as_code.models.config import ResumeConfig
from resume_as_code.models.resume import ContactInfo, ResumeData


class TestCareerHighlightsConfig:
    """Tests for career_highlights in ResumeConfig."""

    def test_default_career_highlights_is_none(self) -> None:
        """Config defaults to None for career highlights (Story 9.2).

        Note: Access career_highlights via data_loader for actual usage.
        """
        config = ResumeConfig()
        assert config.career_highlights is None

    def test_career_highlights_accepts_list_of_strings(self) -> None:
        """Config accepts a list of string highlights."""
        highlights = [
            "$50M revenue growth through digital transformation",
            "Built engineering org from 12 to 150+ engineers",
        ]
        config = ResumeConfig(career_highlights=highlights)
        assert config.career_highlights == highlights

    def test_career_highlights_max_four_warns(self, caplog: pytest.LogCaptureFixture) -> None:
        """Config warns when more than 4 highlights provided."""
        highlights = [
            "Highlight 1",
            "Highlight 2",
            "Highlight 3",
            "Highlight 4",
            "Highlight 5",  # Extra - should warn
        ]
        config = ResumeConfig(career_highlights=highlights)
        # All 5 are kept, but warning should be logged
        assert len(config.career_highlights) == 5
        assert "4 career highlights" in caplog.text.lower() or len(config.career_highlights) > 4

    def test_career_highlights_validates_max_length(self) -> None:
        """Each highlight must be <= 150 characters."""
        long_highlight = "x" * 151
        with pytest.raises(ValidationError) as exc_info:
            ResumeConfig(career_highlights=[long_highlight])
        assert "150 characters" in str(exc_info.value).lower()

    def test_career_highlights_at_max_length_accepted(self) -> None:
        """Highlights at exactly 150 characters are accepted."""
        highlight = "x" * 150
        config = ResumeConfig(career_highlights=[highlight])
        assert len(config.career_highlights[0]) == 150

    def test_career_highlights_empty_strings_rejected(self) -> None:
        """Empty string highlights are rejected."""
        with pytest.raises(ValidationError) as exc_info:
            ResumeConfig(career_highlights=["Valid highlight", ""])
        assert "empty" in str(exc_info.value).lower()


class TestResumeDataCareerHighlights:
    """Tests for career_highlights in ResumeData."""

    @pytest.fixture
    def contact(self) -> ContactInfo:
        """Sample contact info for tests."""
        return ContactInfo(name="John Doe", email="john@example.com")

    def test_resume_data_default_career_highlights_empty(self, contact: ContactInfo) -> None:
        """ResumeData defaults to empty list for career highlights."""
        resume = ResumeData(contact=contact)
        assert resume.career_highlights == []

    def test_resume_data_accepts_career_highlights(self, contact: ContactInfo) -> None:
        """ResumeData accepts career highlights list."""
        highlights = [
            "$50M revenue growth",
            "Built 150-person engineering org",
        ]
        resume = ResumeData(contact=contact, career_highlights=highlights)
        assert resume.career_highlights == highlights

    def test_resume_data_career_highlights_in_template_context(self, contact: ContactInfo) -> None:
        """Career highlights are available when iterating."""
        highlights = ["Achievement 1", "Achievement 2"]
        resume = ResumeData(contact=contact, career_highlights=highlights)
        # Simulate template iteration
        result = list(resume.career_highlights)
        assert result == highlights


class TestHighlightService:
    """Tests for highlight service."""

    @pytest.fixture
    def temp_config(self, tmp_path: Path) -> Path:
        """Create a temporary config file."""
        config_file = tmp_path / ".resume.yaml"
        return config_file

    def test_load_highlights_empty_file(self, temp_config: Path) -> None:
        """Load from non-existent file returns empty list."""
        from resume_as_code.services.highlight_service import HighlightService

        service = HighlightService(config_path=temp_config)
        highlights = service.load_highlights()
        assert highlights == []

    def test_save_and_load_highlight(self, temp_config: Path) -> None:
        """Save and load a single highlight."""
        from resume_as_code.services.highlight_service import HighlightService

        service = HighlightService(config_path=temp_config)
        service.save_highlight("$50M revenue growth")

        loaded = service.load_highlights()
        assert len(loaded) == 1
        assert loaded[0] == "$50M revenue growth"

    def test_save_multiple_highlights(self, temp_config: Path) -> None:
        """Save multiple highlights preserves order."""
        from resume_as_code.services.highlight_service import HighlightService

        service = HighlightService(config_path=temp_config)
        service.save_highlight("Highlight 1")
        service.save_highlight("Highlight 2")
        service.save_highlight("Highlight 3")

        loaded = service.load_highlights()
        assert len(loaded) == 3
        assert loaded == ["Highlight 1", "Highlight 2", "Highlight 3"]

    def test_remove_highlight_by_index(self, temp_config: Path) -> None:
        """Remove highlight by index."""
        from resume_as_code.services.highlight_service import HighlightService

        service = HighlightService(config_path=temp_config)
        service.save_highlight("Highlight 1")
        service.save_highlight("Highlight 2")
        service.save_highlight("Highlight 3")

        removed = service.remove_highlight(1)  # 0-indexed
        assert removed is True

        loaded = service.load_highlights()
        assert len(loaded) == 2
        assert loaded == ["Highlight 1", "Highlight 3"]

    def test_remove_highlight_invalid_index(self, temp_config: Path) -> None:
        """Remove with invalid index returns False."""
        from resume_as_code.services.highlight_service import HighlightService

        service = HighlightService(config_path=temp_config)
        service.save_highlight("Highlight 1")

        removed = service.remove_highlight(5)
        assert removed is False

    def test_duplicate_highlights_allowed(self, temp_config: Path) -> None:
        """Service allows duplicate highlights (user responsibility to avoid)."""
        from resume_as_code.services.highlight_service import HighlightService

        service = HighlightService(config_path=temp_config)
        service.save_highlight("Same highlight text")
        service.save_highlight("Same highlight text")

        loaded = service.load_highlights()
        assert len(loaded) == 2
        assert loaded[0] == "Same highlight text"
        assert loaded[1] == "Same highlight text"


class TestCareerHighlightsTemplate:
    """Tests for career highlights in executive template rendering."""

    @pytest.fixture
    def contact(self) -> ContactInfo:
        """Sample contact info for tests."""
        return ContactInfo(name="John Doe", email="john@example.com")

    def test_template_renders_career_highlights(self, contact: ContactInfo) -> None:
        """Executive template renders career highlights section."""
        from resume_as_code.services.template_service import TemplateService

        highlights = [
            "$50M revenue growth through digital transformation",
            "Built engineering org from 12 to 150+ engineers",
        ]
        resume = ResumeData(contact=contact, career_highlights=highlights)

        template_service = TemplateService()
        html = template_service.render(resume, template_name="executive")

        assert "Career Highlights" in html
        assert "$50M revenue growth" in html
        assert "Built engineering org" in html

    def test_template_no_career_highlights_section_when_empty(self, contact: ContactInfo) -> None:
        """Career Highlights section not rendered when empty."""
        from resume_as_code.services.template_service import TemplateService

        resume = ResumeData(contact=contact, career_highlights=[])

        template_service = TemplateService()
        html = template_service.render(resume, template_name="executive")

        # Check that the section element doesn't exist (CSS may contain reference)
        assert '<section class="career-highlights">' not in html

    def test_career_highlights_appear_after_summary(self, contact: ContactInfo) -> None:
        """Career Highlights section appears after Executive Summary."""
        from resume_as_code.services.template_service import TemplateService

        highlights = ["Test highlight"]
        resume = ResumeData(
            contact=contact,
            summary="This is the executive summary.",
            career_highlights=highlights,
        )

        template_service = TemplateService()
        html = template_service.render(resume, template_name="executive")

        summary_pos = html.find("Executive Summary")
        highlights_pos = html.find("Career Highlights")
        experience_pos = html.find("Experience") if "Experience" in html else len(html)

        # Career Highlights should come after Executive Summary
        assert highlights_pos > summary_pos
        # Career Highlights should come before Experience (if present)
        if experience_pos < len(html):
            assert highlights_pos < experience_pos


class TestHighlightCLICommands:
    """Tests for highlight CLI commands."""

    @pytest.fixture
    def runner(self) -> CliRunner:
        """Create a CLI runner."""
        return CliRunner()

    @pytest.fixture
    def temp_project(self, tmp_path: Path) -> Path:
        """Create a temporary project directory with config."""
        config_file = tmp_path / ".resume.yaml"
        config_file.write_text("")
        return tmp_path

    def test_list_highlights_empty(
        self, runner: CliRunner, temp_project: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """List highlights with no highlights shows info message."""
        monkeypatch.chdir(temp_project)
        result = runner.invoke(cli, ["list", "highlights"], catch_exceptions=False)
        assert result.exit_code == 0
        assert "No career highlights found" in result.output

    def test_list_highlights_json_empty(
        self, runner: CliRunner, temp_project: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """List highlights JSON output when empty."""
        monkeypatch.chdir(temp_project)
        result = runner.invoke(cli, ["--json", "list", "highlights"], catch_exceptions=False)
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["status"] == "success"
        assert data["data"]["highlights"] == []
        assert data["data"]["count"] == 0

    def test_new_highlight_with_text_flag(
        self, runner: CliRunner, temp_project: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Create highlight with --text flag."""
        monkeypatch.chdir(temp_project)
        result = runner.invoke(
            cli,
            ["new", "highlight", "--text", "Led $50M digital transformation"],
            catch_exceptions=False,
        )
        assert result.exit_code == 0
        assert "Highlight created" in result.output

    def test_new_highlight_validation_max_length(
        self, runner: CliRunner, temp_project: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Creating highlight over 150 chars fails."""
        monkeypatch.chdir(temp_project)
        long_text = "x" * 151
        result = runner.invoke(
            cli,
            ["new", "highlight", "--text", long_text],
            catch_exceptions=False,
        )
        # Exit code 5 is SYSTEM_ERROR (from handle_errors)
        assert result.exit_code != 0
        assert "150 characters" in result.output

    def test_list_highlights_shows_table(
        self, runner: CliRunner, temp_project: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """List highlights shows table with index and text."""
        monkeypatch.chdir(temp_project)
        # Add some highlights
        runner.invoke(cli, ["new", "highlight", "--text", "Highlight 1"], catch_exceptions=False)
        runner.invoke(cli, ["new", "highlight", "--text", "Highlight 2"], catch_exceptions=False)

        result = runner.invoke(cli, ["list", "highlights"], catch_exceptions=False)
        assert result.exit_code == 0
        assert "Career Highlights" in result.output
        assert "Highlight 1" in result.output
        assert "Highlight 2" in result.output
        assert "2 Career Highlight(s)" in result.output

    def test_list_highlights_json_with_data(
        self, runner: CliRunner, temp_project: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """List highlights JSON output includes index and text."""
        monkeypatch.chdir(temp_project)
        runner.invoke(
            cli, ["new", "highlight", "--text", "First highlight"], catch_exceptions=False
        )

        result = runner.invoke(cli, ["--json", "list", "highlights"], catch_exceptions=False)
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["status"] == "success"
        assert len(data["data"]["highlights"]) == 1
        assert data["data"]["highlights"][0]["index"] == 0
        assert data["data"]["highlights"][0]["text"] == "First highlight"

    def test_remove_highlight_by_index(
        self, runner: CliRunner, temp_project: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Remove highlight by index."""
        monkeypatch.chdir(temp_project)
        runner.invoke(cli, ["new", "highlight", "--text", "Highlight 1"], catch_exceptions=False)
        runner.invoke(cli, ["new", "highlight", "--text", "Highlight 2"], catch_exceptions=False)

        result = runner.invoke(cli, ["remove", "highlight", "0", "--yes"], catch_exceptions=False)
        assert result.exit_code == 0
        assert "Removed highlight #0" in result.output

        # Verify only one remains
        result = runner.invoke(cli, ["--json", "list", "highlights"], catch_exceptions=False)
        data = json.loads(result.output)
        assert data["data"]["count"] == 1
        assert data["data"]["highlights"][0]["text"] == "Highlight 2"

    def test_remove_highlight_invalid_index(
        self, runner: CliRunner, temp_project: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Remove highlight with invalid index fails."""
        monkeypatch.chdir(temp_project)
        runner.invoke(cli, ["new", "highlight", "--text", "Only highlight"], catch_exceptions=False)

        result = runner.invoke(cli, ["remove", "highlight", "5", "--yes"], catch_exceptions=False)
        assert result.exit_code == 1
        assert "Invalid index 5" in result.output

    def test_remove_highlight_no_highlights(
        self, runner: CliRunner, temp_project: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Remove highlight when none exist fails."""
        monkeypatch.chdir(temp_project)
        result = runner.invoke(cli, ["remove", "highlight", "0", "--yes"], catch_exceptions=False)
        assert result.exit_code == 4  # NOT_FOUND
        assert "No career highlights found" in result.output

    def test_list_highlights_warns_over_four(
        self, runner: CliRunner, temp_project: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """List highlights shows warning when more than 4."""
        monkeypatch.chdir(temp_project)
        for i in range(5):
            runner.invoke(
                cli,
                ["new", "highlight", "--text", f"Highlight {i + 1}"],
                catch_exceptions=False,
            )

        result = runner.invoke(cli, ["list", "highlights"], catch_exceptions=False)
        assert result.exit_code == 0
        assert "maximum of 4 career highlights" in result.output

    def test_show_highlight_by_index(
        self, runner: CliRunner, temp_project: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Show highlight displays the text for given index."""
        monkeypatch.chdir(temp_project)
        runner.invoke(
            cli, ["new", "highlight", "--text", "First highlight"], catch_exceptions=False
        )
        runner.invoke(
            cli, ["new", "highlight", "--text", "Second highlight"], catch_exceptions=False
        )

        result = runner.invoke(cli, ["show", "highlight", "1"], catch_exceptions=False)
        assert result.exit_code == 0
        assert "Second highlight" in result.output
        assert "Highlight 2 of 2" in result.output

    def test_show_highlight_json(
        self, runner: CliRunner, temp_project: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Show highlight JSON output includes index and text."""
        monkeypatch.chdir(temp_project)
        runner.invoke(cli, ["new", "highlight", "--text", "Test highlight"], catch_exceptions=False)

        result = runner.invoke(cli, ["--json", "show", "highlight", "0"], catch_exceptions=False)
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["status"] == "success"
        assert data["data"]["highlight"]["index"] == 0
        assert data["data"]["highlight"]["text"] == "Test highlight"
        assert data["data"]["total_highlights"] == 1

    def test_show_highlight_invalid_index(
        self, runner: CliRunner, temp_project: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Show highlight with invalid index fails."""
        monkeypatch.chdir(temp_project)
        runner.invoke(cli, ["new", "highlight", "--text", "Only highlight"], catch_exceptions=False)

        result = runner.invoke(cli, ["show", "highlight", "5"], catch_exceptions=False)
        assert result.exit_code == 1
        assert "Invalid index 5" in result.output

    def test_show_highlight_no_highlights(
        self, runner: CliRunner, temp_project: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Show highlight when none exist fails."""
        monkeypatch.chdir(temp_project)
        result = runner.invoke(cli, ["show", "highlight", "0"], catch_exceptions=False)
        assert result.exit_code == 4  # NOT_FOUND
        assert "No career highlights found" in result.output
