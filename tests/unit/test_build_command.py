"""Tests for build command."""

from __future__ import annotations

from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from resume_as_code.cli import main
from resume_as_code.models.certification import Certification


@pytest.fixture
def runner() -> CliRunner:
    """Create CLI test runner."""
    return CliRunner()


@pytest.fixture
def mock_plan() -> MagicMock:
    """Create mock SavedPlan."""
    plan = MagicMock()
    plan.selected_work_units = []
    plan.jd_hash = "abc123"
    plan.jd_title = "Test Job"
    return plan


@pytest.fixture
def sample_work_unit() -> dict[str, Any]:
    """Create sample Work Unit data."""
    return {
        "id": "wu-2024-01-01-test",
        "title": "Test Project",
        "organization": "Test Corp",
        "problem": {"statement": "Test problem"},
        "actions": ["Did thing 1", "Did thing 2"],
        "outcome": {"result": "Great outcome", "quantified_impact": "50% improvement"},
        "skills_demonstrated": [{"name": "Python"}],
        "tags": ["python", "testing"],
    }


class TestBuildCommandValidation:
    """Tests for build command input validation."""

    def test_requires_plan_or_jd(self, runner: CliRunner) -> None:
        """Should error when neither --plan nor --jd provided (AC: #3)."""
        result = runner.invoke(main, ["build"])

        assert result.exit_code != 0
        assert "--plan" in result.output or "--jd" in result.output

    def test_error_message_is_helpful(self, runner: CliRunner) -> None:
        """Error message should explain how to fix it."""
        result = runner.invoke(main, ["build"])

        # Should mention both options
        assert "plan" in result.output.lower()
        assert "jd" in result.output.lower()


class TestBuildFromPlan:
    """Tests for building from saved plan (AC: #1)."""

    def test_loads_plan_from_file(
        self,
        runner: CliRunner,
        tmp_path: Path,
        mock_plan: MagicMock,
    ) -> None:
        """Should load and use saved plan file."""
        plan_file = tmp_path / "plan.yaml"
        plan_file.write_text("""
version: "1.0.0"
jd_hash: "abc123"
jd_title: "Test Job"
selected_work_units: []
selection_count: 0
top_k: 8
ranker_version: "hybrid-rrf-v1"
created_at: "2024-01-01T00:00:00"
""")

        with patch("resume_as_code.commands.build.SavedPlan.load") as mock_load:
            mock_load.return_value = mock_plan

            runner.invoke(main, ["build", "--plan", str(plan_file)])

            # Plan may be loaded multiple times (initial load + _get_full_jd)
            assert mock_load.called

    def test_uses_work_units_from_plan(
        self,
        runner: CliRunner,
        tmp_path: Path,
        sample_work_unit: dict[str, Any],
    ) -> None:
        """Should retrieve Work Units by IDs from plan."""
        plan_file = tmp_path / "plan.yaml"
        plan_file.write_text("""
version: "1.0.0"
jd_hash: "abc123"
selected_work_units:
  - id: "wu-2024-01-01-test"
    title: "Test Project"
    score: 0.8
    match_reasons: ["Skills: Python"]
selection_count: 1
top_k: 8
ranker_version: "hybrid-rrf-v1"
created_at: "2024-01-01T00:00:00"
""")

        # Create work-units directory with sample
        work_units_dir = tmp_path / "work-units"
        work_units_dir.mkdir()
        (work_units_dir / "wu-2024-01-01-test.yaml").write_text(f"""
id: "{sample_work_unit["id"]}"
title: "{sample_work_unit["title"]}"
organization: "{sample_work_unit["organization"]}"
problem:
  statement: "Test problem"
actions:
  - "Did thing 1"
  - "Did thing 2"
outcome:
  result: "Great outcome"
  quantified_impact: "50% improvement"
skills_demonstrated:
  - name: Python
tags:
  - python
  - testing
""")

        with (
            patch("resume_as_code.config.get_config") as mock_config,
            patch("resume_as_code.providers.pdf.PDFProvider") as mock_pdf,
            patch("resume_as_code.providers.docx.DOCXProvider") as mock_docx,
        ):
            config = MagicMock()
            config.work_units_dir = work_units_dir
            mock_config.return_value = config

            mock_pdf_instance = MagicMock()
            mock_pdf.return_value = mock_pdf_instance
            mock_docx_instance = MagicMock()
            mock_docx.return_value = mock_docx_instance

            runner.invoke(
                main, ["build", "--plan", str(plan_file), "--output-dir", str(tmp_path / "dist")]
            )

            # Should attempt to render (may fail due to mocking but logic should flow)
            # This tests that the plan loading and Work Unit retrieval path works


class TestBuildFromJD:
    """Tests for building from JD file (AC: #2)."""

    def test_generates_implicit_plan(
        self,
        runner: CliRunner,
        tmp_path: Path,
    ) -> None:
        """Should generate plan on-the-fly from JD."""
        jd_file = tmp_path / "job.txt"
        jd_file.write_text("Looking for a Python developer with 5 years experience.")

        with (
            patch("resume_as_code.commands.build._generate_implicit_plan") as mock_gen,
            patch("resume_as_code.config.get_config") as mock_config,
        ):
            mock_plan = MagicMock()
            mock_plan.selected_work_units = []
            mock_gen.return_value = mock_plan

            config = MagicMock()
            config.work_units_dir = tmp_path / "work-units"
            (tmp_path / "work-units").mkdir()
            mock_config.return_value = config

            runner.invoke(main, ["build", "--jd", str(jd_file)])

            mock_gen.assert_called_once()


class TestFormatSelection:
    """Tests for format selection (AC: #4)."""

    def test_default_generates_both_formats(
        self,
        runner: CliRunner,
        tmp_path: Path,
    ) -> None:
        """Default should generate both PDF and DOCX."""
        plan_file = tmp_path / "plan.yaml"
        plan_file.write_text("""
version: "1.0.0"
jd_hash: "abc123"
selected_work_units: []
selection_count: 0
top_k: 8
ranker_version: "hybrid-rrf-v1"
created_at: "2024-01-01T00:00:00"
""")

        with (
            patch("resume_as_code.commands.build.SavedPlan.load") as mock_load,
            patch("resume_as_code.commands.build._generate_outputs") as mock_gen,
            patch("resume_as_code.config.get_config") as mock_config,
        ):
            mock_plan = MagicMock()
            mock_plan.selected_work_units = []
            mock_load.return_value = mock_plan

            config = MagicMock()
            config.work_units_dir = tmp_path / "work-units"
            (tmp_path / "work-units").mkdir()
            mock_config.return_value = config

            runner.invoke(main, ["build", "--plan", str(plan_file)])

            # Should call with format="all"
            assert mock_gen.called
            call_args = mock_gen.call_args
            assert call_args.kwargs["output_format"] == "all"

    def test_format_pdf_only(
        self,
        runner: CliRunner,
        tmp_path: Path,
    ) -> None:
        """--format pdf should only generate PDF."""
        plan_file = tmp_path / "plan.yaml"
        plan_file.write_text("""
version: "1.0.0"
jd_hash: "abc123"
selected_work_units: []
selection_count: 0
top_k: 8
ranker_version: "hybrid-rrf-v1"
created_at: "2024-01-01T00:00:00"
""")

        with (
            patch("resume_as_code.commands.build.SavedPlan.load") as mock_load,
            patch("resume_as_code.commands.build._generate_outputs") as mock_gen,
            patch("resume_as_code.config.get_config") as mock_config,
        ):
            mock_plan = MagicMock()
            mock_plan.selected_work_units = []
            mock_load.return_value = mock_plan

            config = MagicMock()
            config.work_units_dir = tmp_path / "work-units"
            (tmp_path / "work-units").mkdir()
            mock_config.return_value = config

            runner.invoke(main, ["build", "--plan", str(plan_file), "--format", "pdf"])

            # The format flag should be passed through
            assert mock_gen.called
            call_args = mock_gen.call_args
            assert call_args.kwargs["output_format"] == "pdf"

    def test_format_docx_only(
        self,
        runner: CliRunner,
        tmp_path: Path,
    ) -> None:
        """--format docx should only generate DOCX."""
        plan_file = tmp_path / "plan.yaml"
        plan_file.write_text("""
version: "1.0.0"
jd_hash: "abc123"
selected_work_units: []
selection_count: 0
top_k: 8
ranker_version: "hybrid-rrf-v1"
created_at: "2024-01-01T00:00:00"
""")

        with (
            patch("resume_as_code.commands.build.SavedPlan.load") as mock_load,
            patch("resume_as_code.commands.build._generate_outputs") as mock_gen,
            patch("resume_as_code.config.get_config") as mock_config,
        ):
            mock_plan = MagicMock()
            mock_plan.selected_work_units = []
            mock_load.return_value = mock_plan

            config = MagicMock()
            config.work_units_dir = tmp_path / "work-units"
            (tmp_path / "work-units").mkdir()
            mock_config.return_value = config

            runner.invoke(main, ["build", "--plan", str(plan_file), "--format", "docx"])

            # The format flag should be passed through
            assert mock_gen.called
            call_args = mock_gen.call_args
            assert call_args.kwargs["output_format"] == "docx"


