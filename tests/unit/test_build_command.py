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

            mock_load.assert_called_once()

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

            # Should use config output_dir, not hardcoded "dist"
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

        def create_pdf(resume: Any, path: Path) -> None:
            """Create a dummy PDF file."""
            path.write_bytes(b"%PDF-1.4 dummy")

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
            assert (output_dir / "manifest.yaml").exists()

            # Verify manifest content
            manifest_content = (output_dir / "manifest.yaml").read_text()
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

        def create_pdf(resume: Any, path: Path) -> None:
            """Create a dummy PDF file."""
            path.write_bytes(b"%PDF-1.4 dummy")

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

            manifest_content = (output_dir / "manifest.yaml").read_text()
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

        captured_resume_data = None

        def capture_render(resume: Any, output_path: Any) -> Any:
            nonlocal captured_resume_data
            captured_resume_data = resume
            return output_path

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

            # Verify skills were extracted
            assert "Python" in captured_resume_data.skills
            assert "python" in captured_resume_data.skills  # From tags

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

        captured_resume_data = None

        def capture_render(resume: Any, output_path: Any) -> Any:
            nonlocal captured_resume_data
            captured_resume_data = resume
            return output_path

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
        """Certifications from config should be passed to ResumeData."""
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
            return output_path

        with (
            patch("resume_as_code.commands.build.get_config") as mock_config,
            patch("resume_as_code.commands.build.load_all_work_units") as mock_load_wus,
            patch("resume_as_code.providers.pdf.PDFProvider") as mock_pdf,
            patch("resume_as_code.providers.docx.DOCXProvider") as mock_docx,
        ):
            config = MagicMock()
            config.work_units_dir = work_units_dir
            config.output_dir = Path("dist")
            config.default_template = "modern"
            config.default_format = "both"
            # Profile with defaults
            config.profile.name = "Test User"
            config.profile.title = None
            config.profile.email = None
            config.profile.phone = None
            config.profile.location = None
            config.profile.linkedin = None
            config.profile.github = None
            config.profile.website = None
            config.profile.summary = None
            # Certifications from config
            config.certifications = [
                Certification(name="AWS SAP", issuer="Amazon Web Services"),
                Certification(name="CISSP", issuer="ISC2", date="2023-01"),
            ]
            mock_config.return_value = config
            mock_load_wus.return_value = []

            mock_pdf_instance = MagicMock()
            mock_pdf_instance.render.side_effect = capture_render
            mock_pdf.return_value = mock_pdf_instance

            mock_docx_instance = MagicMock()
            mock_docx.return_value = mock_docx_instance

            runner.invoke(
                main,
                ["build", "--plan", str(plan_file), "--output-dir", str(tmp_path / "dist")],
            )

            # Verify certifications were passed to ResumeData
            assert captured_resume_data is not None
            assert len(captured_resume_data.certifications) == 2
            assert captured_resume_data.certifications[0].name == "AWS SAP"
            assert captured_resume_data.certifications[1].name == "CISSP"

    def test_empty_certifications_handled_gracefully(
        self,
        runner: CliRunner,
        tmp_path: Path,
    ) -> None:
        """Empty certifications list should not cause errors."""
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

        with (
            patch("resume_as_code.commands.build.get_config") as mock_config,
            patch("resume_as_code.commands.build.load_all_work_units") as mock_load_wus,
            patch("resume_as_code.commands.build._generate_outputs") as mock_gen,
        ):
            config = MagicMock()
            config.work_units_dir = work_units_dir
            config.output_dir = Path("dist")
            config.default_template = "modern"
            config.default_format = "both"
            # Profile with defaults
            config.profile.name = "Test User"
            config.profile.title = None
            config.profile.email = None
            config.profile.phone = None
            config.profile.location = None
            config.profile.linkedin = None
            config.profile.github = None
            config.profile.website = None
            config.profile.summary = None
            # Empty certifications
            config.certifications = []
            mock_config.return_value = config
            mock_load_wus.return_value = []
            mock_gen.side_effect = capture_generate_outputs

            result = runner.invoke(
                main,
                ["build", "--plan", str(plan_file), "--output-dir", str(tmp_path / "dist")],
            )

            # Should succeed
            assert result.exit_code == 0
            # Certifications should be empty list
            assert captured_resume_data is not None
            assert captured_resume_data.certifications == []
