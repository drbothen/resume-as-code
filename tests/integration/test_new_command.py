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


class TestFromMemoryMode:
    """Tests for --from-memory quick capture mode (Story 2.4)."""

    def test_from_memory_uses_minimal_archetype(
        self, runner: CliRunner, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """--from-memory should use minimal archetype (AC #1)."""
        monkeypatch.chdir(tmp_path)

        result = runner.invoke(
            main,
            ["new", "work-unit", "--from-memory", "--title", "Quick win", "--no-edit"],
        )

        assert result.exit_code == 0, f"Command failed: {result.output}"
        files = list((tmp_path / "work-units").glob("*.yaml"))
        assert len(files) == 1
        content = files[0].read_text()
        # Minimal archetype has confidence: medium
        assert "confidence: medium" in content

    def test_from_memory_essential_fields_only(
        self, runner: CliRunner, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """--from-memory should scaffold only essential fields (AC #2)."""
        monkeypatch.chdir(tmp_path)

        result = runner.invoke(
            main,
            ["new", "work-unit", "--from-memory", "--title", "Quick win", "--no-edit"],
        )

        assert result.exit_code == 0
        files = list((tmp_path / "work-units").glob("*.yaml"))
        content = files[0].read_text()

        # Essential fields should be present
        assert "title:" in content
        assert "problem:" in content
        assert "statement:" in content
        assert "actions:" in content
        assert "outcome:" in content
        assert "result:" in content

        # Optional fields should be commented out
        assert "# time_started:" in content
        assert "# time_ended:" in content
        assert "# skills_demonstrated:" in content
        assert "# evidence:" in content

    def test_from_memory_prefills_title(
        self, runner: CliRunner, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """--from-memory --title should pre-fill the title (AC #3)."""
        monkeypatch.chdir(tmp_path)

        result = runner.invoke(
            main,
            ["new", "work-unit", "--from-memory", "--title", "Quick win", "--no-edit"],
        )

        assert result.exit_code == 0
        files = list((tmp_path / "work-units").glob("*.yaml"))
        content = files[0].read_text()
        assert 'title: "Quick win"' in content

    def test_from_memory_skips_archetype_prompt(
        self, runner: CliRunner, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """--from-memory should skip archetype selection (AC #1)."""
        monkeypatch.chdir(tmp_path)

        result = runner.invoke(
            main,
            ["new", "work-unit", "--from-memory", "--title", "Quick win", "--no-edit"],
        )

        assert result.exit_code == 0
        # Should NOT show archetype selection prompt
        assert "Select an archetype:" not in result.output

    def test_from_memory_no_prompts_with_title(
        self, runner: CliRunner, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """--from-memory --title should open editor immediately without prompts (AC #3)."""
        monkeypatch.chdir(tmp_path)

        result = runner.invoke(
            main,
            ["new", "work-unit", "--from-memory", "--title", "Quick win", "--no-edit"],
        )

        assert result.exit_code == 0
        # Should NOT prompt for anything
        assert "Work Unit title" not in result.output
        assert "Select an archetype:" not in result.output

    def test_from_memory_without_title_prompts_for_title(
        self, runner: CliRunner, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """--from-memory without --title should prompt for quick title."""
        monkeypatch.chdir(tmp_path)

        result = runner.invoke(
            main,
            ["new", "work-unit", "--from-memory", "--no-edit"],
            input="My quick note\n",
        )

        assert result.exit_code == 0
        assert "Quick title" in result.output
        files = list((tmp_path / "work-units").glob("*.yaml"))
        content = files[0].read_text()
        assert "My quick note" in content

    def test_from_memory_json_mode(
        self, runner: CliRunner, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """--from-memory should work with --json mode."""
        monkeypatch.chdir(tmp_path)

        result = runner.invoke(
            main,
            ["--json", "new", "work-unit", "--from-memory", "--title", "Quick win"],
        )

        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["status"] == "success"
        assert data["data"]["archetype"] == "minimal"
        assert "quick-win" in data["data"]["id"]

    def test_from_memory_ignores_archetype_flag(
        self, runner: CliRunner, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """--from-memory should override --archetype flag."""
        monkeypatch.chdir(tmp_path)

        result = runner.invoke(
            main,
            [
                "new",
                "work-unit",
                "--from-memory",
                "--archetype",
                "incident",
                "--title",
                "Quick win",
                "--no-edit",
            ],
        )

        assert result.exit_code == 0
        files = list((tmp_path / "work-units").glob("*.yaml"))
        content = files[0].read_text()
        # Should use minimal, not incident
        assert "confidence: medium" in content

    def test_from_memory_warns_when_archetype_overridden(
        self, runner: CliRunner, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """--from-memory should warn user when --archetype is overridden."""
        monkeypatch.chdir(tmp_path)

        result = runner.invoke(
            main,
            [
                "new",
                "work-unit",
                "--from-memory",
                "--archetype",
                "incident",
                "--title",
                "Quick win",
                "--no-edit",
            ],
        )

        assert result.exit_code == 0
        # Should show warning about override
        assert "--from-memory overrides --archetype=incident" in result.output

    def test_from_memory_opens_editor_by_default(
        self, runner: CliRunner, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """--from-memory --title should attempt to open editor (AC #3)."""
        monkeypatch.chdir(tmp_path)

        # Track if open_in_editor was called
        editor_calls: list[Path] = []

        def mock_open_in_editor(file_path: Path, editor: str) -> None:
            editor_calls.append(file_path)

        monkeypatch.setattr("resume_as_code.commands.new.open_in_editor", mock_open_in_editor)
        monkeypatch.setenv("EDITOR", "vim")

        result = runner.invoke(
            main,
            ["new", "work-unit", "--from-memory", "--title", "Quick win"],
        )

        assert result.exit_code == 0
        # Editor should have been called (AC #3: editor opens immediately)
        assert len(editor_calls) == 1
        assert "quick-win" in str(editor_calls[0])

    def test_from_memory_missing_archetype_error(
        self, runner: CliRunner, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """--from-memory should fail gracefully if minimal archetype is missing."""
        monkeypatch.chdir(tmp_path)

        # Mock load_archetype to simulate missing file
        def mock_load_archetype(name: str) -> str:
            raise FileNotFoundError(f"Archetype not found: {name}")

        monkeypatch.setattr(
            "resume_as_code.services.work_unit_service.load_archetype",
            mock_load_archetype,
        )

        result = runner.invoke(
            main,
            ["new", "work-unit", "--from-memory", "--title", "Quick win", "--no-edit"],
        )

        # Should fail with error, not crash
        assert result.exit_code != 0


class TestNewWorkUnitPositionSelection:
    """Tests for position selection during work unit creation (Story 6.8)."""

    def test_position_id_flag_adds_position_to_file(
        self, runner: CliRunner, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should add position_id to file when --position-id provided."""
        monkeypatch.chdir(tmp_path)

        # Create positions file first
        (tmp_path / "positions.yaml").write_text(
            """schema_version: "4.0.0"
archetype: minimal
positions:
  pos-techcorp-engineer:
    employer: TechCorp
    title: Engineer
    start_date: "2022-01"
"""
        )

        result = runner.invoke(
            main,
            [
                "new",
                "work-unit",
                "--archetype",
                "greenfield",
                "--title",
                "Test Project",
                "--position-id",
                "pos-techcorp-engineer",
                "--no-edit",
            ],
        )

        assert result.exit_code == 0, f"Command failed: {result.output}"
        files = list((tmp_path / "work-units").glob("*.yaml"))
        content = files[0].read_text()
        assert 'position_id: "pos-techcorp-engineer"' in content

    def test_position_id_in_json_output(
        self, runner: CliRunner, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should include position_id in JSON output."""
        monkeypatch.chdir(tmp_path)

        # Create position first (required since AC#3 validates position ID exists)
        (tmp_path / "positions.yaml").write_text(
            """schema_version: "4.0.0"
archetype: minimal
positions:
  pos-test:
    employer: "Test Corp"
    title: "Engineer"
    start_date: "2022-01"
"""
        )

        result = runner.invoke(
            main,
            [
                "--json",
                "new",
                "work-unit",
                "--archetype",
                "incident",
                "--title",
                "Test",
                "--position-id",
                "pos-test",
            ],
        )

        assert result.exit_code == 0, f"Failed: {result.output}"
        data = json.loads(result.output)
        assert data["data"]["position_id"] == "pos-test"

    def test_interactive_position_selection_shows_positions(
        self, runner: CliRunner, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should show position selection menu when positions exist."""
        monkeypatch.chdir(tmp_path)

        (tmp_path / "positions.yaml").write_text(
            """schema_version: "4.0.0"
archetype: minimal
positions:
  pos-techcorp-senior:
    employer: TechCorp
    title: Senior Engineer
    start_date: "2022-01"
"""
        )

        # Select "No position" (last option)
        # Options: 1. Position, 2. Create new..., 3. No position
        result = runner.invoke(
            main,
            ["new", "work-unit", "--archetype", "greenfield", "--title", "Test", "--no-edit"],
            input="3\n",  # "No position" is option 3 when 1 position exists
        )

        assert result.exit_code == 0
        assert "Select Position" in result.output
        assert "Senior Engineer at TechCorp" in result.output

    def test_interactive_position_selection_with_selection(
        self, runner: CliRunner, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should add position_id when user selects a position."""
        monkeypatch.chdir(tmp_path)

        (tmp_path / "positions.yaml").write_text(
            """schema_version: "4.0.0"
archetype: minimal
positions:
  pos-techcorp-senior:
    employer: TechCorp
    title: Senior Engineer
    start_date: "2022-01"
"""
        )

        # Select first position (option 1)
        result = runner.invoke(
            main,
            ["new", "work-unit", "--archetype", "greenfield", "--title", "Test", "--no-edit"],
            input="1\n",  # Select first position
        )

        assert result.exit_code == 0
        files = list((tmp_path / "work-units").glob("*.yaml"))
        content = files[0].read_text()
        assert 'position_id: "pos-techcorp-senior"' in content

    def test_no_position_selection_when_quiet(
        self, runner: CliRunner, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should skip position prompt in quiet mode."""
        monkeypatch.chdir(tmp_path)

        (tmp_path / "positions.yaml").write_text(
            """schema_version: "4.0.0"
archetype: minimal
positions:
  pos-test:
    employer: Test
    title: Dev
    start_date: "2022-01"
"""
        )

        result = runner.invoke(
            main,
            ["--quiet", "new", "work-unit", "--archetype", "greenfield", "--title", "Test"],
        )

        assert result.exit_code == 0
        assert "Select Position" not in result.output

    def test_no_position_selection_when_json(
        self, runner: CliRunner, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should skip position prompt in JSON mode."""
        monkeypatch.chdir(tmp_path)

        (tmp_path / "positions.yaml").write_text(
            """schema_version: "4.0.0"
archetype: minimal
positions:
  pos-test:
    employer: Test
    title: Dev
    start_date: "2022-01"
"""
        )

        result = runner.invoke(
            main,
            ["--json", "new", "work-unit", "--archetype", "greenfield", "--title", "Test"],
        )

        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "position_id" not in data["data"]  # Not added when not provided