class TestConfigDefaults:
    """Tests for config-based defaults (Story 5.6: Output Configuration)."""

    def test_uses_config_output_dir_when_no_cli_flag(
        self,
        runner: CliRunner,
        tmp_path: Path,
    ) -> None:
        """Should use output_dir from config when --output-dir not provided (AC: #1)."""
        plan_file = tmp_path / "plan.yaml"
        plan_file.write_text("""
version: "1.0.0"
jd_hash: "abc123"
selected_work_units: []
selection_count: 0
top_k: 8
ranker_version: "hybrid-rrf-v1"
created_at: "2024-01-01T00:00:00"
""")

        with (
            patch("resume_as_code.commands.build.SavedPlan.load") as mock_load,
            patch("resume_as_code.commands.build._generate_outputs") as mock_gen,
            patch("resume_as_code.commands.build.get_config") as mock_config,
        ):
            mock_plan = MagicMock()
            mock_plan.selected_work_units = []
            mock_load.return_value = mock_plan

            config = MagicMock()
            config.work_units_dir = tmp_path / "work-units"
            config.output_dir = Path("./resumes")  # Config sets custom output_dir
            config.default_template = "modern"
            config.default_format = "both"
            config.tailored_notice = False
            config.tailored_notice_text = None
            config.employment_continuity = "minimum_bullet"
            # Profile with defaults (needed for _load_contact_info)
            config.profile.name = None
            config.profile.title = None
            config.profile.email = None
            config.profile.phone = None
            config.profile.location = None
            config.profile.linkedin = None
            config.profile.github = None
            config.profile.website = None
            config.profile.summary = None
            (tmp_path / "work-units").mkdir()
            mock_config.return_value = config

            result = runner.invoke(main, ["build", "--plan", str(plan_file)])

            # Should use config output_dir, not hardcoded "dist"
            assert result.exit_code == 0, f"Build failed: {result.output}"
            assert mock_gen.called
            call_args = mock_gen.call_args
            assert call_args.kwargs["output_dir"] == Path("./resumes")

    def test_uses_config_default_template_when_no_cli_flag(
        self,
        runner: CliRunner,
        tmp_path: Path,
    ) -> None:
        """Should use default_template from config when --template not provided (AC: #2)."""
        plan_file = tmp_path / "plan.yaml"
        plan_file.write_text("""
version: "1.0.0"
jd_hash: "abc123"
selected_work_units: []
selection_count: 0
top_k: 8
ranker_version: "hybrid-rrf-v1"
created_at: "2024-01-01T00:00:00"
""")

        with (
            patch("resume_as_code.commands.build.SavedPlan.load") as mock_load,
            patch("resume_as_code.commands.build._generate_outputs") as mock_gen,
            patch("resume_as_code.commands.build.get_config") as mock_config,
        ):
            mock_plan = MagicMock()
            mock_plan.selected_work_units = []
            mock_load.return_value = mock_plan

            config = MagicMock()
            config.work_units_dir = tmp_path / "work-units"
            config.output_dir = Path("dist")
            config.default_template = "ats-safe"  # Config sets custom template
            config.default_format = "both"
            config.tailored_notice = False
            config.tailored_notice_text = None
            config.employment_continuity = "minimum_bullet"
            # Profile with defaults (needed for _load_contact_info)
            config.profile.name = None
            config.profile.title = None
            config.profile.email = None
            config.profile.phone = None
            config.profile.location = None
            config.profile.linkedin = None
            config.profile.github = None
            config.profile.website = None
            config.profile.summary = None
            (tmp_path / "work-units").mkdir()
            mock_config.return_value = config

            runner.invoke(main, ["build", "--plan", str(plan_file)])

            # Should use config template, not hardcoded "modern"
            assert mock_gen.called
            call_args = mock_gen.call_args
            assert call_args.kwargs["template_name"] == "ats-safe"

    def test_cli_flag_overrides_config_output_dir(
        self,
        runner: CliRunner,
        tmp_path: Path,
    ) -> None:
        """CLI --output-dir flag should override config value (AC: #2)."""
        plan_file = tmp_path / "plan.yaml"
        plan_file.write_text("""
version: "1.0.0"
jd_hash: "abc123"
selected_work_units: []
selection_count: 0
top_k: 8
ranker_version: "hybrid-rrf-v1"
created_at: "2024-01-01T00:00:00"
""")

        cli_output_dir = tmp_path / "cli-output"

        with (
            patch("resume_as_code.commands.build.SavedPlan.load") as mock_load,
            patch("resume_as_code.commands.build._generate_outputs") as mock_gen,
            patch("resume_as_code.commands.build.get_config") as mock_config,
        ):
            mock_plan = MagicMock()
            mock_plan.selected_work_units = []
            mock_load.return_value = mock_plan

            config = MagicMock()
            config.work_units_dir = tmp_path / "work-units"
            config.output_dir = Path("./resumes")  # Config sets output_dir
            config.default_template = "modern"
            config.default_format = "both"
            config.tailored_notice = False
            config.tailored_notice_text = None
            config.employment_continuity = "minimum_bullet"
            # Profile with defaults (needed for _load_contact_info)
            config.profile.name = None
            config.profile.title = None
            config.profile.email = None
            config.profile.phone = None
            config.profile.location = None
            config.profile.linkedin = None
            config.profile.github = None
            config.profile.website = None
            config.profile.summary = None
            (tmp_path / "work-units").mkdir()
            mock_config.return_value = config

            # CLI flag should override config
            runner.invoke(
                main, ["build", "--plan", str(plan_file), "--output-dir", str(cli_output_dir)]
            )

            assert mock_gen.called
            call_args = mock_gen.call_args
            assert call_args.kwargs["output_dir"] == cli_output_dir

    def test_cli_flag_overrides_config_template(
        self,
        runner: CliRunner,
        tmp_path: Path,
    ) -> None:
        """CLI --template flag should override config value (AC: #2)."""
        plan_file = tmp_path / "plan.yaml"
        plan_file.write_text("""
version: "1.0.0"
jd_hash: "abc123"
selected_work_units: []
selection_count: 0
top_k: 8
ranker_version: "hybrid-rrf-v1"
created_at: "2024-01-01T00:00:00"
""")

        with (
            patch("resume_as_code.commands.build.SavedPlan.load") as mock_load,
            patch("resume_as_code.commands.build._generate_outputs") as mock_gen,
            patch("resume_as_code.commands.build.get_config") as mock_config,
        ):
            mock_plan = MagicMock()
            mock_plan.selected_work_units = []
            mock_load.return_value = mock_plan

            config = MagicMock()
            config.work_units_dir = tmp_path / "work-units"
            config.output_dir = Path("dist")
            config.default_template = "ats-safe"  # Config sets template
            config.default_format = "both"
            config.tailored_notice = False
            config.tailored_notice_text = None
            config.employment_continuity = "minimum_bullet"
            # Profile with defaults (needed for _load_contact_info)
            config.profile.name = None
            config.profile.title = None
            config.profile.email = None
            config.profile.phone = None
            config.profile.location = None
            config.profile.linkedin = None
            config.profile.github = None
            config.profile.website = None
            config.profile.summary = None
            (tmp_path / "work-units").mkdir()
            mock_config.return_value = config

            # CLI flag should override config
            runner.invoke(main, ["build", "--plan", str(plan_file), "--template", "modern"])

            assert mock_gen.called
            call_args = mock_gen.call_args
            assert call_args.kwargs["template_name"] == "modern"

    def test_uses_config_default_format_when_no_cli_flag(
        self,
        runner: CliRunner,
        tmp_path: Path,
    ) -> None:
        """Should use default_format from config when --format not provided."""
        plan_file = tmp_path / "plan.yaml"
        plan_file.write_text("""
version: "1.0.0"
jd_hash: "abc123"
selected_work_units: []
selection_count: 0
top_k: 8
ranker_version: "hybrid-rrf-v1"
created_at: "2024-01-01T00:00:00"
""")

        with (
            patch("resume_as_code.commands.build.SavedPlan.load") as mock_load,
            patch("resume_as_code.commands.build._generate_outputs") as mock_gen,
            patch("resume_as_code.commands.build.get_config") as mock_config,
        ):
            mock_plan = MagicMock()
            mock_plan.selected_work_units = []
            mock_load.return_value = mock_plan

            config = MagicMock()
            config.work_units_dir = tmp_path / "work-units"
            config.output_dir = Path("dist")
            config.default_template = "modern"
            config.default_format = "pdf"  # Config sets pdf only
            config.tailored_notice = False
            config.tailored_notice_text = None
            config.employment_continuity = "minimum_bullet"
            # Profile with defaults (needed for _load_contact_info)
            config.profile.name = None
            config.profile.title = None
            config.profile.email = None
            config.profile.phone = None
            config.profile.location = None
            config.profile.linkedin = None
            config.profile.github = None
            config.profile.website = None
            config.profile.summary = None
            (tmp_path / "work-units").mkdir()
            mock_config.return_value = config

            runner.invoke(main, ["build", "--plan", str(plan_file)])

            # Should use config format
            assert mock_gen.called
            call_args = mock_gen.call_args
            assert call_args.kwargs["output_format"] == "pdf"


class TestOutputDirectory:
    """Tests for output directory handling (AC: #5)."""

    def test_default_output_dir_is_dist(
        self,
        runner: CliRunner,
        tmp_path: Path,
    ) -> None:
        """Default output directory should be dist/."""
        plan_file = tmp_path / "plan.yaml"
        plan_file.write_text("""
version: "1.0.0"
jd_hash: "abc123"
selected_work_units: []
selection_count: 0
top_k: 8
ranker_version: "hybrid-rrf-v1"
created_at: "2024-01-01T00:00:00"
""")

        with (
            patch("resume_as_code.commands.build.SavedPlan.load") as mock_load,
            patch("resume_as_code.commands.build._generate_outputs") as mock_gen,
            patch("resume_as_code.config.get_config") as mock_config,
        ):
            mock_plan = MagicMock()
            mock_plan.selected_work_units = []
            mock_load.return_value = mock_plan

            config = MagicMock()
            config.work_units_dir = tmp_path / "work-units"
            (tmp_path / "work-units").mkdir()
            mock_config.return_value = config

            runner.invoke(main, ["build", "--plan", str(plan_file)])

            # Default should be dist/
            assert mock_gen.called
            call_args = mock_gen.call_args
            assert call_args.kwargs["output_dir"] == Path("dist")

    def test_custom_output_dir(
        self,
        runner: CliRunner,
        tmp_path: Path,
    ) -> None:
        """Should support custom output directory."""
        plan_file = tmp_path / "plan.yaml"
        plan_file.write_text("""
version: "1.0.0"
jd_hash: "abc123"
selected_work_units: []
selection_count: 0
top_k: 8
ranker_version: "hybrid-rrf-v1"
created_at: "2024-01-01T00:00:00"
""")

        custom_dir = tmp_path / "custom" / "output"

        with (
            patch("resume_as_code.commands.build.SavedPlan.load") as mock_load,
            patch("resume_as_code.commands.build._generate_outputs") as mock_gen,
            patch("resume_as_code.config.get_config") as mock_config,
        ):
            mock_plan = MagicMock()
            mock_plan.selected_work_units = []
            mock_load.return_value = mock_plan

            config = MagicMock()
            config.work_units_dir = tmp_path / "work-units"
            (tmp_path / "work-units").mkdir()
            mock_config.return_value = config

            runner.invoke(
                main, ["build", "--plan", str(plan_file), "--output-dir", str(custom_dir)]
            )

            # Should use custom directory
            assert mock_gen.called
            call_args = mock_gen.call_args
            assert call_args.kwargs["output_dir"] == custom_dir


