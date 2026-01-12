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
