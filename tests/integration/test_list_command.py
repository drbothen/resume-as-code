"""Integration tests for list command."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from click.testing import CliRunner

from resume_as_code.cli import main


def _create_work_unit(
    path: Path,
    wu_id: str,
    title: str,
    tags: list[str] | None = None,
    confidence: str = "high",
) -> None:
    """Helper to create a Work Unit file."""
    tags = tags or []
    tags_yaml = "\n".join([f'  - "{t}"' for t in tags]) if tags else ""
    tags_section = f"tags:\n{tags_yaml}" if tags else "tags: []"

    content = f"""\
schema_version: "4.0.0"
archetype: minimal
id: "{wu_id}"
title: "{title}"
problem:
  statement: "Test problem statement that is long enough"
actions:
  - "Test action that is long enough"
outcome:
  result: "Test result that is long enough"
{tags_section}
confidence: {confidence}
"""
    path.write_text(content)


class TestListCommandTableOutput:
    """Tests for list command table output (AC #1)."""

    def test_list_shows_all_work_units(
        self, tmp_path: Path, cli_runner: CliRunner, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should list all Work Units in table format (AC #1)."""
        monkeypatch.chdir(tmp_path)

        work_units = tmp_path / "work-units"
        work_units.mkdir()
        _create_work_unit(work_units / "wu-a.yaml", "wu-2026-01-01-a", "Project A")
        _create_work_unit(work_units / "wu-b.yaml", "wu-2026-01-02-b", "Project B")

        result = cli_runner.invoke(main, ["list"])

        assert result.exit_code == 0
        assert "Project A" in result.output
        assert "Project B" in result.output
        assert "2 Work Unit(s)" in result.output

    def test_list_table_has_required_columns(
        self, tmp_path: Path, cli_runner: CliRunner, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should show columns: ID, Title, Date, Confidence, Tags (AC #1)."""
        monkeypatch.chdir(tmp_path)

        work_units = tmp_path / "work-units"
        work_units.mkdir()
        _create_work_unit(
            work_units / "wu-a.yaml",
            "wu-2026-01-01-test",
            "Test Project",
            tags=["python"],
            confidence="high",
        )

        result = cli_runner.invoke(main, ["list"])

        assert result.exit_code == 0
        # Check column headers or data presence
        # Note: Title may wrap across lines, so check for key parts
        assert "Test" in result.output
        assert "Project" in result.output
        assert "2026-01-01" in result.output
        assert "high" in result.output
        assert "python" in result.output
        assert "Archetype" in result.output  # Story 12.5: AC2 - Archetype column


class TestListCommandJsonOutput:
    """Tests for list command JSON output (AC #2)."""

    def test_list_json_output_structure(
        self, tmp_path: Path, cli_runner: CliRunner, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should output valid JSON array of Work Unit summaries (AC #2)."""
        monkeypatch.chdir(tmp_path)

        work_units = tmp_path / "work-units"
        work_units.mkdir()
        _create_work_unit(work_units / "wu-a.yaml", "wu-2026-01-01-a", "Project A")

        result = cli_runner.invoke(main, ["--json", "list"])

        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["status"] == "success"
        assert data["command"] == "list"
        assert "work_units" in data["data"]
        assert "count" in data["data"]
        assert data["data"]["count"] == 1

    def test_list_json_includes_all_fields(
        self, tmp_path: Path, cli_runner: CliRunner, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should include all fields in JSON (no truncation) (AC #2)."""
        monkeypatch.chdir(tmp_path)

        work_units = tmp_path / "work-units"
        work_units.mkdir()
        _create_work_unit(
            work_units / "wu-a.yaml",
            "wu-2026-01-01-test",
            "Project A",
            tags=["python", "aws", "docker", "k8s"],
            confidence="high",
        )

        result = cli_runner.invoke(main, ["--json", "list"])

        assert result.exit_code == 0
        data = json.loads(result.output)
        wu = data["data"]["work_units"][0]
        assert wu["id"] == "wu-2026-01-01-test"
        assert wu["title"] == "Project A"
        assert wu["confidence"] == "high"
        assert len(wu["tags"]) == 4  # All tags, no truncation


class TestListCommandFiltering:
    """Tests for list command filtering (AC #3, #4, #5)."""

    def test_list_filter_by_tag(
        self, tmp_path: Path, cli_runner: CliRunner, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should filter by tag (AC #3)."""
        monkeypatch.chdir(tmp_path)

        work_units = tmp_path / "work-units"
        work_units.mkdir()
        _create_work_unit(work_units / "wu-a.yaml", "wu-2026-01-01-a", "Python Project", ["python"])
        _create_work_unit(work_units / "wu-b.yaml", "wu-2026-01-02-b", "Java Project", ["java"])

        result = cli_runner.invoke(main, ["list", "--filter", "tag:python"])

        assert result.exit_code == 0
        # Note: Title may wrap across lines, so check for key parts
        assert "Python" in result.output
        assert "Java" not in result.output
        assert "1 Work Unit(s)" in result.output

    def test_list_filter_by_confidence(
        self, tmp_path: Path, cli_runner: CliRunner, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should filter by confidence (AC #4)."""
        monkeypatch.chdir(tmp_path)

        work_units = tmp_path / "work-units"
        work_units.mkdir()
        _create_work_unit(
            work_units / "wu-a.yaml",
            "wu-2026-01-01-a",
            "High Confidence",
            confidence="high",
        )
        _create_work_unit(
            work_units / "wu-b.yaml",
            "wu-2026-01-02-b",
            "Low Confidence",
            confidence="low",
        )

        result = cli_runner.invoke(main, ["list", "--filter", "confidence:high"])

        assert result.exit_code == 0
        # Note: Title may wrap across lines, so check unique identifier
        assert "High" in result.output
        assert "Low" not in result.output
        assert "1 Work Unit(s)" in result.output

    def test_list_filter_free_text_in_date(
        self, tmp_path: Path, cli_runner: CliRunner, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should filter by free text in ID/date (AC #5)."""
        monkeypatch.chdir(tmp_path)

        work_units = tmp_path / "work-units"
        work_units.mkdir()
        _create_work_unit(work_units / "wu-a.yaml", "wu-2026-01-01-a", "Project 2026")
        _create_work_unit(work_units / "wu-b.yaml", "wu-2025-06-15-b", "Project 2025")

        result = cli_runner.invoke(main, ["list", "--filter", "2026"])

        assert result.exit_code == 0
        assert "Project 2026" in result.output
        assert "Project 2025" not in result.output


class TestListCommandMultipleFilters:
    """Tests for multiple filters with AND logic (AC #3, #4, #5 combined)."""

    def test_list_multiple_filters_and_logic(
        self, tmp_path: Path, cli_runner: CliRunner, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should apply multiple filters with AND logic."""
        monkeypatch.chdir(tmp_path)

        work_units = tmp_path / "work-units"
        work_units.mkdir()
        _create_work_unit(
            work_units / "wu-a.yaml",
            "wu-2026-01-01-a",
            "Python High",
            tags=["python"],
            confidence="high",
        )
        _create_work_unit(
            work_units / "wu-b.yaml",
            "wu-2026-01-02-b",
            "Python Low",
            tags=["python"],
            confidence="low",
        )
        _create_work_unit(
            work_units / "wu-c.yaml",
            "wu-2026-01-03-c",
            "Java High",
            tags=["java"],
            confidence="high",
        )

        # Filter by both python AND high confidence
        result = cli_runner.invoke(
            main, ["list", "--filter", "tag:python", "--filter", "confidence:high"]
        )

        assert result.exit_code == 0
        assert "Python High" in result.output
        assert "Python Low" not in result.output
        assert "Java High" not in result.output
        assert "1 Work Unit(s)" in result.output

    def test_list_multiple_filters_no_match(
        self, tmp_path: Path, cli_runner: CliRunner, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Conflicting filters should return empty."""
        monkeypatch.chdir(tmp_path)

        work_units = tmp_path / "work-units"
        work_units.mkdir()
        _create_work_unit(work_units / "wu-a.yaml", "wu-2026-01-01-a", "Python Only", ["python"])

        # Filter by python AND java (impossible match)
        result = cli_runner.invoke(main, ["list", "--filter", "tag:python", "--filter", "tag:java"])

        assert result.exit_code == 0
        assert "0 Work Unit(s)" in result.output


class TestListCommandEmptyState:
    """Tests for list command empty state (AC #6)."""

    def test_list_empty_state_no_directory(
        self, tmp_path: Path, cli_runner: CliRunner, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should show helpful message when no Work Units exist (AC #6)."""
        monkeypatch.chdir(tmp_path)

        result = cli_runner.invoke(main, ["list"])

        assert result.exit_code == 0
        assert "No Work Units found" in result.output
        assert "resume new work-unit" in result.output

    def test_list_empty_state_empty_directory(
        self, tmp_path: Path, cli_runner: CliRunner, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should show helpful message when directory is empty."""
        monkeypatch.chdir(tmp_path)
        (tmp_path / "work-units").mkdir()

        result = cli_runner.invoke(main, ["list"])

        assert result.exit_code == 0
        assert "No Work Units found" in result.output

    def test_list_empty_state_json_output(
        self, tmp_path: Path, cli_runner: CliRunner, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should return empty array in JSON mode (AC #6)."""
        monkeypatch.chdir(tmp_path)

        result = cli_runner.invoke(main, ["--json", "list"])

        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["data"]["work_units"] == []
        assert data["data"]["count"] == 0


class TestListCommandSorting:
    """Tests for list command sorting (AC #7)."""

    def test_list_sort_by_date_default(
        self, tmp_path: Path, cli_runner: CliRunner, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should sort by date newest first by default (AC #7)."""
        monkeypatch.chdir(tmp_path)

        work_units = tmp_path / "work-units"
        work_units.mkdir()
        _create_work_unit(work_units / "wu-old.yaml", "wu-2024-01-01-old", "Old Project")
        _create_work_unit(work_units / "wu-new.yaml", "wu-2026-01-01-new", "New Project")

        result = cli_runner.invoke(main, ["list"])

        assert result.exit_code == 0
        # New Project should appear before Old Project
        new_pos = result.output.find("New Project")
        old_pos = result.output.find("Old Project")
        assert new_pos < old_pos

    def test_list_sort_by_title(
        self, tmp_path: Path, cli_runner: CliRunner, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should sort by title alphabetically."""
        monkeypatch.chdir(tmp_path)

        work_units = tmp_path / "work-units"
        work_units.mkdir()
        _create_work_unit(work_units / "wu-z.yaml", "wu-2026-01-01-z", "Zebra Project")
        _create_work_unit(work_units / "wu-a.yaml", "wu-2026-01-02-a", "Alpha Project")

        result = cli_runner.invoke(main, ["list", "--sort", "title"])

        assert result.exit_code == 0
        alpha_pos = result.output.find("Alpha Project")
        zebra_pos = result.output.find("Zebra Project")
        assert alpha_pos < zebra_pos

    def test_list_sort_reverse(
        self, tmp_path: Path, cli_runner: CliRunner, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should reverse sort order with --reverse flag."""
        monkeypatch.chdir(tmp_path)

        work_units = tmp_path / "work-units"
        work_units.mkdir()
        _create_work_unit(work_units / "wu-old.yaml", "wu-2024-01-01-old", "Old Project")
        _create_work_unit(work_units / "wu-new.yaml", "wu-2026-01-01-new", "New Project")

        result = cli_runner.invoke(main, ["list", "--reverse"])

        assert result.exit_code == 0
        # Old Project should appear before New Project (reversed)
        new_pos = result.output.find("New Project")
        old_pos = result.output.find("Old Project")
        assert old_pos < new_pos


def _create_work_unit_with_archetype(
    path: Path,
    wu_id: str,
    title: str,
    archetype: str = "minimal",
    tags: list[str] | None = None,
    confidence: str = "high",
) -> None:
    """Helper to create a Work Unit file with specific archetype."""
    tags = tags or []
    tags_yaml = "\n".join([f'  - "{t}"' for t in tags]) if tags else ""
    tags_section = f"tags:\n{tags_yaml}" if tags else "tags: []"

    content = f"""\
schema_version: "4.0.0"
archetype: {archetype}
id: "{wu_id}"
title: "{title}"
problem:
  statement: "Test problem statement that is long enough"
actions:
  - "Test action that is long enough"
outcome:
  result: "Test result that is long enough"
{tags_section}
confidence: {confidence}
"""
    path.write_text(content)


class TestListCommandArchetypeFilter:
    """Tests for archetype filtering (Story 12.5 AC1, AC5)."""

    def test_list_filter_by_archetype(
        self, tmp_path: Path, cli_runner: CliRunner, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should filter by archetype (AC1)."""
        monkeypatch.chdir(tmp_path)

        work_units = tmp_path / "work-units"
        work_units.mkdir()
        _create_work_unit_with_archetype(
            work_units / "wu-a.yaml", "wu-2026-01-01-a", "Incident Response", archetype="incident"
        )
        _create_work_unit_with_archetype(
            work_units / "wu-b.yaml", "wu-2026-01-02-b", "New Feature", archetype="greenfield"
        )

        result = cli_runner.invoke(main, ["list", "--filter", "archetype:incident"])

        assert result.exit_code == 0
        assert "Incident" in result.output
        assert "New Feature" not in result.output
        assert "1 Work Unit(s)" in result.output

    def test_list_filter_by_archetype_case_insensitive(
        self, tmp_path: Path, cli_runner: CliRunner, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should filter by archetype case-insensitively (AC5)."""
        monkeypatch.chdir(tmp_path)

        work_units = tmp_path / "work-units"
        work_units.mkdir()
        _create_work_unit_with_archetype(
            work_units / "wu-a.yaml", "wu-2026-01-01-a", "Incident Response", archetype="incident"
        )

        # Test uppercase filter
        result = cli_runner.invoke(main, ["list", "--filter", "archetype:INCIDENT"])

        assert result.exit_code == 0
        assert "Incident" in result.output
        assert "1 Work Unit(s)" in result.output


class TestListCommandArchetypeStats:
    """Tests for archetype statistics (Story 12.5 AC3)."""

    def test_list_stats_shows_archetype_distribution(
        self, tmp_path: Path, cli_runner: CliRunner, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should show archetype distribution with --stats flag (AC3)."""
        monkeypatch.chdir(tmp_path)

        work_units = tmp_path / "work-units"
        work_units.mkdir()
        _create_work_unit_with_archetype(
            work_units / "wu-a.yaml", "wu-2026-01-01-a", "Incident 1", archetype="incident"
        )
        _create_work_unit_with_archetype(
            work_units / "wu-b.yaml", "wu-2026-01-02-b", "Incident 2", archetype="incident"
        )
        _create_work_unit_with_archetype(
            work_units / "wu-c.yaml", "wu-2026-01-03-c", "New Feature", archetype="greenfield"
        )

        result = cli_runner.invoke(main, ["list", "--stats"])

        assert result.exit_code == 0
        assert "Archetype Distribution" in result.output
        assert "incident" in result.output
        assert "greenfield" in result.output
        assert "Total: 3 work units" in result.output

    def test_list_stats_json_includes_archetype_stats(
        self, tmp_path: Path, cli_runner: CliRunner, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """JSON output with --stats should include archetype_stats field."""
        monkeypatch.chdir(tmp_path)

        work_units = tmp_path / "work-units"
        work_units.mkdir()
        _create_work_unit_with_archetype(
            work_units / "wu-a.yaml", "wu-2026-01-01-a", "Incident", archetype="incident"
        )
        _create_work_unit_with_archetype(
            work_units / "wu-b.yaml", "wu-2026-01-02-b", "Feature", archetype="greenfield"
        )

        result = cli_runner.invoke(main, ["--json", "list", "--stats"])

        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "archetype_stats" in data["data"]
        assert data["data"]["archetype_stats"]["incident"] == 1
        assert data["data"]["archetype_stats"]["greenfield"] == 1


class TestListCommandArchetypeInOutput:
    """Tests for archetype in output (Story 12.5 AC2, AC4)."""

    def test_list_table_shows_archetype_column(
        self, tmp_path: Path, cli_runner: CliRunner, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Table output should include Archetype column (AC2)."""
        monkeypatch.chdir(tmp_path)

        work_units = tmp_path / "work-units"
        work_units.mkdir()
        _create_work_unit_with_archetype(
            work_units / "wu-a.yaml", "wu-2026-01-01-a", "Test Project", archetype="incident"
        )

        result = cli_runner.invoke(main, ["list"])

        assert result.exit_code == 0
        assert "Archetype" in result.output
        assert "incident" in result.output

    def test_list_json_includes_archetype_field(
        self, tmp_path: Path, cli_runner: CliRunner, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """JSON output should include archetype field for each work unit (AC4)."""
        monkeypatch.chdir(tmp_path)

        work_units = tmp_path / "work-units"
        work_units.mkdir()
        _create_work_unit_with_archetype(
            work_units / "wu-a.yaml", "wu-2026-01-01-a", "Test Project", archetype="incident"
        )

        result = cli_runner.invoke(main, ["--json", "list"])

        assert result.exit_code == 0
        data = json.loads(result.output)
        assert len(data["data"]["work_units"]) == 1
        wu = data["data"]["work_units"][0]
        assert "archetype" in wu
        assert wu["archetype"] == "incident"