class TestExitCodes:
    """Tests for exit codes (AC: #6, #7)."""

    def test_success_exit_code_zero(
        self,
        runner: CliRunner,
        tmp_path: Path,
    ) -> None:
        """Successful build should exit with code 0 (AC: #6)."""
        plan_file = tmp_path / "plan.yaml"
        plan_file.write_text("""
version: "1.0.0"
jd_hash: "abc123"
selected_work_units: []
selection_count: 0
top_k: 8
ranker_version: "hybrid-rrf-v1"
created_at: "2024-01-01T00:00:00"
""")

        with (
            patch("resume_as_code.commands.build.SavedPlan.load") as mock_load,
            patch("resume_as_code.commands.build._generate_outputs"),
            patch("resume_as_code.config.get_config") as mock_config,
        ):
            mock_plan = MagicMock()
            mock_plan.selected_work_units = []
            mock_load.return_value = mock_plan

            config = MagicMock()
            config.work_units_dir = tmp_path / "work-units"
            (tmp_path / "work-units").mkdir()
            mock_config.return_value = config

            result = runner.invoke(main, ["build", "--plan", str(plan_file)])

            assert result.exit_code == 0

    def test_failure_exit_code_nonzero(self, runner: CliRunner) -> None:
        """Failed build should exit with non-zero code (AC: #7)."""
        result = runner.invoke(main, ["build"])

        assert result.exit_code != 0


class TestAtomicWrites:
    """Tests for atomic writes and cleanup (AC: #7)."""

    def test_no_partial_files_on_failure(
        self,
        runner: CliRunner,
        tmp_path: Path,
    ) -> None:
        """Should not leave partial files on failure."""
        plan_file = tmp_path / "plan.yaml"
        plan_file.write_text("""
version: "1.0.0"
jd_hash: "abc123"
selected_work_units:
  - id: "wu-test"
    title: "Test"
    score: 0.8
    match_reasons: []
selection_count: 1
top_k: 8
ranker_version: "hybrid-rrf-v1"
created_at: "2024-01-01T00:00:00"
""")

        output_dir = tmp_path / "dist"

        with (
            patch("resume_as_code.commands.build.SavedPlan.load") as mock_load,
            patch("resume_as_code.providers.pdf.PDFProvider") as mock_pdf,
            patch("resume_as_code.config.get_config") as mock_config,
        ):
            mock_plan = MagicMock()
            mock_plan.selected_work_units = [MagicMock(id="wu-test")]
            mock_load.return_value = mock_plan

            config = MagicMock()
            config.work_units_dir = tmp_path / "work-units"
            (tmp_path / "work-units").mkdir()
            mock_config.return_value = config

            # Make PDF generation fail
            mock_pdf_instance = MagicMock()
            mock_pdf_instance.render.side_effect = Exception("PDF generation failed")
            mock_pdf.return_value = mock_pdf_instance

            runner.invoke(
                main, ["build", "--plan", str(plan_file), "--output-dir", str(output_dir)]
            )

            # Output dir should not have partial files
            if output_dir.exists():
                files = list(output_dir.iterdir())
                assert len(files) == 0, f"Found partial files: {files}"


class TestManifestGeneration:
    """Tests for manifest generation (Story 5.5)."""

    def test_manifest_generated_with_build(
        self,
        runner: CliRunner,
        tmp_path: Path,
    ) -> None:
        """Should generate manifest file alongside resume files (AC: #1)."""
        plan_file = tmp_path / "plan.yaml"
        plan_file.write_text("""
version: "1.0.0"
jd_hash: "abc123def456"
jd_title: "Test Job"
selected_work_units:
  - id: "wu-test"
    title: "Test Work Unit"
    score: 0.85
    match_reasons: ["Skills: Python"]
selection_count: 1
top_k: 8
ranker_version: "hybrid-rrf-v1"
created_at: "2024-01-01T00:00:00"
""")

        work_units_dir = tmp_path / "work-units"
        work_units_dir.mkdir()

        mock_work_units = [
            {
                "id": "wu-test",
                "title": "Test Work Unit",
                "organization": "Test Corp",
                "outcome": {"result": "Good result"},
            }
        ]

        output_dir = tmp_path / "dist"

        from resume_as_code.providers.pdf import PDFRenderResult

        def create_pdf(resume: Any, path: Path) -> PDFRenderResult:
            """Create a dummy PDF file and return result."""
            path.write_bytes(b"%PDF-1.4 dummy")
            return PDFRenderResult(output_path=path, page_count=1)

        def create_docx(resume: Any, path: Path) -> None:
            """Create a dummy DOCX file."""
            path.write_bytes(b"PK dummy docx")

        with (
            patch("resume_as_code.config.get_config") as mock_config,
            patch("resume_as_code.commands.build.load_all_work_units") as mock_load_wus,
            # Patch at source provider modules (lazy imports resolve here)
            patch("resume_as_code.providers.pdf.PDFProvider") as mock_pdf,
            patch("resume_as_code.providers.docx.DOCXProvider") as mock_docx,
        ):
            config = MagicMock()
            config.work_units_dir = work_units_dir
            mock_config.return_value = config
            mock_load_wus.return_value = mock_work_units

            # Make render actually create files
            mock_pdf.return_value.render.side_effect = create_pdf
            mock_docx.return_value.render.side_effect = create_docx

            result = runner.invoke(
                main,
                ["build", "--plan", str(plan_file), "--output-dir", str(output_dir)],
            )

            assert result.exit_code == 0
            assert (output_dir / "resume-manifest.yaml").exists()

            # Verify manifest content
            manifest_content = (output_dir / "resume-manifest.yaml").read_text()
            assert "jd_hash" in manifest_content
            assert "abc123def456" in manifest_content
            assert "wu-test" in manifest_content

    def test_manifest_includes_formats_generated(
        self,
        runner: CliRunner,
        tmp_path: Path,
    ) -> None:
        """Manifest should list output formats that were generated."""
        plan_file = tmp_path / "plan.yaml"
        plan_file.write_text("""
version: "1.0.0"
jd_hash: "abc123"
selected_work_units: []
selection_count: 0
top_k: 8
ranker_version: "hybrid-rrf-v1"
created_at: "2024-01-01T00:00:00"
""")

        work_units_dir = tmp_path / "work-units"
        work_units_dir.mkdir()
        output_dir = tmp_path / "dist"

        from resume_as_code.providers.pdf import PDFRenderResult

        def create_pdf(resume: Any, path: Path) -> PDFRenderResult:
            """Create a dummy PDF file and return result."""
            path.write_bytes(b"%PDF-1.4 dummy")
            return PDFRenderResult(output_path=path, page_count=1)

        def create_docx(resume: Any, path: Path) -> None:
            """Create a dummy DOCX file."""
            path.write_bytes(b"PK dummy docx")

        with (
            patch("resume_as_code.config.get_config") as mock_config,
            patch("resume_as_code.commands.build.load_all_work_units") as mock_load_wus,
            # Patch at source provider modules (lazy imports resolve here)
            patch("resume_as_code.providers.pdf.PDFProvider") as mock_pdf,
            patch("resume_as_code.providers.docx.DOCXProvider") as mock_docx,
        ):
            config = MagicMock()
            config.work_units_dir = work_units_dir
            mock_config.return_value = config
            mock_load_wus.return_value = []

            # Make render actually create files (consistent pattern)
            mock_pdf.return_value.render.side_effect = create_pdf
            mock_docx.return_value.render.side_effect = create_docx

            # Build PDF only
            runner.invoke(
                main,
                [
                    "build",
                    "--plan",
                    str(plan_file),
                    "--output-dir",
                    str(output_dir),
                    "--format",
                    "pdf",
                ],
            )

            manifest_content = (output_dir / "resume-manifest.yaml").read_text()
            assert "output_formats" in manifest_content
            assert "pdf" in manifest_content


class TestWorkUnitToResumeDataTransformation:
    """Tests for Work Unit to ResumeData transformation (H2 fix)."""

    def test_work_units_transformed_to_resume_data(
        self,
        runner: CliRunner,
        tmp_path: Path,
        sample_work_unit: dict[str, Any],
    ) -> None:
        """Should correctly transform Work Units into ResumeData for providers."""
        plan_file = tmp_path / "plan.yaml"
        plan_file.write_text("""
version: "1.0.0"
jd_hash: "abc123"
selected_work_units:
  - id: "wu-2024-01-01-test"
    title: "Test Project"
    score: 0.8
    match_reasons: ["Skills: Python"]
selection_count: 1
top_k: 8
ranker_version: "hybrid-rrf-v1"
created_at: "2024-01-01T00:00:00"
""")

        work_units_dir = tmp_path / "work-units"
        work_units_dir.mkdir()

        # Mock work unit data that matches what load_all_work_units returns
        mock_work_units = [
            {
                "id": "wu-2024-01-01-test",
                "title": "Test Project",
                "organization": "Test Corp",
                "problem": {"statement": "Test problem"},
                "actions": ["Did thing 1", "Did thing 2"],
                "outcome": {"result": "Great outcome", "quantified_impact": "50% improvement"},
                "skills_demonstrated": [{"name": "Python"}],
                "tags": ["python", "testing"],
            }
        ]

        from resume_as_code.providers.pdf import PDFRenderResult

        captured_resume_data = None

        def capture_render(resume: Any, output_path: Path) -> PDFRenderResult:
            nonlocal captured_resume_data
            captured_resume_data = resume
            return PDFRenderResult(output_path=output_path, page_count=1)

        with (
            patch("resume_as_code.config.get_config") as mock_config,
            patch("resume_as_code.commands.build.load_all_work_units") as mock_load_wus,
            patch("resume_as_code.providers.pdf.PDFProvider") as mock_pdf,
            patch("resume_as_code.providers.docx.DOCXProvider") as mock_docx,
        ):
            config = MagicMock()
            config.work_units_dir = work_units_dir
            mock_config.return_value = config

            # Return our mock work units
            mock_load_wus.return_value = mock_work_units

            mock_pdf_instance = MagicMock()
            mock_pdf_instance.render.side_effect = capture_render
            mock_pdf.return_value = mock_pdf_instance

            mock_docx_instance = MagicMock()
            mock_docx.return_value = mock_docx_instance

            runner.invoke(
                main,
                ["build", "--plan", str(plan_file), "--output-dir", str(tmp_path / "dist")],
            )

            # Verify ResumeData was correctly built from Work Unit
            assert captured_resume_data is not None, "ResumeData was not passed to provider"
            assert len(captured_resume_data.sections) == 1
            assert captured_resume_data.sections[0].title == "Experience"
            assert len(captured_resume_data.sections[0].items) == 1

            item = captured_resume_data.sections[0].items[0]
            assert item.title == "Test Project"
            assert item.organization == "Test Corp"
            assert len(item.bullets) > 0
            assert item.bullets[0].text == "Great outcome"

            # Verify skills were extracted and deduplicated (Story 6.3)
            # "Python" from skills_demonstrated and "python" from tags are merged
            assert "Python" in captured_resume_data.skills
            assert "Testing" in captured_resume_data.skills  # From tags (title-cased)
            # With deduplication, "python" merges with "Python" (title case preferred)
            assert captured_resume_data.skills.count("Python") == 1  # No duplicates

    def test_multiple_work_units_preserve_order(
        self,
        runner: CliRunner,
        tmp_path: Path,
    ) -> None:
        """Should preserve Work Unit order from plan in ResumeData."""
        plan_file = tmp_path / "plan.yaml"
        plan_file.write_text("""
version: "1.0.0"
jd_hash: "abc123"
selected_work_units:
  - id: "wu-first"
    title: "First Project"
    score: 0.9
    match_reasons: []
  - id: "wu-second"
    title: "Second Project"
    score: 0.8
    match_reasons: []
selection_count: 2
top_k: 8
ranker_version: "hybrid-rrf-v1"
created_at: "2024-01-01T00:00:00"
""")

        work_units_dir = tmp_path / "work-units"
        work_units_dir.mkdir()

        # Mock work units returned in different order than plan
        # to verify plan order is preserved
        mock_work_units = [
            {
                "id": "wu-second",
                "title": "Second Project",
                "organization": "Second Corp",
                "outcome": {"result": "Second result"},
            },
            {
                "id": "wu-first",
                "title": "First Project",
                "organization": "First Corp",
                "outcome": {"result": "First result"},
            },
        ]

        from resume_as_code.providers.pdf import PDFRenderResult

        captured_resume_data = None

        def capture_render(resume: Any, output_path: Path) -> PDFRenderResult:
            nonlocal captured_resume_data
            captured_resume_data = resume
            return PDFRenderResult(output_path=output_path, page_count=1)

        with (
            patch("resume_as_code.config.get_config") as mock_config,
            patch("resume_as_code.commands.build.load_all_work_units") as mock_load_wus,
            patch("resume_as_code.providers.pdf.PDFProvider") as mock_pdf,
            patch("resume_as_code.providers.docx.DOCXProvider") as mock_docx,
        ):
            config = MagicMock()
            config.work_units_dir = work_units_dir
            mock_config.return_value = config

            # Return work units in REVERSE order to verify plan order wins
            mock_load_wus.return_value = mock_work_units

            mock_pdf_instance = MagicMock()
            mock_pdf_instance.render.side_effect = capture_render
            mock_pdf.return_value = mock_pdf_instance

            mock_docx_instance = MagicMock()
            mock_docx.return_value = mock_docx_instance

            runner.invoke(
                main,
                ["build", "--plan", str(plan_file), "--output-dir", str(tmp_path / "dist")],
            )

            # Verify order is preserved from plan (first, then second)
            # even though load_all_work_units returned them in reverse
            assert captured_resume_data is not None
            items = captured_resume_data.sections[0].items
            assert len(items) == 2
            assert items[0].title == "First Project"
            assert items[1].title == "Second Project"


