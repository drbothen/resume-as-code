"""Integration tests for new work-unit command."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from click.testing import CliRunner

from resume_as_code.cli import main


@pytest.fixture
def runner() -> CliRunner:
    """Provide a Click CLI test runner."""
    return CliRunner()


class TestNewWorkUnitCommand:
    """Tests for resume new work-unit command."""

    def test_creates_file_with_archetype_and_title(
        self, runner: CliRunner, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should create work unit file when archetype and title provided."""
        monkeypatch.chdir(tmp_path)

        result = runner.invoke(
            main,
            [
                "new",
                "work-unit",
                "--archetype",
                "greenfield",
                "--title",
                "Test Project",
                "--no-edit",
            ],
        )

        assert result.exit_code == 0, f"Command failed: {result.output}"
        assert (tmp_path / "work-units").exists()

        files = list((tmp_path / "work-units").glob("*.yaml"))
        assert len(files) == 1
        assert "test-project" in files[0].name

    def test_creates_directory_if_not_exists(
        self, runner: CliRunner, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should create work-units directory if it doesn't exist (AC #4)."""
        monkeypatch.chdir(tmp_path)

        # Ensure directory does not exist
        assert not (tmp_path / "work-units").exists()

        result = runner.invoke(
            main,
            ["new", "work-unit", "--archetype", "incident", "--title", "First Unit", "--no-edit"],
        )

        assert result.exit_code == 0
        assert (tmp_path / "work-units").exists()

    def test_slug_derived_from_title(
        self, runner: CliRunner, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Slug should be derived from title (AC #3)."""
        monkeypatch.chdir(tmp_path)

        result = runner.invoke(
            main,
            [
                "new",
                "work-unit",
                "--archetype",
                "greenfield",
                "--title",
                "My Cool Project",
                "--no-edit",
            ],
        )

        assert result.exit_code == 0
        files = list((tmp_path / "work-units").glob("*.yaml"))
        assert len(files) == 1
        # Slug should be lowercase hyphenated
        assert "my-cool-project" in files[0].name

    def test_json_output_format(
        self, runner: CliRunner, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should output JSON when --json flag used."""
        monkeypatch.chdir(tmp_path)

        result = runner.invoke(
            main,
            ["--json", "new", "work-unit", "--archetype", "incident", "--title", "Outage"],
        )

        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["status"] == "success"
        assert data["data"]["archetype"] == "incident"
        assert "outage" in data["data"]["id"]
        assert "file" in data["data"]

    def test_file_naming_convention(
        self, runner: CliRunner, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """File should be named wu-YYYY-MM-DD-<slug>.yaml (AC #1)."""
        monkeypatch.chdir(tmp_path)

        result = runner.invoke(
            main,
            ["new", "work-unit", "--archetype", "greenfield", "--title", "Test", "--no-edit"],
        )

        assert result.exit_code == 0
        files = list((tmp_path / "work-units").glob("*.yaml"))
        assert len(files) == 1
        # Check naming pattern: wu-YYYY-MM-DD-slug.yaml
        filename = files[0].name
        assert filename.startswith("wu-")
        assert filename.endswith(".yaml")
        # Has date component (YYYY-MM-DD pattern)
        parts = filename.replace(".yaml", "").split("-")
        assert len(parts) >= 5  # wu, YYYY, MM, DD, slug

    def test_no_archetype_prompt_when_provided(
        self, runner: CliRunner, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should not prompt for archetype when --archetype provided (AC #2)."""
        monkeypatch.chdir(tmp_path)

        # Using --json ensures no interactive prompts
        result = runner.invoke(
            main,
            ["--json", "new", "work-unit", "--archetype", "incident", "--title", "Test"],
        )

        assert result.exit_code == 0
        # Command should complete without any prompts
        data = json.loads(result.output)
        assert data["data"]["archetype"] == "incident"

    def test_quiet_mode_no_output(
        self, runner: CliRunner, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should produce no output in quiet mode."""
        monkeypatch.chdir(tmp_path)

        result = runner.invoke(
            main,
            ["--quiet", "new", "work-unit", "--archetype", "greenfield", "--title", "Quiet Test"],
        )

        assert result.exit_code == 0
        # In quiet mode, should have no output
        assert result.output.strip() == ""


class TestNewWorkUnitInteractive:
    """Tests for interactive mode prompts."""

    def test_interactive_archetype_selection(
        self, runner: CliRunner, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should allow interactive archetype selection via numbered menu."""
        monkeypatch.chdir(tmp_path)

        # Input "2" to select second archetype, then provide title
        result = runner.invoke(
            main,
            ["new", "work-unit", "--title", "Test Project", "--no-edit"],
            input="2\n",  # Select archetype #2
        )

        assert result.exit_code == 0
        assert "Select an archetype:" in result.output
        files = list((tmp_path / "work-units").glob("*.yaml"))
        assert len(files) == 1

    def test_interactive_archetype_default_selection(
        self, runner: CliRunner, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should use default archetype when Enter pressed with no input."""
        monkeypatch.chdir(tmp_path)

        # Press Enter to accept default (greenfield)
        result = runner.invoke(
            main,
            ["new", "work-unit", "--title", "Default Test", "--no-edit"],
            input="\n",  # Accept default
        )

        assert result.exit_code == 0
        files = list((tmp_path / "work-units").glob("*.yaml"))
        assert len(files) == 1
        content = files[0].read_text()
        # Greenfield template has time_started field
        assert "time_started:" in content

    def test_interactive_title_prompt(
        self, runner: CliRunner, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should prompt for title when not provided."""
        monkeypatch.chdir(tmp_path)

        # Input: accept default archetype, then provide title
        result = runner.invoke(
            main,
            ["new", "work-unit", "--archetype", "greenfield", "--no-edit"],
            input="My Interactive Title\n",
        )

        assert result.exit_code == 0
        assert "Work Unit title" in result.output
        files = list((tmp_path / "work-units").glob("*.yaml"))
        assert len(files) == 1
        content = files[0].read_text()
        assert "My Interactive Title" in content

    def test_full_interactive_flow(
        self, runner: CliRunner, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should handle full interactive flow (archetype + title)."""
        monkeypatch.chdir(tmp_path)

        # Input: select archetype #1, then provide title
        result = runner.invoke(
            main,
            ["new", "work-unit", "--no-edit"],
            input="1\nFully Interactive Project\n",
        )

        assert result.exit_code == 0
        assert "Select an archetype:" in result.output
        files = list((tmp_path / "work-units").glob("*.yaml"))
        assert len(files) == 1
        assert "fully-interactive-project" in files[0].name


class TestNewWorkUnitArchetypes:
    """Test different archetype templates."""

    def test_incident_archetype(
        self, runner: CliRunner, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should create file with incident archetype."""
        monkeypatch.chdir(tmp_path)

        result = runner.invoke(
            main,
            ["new", "work-unit", "--archetype", "incident", "--title", "P1 Outage", "--no-edit"],
        )

        assert result.exit_code == 0
        files = list((tmp_path / "work-units").glob("*.yaml"))
        content = files[0].read_text()
        assert "problem:" in content
        assert "actions:" in content

    def test_greenfield_archetype(
        self, runner: CliRunner, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should create file with greenfield archetype."""
        monkeypatch.chdir(tmp_path)

        result = runner.invoke(
            main,
            [
                "new",
                "work-unit",
                "--archetype",
                "greenfield",
                "--title",
                "New Feature",
                "--no-edit",
            ],
        )

        assert result.exit_code == 0
        files = list((tmp_path / "work-units").glob("*.yaml"))
        content = files[0].read_text()
        assert "time_started:" in content
        assert "time_ended:" in content

    def test_leadership_archetype(
        self, runner: CliRunner, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should create file with leadership archetype."""
        monkeypatch.chdir(tmp_path)

        result = runner.invoke(
            main,
            ["new", "work-unit", "--archetype", "leadership", "--title", "Team Lead", "--no-edit"],
        )

        assert result.exit_code == 0
        files = list((tmp_path / "work-units").glob("*.yaml"))
        content = files[0].read_text()
        assert "scope:" in content
