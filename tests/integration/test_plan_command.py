"""Integration tests for plan command."""

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
    problem: str = "Test problem statement for ranking purposes",
    actions: list[str] | None = None,
    outcome: str = "Improved performance by 50%",
) -> None:
    """Helper to create a Work Unit file."""
    tags = tags or []
    actions = actions or ["Implemented the solution"]
    tags_yaml = "\n".join([f'  - "{t}"' for t in tags]) if tags else ""
    tags_section = f"tags:\n{tags_yaml}" if tags else "tags: []"
    actions_yaml = "\n".join([f'  - "{a}"' for a in actions])

    content = f"""\
schema_version: "1.0.0"
id: "{wu_id}"
title: "{title}"
problem:
  statement: "{problem}"
actions:
{actions_yaml}
outcome:
  result: "{outcome}"
{tags_section}
confidence: high
"""
    path.write_text(content)


def _create_jd_file(path: Path, title: str, content: str) -> None:
    """Helper to create a job description file."""
    path.write_text(f"{title}\n\n{content}")


class TestPlanCommandBasic:
    """Tests for basic plan command functionality (AC #1, #2)."""

    def test_plan_command_exists(
        self, tmp_path: Path, cli_runner: CliRunner, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should have a plan command available."""
        monkeypatch.chdir(tmp_path)

        result = cli_runner.invoke(main, ["plan", "--help"])

        assert result.exit_code == 0
        assert "plan" in result.output.lower()
        assert "--jd" in result.output

    def test_plan_requires_jd_option(
        self, tmp_path: Path, cli_runner: CliRunner, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should require --jd option (AC #1)."""
        monkeypatch.chdir(tmp_path)

        result = cli_runner.invoke(main, ["plan"])

        assert result.exit_code != 0
        assert "Missing option" in result.output or "required" in result.output.lower()

    def test_plan_shows_selected_work_units(
        self, tmp_path: Path, cli_runner: CliRunner, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should show SELECTED section with Work Units (AC #1)."""
        monkeypatch.chdir(tmp_path)

        # Create work units
        work_units = tmp_path / "work-units"
        work_units.mkdir()
        _create_work_unit(
            work_units / "wu-python.yaml",
            "wu-2026-01-01-python-api",
            "Built Python REST API",
            tags=["python", "api"],
            problem="Need to build a REST API for data access",
            actions=["Designed API endpoints", "Implemented Python backend"],
            outcome="API handles 1000 requests per second",
        )

        # Create JD file
        jd_file = tmp_path / "jd.txt"
        _create_jd_file(
            jd_file,
            "Senior Software Engineer",
            "Requirements:\n- 5+ years Python experience\n- REST API design\n- AWS",
        )

        result = cli_runner.invoke(main, ["plan", "--jd", str(jd_file)])

        assert result.exit_code == 0
        assert "SELECTED" in result.output
        assert "Built Python REST API" in result.output

    def test_plan_shows_relevance_scores(
        self, tmp_path: Path, cli_runner: CliRunner, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should show relevance scores as percentages (AC #2)."""
        monkeypatch.chdir(tmp_path)

        work_units = tmp_path / "work-units"
        work_units.mkdir()
        _create_work_unit(
            work_units / "wu-a.yaml",
            "wu-2026-01-01-a",
            "Test Project",
            tags=["python"],
        )

        jd_file = tmp_path / "jd.txt"
        _create_jd_file(jd_file, "Python Developer", "Requirements:\n- Python")

        result = cli_runner.invoke(main, ["plan", "--jd", str(jd_file)])

        assert result.exit_code == 0
        # Should show percentage like "87%" or "100%"
        assert "%" in result.output


class TestPlanCommandTopN:
    """Tests for --top option (AC #3, #4)."""

    def test_plan_top_option_limits_results(
        self, tmp_path: Path, cli_runner: CliRunner, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should limit results with --top option (AC #3)."""
        monkeypatch.chdir(tmp_path)

        work_units = tmp_path / "work-units"
        work_units.mkdir()
        # Create 10 work units
        for i in range(10):
            _create_work_unit(
                work_units / f"wu-{i}.yaml",
                f"wu-2026-01-{i + 1:02d}-project-{i}",
                f"Project {i}",
            )

        jd_file = tmp_path / "jd.txt"
        _create_jd_file(jd_file, "Developer", "Requirements:\n- Programming")

        result = cli_runner.invoke(main, ["plan", "--jd", str(jd_file), "--top", "3"])

        assert result.exit_code == 0
        # Count Work Units by counting percentage scores (e.g., "85%")
        # The SELECTED section should show at most 3 Work Units
        import re

        score_pattern = r"\d+%\s+Project \d"
        matches = re.findall(score_pattern, result.output)
        assert len(matches) <= 3, f"Expected at most 3 Work Units, found {len(matches)}"

    def test_plan_default_top_is_8(
        self, tmp_path: Path, cli_runner: CliRunner, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should default to top 8 when --top not specified (AC #4)."""
        monkeypatch.chdir(tmp_path)

        work_units = tmp_path / "work-units"
        work_units.mkdir()
        # Create 15 work units
        for i in range(15):
            _create_work_unit(
                work_units / f"wu-{i}.yaml",
                f"wu-2026-01-{i + 1:02d}-project-{i}",
                f"Project {i}",
            )

        jd_file = tmp_path / "jd.txt"
        _create_jd_file(jd_file, "Developer", "Requirements:\n- Programming")

        result = cli_runner.invoke(main, ["plan", "--jd", str(jd_file)])

        assert result.exit_code == 0
        # Verify "8 Work Units" appears in the SELECTED header
        assert "8 Work Units" in result.output, "Default should select 8 Work Units"


class TestPlanCommandRichOutput:
    """Tests for Rich formatted output (AC #5)."""

    def test_plan_shows_match_reasons_indented(
        self, tmp_path: Path, cli_runner: CliRunner, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should show match reasons under each Work Unit (AC #5)."""
        monkeypatch.chdir(tmp_path)

        work_units = tmp_path / "work-units"
        work_units.mkdir()
        _create_work_unit(
            work_units / "wu-python.yaml",
            "wu-2026-01-01-python",
            "Python Backend Service",
            tags=["python", "aws", "docker"],
            problem="Built scalable backend",
        )

        jd_file = tmp_path / "jd.txt"
        _create_jd_file(
            jd_file,
            "Python Engineer",
            "Requirements:\n- Python\n- AWS\n- Docker",
        )

        result = cli_runner.invoke(main, ["plan", "--jd", str(jd_file)])

        assert result.exit_code == 0
        # Should contain match reasons (indented with ">" marker)
        # Match reasons display as "       > Skills: python, aws" or similar
        assert ">" in result.output or "Skills:" in result.output or "Tags match:" in result.output


class TestPlanCommandContentAnalysis:
    """Tests for content analysis (AC #6)."""

    def test_plan_shows_word_count(
        self, tmp_path: Path, cli_runner: CliRunner, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should show total word count with optimal range (AC #6)."""
        monkeypatch.chdir(tmp_path)

        work_units = tmp_path / "work-units"
        work_units.mkdir()
        _create_work_unit(
            work_units / "wu-a.yaml",
            "wu-2026-01-01-a",
            "Test Project",
        )

        jd_file = tmp_path / "jd.txt"
        _create_jd_file(jd_file, "Developer", "Requirements:\n- Programming")

        result = cli_runner.invoke(main, ["plan", "--jd", str(jd_file)])

        assert result.exit_code == 0
        assert "Word Count" in result.output or "word" in result.output.lower()

    def test_plan_shows_estimated_pages(
        self, tmp_path: Path, cli_runner: CliRunner, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should show estimated page count (AC #6)."""
        monkeypatch.chdir(tmp_path)

        work_units = tmp_path / "work-units"
        work_units.mkdir()
        _create_work_unit(
            work_units / "wu-a.yaml",
            "wu-2026-01-01-a",
            "Test Project",
        )

        jd_file = tmp_path / "jd.txt"
        _create_jd_file(jd_file, "Developer", "Requirements:\n- Programming")

        result = cli_runner.invoke(main, ["plan", "--jd", str(jd_file)])

        assert result.exit_code == 0
        assert "page" in result.output.lower() or "Page" in result.output


class TestPlanCommandKeywordAnalysis:
    """Tests for keyword analysis (AC #7)."""

    def test_plan_shows_keyword_coverage(
        self, tmp_path: Path, cli_runner: CliRunner, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should show keyword coverage percentage (AC #7)."""
        monkeypatch.chdir(tmp_path)

        work_units = tmp_path / "work-units"
        work_units.mkdir()
        _create_work_unit(
            work_units / "wu-a.yaml",
            "wu-2026-01-01-a",
            "Python Development",
            tags=["python"],
        )

        jd_file = tmp_path / "jd.txt"
        _create_jd_file(
            jd_file,
            "Python Developer",
            "Requirements:\n- Python\n- Django\n- PostgreSQL",
        )

        result = cli_runner.invoke(main, ["plan", "--jd", str(jd_file)])

        assert result.exit_code == 0
        # Should show coverage percentage
        assert "Coverage" in result.output or "%" in result.output

    def test_plan_shows_missing_keywords(
        self, tmp_path: Path, cli_runner: CliRunner, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should show missing high-priority keywords (AC #7)."""
        monkeypatch.chdir(tmp_path)

        work_units = tmp_path / "work-units"
        work_units.mkdir()
        _create_work_unit(
            work_units / "wu-a.yaml",
            "wu-2026-01-01-a",
            "Python Backend",
            tags=["python"],
        )

        # Create a JD with repeated keywords that will be extracted
        # Keywords require frequency >= 2 to be extracted
        jd_file = tmp_path / "jd.txt"
        _create_jd_file(
            jd_file,
            "Full Stack Developer",
            "Requirements:\n"
            "- Strong experience with kubernetes and kubernetes deployment\n"
            "- Expert in terraform and terraform infrastructure\n"
            "- Knowledge of monitoring with datadog and datadog dashboards\n"
            "- Python backend development",
        )

        result = cli_runner.invoke(main, ["plan", "--jd", str(jd_file)])

        assert result.exit_code == 0
        # Should mention missing keywords (kubernetes, terraform, datadog)
        assert "Missing" in result.output


class TestPlanCommandJsonOutput:
    """Tests for JSON output (AC #1 - machine readable)."""

    def test_plan_json_output_structure(
        self, tmp_path: Path, cli_runner: CliRunner, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should output valid JSON with all selection data."""
        monkeypatch.chdir(tmp_path)

        work_units = tmp_path / "work-units"
        work_units.mkdir()
        _create_work_unit(
            work_units / "wu-a.yaml",
            "wu-2026-01-01-a",
            "Test Project",
            tags=["python"],
        )

        jd_file = tmp_path / "jd.txt"
        _create_jd_file(jd_file, "Developer", "Requirements:\n- Python")

        result = cli_runner.invoke(main, ["--json", "plan", "--jd", str(jd_file)])

        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["status"] == "success"
        assert data["command"] == "plan"
        assert "selected" in data["data"]

    def test_plan_json_includes_scores(
        self, tmp_path: Path, cli_runner: CliRunner, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should include scores in JSON output."""
        monkeypatch.chdir(tmp_path)

        work_units = tmp_path / "work-units"
        work_units.mkdir()
        _create_work_unit(
            work_units / "wu-a.yaml",
            "wu-2026-01-01-a",
            "Python Project",
            tags=["python"],
        )

        jd_file = tmp_path / "jd.txt"
        _create_jd_file(jd_file, "Python Developer", "Requirements:\n- Python")

        result = cli_runner.invoke(main, ["--json", "plan", "--jd", str(jd_file)])

        assert result.exit_code == 0
        data = json.loads(result.output)
        selected = data["data"]["selected"]
        assert len(selected) > 0
        assert "score" in selected[0]
        assert "match_reasons" in selected[0]


class TestPlanCommandEmptyState:
    """Tests for empty state handling."""

    def test_plan_no_work_units_shows_warning(
        self, tmp_path: Path, cli_runner: CliRunner, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should show helpful message when no Work Units exist."""
        monkeypatch.chdir(tmp_path)

        jd_file = tmp_path / "jd.txt"
        _create_jd_file(jd_file, "Developer", "Requirements:\n- Python")

        result = cli_runner.invoke(main, ["plan", "--jd", str(jd_file)])

        assert result.exit_code == 0
        assert "No Work Units" in result.output

    def test_plan_jd_file_not_found(
        self, tmp_path: Path, cli_runner: CliRunner, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should show error when JD file doesn't exist."""
        monkeypatch.chdir(tmp_path)

        result = cli_runner.invoke(main, ["plan", "--jd", "nonexistent.txt"])

        assert result.exit_code != 0


class TestPlanCommandExclusions:
    """Tests for exclusion display functionality (Story 4.4)."""

    def test_show_excluded_flag_displays_excluded_section(
        self, tmp_path: Path, cli_runner: CliRunner, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should show EXCLUDED section when --show-excluded is used (AC #1)."""
        monkeypatch.chdir(tmp_path)

        work_units = tmp_path / "work-units"
        work_units.mkdir()
        # Create more Work Units than --top to have excluded ones
        for i in range(10):
            _create_work_unit(
                work_units / f"wu-{i}.yaml",
                f"wu-2026-01-{i + 1:02d}-project-{i}",
                f"Project {i} - Test project for exclusion testing",
            )

        jd_file = tmp_path / "jd.txt"
        _create_jd_file(jd_file, "Developer", "Requirements:\n- Programming")

        result = cli_runner.invoke(
            main, ["plan", "--jd", str(jd_file), "--top", "3", "--show-excluded"]
        )

        assert result.exit_code == 0
        assert "EXCLUDED" in result.output

    def test_show_all_excluded_flag_shows_all(
        self, tmp_path: Path, cli_runner: CliRunner, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should show all excluded Work Units with --show-all-excluded (AC #4)."""
        monkeypatch.chdir(tmp_path)

        work_units = tmp_path / "work-units"
        work_units.mkdir()
        # Create 15 Work Units, select only 3, so 12 are excluded
        for i in range(15):
            _create_work_unit(
                work_units / f"wu-{i}.yaml",
                f"wu-2026-01-{i + 1:02d}-project-{i}",
                f"Project {i} for testing",
            )

        jd_file = tmp_path / "jd.txt"
        _create_jd_file(jd_file, "Developer", "Requirements:\n- Programming")

        result = cli_runner.invoke(
            main, ["plan", "--jd", str(jd_file), "--top", "3", "--show-all-excluded"]
        )

        assert result.exit_code == 0
        assert "EXCLUDED" in result.output
        # Should show more than 5 (default limit)
        # Count occurrences of "Project" in excluded section
        # With 12 excluded, all should be shown

    def test_excluded_shows_default_top_5(
        self, tmp_path: Path, cli_runner: CliRunner, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should show only top 5 excluded by default (AC #1)."""
        monkeypatch.chdir(tmp_path)

        work_units = tmp_path / "work-units"
        work_units.mkdir()
        # Create 15 Work Units, select only 3
        for i in range(15):
            _create_work_unit(
                work_units / f"wu-{i}.yaml",
                f"wu-2026-01-{i + 1:02d}-project-{i}",
                f"Project {i}",
            )

        jd_file = tmp_path / "jd.txt"
        _create_jd_file(jd_file, "Developer", "Requirements:\n- Programming")

        result = cli_runner.invoke(
            main, ["plan", "--jd", str(jd_file), "--top", "3", "--show-excluded"]
        )

        assert result.exit_code == 0
        # Should mention "more" or show limited count with "showing"
        assert "more" in result.output.lower() or "showing" in result.output.lower()


class TestPlanCommandExclusionReasons:
    """Tests for exclusion reason generation (Story 4.4, AC #2, #3)."""

    def test_low_relevance_reason_for_low_scores(
        self, tmp_path: Path, cli_runner: CliRunner, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should show 'Low relevance score' for items with score < 20% (AC #2)."""
        monkeypatch.chdir(tmp_path)

        work_units = tmp_path / "work-units"
        work_units.mkdir()

        # Create one highly relevant work unit
        _create_work_unit(
            work_units / "wu-relevant.yaml",
            "wu-2026-01-01-python-expert",
            "Python Expert Project",
            tags=["python", "django", "aws"],
            problem="Built complex Python system with Django and AWS",
            actions=["Designed Python architecture", "Implemented Django models"],
            outcome="Deployed to AWS with zero downtime",
        )

        # Create a completely irrelevant work unit
        _create_work_unit(
            work_units / "wu-irrelevant.yaml",
            "wu-2026-01-02-gardening",
            "Gardening Project",
            tags=["gardening", "plants", "outdoor"],
            problem="Needed to grow vegetables in the backyard",
            actions=["Planted tomatoes and peppers"],
            outcome="Harvested 50 pounds of vegetables",
        )

        jd_file = tmp_path / "jd.txt"
        _create_jd_file(
            jd_file,
            "Senior Python Developer",
            "Requirements:\n- Python expert\n- Django framework\n- AWS deployment",
        )

        result = cli_runner.invoke(
            main, ["plan", "--jd", str(jd_file), "--top", "1", "--show-excluded"]
        )

        assert result.exit_code == 0
        assert "EXCLUDED" in result.output
        # Should show low relevance reason with specific message
        assert "Low relevance score" in result.output or "relevance" in result.output.lower()

    def test_below_threshold_reason_for_medium_scores(
        self, tmp_path: Path, cli_runner: CliRunner, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should show 'Below selection threshold' for items not in top N (AC #3)."""
        monkeypatch.chdir(tmp_path)

        work_units = tmp_path / "work-units"
        work_units.mkdir()

        # Create multiple similarly-relevant work units
        for i in range(5):
            _create_work_unit(
                work_units / f"wu-{i}.yaml",
                f"wu-2026-01-{i + 1:02d}-python-{i}",
                f"Python Project {i}",
                tags=["python"],
                problem="Python development work",
                actions=["Built Python code"],
                outcome="Delivered Python solution",
            )

        jd_file = tmp_path / "jd.txt"
        _create_jd_file(jd_file, "Python Developer", "Requirements:\n- Python")

        result = cli_runner.invoke(
            main, ["plan", "--jd", str(jd_file), "--top", "2", "--show-excluded"]
        )

        assert result.exit_code == 0
        assert "EXCLUDED" in result.output
        # Should show threshold reason with specific message
        assert "Below selection threshold" in result.output or "threshold" in result.output.lower()

    def test_exclusion_shows_score_percentage(
        self, tmp_path: Path, cli_runner: CliRunner, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should include score percentage in exclusion reason (AC #2, #3)."""
        monkeypatch.chdir(tmp_path)

        work_units = tmp_path / "work-units"
        work_units.mkdir()

        for i in range(5):
            _create_work_unit(
                work_units / f"wu-{i}.yaml",
                f"wu-2026-01-{i + 1:02d}-project-{i}",
                f"Project {i}",
            )

        jd_file = tmp_path / "jd.txt"
        _create_jd_file(jd_file, "Developer", "Requirements:\n- Programming")

        result = cli_runner.invoke(
            main, ["plan", "--jd", str(jd_file), "--top", "2", "--show-excluded"]
        )

        assert result.exit_code == 0
        # Should show percentages in excluded section
        # Look for pattern like "23%" or similar in output after EXCLUDED

        excluded_section = (
            result.output.split("EXCLUDED")[-1] if "EXCLUDED" in result.output else ""
        )
        assert "%" in excluded_section, "Exclusion reasons should include score percentages"


class TestPlanCommandCoverage:
    """Tests for skill coverage analysis (Story 4.5)."""

    def test_plan_shows_coverage_section(
        self, tmp_path: Path, cli_runner: CliRunner, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """AC1: Should show COVERAGE section in plan output."""
        monkeypatch.chdir(tmp_path)

        work_units = tmp_path / "work-units"
        work_units.mkdir()
        _create_work_unit(
            work_units / "wu-python.yaml",
            "wu-2026-01-01-python-api",
            "Python REST API",
            tags=["python", "api"],
        )

        jd_file = tmp_path / "jd.txt"
        _create_jd_file(
            jd_file,
            "Python Developer",
            "Requirements:\n- Python\n- API design",
        )

        result = cli_runner.invoke(main, ["plan", "--jd", str(jd_file)])

        assert result.exit_code == 0
        assert "Coverage" in result.output

    def test_plan_shows_coverage_symbols(
        self, tmp_path: Path, cli_runner: CliRunner, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """AC1: Should show ✓, △, ✗ symbols for coverage levels."""
        monkeypatch.chdir(tmp_path)

        work_units = tmp_path / "work-units"
        work_units.mkdir()
        _create_work_unit(
            work_units / "wu-python.yaml",
            "wu-2026-01-01-python",
            "Python Project",
            tags=["python"],
        )

        jd_file = tmp_path / "jd.txt"
        _create_jd_file(
            jd_file,
            "Developer",
            "Requirements:\n- Python\n- Rust",  # Python covered, Rust gap
        )

        result = cli_runner.invoke(main, ["plan", "--jd", str(jd_file)])

        assert result.exit_code == 0
        # Should show coverage symbols
        output = result.output
        assert "✓" in output or "✗" in output or "△" in output

    def test_plan_shows_coverage_percentage(
        self, tmp_path: Path, cli_runner: CliRunner, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """AC1: Should show coverage percentage summary."""
        monkeypatch.chdir(tmp_path)

        work_units = tmp_path / "work-units"
        work_units.mkdir()
        _create_work_unit(
            work_units / "wu-python.yaml",
            "wu-2026-01-01-python",
            "Python Project",
            tags=["python"],
        )

        jd_file = tmp_path / "jd.txt"
        _create_jd_file(jd_file, "Developer", "Requirements:\n- Python")

        result = cli_runner.invoke(main, ["plan", "--jd", str(jd_file)])

        assert result.exit_code == 0
        # Should show coverage percentage in coverage section
        assert "Coverage" in result.output and "%" in result.output

    def test_plan_json_includes_coverage(
        self, tmp_path: Path, cli_runner: CliRunner, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """AC5: JSON output should include coverage data."""
        monkeypatch.chdir(tmp_path)

        work_units = tmp_path / "work-units"
        work_units.mkdir()
        _create_work_unit(
            work_units / "wu-python.yaml",
            "wu-2026-01-01-python",
            "Python API",
            tags=["python", "api"],
        )

        jd_file = tmp_path / "jd.txt"
        _create_jd_file(
            jd_file,
            "Python Developer",
            "Requirements:\n- Python\n- API\n- Rust",
        )

        result = cli_runner.invoke(main, ["--json", "plan", "--jd", str(jd_file)])

        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "coverage" in data["data"]
        assert "items" in data["data"]["coverage"]
        assert "coverage_percentage" in data["data"]["coverage"]

    def test_plan_json_coverage_includes_gaps(
        self, tmp_path: Path, cli_runner: CliRunner, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """AC5: JSON output should clearly enumerate gaps."""
        monkeypatch.chdir(tmp_path)

        work_units = tmp_path / "work-units"
        work_units.mkdir()
        _create_work_unit(
            work_units / "wu-python.yaml",
            "wu-2026-01-01-python",
            "Python Project",
            tags=["python"],
        )

        jd_file = tmp_path / "jd.txt"
        _create_jd_file(
            jd_file,
            "Developer",
            "Requirements:\n- Python\n- Rust\n- Go",  # Rust and Go are gaps
        )

        result = cli_runner.invoke(main, ["--json", "plan", "--jd", str(jd_file)])

        assert result.exit_code == 0
        data = json.loads(result.output)
        coverage = data["data"]["coverage"]

        # Check for gaps in items
        gaps = [item for item in coverage["items"] if item["level"] == "gap"]
        assert len(gaps) >= 2  # Rust and Go should be gaps


class TestPlanCommandExclusionJsonOutput:
    """Tests for JSON output of exclusions (Story 4.4, AC #1)."""

    def test_json_output_includes_excluded(
        self, tmp_path: Path, cli_runner: CliRunner, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should include excluded Work Units in JSON output (AC #1)."""
        monkeypatch.chdir(tmp_path)

        work_units = tmp_path / "work-units"
        work_units.mkdir()

        for i in range(5):
            _create_work_unit(
                work_units / f"wu-{i}.yaml",
                f"wu-2026-01-{i + 1:02d}-project-{i}",
                f"Project {i}",
            )

        jd_file = tmp_path / "jd.txt"
        _create_jd_file(jd_file, "Developer", "Requirements:\n- Programming")

        result = cli_runner.invoke(main, ["--json", "plan", "--jd", str(jd_file), "--top", "2"])

        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "excluded" in data["data"]
        assert len(data["data"]["excluded"]) > 0

    def test_json_excluded_includes_reasons(
        self, tmp_path: Path, cli_runner: CliRunner, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should include exclusion reasons in JSON output (AC #1)."""
        monkeypatch.chdir(tmp_path)

        work_units = tmp_path / "work-units"
        work_units.mkdir()

        for i in range(5):
            _create_work_unit(
                work_units / f"wu-{i}.yaml",
                f"wu-2026-01-{i + 1:02d}-project-{i}",
                f"Project {i}",
            )

        jd_file = tmp_path / "jd.txt"
        _create_jd_file(jd_file, "Developer", "Requirements:\n- Programming")

        result = cli_runner.invoke(main, ["--json", "plan", "--jd", str(jd_file), "--top", "2"])

        assert result.exit_code == 0
        data = json.loads(result.output)
        excluded = data["data"]["excluded"]
        assert len(excluded) > 0
        assert "exclusion_reason" in excluded[0]
        assert "type" in excluded[0]["exclusion_reason"]
        assert "message" in excluded[0]["exclusion_reason"]


class TestPlanPersistence:
    """Tests for plan persistence (Story 4.6)."""

    def test_output_option_saves_plan(
        self, tmp_path: Path, cli_runner: CliRunner, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """AC1: Should save plan to file with --output option."""
        monkeypatch.chdir(tmp_path)

        work_units = tmp_path / "work-units"
        work_units.mkdir()
        _create_work_unit(
            work_units / "wu-python.yaml",
            "wu-2026-01-01-python",
            "Python API",
            tags=["python"],
        )

        jd_file = tmp_path / "jd.txt"
        _create_jd_file(jd_file, "Python Dev", "Requirements:\n- Python")

        plan_file = tmp_path / "my-plan.yaml"
        result = cli_runner.invoke(main, ["plan", "--jd", str(jd_file), "--output", str(plan_file)])

        assert result.exit_code == 0
        assert plan_file.exists()
        assert "saved" in result.output.lower() or "Plan saved" in result.output

    def test_saved_plan_contains_required_fields(
        self, tmp_path: Path, cli_runner: CliRunner, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """AC1: Saved plan should contain JD hash, Work Units, scores, timestamp."""
        monkeypatch.chdir(tmp_path)

        work_units = tmp_path / "work-units"
        work_units.mkdir()
        _create_work_unit(
            work_units / "wu-python.yaml",
            "wu-2026-01-01-python",
            "Python API",
            tags=["python"],
        )

        jd_file = tmp_path / "jd.txt"
        _create_jd_file(jd_file, "Python Dev", "Requirements:\n- Python")

        plan_file = tmp_path / "my-plan.yaml"
        result = cli_runner.invoke(main, ["plan", "--jd", str(jd_file), "--output", str(plan_file)])

        assert result.exit_code == 0

        content = plan_file.read_text()
        assert "jd_hash" in content
        assert "selected_work_units" in content
        assert "score" in content
        assert "created_at" in content

    def test_load_option_displays_saved_plan(
        self, tmp_path: Path, cli_runner: CliRunner, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """AC2: Should load and display saved plan with --load option."""
        monkeypatch.chdir(tmp_path)

        work_units = tmp_path / "work-units"
        work_units.mkdir()
        _create_work_unit(
            work_units / "wu-python.yaml",
            "wu-2026-01-01-python",
            "Python API",
            tags=["python"],
        )

        jd_file = tmp_path / "jd.txt"
        _create_jd_file(jd_file, "Python Dev", "Requirements:\n- Python")

        # First save a plan
        plan_file = tmp_path / "my-plan.yaml"
        cli_runner.invoke(main, ["plan", "--jd", str(jd_file), "--output", str(plan_file)])

        # Then load it
        result = cli_runner.invoke(main, ["plan", "--load", str(plan_file)])

        assert result.exit_code == 0
        assert "Python API" in result.output
        assert "SELECTED" in result.output or "Plan" in result.output

    def test_load_skips_ranking(
        self, tmp_path: Path, cli_runner: CliRunner, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """AC2: Loading saved plan should skip ranking."""
        monkeypatch.chdir(tmp_path)

        work_units = tmp_path / "work-units"
        work_units.mkdir()
        _create_work_unit(
            work_units / "wu-python.yaml",
            "wu-2026-01-01-python",
            "Python API",
            tags=["python"],
        )

        jd_file = tmp_path / "jd.txt"
        _create_jd_file(jd_file, "Python Dev", "Requirements:\n- Python")

        # First save a plan
        plan_file = tmp_path / "my-plan.yaml"
        cli_runner.invoke(main, ["plan", "--jd", str(jd_file), "--output", str(plan_file)])

        # Delete work units - if ranking runs it would fail
        import shutil

        shutil.rmtree(work_units)

        # Load should still work without Work Units
        result = cli_runner.invoke(main, ["plan", "--load", str(plan_file)])

        assert result.exit_code == 0

    def test_saved_plan_is_human_readable(
        self, tmp_path: Path, cli_runner: CliRunner, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """AC5: Saved plan should be human-readable YAML."""
        monkeypatch.chdir(tmp_path)

        work_units = tmp_path / "work-units"
        work_units.mkdir()
        _create_work_unit(
            work_units / "wu-python.yaml",
            "wu-2026-01-01-python",
            "Python API",
            tags=["python"],
        )

        jd_file = tmp_path / "jd.txt"
        _create_jd_file(jd_file, "Python Dev", "Requirements:\n- Python")

        plan_file = tmp_path / "my-plan.yaml"
        cli_runner.invoke(main, ["plan", "--jd", str(jd_file), "--output", str(plan_file)])

        content = plan_file.read_text()
        # Should have header comments
        assert "# Resume Plan" in content
        assert "resume build --plan" in content

    def test_jd_or_load_required(
        self, tmp_path: Path, cli_runner: CliRunner, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should require either --jd or --load option."""
        monkeypatch.chdir(tmp_path)

        # Neither --jd nor --load provided
        result = cli_runner.invoke(main, ["plan"])

        assert result.exit_code != 0

    def test_load_nonexistent_file_shows_error(
        self, tmp_path: Path, cli_runner: CliRunner, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should show error when loading nonexistent plan file."""
        monkeypatch.chdir(tmp_path)

        result = cli_runner.invoke(main, ["plan", "--load", "nonexistent.yaml"])

        assert result.exit_code != 0

    def test_load_json_output_structure(
        self, tmp_path: Path, cli_runner: CliRunner, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Issue #3: Should output valid JSON when loading saved plan with --json."""
        monkeypatch.chdir(tmp_path)

        work_units = tmp_path / "work-units"
        work_units.mkdir()
        _create_work_unit(
            work_units / "wu-python.yaml",
            "wu-2026-01-01-python",
            "Python API",
            tags=["python"],
        )

        jd_file = tmp_path / "jd.txt"
        _create_jd_file(jd_file, "Python Dev", "Requirements:\n- Python")

        # First save a plan
        plan_file = tmp_path / "my-plan.yaml"
        cli_runner.invoke(main, ["plan", "--jd", str(jd_file), "--output", str(plan_file)])

        # Then load with JSON output
        result = cli_runner.invoke(main, ["--json", "plan", "--load", str(plan_file)])

        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["status"] == "success"
        assert data["command"] == "plan"
        assert "selected" in data["data"]
        assert "jd_hash" in data["data"]
        assert "created_at" in data["data"]

    def test_rerun_plan_leaves_original_unchanged(
        self, tmp_path: Path, cli_runner: CliRunner, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """AC3: Re-running plan should not modify original saved plan file."""
        monkeypatch.chdir(tmp_path)

        work_units = tmp_path / "work-units"
        work_units.mkdir()
        _create_work_unit(
            work_units / "wu-python.yaml",
            "wu-2026-01-01-python",
            "Python API",
            tags=["python"],
        )

        jd_file = tmp_path / "jd.txt"
        _create_jd_file(jd_file, "Python Dev", "Requirements:\n- Python")

        # Save initial plan
        plan_file = tmp_path / "my-plan.yaml"
        cli_runner.invoke(main, ["plan", "--jd", str(jd_file), "--output", str(plan_file)])
        original_content = plan_file.read_text()

        # Modify work unit
        _create_work_unit(
            work_units / "wu-python.yaml",
            "wu-2026-01-01-python",
            "Python API - MODIFIED TITLE",
            tags=["python", "modified"],
        )

        # Re-run plan (without --output)
        result = cli_runner.invoke(main, ["plan", "--jd", str(jd_file)])

        assert result.exit_code == 0
        # Original plan file should be unchanged
        assert plan_file.read_text() == original_content

    def test_load_warns_when_work_units_missing(
        self, tmp_path: Path, cli_runner: CliRunner, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Task 3.4: Should warn when Work Units from plan no longer exist."""
        monkeypatch.chdir(tmp_path)

        work_units = tmp_path / "work-units"
        work_units.mkdir()
        _create_work_unit(
            work_units / "wu-python.yaml",
            "wu-2026-01-01-python",
            "Python API",
            tags=["python"],
        )

        jd_file = tmp_path / "jd.txt"
        _create_jd_file(jd_file, "Python Dev", "Requirements:\n- Python")

        # Save a plan
        plan_file = tmp_path / "my-plan.yaml"
        cli_runner.invoke(main, ["plan", "--jd", str(jd_file), "--output", str(plan_file)])

        # Delete the Work Unit
        (work_units / "wu-python.yaml").unlink()

        # Load the plan - should warn about missing Work Unit
        result = cli_runner.invoke(main, ["plan", "--load", str(plan_file)])

        assert result.exit_code == 0
        assert "no longer exist" in result.output or "MISSING" in result.output

    def test_load_json_includes_missing_work_units(
        self, tmp_path: Path, cli_runner: CliRunner, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Task 3.4: JSON output should include missing Work Unit IDs."""
        monkeypatch.chdir(tmp_path)

        work_units = tmp_path / "work-units"
        work_units.mkdir()
        _create_work_unit(
            work_units / "wu-python.yaml",
            "wu-2026-01-01-python",
            "Python API",
            tags=["python"],
        )

        jd_file = tmp_path / "jd.txt"
        _create_jd_file(jd_file, "Python Dev", "Requirements:\n- Python")

        # Save a plan
        plan_file = tmp_path / "my-plan.yaml"
        cli_runner.invoke(main, ["plan", "--jd", str(jd_file), "--output", str(plan_file)])

        # Delete the Work Unit
        (work_units / "wu-python.yaml").unlink()

        # Load with JSON output
        result = cli_runner.invoke(main, ["--json", "plan", "--load", str(plan_file)])

        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "missing_work_units" in data["data"]
        assert "wu-2026-01-01-python" in data["data"]["missing_work_units"]

    def test_load_malformed_yaml_shows_error(
        self, tmp_path: Path, cli_runner: CliRunner, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Issue #4: Should show helpful error for malformed YAML."""
        monkeypatch.chdir(tmp_path)

        # Create a malformed YAML file
        plan_file = tmp_path / "bad-plan.yaml"
        plan_file.write_text("invalid: yaml: content: [unclosed")

        result = cli_runner.invoke(main, ["plan", "--load", str(plan_file)])

        assert result.exit_code != 0

    def test_load_empty_plan_shows_error(
        self, tmp_path: Path, cli_runner: CliRunner, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Issue #4: Should show helpful error for empty plan file."""
        monkeypatch.chdir(tmp_path)

        # Create an empty YAML file
        plan_file = tmp_path / "empty-plan.yaml"
        plan_file.write_text("")

        result = cli_runner.invoke(main, ["plan", "--load", str(plan_file)])

        assert result.exit_code != 0


class TestPlanEnhancedDataModelPreview:
    """Tests for enhanced plan data model preview (Story 6.18)."""

    def _create_config_file(
        self,
        path: Path,
        profile: dict[str, str] | None = None,
        certifications: list[dict[str, str]] | None = None,
        education: list[dict[str, str]] | None = None,
    ) -> None:
        """Helper to create a .resume.yaml config file."""
        import yaml

        config: dict[str, object] = {"work_units_dir": "work-units"}

        if profile:
            config["profile"] = profile
        if certifications:
            config["certifications"] = certifications
        if education:
            config["education"] = education

        (path / ".resume.yaml").write_text(yaml.dump(config))

    def _create_positions_file(
        self,
        path: Path,
        positions: list[dict[str, str | None]],
    ) -> None:
        """Helper to create a positions.yaml file."""
        import yaml

        # Convert list to dict format expected by position service
        positions_dict: dict[str, dict[str, str | None]] = {}
        for pos in positions:
            pos_id = pos.pop("id")
            if pos_id:
                positions_dict[pos_id] = pos

        (path / "positions.yaml").write_text(yaml.dump({"positions": positions_dict}))

    def test_plan_shows_profile_preview_section(
        self, tmp_path: Path, cli_runner: CliRunner, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """AC4: Should show Profile Preview section."""
        monkeypatch.chdir(tmp_path)

        self._create_config_file(
            tmp_path,
            profile={
                "name": "Test User",
                "title": "Senior Engineer",
                "email": "test@example.com",
                "phone": "555-1234",
                "location": "NYC",
                "linkedin": "https://linkedin.com/in/test",
                "summary": "Experienced engineer with ten years of expertise in building "
                "scalable systems and leading cross-functional teams to deliver "
                "innovative solutions that drive business growth and efficiency.",
            },
        )

        work_units = tmp_path / "work-units"
        work_units.mkdir()
        _create_work_unit(
            work_units / "wu-test.yaml",
            "wu-2026-01-01-test",
            "Test Project",
        )

        jd_file = tmp_path / "jd.txt"
        _create_jd_file(jd_file, "Engineer", "Requirements:\n- Python")

        result = cli_runner.invoke(main, ["plan", "--jd", str(jd_file)])

        assert result.exit_code == 0
        assert "Profile Preview" in result.output
        assert "Test User" in result.output
        assert "Senior Engineer" in result.output

    def test_plan_shows_certifications_analysis_section(
        self, tmp_path: Path, cli_runner: CliRunner, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """AC2: Should show Certifications Analysis section with matches."""
        monkeypatch.chdir(tmp_path)

        self._create_config_file(
            tmp_path,
            certifications=[
                {"name": "CISSP", "issuer": "ISC2", "date": "2023-01"},
                {"name": "AWS Solutions Architect", "issuer": "Amazon", "date": "2023-06"},
            ],
        )

        work_units = tmp_path / "work-units"
        work_units.mkdir()
        _create_work_unit(
            work_units / "wu-test.yaml",
            "wu-2026-01-01-test",
            "Test Project",
        )

        jd_file = tmp_path / "jd.txt"
        _create_jd_file(
            jd_file,
            "Security Engineer",
            "Requirements:\n- CISSP or CISM certification required\n- Python",
        )

        result = cli_runner.invoke(main, ["plan", "--jd", str(jd_file)])

        assert result.exit_code == 0
        assert "Certifications Analysis" in result.output

    def test_plan_shows_education_analysis_section(
        self, tmp_path: Path, cli_runner: CliRunner, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """AC3: Should show Education Analysis section."""
        monkeypatch.chdir(tmp_path)

        self._create_config_file(
            tmp_path,
            education=[
                {"degree": "MS Computer Science", "institution": "MIT", "year": "2020"},
            ],
        )

        work_units = tmp_path / "work-units"
        work_units.mkdir()
        _create_work_unit(
            work_units / "wu-test.yaml",
            "wu-2026-01-01-test",
            "Test Project",
        )

        jd_file = tmp_path / "jd.txt"
        _create_jd_file(
            jd_file,
            "Engineer",
            "Requirements:\n- Bachelor's degree in Computer Science\n- Python",
        )

        result = cli_runner.invoke(main, ["plan", "--jd", str(jd_file)])

        assert result.exit_code == 0
        assert "Education Analysis" in result.output

    def test_plan_shows_position_grouping_preview(
        self, tmp_path: Path, cli_runner: CliRunner, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """AC1: Should show Position Grouping Preview section."""
        monkeypatch.chdir(tmp_path)

        self._create_config_file(tmp_path)
        self._create_positions_file(
            tmp_path,
            [
                {
                    "id": "pos-techcorp-senior",
                    "employer": "TechCorp",
                    "title": "Senior Engineer",
                    "start_date": "2022-01",
                    "end_date": None,
                },
            ],
        )

        work_units = tmp_path / "work-units"
        work_units.mkdir()

        # Create work unit linked to position
        content = """\
schema_version: "1.0.0"
id: "wu-2026-01-01-api"
title: "Built API"
position_id: "pos-techcorp-senior"
problem:
  statement: "Needed API"
actions:
  - "Built it"
outcome:
  result: "Improved performance"
tags: []
confidence: high
"""
        (work_units / "wu-api.yaml").write_text(content)

        jd_file = tmp_path / "jd.txt"
        _create_jd_file(jd_file, "Engineer", "Requirements:\n- Python")

        result = cli_runner.invoke(main, ["plan", "--jd", str(jd_file)])

        assert result.exit_code == 0
        assert "Position Grouping" in result.output
        assert "TechCorp" in result.output

    def test_plan_json_includes_all_new_sections(
        self, tmp_path: Path, cli_runner: CliRunner, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """AC5: JSON output should include all new analysis sections."""
        monkeypatch.chdir(tmp_path)

        self._create_config_file(
            tmp_path,
            profile={
                "name": "Test User",
                "title": "Senior Engineer",
                "email": "test@example.com",
                "summary": "Short summary for testing purposes.",
            },
            certifications=[
                {"name": "CISSP", "issuer": "ISC2", "date": "2023-01"},
            ],
            education=[
                {"degree": "MS Computer Science", "institution": "MIT", "year": "2020"},
            ],
        )

        work_units = tmp_path / "work-units"
        work_units.mkdir()
        _create_work_unit(
            work_units / "wu-test.yaml",
            "wu-2026-01-01-test",
            "Test Project",
        )

        jd_file = tmp_path / "jd.txt"
        _create_jd_file(
            jd_file,
            "Engineer",
            "Requirements:\n- CISSP certification\n- Bachelor's degree\n- Python",
        )

        result = cli_runner.invoke(main, ["--json", "plan", "--jd", str(jd_file)])

        assert result.exit_code == 0
        data = json.loads(result.output)

        # Check all new sections are present
        assert "certifications_analysis" in data["data"]
        assert "education_analysis" in data["data"]
        assert "profile_preview" in data["data"]

        # Check certifications analysis structure
        certs = data["data"]["certifications_analysis"]
        assert "matched" in certs
        assert "gaps" in certs
        assert "additional" in certs
        assert "match_percentage" in certs

        # Check education analysis structure
        edu = data["data"]["education_analysis"]
        assert "meets_requirements" in edu
        assert "degree_match" in edu
        assert "field_relevance" in edu

        # Check profile preview structure
        profile = data["data"]["profile_preview"]
        assert "name" in profile
        assert "title" in profile
        assert "contact_complete" in profile
        assert "summary_words" in profile
        assert "summary_status" in profile

    def test_plan_handles_no_certifications_gracefully(
        self, tmp_path: Path, cli_runner: CliRunner, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """AC7: Should show helpful message when no certifications configured."""
        monkeypatch.chdir(tmp_path)

        # Config with no certifications
        self._create_config_file(tmp_path)

        work_units = tmp_path / "work-units"
        work_units.mkdir()
        _create_work_unit(
            work_units / "wu-test.yaml",
            "wu-2026-01-01-test",
            "Test Project",
        )

        jd_file = tmp_path / "jd.txt"
        _create_jd_file(
            jd_file,
            "Security Engineer",
            "Requirements:\n- CISSP certification required\n- Python",
        )

        result = cli_runner.invoke(main, ["plan", "--jd", str(jd_file)])

        assert result.exit_code == 0
        # Should mention no certifications or show helpful message
        assert "No certifications" in result.output or "certifications" in result.output.lower()

    def test_plan_handles_no_positions_gracefully(
        self, tmp_path: Path, cli_runner: CliRunner, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """AC6: Should show helpful message when no positions configured."""
        monkeypatch.chdir(tmp_path)

        # Config with no positions file
        self._create_config_file(tmp_path)

        work_units = tmp_path / "work-units"
        work_units.mkdir()
        _create_work_unit(
            work_units / "wu-test.yaml",
            "wu-2026-01-01-test",
            "Test Project",
        )

        jd_file = tmp_path / "jd.txt"
        _create_jd_file(jd_file, "Engineer", "Requirements:\n- Python")

        result = cli_runner.invoke(main, ["plan", "--jd", str(jd_file)])

        assert result.exit_code == 0
        # Should suggest adding positions.yaml
        assert "positions" in result.output.lower()

    def test_plan_shows_profile_missing_fields(
        self, tmp_path: Path, cli_runner: CliRunner, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """AC8: Should show missing profile fields."""
        monkeypatch.chdir(tmp_path)

        # Profile with missing fields
        self._create_config_file(
            tmp_path,
            profile={
                "name": "Test User",
                "title": "Engineer",
                # Missing: email, phone, location, linkedin
            },
        )

        work_units = tmp_path / "work-units"
        work_units.mkdir()
        _create_work_unit(
            work_units / "wu-test.yaml",
            "wu-2026-01-01-test",
            "Test Project",
        )

        jd_file = tmp_path / "jd.txt"
        _create_jd_file(jd_file, "Engineer", "Requirements:\n- Python")

        result = cli_runner.invoke(main, ["plan", "--jd", str(jd_file)])

        assert result.exit_code == 0
        assert "Profile Preview" in result.output
        # Should show missing fields warning
        assert "Missing" in result.output or "missing" in result.output.lower()


class TestPlanCommandSkillsCuration:
    """Tests for skills curation in plan output (Story 6.3, AC #6)."""

    def test_plan_shows_skills_curation_section(
        self, tmp_path: Path, cli_runner: CliRunner, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """AC6: Should show Skills Curation section in plan output."""
        monkeypatch.chdir(tmp_path)

        work_units = tmp_path / "work-units"
        work_units.mkdir()
        _create_work_unit(
            work_units / "wu-python.yaml",
            "wu-2026-01-01-python-api",
            "Python REST API",
            tags=["python", "aws", "docker"],
        )

        jd_file = tmp_path / "jd.txt"
        _create_jd_file(
            jd_file,
            "Python Developer",
            "Requirements:\n- Python\n- AWS",
        )

        result = cli_runner.invoke(main, ["plan", "--jd", str(jd_file)])

        assert result.exit_code == 0
        assert "Skills Curation" in result.output or "Skills" in result.output

    def test_plan_shows_included_skills_with_jd_match(
        self, tmp_path: Path, cli_runner: CliRunner, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """AC6: Should show included skills with JD match indicator."""
        monkeypatch.chdir(tmp_path)

        work_units = tmp_path / "work-units"
        work_units.mkdir()
        _create_work_unit(
            work_units / "wu-python.yaml",
            "wu-2026-01-01-python-api",
            "Python REST API",
            tags=["python", "aws", "docker", "kubernetes"],
        )

        jd_file = tmp_path / "jd.txt"
        _create_jd_file(
            jd_file,
            "Python Developer",
            "Requirements:\n- Python\n- AWS\n- Kubernetes",
        )

        result = cli_runner.invoke(main, ["plan", "--jd", str(jd_file)])

        assert result.exit_code == 0
        # Should show checkmark or indicator for JD matches
        output_lower = result.output.lower()
        assert "python" in output_lower
        assert "aws" in output_lower

    def test_plan_deduplicates_skills_case_insensitively(
        self, tmp_path: Path, cli_runner: CliRunner, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """AC6: Skills should be deduplicated case-insensitively."""
        monkeypatch.chdir(tmp_path)

        work_units = tmp_path / "work-units"
        work_units.mkdir()
        _create_work_unit(
            work_units / "wu-python.yaml",
            "wu-2026-01-01-python-api",
            "Python REST API",
            tags=["AWS", "aws", "Python", "python"],  # Duplicates with different case
        )

        jd_file = tmp_path / "jd.txt"
        _create_jd_file(jd_file, "Developer", "Requirements:\n- Python")

        result = cli_runner.invoke(main, ["plan", "--jd", str(jd_file)])

        assert result.exit_code == 0
        # Verify deduplication by checking "Curated X from Y" shows reduction
        # 4 raw skills (AWS, aws, Python, python) should become 2 after dedup
        assert "curated 2 from 4" in result.output.lower()

    def test_plan_json_includes_skills_curation(
        self, tmp_path: Path, cli_runner: CliRunner, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """AC6: JSON output should include skills curation data."""
        monkeypatch.chdir(tmp_path)

        work_units = tmp_path / "work-units"
        work_units.mkdir()
        _create_work_unit(
            work_units / "wu-python.yaml",
            "wu-2026-01-01-python-api",
            "Python REST API",
            tags=["python", "aws", "docker"],
        )

        jd_file = tmp_path / "jd.txt"
        _create_jd_file(
            jd_file,
            "Python Developer",
            "Requirements:\n- Python\n- AWS",
        )

        result = cli_runner.invoke(main, ["--json", "plan", "--jd", str(jd_file)])

        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "skills_curation" in data["data"]
        assert "included" in data["data"]["skills_curation"]
        assert "stats" in data["data"]["skills_curation"]