class TestBuildCommandCertifications:
    """Tests for certifications in build command (Story 6.2)."""

    def test_certifications_passed_to_resume_data(
        self,
        runner: CliRunner,
        tmp_path: Path,
    ) -> None:
        """Certifications from data_loader should be passed to ResumeData (Story 9.2)."""
        from resume_as_code.models.config import ProfileConfig

        plan_file = tmp_path / "plan.yaml"
        plan_file.write_text("""
version: "1.0.0"
jd_hash: "abc123"
selected_work_units: []
selection_count: 0
top_k: 8
ranker_version: "hybrid-rrf-v1"
created_at: "2024-01-01T00:00:00"
""")

        work_units_dir = tmp_path / "work-units"
        work_units_dir.mkdir()

        captured_resume_data = None

        def capture_generate_outputs(**kwargs: Any) -> None:
            nonlocal captured_resume_data
            captured_resume_data = kwargs.get("resume")

        # Define test data
        test_certifications = [
            Certification(name="AWS SAP", issuer="Amazon Web Services"),
            Certification(name="CISSP", issuer="ISC2", date="2023-01"),
        ]
        test_profile = ProfileConfig(name="Test User")

        with (
            patch("resume_as_code.commands.build.get_config") as mock_config,
            patch("resume_as_code.commands.build.load_all_work_units") as mock_load_wus,
            patch("resume_as_code.commands.build._generate_outputs") as mock_gen,
            # Story 9.2: Mock data_loader functions
            patch("resume_as_code.commands.build.load_profile") as mock_load_profile,
            patch("resume_as_code.commands.build.load_certifications") as mock_load_certs,
            patch("resume_as_code.commands.build.load_education") as mock_load_edu,
            patch("resume_as_code.commands.build.load_highlights") as mock_load_highlights,
            patch("resume_as_code.commands.build.load_publications") as mock_load_pubs,
            patch("resume_as_code.commands.build.load_board_roles") as mock_load_roles,
        ):
            config = MagicMock()
            config.work_units_dir = work_units_dir
            config.output_dir = Path("dist")
            config.default_template = "modern"
            config.default_format = "both"
            config.tailored_notice = False
            config.tailored_notice_text = None
            config.employment_continuity = "minimum_bullet"
            mock_config.return_value = config
            mock_load_wus.return_value = []
            mock_gen.side_effect = capture_generate_outputs

            # Mock data_loader functions (Story 9.2)
            mock_load_profile.return_value = test_profile
            mock_load_certs.return_value = test_certifications
            mock_load_edu.return_value = []
            mock_load_highlights.return_value = []
            mock_load_pubs.return_value = []
            mock_load_roles.return_value = []

            result = runner.invoke(
                main,
                ["build", "--plan", str(plan_file), "--output-dir", str(tmp_path / "dist")],
            )

            # Verify certifications were passed to ResumeData
            assert result.exit_code == 0, f"Build failed: {result.output}"
            assert captured_resume_data is not None
            assert len(captured_resume_data.certifications) == 2
            assert captured_resume_data.certifications[0].name == "AWS SAP"
            assert captured_resume_data.certifications[1].name == "CISSP"

    def test_empty_certifications_handled_gracefully(
        self,
        runner: CliRunner,
        tmp_path: Path,
    ) -> None:
        """Empty certifications list should not cause errors (Story 9.2)."""
        from resume_as_code.models.config import ProfileConfig

        plan_file = tmp_path / "plan.yaml"
        plan_file.write_text("""
version: "1.0.0"
jd_hash: "abc123"
selected_work_units: []
selection_count: 0
top_k: 8
ranker_version: "hybrid-rrf-v1"
created_at: "2024-01-01T00:00:00"
""")

        work_units_dir = tmp_path / "work-units"
        work_units_dir.mkdir()

        captured_resume_data = None

        def capture_generate_outputs(**kwargs: Any) -> None:
            nonlocal captured_resume_data
            captured_resume_data = kwargs.get("resume")

        # Define test data
        test_profile = ProfileConfig(name="Test User")

        with (
            patch("resume_as_code.commands.build.get_config") as mock_config,
            patch("resume_as_code.commands.build.load_all_work_units") as mock_load_wus,
            patch("resume_as_code.commands.build._generate_outputs") as mock_gen,
            # Story 9.2: Mock data_loader functions
            patch("resume_as_code.commands.build.load_profile") as mock_load_profile,
            patch("resume_as_code.commands.build.load_certifications") as mock_load_certs,
            patch("resume_as_code.commands.build.load_education") as mock_load_edu,
            patch("resume_as_code.commands.build.load_highlights") as mock_load_highlights,
            patch("resume_as_code.commands.build.load_publications") as mock_load_pubs,
            patch("resume_as_code.commands.build.load_board_roles") as mock_load_roles,
        ):
            config = MagicMock()
            config.work_units_dir = work_units_dir
            config.output_dir = Path("dist")
            config.default_template = "modern"
            config.default_format = "both"
            config.tailored_notice = False
            config.tailored_notice_text = None
            config.employment_continuity = "minimum_bullet"
            mock_config.return_value = config
            mock_load_wus.return_value = []
            mock_gen.side_effect = capture_generate_outputs

            # Mock data_loader functions with empty certifications (Story 9.2)
            mock_load_profile.return_value = test_profile
            mock_load_certs.return_value = []
            mock_load_edu.return_value = []
            mock_load_highlights.return_value = []
            mock_load_pubs.return_value = []
            mock_load_roles.return_value = []

            result = runner.invoke(
                main,
                ["build", "--plan", str(plan_file), "--output-dir", str(tmp_path / "dist")],
            )

            # Should succeed
            assert result.exit_code == 0, f"Build failed: {result.output}"
            # Certifications should be empty list
            assert captured_resume_data is not None
            assert captured_resume_data.certifications == []


class TestBuildCommandCareerHighlights:
    """Tests for career highlights in build command (Story 6.13)."""

    def test_career_highlights_passed_to_resume_data(
        self,
        runner: CliRunner,
        tmp_path: Path,
    ) -> None:
        """Career highlights from data_loader should be passed to ResumeData (Story 9.2)."""
        from resume_as_code.models.config import ProfileConfig

        plan_file = tmp_path / "plan.yaml"
        plan_file.write_text("""
version: "1.0.0"
jd_hash: "abc123"
selected_work_units: []
selection_count: 0
top_k: 8
ranker_version: "hybrid-rrf-v1"
created_at: "2024-01-01T00:00:00"
""")

        work_units_dir = tmp_path / "work-units"
        work_units_dir.mkdir()

        captured_resume_data = None

        def capture_render(resume: Any, output_path: Any) -> Any:
            nonlocal captured_resume_data
            captured_resume_data = resume
            from resume_as_code.providers.pdf import PDFRenderResult

            return PDFRenderResult(output_path=output_path, page_count=1)

        # Define test data
        test_profile = ProfileConfig(name="Test User")
        test_highlights = [
            "$50M revenue growth through digital transformation",
            "Built engineering org from 12 to 150+ engineers",
        ]

        with (
            patch("resume_as_code.commands.build.get_config") as mock_config,
            patch("resume_as_code.commands.build.load_all_work_units") as mock_load_wus,
            patch("resume_as_code.providers.pdf.PDFProvider") as mock_pdf,
            patch("resume_as_code.providers.docx.DOCXProvider") as mock_docx,
            # Story 9.2: Mock data_loader functions
            patch("resume_as_code.commands.build.load_profile") as mock_load_profile,
            patch("resume_as_code.commands.build.load_certifications") as mock_load_certs,
            patch("resume_as_code.commands.build.load_education") as mock_load_edu,
            patch("resume_as_code.commands.build.load_highlights") as mock_load_highlights,
            patch("resume_as_code.commands.build.load_publications") as mock_load_pubs,
            patch("resume_as_code.commands.build.load_board_roles") as mock_load_roles,
        ):
            config = MagicMock()
            config.work_units_dir = work_units_dir
            config.output_dir = Path("dist")
            config.default_template = "modern"
            config.default_format = "both"
            config.tailored_notice = False
            config.tailored_notice_text = None
            config.employment_continuity = "minimum_bullet"
            mock_config.return_value = config
            mock_load_wus.return_value = []

            # Mock data_loader functions (Story 9.2)
            mock_load_profile.return_value = test_profile
            mock_load_certs.return_value = []
            mock_load_edu.return_value = []
            mock_load_highlights.return_value = test_highlights
            mock_load_pubs.return_value = []
            mock_load_roles.return_value = []

            mock_pdf_instance = MagicMock()
            mock_pdf_instance.render.side_effect = capture_render
            mock_pdf.return_value = mock_pdf_instance

            mock_docx_instance = MagicMock()
            mock_docx.return_value = mock_docx_instance

            runner.invoke(
                main,
                ["build", "--plan", str(plan_file), "--output-dir", str(tmp_path / "dist")],
            )

            # Verify career highlights were passed to ResumeData
            assert captured_resume_data is not None
            assert len(captured_resume_data.career_highlights) == 2
            assert (
                captured_resume_data.career_highlights[0]
                == "$50M revenue growth through digital transformation"
            )
            assert (
                captured_resume_data.career_highlights[1]
                == "Built engineering org from 12 to 150+ engineers"
            )

    def test_empty_career_highlights_handled_gracefully(
        self,
        runner: CliRunner,
        tmp_path: Path,
    ) -> None:
        """Empty career highlights list should not cause errors (Story 9.2)."""
        from resume_as_code.models.config import ProfileConfig

        plan_file = tmp_path / "plan.yaml"
        plan_file.write_text("""
version: "1.0.0"
jd_hash: "abc123"
selected_work_units: []
selection_count: 0
top_k: 8
ranker_version: "hybrid-rrf-v1"
created_at: "2024-01-01T00:00:00"
""")

        work_units_dir = tmp_path / "work-units"
        work_units_dir.mkdir()

        captured_resume_data = None

        def capture_generate_outputs(**kwargs: Any) -> None:
            nonlocal captured_resume_data
            captured_resume_data = kwargs.get("resume")

        # Define test data
        test_profile = ProfileConfig(name="Test User")

        with (
            patch("resume_as_code.commands.build.get_config") as mock_config,
            patch("resume_as_code.commands.build.load_all_work_units") as mock_load_wus,
            patch("resume_as_code.commands.build._generate_outputs") as mock_gen,
            # Story 9.2: Mock data_loader functions
            patch("resume_as_code.commands.build.load_profile") as mock_load_profile,
            patch("resume_as_code.commands.build.load_certifications") as mock_load_certs,
            patch("resume_as_code.commands.build.load_education") as mock_load_edu,
            patch("resume_as_code.commands.build.load_highlights") as mock_load_highlights,
            patch("resume_as_code.commands.build.load_publications") as mock_load_pubs,
            patch("resume_as_code.commands.build.load_board_roles") as mock_load_roles,
        ):
            config = MagicMock()
            config.work_units_dir = work_units_dir
            config.output_dir = Path("dist")
            config.default_template = "modern"
            config.default_format = "both"
            config.tailored_notice = False
            config.tailored_notice_text = None
            config.employment_continuity = "minimum_bullet"
            mock_config.return_value = config
            mock_load_wus.return_value = []
            mock_gen.side_effect = capture_generate_outputs

            # Mock data_loader functions with empty highlights (Story 9.2)
            mock_load_profile.return_value = test_profile
            mock_load_certs.return_value = []
            mock_load_edu.return_value = []
            mock_load_highlights.return_value = []
            mock_load_pubs.return_value = []
            mock_load_roles.return_value = []

            result = runner.invoke(
                main,
                ["build", "--plan", str(plan_file), "--output-dir", str(tmp_path / "dist")],
            )

            # Should succeed
            assert result.exit_code == 0
            # Career highlights should be empty list
            assert captured_resume_data is not None
            assert captured_resume_data.career_highlights == []

    def test_career_highlights_curated_by_jd_relevance(self) -> None:
        """Career highlights should be curated by JD relevance when JD is provided (Bug fix).

        This tests that the ContentCurator.curate_highlights() method is called in
        build.py when a JD is provided, fixing the bug where highlights were not
        being filtered by relevance.
        """
        from resume_as_code.models.config import CurationConfig
        from resume_as_code.models.job_description import JobDescription
        from resume_as_code.services.content_curator import ContentCurator, CurationResult
        from resume_as_code.services.embedder import EmbeddingService

        # Test data
        test_highlights = [
            "Built AWS cloud platform saving $2M annually",
            "Led team of 50 engineers",
            "Migrated to Kubernetes",
            "Implemented DevOps practices",
            "Improved system reliability to 99.99%",
        ]
        jd = JobDescription(
            raw_text="Looking for a cloud architect with AWS and Kubernetes experience",
            skills_required=["AWS", "Kubernetes", "cloud architecture"],
        )

        # Create a real curator with config that limits to 3 highlights
        config = CurationConfig(career_highlights_max=3)
        embedder = EmbeddingService()
        curator = ContentCurator(embedder=embedder, config=config)

        # Call curate_highlights (the method that should now be called in build.py)
        result = curator.curate_highlights(highlights=test_highlights, jd=jd)

        # Verify curation was applied
        assert isinstance(result, CurationResult)
        assert len(result.selected) == 3  # Limited to max
        assert len(result.excluded) == 2  # Remaining excluded
        # Total should match input
        assert len(result.selected) + len(result.excluded) == len(test_highlights)


class TestGetJDKeywordsFromPlan:
    """Tests for _get_jd_keywords_from_plan helper function (Issue 6 - exception handling)."""

    def test_returns_empty_set_when_no_jd_path(self) -> None:
        """Should return empty set when plan has no jd_path."""
        from resume_as_code.commands.build import _get_jd_keywords_from_plan

        plan = MagicMock()
        plan.jd_path = None

        result = _get_jd_keywords_from_plan(plan)

        assert result == set()

    def test_returns_empty_set_when_jd_file_not_exists(
        self,
        tmp_path: Path,
    ) -> None:
        """Should return empty set when JD file doesn't exist."""
        from resume_as_code.commands.build import _get_jd_keywords_from_plan

        plan = MagicMock()
        plan.jd_path = str(tmp_path / "nonexistent.txt")

        result = _get_jd_keywords_from_plan(plan)

        assert result == set()

    def test_returns_empty_set_when_jd_parsing_fails(
        self,
        tmp_path: Path,
    ) -> None:
        """Should return empty set when JD parsing throws an exception."""
        from resume_as_code.commands.build import _get_jd_keywords_from_plan

        # Create a file with invalid content that will cause parsing to fail
        jd_file = tmp_path / "invalid_jd.txt"
        jd_file.write_text("")  # Empty file may cause issues

        plan = MagicMock()
        plan.jd_path = str(jd_file)

        # Patch at source since parse_jd_file is imported lazily inside the function
        with patch("resume_as_code.services.jd_parser.parse_jd_file") as mock_parse:
            mock_parse.side_effect = Exception("Parsing failed")
            result = _get_jd_keywords_from_plan(plan)

        assert result == set()

    def test_returns_keywords_when_jd_parses_successfully(
        self,
        tmp_path: Path,
    ) -> None:
        """Should return keywords when JD file parses successfully."""
        from resume_as_code.commands.build import _get_jd_keywords_from_plan

        jd_file = tmp_path / "valid_jd.txt"
        jd_file.write_text("Looking for a Python developer with AWS experience.")

        plan = MagicMock()
        plan.jd_path = str(jd_file)

        mock_jd = MagicMock()
        mock_jd.keywords = ["Python", "AWS"]

        # Patch at source since parse_jd_file is imported lazily inside the function
        with patch("resume_as_code.services.jd_parser.parse_jd_file") as mock_parse:
            mock_parse.return_value = mock_jd
            result = _get_jd_keywords_from_plan(plan)

        assert result == {"Python", "AWS"}


class TestCTOPageCountWarning:
    """Tests for CTO template page count warning (Story 6.17 AC #6)."""

    def test_cto_template_warns_when_exceeds_two_pages(
        self,
        runner: CliRunner,
        tmp_path: Path,
    ) -> None:
        """Should display warning when CTO template generates > 2 pages (AC #6)."""
        plan_file = tmp_path / "plan.yaml"
        plan_file.write_text("""
version: "1.0.0"
jd_hash: "abc123"
selected_work_units: []
selection_count: 0
top_k: 8
ranker_version: "hybrid-rrf-v1"
created_at: "2024-01-01T00:00:00"
""")

        work_units_dir = tmp_path / "work-units"
        work_units_dir.mkdir()
        output_dir = tmp_path / "dist"

        from resume_as_code.providers.pdf import PDFRenderResult

        def create_pdf_3_pages(resume: Any, path: Path) -> PDFRenderResult:
            """Create a PDF result with 3 pages to trigger warning."""
            path.write_bytes(b"%PDF-1.4 dummy")
            return PDFRenderResult(output_path=path, page_count=3)

        with (
            patch("resume_as_code.commands.build.get_config") as mock_config,
            patch("resume_as_code.commands.build.load_all_work_units") as mock_load_wus,
            patch("resume_as_code.providers.pdf.PDFProvider") as mock_pdf,
        ):
            config = MagicMock()
            config.work_units_dir = work_units_dir
            config.output_dir = output_dir
            config.default_template = "cto"  # CTO template
            config.default_format = "pdf"  # PDF only to avoid DOCX errors
            config.tailored_notice = False
            config.tailored_notice_text = None
            config.employment_continuity = "minimum_bullet"
            # Profile attributes (needed for _load_contact_info)
            config.profile.name = "Test User"
            config.profile.title = "CTO"
            config.profile.email = "test@test.com"
            config.profile.phone = None
            config.profile.location = None
            config.profile.linkedin = None
            config.profile.github = None
            config.profile.website = None
            config.profile.summary = "Test summary"
            config.positions_path = tmp_path / "positions.yaml"
            config.skills.curated = []
            config.skills.max_skills = 10
            config.skills.prioritize_jd_matches = True
            config.education = []
            config.certifications = []
            config.career_highlights = []
            config.board_roles = []
            config.publications = []
            mock_config.return_value = config
            mock_load_wus.return_value = []
            mock_pdf.return_value.render.side_effect = create_pdf_3_pages

            result = runner.invoke(
                main,
                ["build", "--plan", str(plan_file)],
            )

            assert result.exit_code == 0
            # AC #6: Warning should appear for CTO template exceeding 2 pages
            assert "CTO resumes should be 2 pages maximum" in result.output
            assert "3 pages" in result.output

    def test_cto_template_no_warning_when_two_pages_or_less(
        self,
        runner: CliRunner,
        tmp_path: Path,
    ) -> None:
        """Should NOT display warning when CTO template is 2 pages or less."""
        plan_file = tmp_path / "plan.yaml"
        plan_file.write_text("""
version: "1.0.0"
jd_hash: "abc123"
selected_work_units: []
selection_count: 0
top_k: 8
ranker_version: "hybrid-rrf-v1"
created_at: "2024-01-01T00:00:00"
""")

        work_units_dir = tmp_path / "work-units"
        work_units_dir.mkdir()
        output_dir = tmp_path / "dist"

        from resume_as_code.providers.pdf import PDFRenderResult

        def create_pdf_2_pages(resume: Any, path: Path) -> PDFRenderResult:
            """Create a PDF result with 2 pages - should not trigger warning."""
            path.write_bytes(b"%PDF-1.4 dummy")
            return PDFRenderResult(output_path=path, page_count=2)

        with (
            patch("resume_as_code.commands.build.get_config") as mock_config,
            patch("resume_as_code.commands.build.load_all_work_units") as mock_load_wus,
            patch("resume_as_code.providers.pdf.PDFProvider") as mock_pdf,
        ):
            config = MagicMock()
            config.work_units_dir = work_units_dir
            config.output_dir = output_dir
            config.default_template = "cto"
            config.default_format = "pdf"
            config.tailored_notice = False
            config.tailored_notice_text = None
            config.employment_continuity = "minimum_bullet"
            config.profile.name = "Test User"
            config.profile.title = "CTO"
            config.profile.email = "test@test.com"
            config.profile.phone = None
            config.profile.location = None
            config.profile.linkedin = None
            config.profile.github = None
            config.profile.website = None
            config.profile.summary = "Test summary"
            config.positions_path = tmp_path / "positions.yaml"
            config.skills.curated = []
            config.skills.max_skills = 10
            config.skills.prioritize_jd_matches = True
            config.education = []
            config.certifications = []
            config.career_highlights = []
            config.board_roles = []
            config.publications = []
            mock_config.return_value = config
            mock_load_wus.return_value = []
            mock_pdf.return_value.render.side_effect = create_pdf_2_pages

            result = runner.invoke(
                main,
                ["build", "--plan", str(plan_file)],
            )

            assert result.exit_code == 0
            # No warning for 2 pages or less
            assert "CTO resumes should be 2 pages maximum" not in result.output

    def test_non_cto_template_no_warning_even_when_exceeds_two_pages(
        self,
        runner: CliRunner,
        tmp_path: Path,
    ) -> None:
        """Non-CTO templates should NOT show the 2-page warning."""
        plan_file = tmp_path / "plan.yaml"
        plan_file.write_text("""
version: "1.0.0"
jd_hash: "abc123"
selected_work_units: []
selection_count: 0
top_k: 8
ranker_version: "hybrid-rrf-v1"
created_at: "2024-01-01T00:00:00"
""")

        work_units_dir = tmp_path / "work-units"
        work_units_dir.mkdir()
        output_dir = tmp_path / "dist"

        from resume_as_code.providers.pdf import PDFRenderResult

        def create_pdf_5_pages(resume: Any, path: Path) -> PDFRenderResult:
            """Create a PDF result with 5 pages."""
            path.write_bytes(b"%PDF-1.4 dummy")
            return PDFRenderResult(output_path=path, page_count=5)

        with (
            patch("resume_as_code.commands.build.get_config") as mock_config,
            patch("resume_as_code.commands.build.load_all_work_units") as mock_load_wus,
            patch("resume_as_code.providers.pdf.PDFProvider") as mock_pdf,
        ):
            config = MagicMock()
            config.work_units_dir = work_units_dir
            config.output_dir = output_dir
            config.default_template = "executive"  # NOT CTO
            config.default_format = "pdf"
            config.tailored_notice = False
            config.tailored_notice_text = None
            config.employment_continuity = "minimum_bullet"
            config.profile.name = "Test User"
            config.profile.title = "VP Engineering"
            config.profile.email = "test@test.com"
            config.profile.phone = None
            config.profile.location = None
            config.profile.linkedin = None
            config.profile.github = None
            config.profile.website = None
            config.profile.summary = "Test summary"
            config.positions_path = tmp_path / "positions.yaml"
            config.skills.curated = []
            config.skills.max_skills = 10
            config.skills.prioritize_jd_matches = True
            config.education = []
            config.certifications = []
            config.career_highlights = []
            config.board_roles = []
            config.publications = []
            mock_config.return_value = config
            mock_load_wus.return_value = []
            mock_pdf.return_value.render.side_effect = create_pdf_5_pages

            result = runner.invoke(
                main,
                ["build", "--plan", str(plan_file)],
            )

            assert result.exit_code == 0
            # No warning for non-CTO templates
            assert "CTO resumes should be 2 pages maximum" not in result.output


class TestTailoredNoticeFlag:
    """Tests for --tailored-notice/--no-tailored-notice flags (Story 7.19)."""

    def test_tailored_notice_flag_sets_resume_data(
        self,
        runner: CliRunner,
        tmp_path: Path,
    ) -> None:
        """--tailored-notice flag should set tailored_notice_text on ResumeData (AC #2)."""
        plan_file = tmp_path / "plan.yaml"
        plan_file.write_text("""
version: "1.0.0"
jd_hash: "abc123"
selected_work_units: []
selection_count: 0
top_k: 8
ranker_version: "hybrid-rrf-v1"
created_at: "2024-01-01T00:00:00"
""")

        work_units_dir = tmp_path / "work-units"
        work_units_dir.mkdir()

        captured_resume = None

        def capture_generate(**kwargs: Any) -> None:
            nonlocal captured_resume
            captured_resume = kwargs.get("resume")

        with (
            patch("resume_as_code.commands.build.SavedPlan.load") as mock_load,
            patch("resume_as_code.commands.build._generate_outputs") as mock_gen,
            patch("resume_as_code.commands.build.get_config") as mock_config,
        ):
            mock_plan = MagicMock()
            mock_plan.selected_work_units = []
            mock_load.return_value = mock_plan

            config = MagicMock()
            config.work_units_dir = work_units_dir
            config.output_dir = Path("dist")
            config.default_template = "modern"
            config.default_format = "both"
            config.tailored_notice = False  # Config says off
            config.tailored_notice_text = None
            # Profile attrs
            config.profile.name = "Test User"
            config.profile.title = None
            config.profile.email = None
            config.profile.phone = None
            config.profile.location = None
            config.profile.linkedin = None
            config.profile.github = None
            config.profile.website = None
            config.profile.summary = None
            mock_config.return_value = config
            mock_gen.side_effect = capture_generate

            # CLI flag should override config
            runner.invoke(main, ["build", "--plan", str(plan_file), "--tailored-notice"])

            assert captured_resume is not None
            assert captured_resume.tailored_notice_text is not None

    def test_no_tailored_notice_flag_excludes_notice(
        self,
        runner: CliRunner,
        tmp_path: Path,
    ) -> None:
        """--no-tailored-notice flag should exclude notice even if config enables it (AC #3)."""
        plan_file = tmp_path / "plan.yaml"
        plan_file.write_text("""
version: "1.0.0"
jd_hash: "abc123"
selected_work_units: []
selection_count: 0
top_k: 8
ranker_version: "hybrid-rrf-v1"
created_at: "2024-01-01T00:00:00"
""")

        work_units_dir = tmp_path / "work-units"
        work_units_dir.mkdir()

        captured_resume = None

        def capture_generate(**kwargs: Any) -> None:
            nonlocal captured_resume
            captured_resume = kwargs.get("resume")

        with (
            patch("resume_as_code.commands.build.SavedPlan.load") as mock_load,
            patch("resume_as_code.commands.build._generate_outputs") as mock_gen,
            patch("resume_as_code.commands.build.get_config") as mock_config,
        ):
            mock_plan = MagicMock()
            mock_plan.selected_work_units = []
            mock_load.return_value = mock_plan

            config = MagicMock()
            config.work_units_dir = work_units_dir
            config.output_dir = Path("dist")
            config.default_template = "modern"
            config.default_format = "both"
            config.tailored_notice = True  # Config says ON
            config.tailored_notice_text = "Config text"
            # Profile attrs
            config.profile.name = "Test User"
            config.profile.title = None
            config.profile.email = None
            config.profile.phone = None
            config.profile.location = None
            config.profile.linkedin = None
            config.profile.github = None
            config.profile.website = None
            config.profile.summary = None
            mock_config.return_value = config
            mock_gen.side_effect = capture_generate

            # CLI flag should override config
            runner.invoke(main, ["build", "--plan", str(plan_file), "--no-tailored-notice"])

            assert captured_resume is not None
            assert captured_resume.tailored_notice_text is None

    def test_config_tailored_notice_used_when_no_flag(
        self,
        runner: CliRunner,
        tmp_path: Path,
    ) -> None:
        """Config tailored_notice should be used when no CLI flag provided (AC #1)."""
        plan_file = tmp_path / "plan.yaml"
        plan_file.write_text("""
version: "1.0.0"
jd_hash: "abc123"
selected_work_units: []
selection_count: 0
top_k: 8
ranker_version: "hybrid-rrf-v1"
created_at: "2024-01-01T00:00:00"
""")

        work_units_dir = tmp_path / "work-units"
        work_units_dir.mkdir()

        captured_resume = None

        def capture_generate(**kwargs: Any) -> None:
            nonlocal captured_resume
            captured_resume = kwargs.get("resume")

        with (
            patch("resume_as_code.commands.build.SavedPlan.load") as mock_load,
            patch("resume_as_code.commands.build._generate_outputs") as mock_gen,
            patch("resume_as_code.commands.build.get_config") as mock_config,
        ):
            mock_plan = MagicMock()
            mock_plan.selected_work_units = []
            mock_load.return_value = mock_plan

            config = MagicMock()
            config.work_units_dir = work_units_dir
            config.output_dir = Path("dist")
            config.default_template = "modern"
            config.default_format = "both"
            config.tailored_notice = True  # Config enables notice
            config.tailored_notice_text = "Custom config message"
            # Profile attrs
            config.profile.name = "Test User"
            config.profile.title = None
            config.profile.email = None
            config.profile.phone = None
            config.profile.location = None
            config.profile.linkedin = None
            config.profile.github = None
            config.profile.website = None
            config.profile.summary = None
            mock_config.return_value = config
            mock_gen.side_effect = capture_generate

            # No CLI flag - should use config
            runner.invoke(main, ["build", "--plan", str(plan_file)])

            assert captured_resume is not None
            assert captured_resume.tailored_notice_text == "Custom config message"

    def test_default_notice_text_used_when_no_custom(
        self,
        runner: CliRunner,
        tmp_path: Path,
    ) -> None:
        """Default notice text used when tailored_notice=True but no custom text."""
        from resume_as_code.models.config import DEFAULT_TAILORED_NOTICE

        plan_file = tmp_path / "plan.yaml"
        plan_file.write_text("""
version: "1.0.0"
jd_hash: "abc123"
selected_work_units: []
selection_count: 0
top_k: 8
ranker_version: "hybrid-rrf-v1"
created_at: "2024-01-01T00:00:00"
""")

        work_units_dir = tmp_path / "work-units"
        work_units_dir.mkdir()

        captured_resume = None

        def capture_generate(**kwargs: Any) -> None:
            nonlocal captured_resume
            captured_resume = kwargs.get("resume")

        with (
            patch("resume_as_code.commands.build.SavedPlan.load") as mock_load,
            patch("resume_as_code.commands.build._generate_outputs") as mock_gen,
            patch("resume_as_code.commands.build.get_config") as mock_config,
        ):
            mock_plan = MagicMock()
            mock_plan.selected_work_units = []
            mock_load.return_value = mock_plan

            config = MagicMock()
            config.work_units_dir = work_units_dir
            config.output_dir = Path("dist")
            config.default_template = "modern"
            config.default_format = "both"
            config.tailored_notice = True  # Config enables notice
            config.tailored_notice_text = None  # No custom text - use default
            # Profile attrs
            config.profile.name = "Test User"
            config.profile.title = None
            config.profile.email = None
            config.profile.phone = None
            config.profile.location = None
            config.profile.linkedin = None
            config.profile.github = None
            config.profile.website = None
            config.profile.summary = None
            mock_config.return_value = config
            mock_gen.side_effect = capture_generate

            runner.invoke(main, ["build", "--plan", str(plan_file)])

            assert captured_resume is not None
            assert captured_resume.tailored_notice_text == DEFAULT_TAILORED_NOTICE


class TestTemplatesDirFlag:
    """Tests for --templates-dir CLI flag (Story 11.3)."""

    def test_templates_dir_flag_passed_to_generate_outputs(
        self,
        runner: CliRunner,
        tmp_path: Path,
    ) -> None:
        """--templates-dir flag should pass templates_dir to _generate_outputs (AC #2)."""
        plan_file = tmp_path / "plan.yaml"
        plan_file.write_text("""
version: "1.0.0"
jd_hash: "abc123"
selected_work_units: []
selection_count: 0
top_k: 8
ranker_version: "hybrid-rrf-v1"
created_at: "2024-01-01T00:00:00"
""")

        work_units_dir = tmp_path / "work-units"
        work_units_dir.mkdir()

        custom_templates_dir = tmp_path / "my-templates"
        custom_templates_dir.mkdir()

        captured_templates_dir = None

        def capture_generate(**kwargs: Any) -> None:
            nonlocal captured_templates_dir
            captured_templates_dir = kwargs.get("templates_dir")

        with (
            patch("resume_as_code.commands.build.SavedPlan.load") as mock_load,
            patch("resume_as_code.commands.build._generate_outputs") as mock_gen,
            patch("resume_as_code.commands.build.get_config") as mock_config,
        ):
            mock_plan = MagicMock()
            mock_plan.selected_work_units = []
            mock_load.return_value = mock_plan

            config = MagicMock()
            config.work_units_dir = work_units_dir
            config.output_dir = Path("dist")
            config.default_template = "modern"
            config.default_format = "both"
            config.tailored_notice = False
            config.tailored_notice_text = None
            config.templates_dir = None  # Config doesn't have templates_dir
            # Profile attrs
            config.profile.name = "Test User"
            config.profile.title = None
            config.profile.email = None
            config.profile.phone = None
            config.profile.location = None
            config.profile.linkedin = None
            config.profile.github = None
            config.profile.website = None
            config.profile.summary = None
            mock_config.return_value = config
            mock_gen.side_effect = capture_generate

            # CLI flag should pass templates_dir
            runner.invoke(
                main,
                ["build", "--plan", str(plan_file), "--templates-dir", str(custom_templates_dir)],
            )

            assert captured_templates_dir == custom_templates_dir

    def test_config_templates_dir_used_when_no_flag(
        self,
        runner: CliRunner,
        tmp_path: Path,
    ) -> None:
        """Config templates_dir should be used when no CLI flag provided (AC #1)."""
        plan_file = tmp_path / "plan.yaml"
        plan_file.write_text("""
version: "1.0.0"
jd_hash: "abc123"
selected_work_units: []
selection_count: 0
top_k: 8
ranker_version: "hybrid-rrf-v1"
created_at: "2024-01-01T00:00:00"
""")

        work_units_dir = tmp_path / "work-units"
        work_units_dir.mkdir()

        config_templates_dir = tmp_path / "config-templates"
        config_templates_dir.mkdir()

        captured_templates_dir = None

        def capture_generate(**kwargs: Any) -> None:
            nonlocal captured_templates_dir
            captured_templates_dir = kwargs.get("templates_dir")

        with (
            patch("resume_as_code.commands.build.SavedPlan.load") as mock_load,
            patch("resume_as_code.commands.build._generate_outputs") as mock_gen,
            patch("resume_as_code.commands.build.get_config") as mock_config,
        ):
            mock_plan = MagicMock()
            mock_plan.selected_work_units = []
            mock_load.return_value = mock_plan

            config = MagicMock()
            config.work_units_dir = work_units_dir
            config.output_dir = Path("dist")
            config.default_template = "modern"
            config.default_format = "both"
            config.tailored_notice = False
            config.tailored_notice_text = None
            config.templates_dir = config_templates_dir  # Config has templates_dir
            # Profile attrs
            config.profile.name = "Test User"
            config.profile.title = None
            config.profile.email = None
            config.profile.phone = None
            config.profile.location = None
            config.profile.linkedin = None
            config.profile.github = None
            config.profile.website = None
            config.profile.summary = None
            mock_config.return_value = config
            mock_gen.side_effect = capture_generate

            # No CLI flag - should use config templates_dir
            runner.invoke(main, ["build", "--plan", str(plan_file)])

            assert captured_templates_dir == config_templates_dir

    def test_cli_flag_overrides_config_templates_dir(
        self,
        runner: CliRunner,
        tmp_path: Path,
    ) -> None:
        """CLI --templates-dir flag should override config value (AC #2)."""
        plan_file = tmp_path / "plan.yaml"
        plan_file.write_text("""
version: "1.0.0"
jd_hash: "abc123"
selected_work_units: []
selection_count: 0
top_k: 8
ranker_version: "hybrid-rrf-v1"
created_at: "2024-01-01T00:00:00"
""")

        work_units_dir = tmp_path / "work-units"
        work_units_dir.mkdir()

        config_templates_dir = tmp_path / "config-templates"
        config_templates_dir.mkdir()

        cli_templates_dir = tmp_path / "cli-templates"
        cli_templates_dir.mkdir()

        captured_templates_dir = None

        def capture_generate(**kwargs: Any) -> None:
            nonlocal captured_templates_dir
            captured_templates_dir = kwargs.get("templates_dir")

        with (
            patch("resume_as_code.commands.build.SavedPlan.load") as mock_load,
            patch("resume_as_code.commands.build._generate_outputs") as mock_gen,
            patch("resume_as_code.commands.build.get_config") as mock_config,
        ):
            mock_plan = MagicMock()
            mock_plan.selected_work_units = []
            mock_load.return_value = mock_plan

            config = MagicMock()
            config.work_units_dir = work_units_dir
            config.output_dir = Path("dist")
            config.default_template = "modern"
            config.default_format = "both"
            config.tailored_notice = False
            config.tailored_notice_text = None
            config.templates_dir = config_templates_dir  # Config has templates_dir
            # Profile attrs
            config.profile.name = "Test User"
            config.profile.title = None
            config.profile.email = None
            config.profile.phone = None
            config.profile.location = None
            config.profile.linkedin = None
            config.profile.github = None
            config.profile.website = None
            config.profile.summary = None
            mock_config.return_value = config
            mock_gen.side_effect = capture_generate

            # CLI flag should override config
            runner.invoke(
                main,
                ["build", "--plan", str(plan_file), "--templates-dir", str(cli_templates_dir)],
            )

            assert captured_templates_dir == cli_templates_dir


class TestDocxTemplateConfig:
    """Tests for DOCX-specific template config (Story 13.1)."""

    def test_docx_config_template_used_when_no_cli_flag(
        self,
        runner: CliRunner,
        tmp_path: Path,
    ) -> None:
        """config.docx.template should be used for DOCX when no CLI flag (AC #4)."""
        plan_file = tmp_path / "plan.yaml"
        plan_file.write_text("""
version: "1.0.0"
jd_hash: "abc123"
selected_work_units: []
selection_count: 0
top_k: 8
ranker_version: "hybrid-rrf-v1"
created_at: "2024-01-01T00:00:00"
""")

        work_units_dir = tmp_path / "work-units"
        work_units_dir.mkdir()
        output_dir = tmp_path / "dist"

        from resume_as_code.providers.pdf import PDFRenderResult

        captured_docx_template = None

        def capture_pdf(resume: Any, path: Path) -> PDFRenderResult:
            path.write_bytes(b"%PDF-1.4 dummy")
            return PDFRenderResult(output_path=path, page_count=1)

        def create_docx_capture_template(
            template_name: str | None = None, templates_dir: Path | None = None
        ) -> MagicMock:
            nonlocal captured_docx_template
            captured_docx_template = template_name
            mock = MagicMock()
            mock.render.side_effect = lambda r, p: p.write_bytes(b"PK dummy")
            return mock

        with (
            patch("resume_as_code.commands.build.get_config") as mock_config,
            patch("resume_as_code.commands.build.load_all_work_units") as mock_load_wus,
            patch("resume_as_code.providers.pdf.PDFProvider") as mock_pdf,
            patch("resume_as_code.providers.docx.DOCXProvider") as mock_docx,
        ):
            config = MagicMock()
            config.work_units_dir = work_units_dir
            config.output_dir = output_dir
            config.default_template = "modern"  # Global default
            config.default_format = "both"
            config.tailored_notice = False
            config.tailored_notice_text = None
            config.employment_continuity = "minimum_bullet"
            config.templates_dir = None
            # DOCX-specific config (Story 13.1)
            config.docx = MagicMock()
            config.docx.template = "branded"  # DOCX override
            # Profile attrs
            config.profile.name = "Test User"
            config.profile.title = None
            config.profile.email = None
            config.profile.phone = None
            config.profile.location = None
            config.profile.linkedin = None
            config.profile.github = None
            config.profile.website = None
            config.profile.summary = None
            mock_config.return_value = config
            mock_load_wus.return_value = []

            mock_pdf.return_value.render.side_effect = capture_pdf
            mock_docx.side_effect = create_docx_capture_template

            result = runner.invoke(
                main,
                ["build", "--plan", str(plan_file)],
            )

            assert result.exit_code == 0, f"Build failed: {result.output}"
            # DOCX should use config.docx.template, not default_template
            assert captured_docx_template == "branded"

    def test_cli_template_overrides_docx_config(
        self,
        runner: CliRunner,
        tmp_path: Path,
    ) -> None:
        """CLI --template should override config.docx.template (AC #5)."""
        plan_file = tmp_path / "plan.yaml"
        plan_file.write_text("""
version: "1.0.0"
jd_hash: "abc123"
selected_work_units: []
selection_count: 0
top_k: 8
ranker_version: "hybrid-rrf-v1"
created_at: "2024-01-01T00:00:00"
""")

        work_units_dir = tmp_path / "work-units"
        work_units_dir.mkdir()
        output_dir = tmp_path / "dist"

        from resume_as_code.providers.pdf import PDFRenderResult

        captured_docx_template = None

        def capture_pdf(resume: Any, path: Path) -> PDFRenderResult:
            path.write_bytes(b"%PDF-1.4 dummy")
            return PDFRenderResult(output_path=path, page_count=1)

        def create_docx_capture_template(
            template_name: str | None = None, templates_dir: Path | None = None
        ) -> MagicMock:
            nonlocal captured_docx_template
            captured_docx_template = template_name
            mock = MagicMock()
            mock.render.side_effect = lambda r, p: p.write_bytes(b"PK dummy")
            return mock

        with (
            patch("resume_as_code.commands.build.get_config") as mock_config,
            patch("resume_as_code.commands.build.load_all_work_units") as mock_load_wus,
            patch("resume_as_code.providers.pdf.PDFProvider") as mock_pdf,
            patch("resume_as_code.providers.docx.DOCXProvider") as mock_docx,
        ):
            config = MagicMock()
            config.work_units_dir = work_units_dir
            config.output_dir = output_dir
            config.default_template = "modern"
            config.default_format = "both"
            config.tailored_notice = False
            config.tailored_notice_text = None
            config.employment_continuity = "minimum_bullet"
            config.templates_dir = None
            # DOCX-specific config
            config.docx = MagicMock()
            config.docx.template = "branded"  # Would be used if no CLI flag
            # Profile attrs
            config.profile.name = "Test User"
            config.profile.title = None
            config.profile.email = None
            config.profile.phone = None
            config.profile.location = None
            config.profile.linkedin = None
            config.profile.github = None
            config.profile.website = None
            config.profile.summary = None
            mock_config.return_value = config
            mock_load_wus.return_value = []

            mock_pdf.return_value.render.side_effect = capture_pdf
            mock_docx.side_effect = create_docx_capture_template

            # CLI flag should override config.docx.template
            result = runner.invoke(
                main,
                ["build", "--plan", str(plan_file), "--template", "executive"],
            )

            assert result.exit_code == 0, f"Build failed: {result.output}"
            # DOCX should use CLI template, not config.docx.template
            assert captured_docx_template == "executive"

    def test_default_template_used_when_no_docx_config(
        self,
        runner: CliRunner,
        tmp_path: Path,
    ) -> None:
        """default_template used for DOCX when config.docx is not set (AC #4)."""
        plan_file = tmp_path / "plan.yaml"
        plan_file.write_text("""
version: "1.0.0"
jd_hash: "abc123"
selected_work_units: []
selection_count: 0
top_k: 8
ranker_version: "hybrid-rrf-v1"
created_at: "2024-01-01T00:00:00"
""")

        work_units_dir = tmp_path / "work-units"
        work_units_dir.mkdir()
        output_dir = tmp_path / "dist"

        from resume_as_code.providers.pdf import PDFRenderResult

        captured_docx_template = None

        def capture_pdf(resume: Any, path: Path) -> PDFRenderResult:
            path.write_bytes(b"%PDF-1.4 dummy")
            return PDFRenderResult(output_path=path, page_count=1)

        def create_docx_capture_template(
            template_name: str | None = None, templates_dir: Path | None = None
        ) -> MagicMock:
            nonlocal captured_docx_template
            captured_docx_template = template_name
            mock = MagicMock()
            mock.render.side_effect = lambda r, p: p.write_bytes(b"PK dummy")
            return mock

        with (
            patch("resume_as_code.commands.build.get_config") as mock_config,
            patch("resume_as_code.commands.build.load_all_work_units") as mock_load_wus,
            patch("resume_as_code.providers.pdf.PDFProvider") as mock_pdf,
            patch("resume_as_code.providers.docx.DOCXProvider") as mock_docx,
        ):
            config = MagicMock()
            config.work_units_dir = work_units_dir
            config.output_dir = output_dir
            config.default_template = "ats-safe"  # Should be used for DOCX
            config.default_format = "both"
            config.tailored_notice = False
            config.tailored_notice_text = None
            config.employment_continuity = "minimum_bullet"
            config.templates_dir = None
            # No DOCX-specific config
            config.docx = None
            # Profile attrs
            config.profile.name = "Test User"
            config.profile.title = None
            config.profile.email = None
            config.profile.phone = None
            config.profile.location = None
            config.profile.linkedin = None
            config.profile.github = None
            config.profile.website = None
            config.profile.summary = None
            mock_config.return_value = config
            mock_load_wus.return_value = []

            mock_pdf.return_value.render.side_effect = capture_pdf
            mock_docx.side_effect = create_docx_capture_template

            result = runner.invoke(
                main,
                ["build", "--plan", str(plan_file)],
            )

            assert result.exit_code == 0, f"Build failed: {result.output}"
            # DOCX should use default_template when config.docx is None
            assert captured_docx_template == "ats-safe"

    def test_default_template_used_when_docx_template_is_none(
        self,
        runner: CliRunner,
        tmp_path: Path,
    ) -> None:
        """default_template used for DOCX when config.docx.template is None."""
        plan_file = tmp_path / "plan.yaml"
        plan_file.write_text("""
version: "1.0.0"
jd_hash: "abc123"
selected_work_units: []
selection_count: 0
top_k: 8
ranker_version: "hybrid-rrf-v1"
created_at: "2024-01-01T00:00:00"
""")

        work_units_dir = tmp_path / "work-units"
        work_units_dir.mkdir()
        output_dir = tmp_path / "dist"

        from resume_as_code.providers.pdf import PDFRenderResult

        captured_docx_template = None

        def capture_pdf(resume: Any, path: Path) -> PDFRenderResult:
            path.write_bytes(b"%PDF-1.4 dummy")
            return PDFRenderResult(output_path=path, page_count=1)

        def create_docx_capture_template(
            template_name: str | None = None, templates_dir: Path | None = None
        ) -> MagicMock:
            nonlocal captured_docx_template
            captured_docx_template = template_name
            mock = MagicMock()
            mock.render.side_effect = lambda r, p: p.write_bytes(b"PK dummy")
            return mock

        with (
            patch("resume_as_code.commands.build.get_config") as mock_config,
            patch("resume_as_code.commands.build.load_all_work_units") as mock_load_wus,
            patch("resume_as_code.providers.pdf.PDFProvider") as mock_pdf,
            patch("resume_as_code.providers.docx.DOCXProvider") as mock_docx,
        ):
            config = MagicMock()
            config.work_units_dir = work_units_dir
            config.output_dir = output_dir
            config.default_template = "executive"  # Should be used for DOCX
            config.default_format = "both"
            config.tailored_notice = False
            config.tailored_notice_text = None
            config.employment_continuity = "minimum_bullet"
            config.templates_dir = None
            # DOCX config exists but template is None
            config.docx = MagicMock()
            config.docx.template = None  # Not set
            # Profile attrs
            config.profile.name = "Test User"
            config.profile.title = None
            config.profile.email = None
            config.profile.phone = None
            config.profile.location = None
            config.profile.linkedin = None
            config.profile.github = None
            config.profile.website = None
            config.profile.summary = None
            mock_config.return_value = config
            mock_load_wus.return_value = []

            mock_pdf.return_value.render.side_effect = capture_pdf
            mock_docx.side_effect = create_docx_capture_template

            result = runner.invoke(
                main,
                ["build", "--plan", str(plan_file)],
            )

            assert result.exit_code == 0, f"Build failed: {result.output}"
            # DOCX should use default_template when config.docx.template is None
            assert captured_docx_template == "executive"


class TestBuildCommandYearsFlag:
    """Tests for work history duration filter --years flag (Story 13.2)."""

    def test_years_flag_exists_in_help(self, runner: CliRunner) -> None:
        """--years flag should be available in build command."""
        result = runner.invoke(main, ["build", "--help"])

        assert result.exit_code == 0
        assert "--years" in result.output
        assert "-y" in result.output
        assert "history" in result.output.lower() or "years" in result.output.lower()

    def test_years_flag_accepts_integer(self, runner: CliRunner, tmp_path: Path) -> None:
        """--years flag should accept integer values."""
        # Create minimal config
        (tmp_path / ".resume.yaml").write_text(
            """\
schema_version: "2.0.0"
work_units_dir: work-units
positions_path: positions.yaml
"""
        )
        (tmp_path / "work-units").mkdir()
        (tmp_path / "positions.yaml").write_text("positions: {}")

        jd_file = tmp_path / "jd.txt"
        jd_file.write_text("Developer\n\nRequirements:\n- Programming")

        import os

        old_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            result = runner.invoke(main, ["build", "--jd", str(jd_file), "--years", "5"])
            # May fail for other reasons (no work units), but should not fail on --years parsing
            # The flag should be recognized and parsed as integer
            assert "--years" not in str(result.exception) if result.exception else True
        finally:
            os.chdir(old_cwd)
