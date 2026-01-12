# Story 5.4: Build Command

Status: done

## Story

As a **user**,
I want **to generate my resume with a single command**,
So that **I get output files ready for job applications**.

## Acceptance Criteria

1. **Given** I run `resume build --plan plan.yaml`
   **When** the build executes
   **Then** Work Units specified in the plan are used
   **And** output files are generated in `dist/`

2. **Given** I run `resume build --jd senior-engineer.txt`
   **When** the build executes
   **Then** an implicit plan is generated (same as `resume plan`)
   **And** output files are generated based on that plan

3. **Given** I run `resume build` with no arguments
   **When** the build executes
   **Then** an error message explains that `--plan` or `--jd` is required

4. **Given** I run `resume build --jd file.txt --format pdf`
   **When** the build completes
   **Then** only PDF output is generated (no DOCX)

5. **Given** I run `resume build --jd file.txt --output-dir ./applications/google/`
   **When** the build completes
   **Then** output files are written to the specified directory
   **And** the directory is created if it doesn't exist

6. **Given** the build succeeds
   **When** I check the exit code
   **Then** it is 0

7. **Given** the build fails (e.g., missing template)
   **When** I check the exit code
   **Then** it is non-zero
   **And** no partial output files are left in `dist/` (NFR7)

## Tasks / Subtasks

- [x] Task 1: Create build command structure (AC: #1, #2, #3)
  - [x] 1.1: Create `src/resume_as_code/commands/build.py`
  - [x] 1.2: Add Click command with `--plan`, `--jd`, `--format`, `--output-dir` flags
  - [x] 1.3: Register command in main CLI group
  - [x] 1.4: Validate that `--plan` or `--jd` is provided

- [x] Task 2: Implement plan-based build (AC: #1)
  - [x] 2.1: Load saved plan from YAML file
  - [x] 2.2: Retrieve Work Units by IDs from plan
  - [x] 2.3: Build ResumeData from Work Units
  - [x] 2.4: Pass to providers for rendering

- [x] Task 3: Implement JD-based build (AC: #2)
  - [x] 3.1: Run implicit plan (reuse plan command logic)
  - [x] 3.2: Generate plan on-the-fly
  - [x] 3.3: Continue with rendering

- [x] Task 4: Implement format selection (AC: #4)
  - [x] 4.1: Add `--format` option (pdf, docx, all)
  - [x] 4.2: Default to generating both formats
  - [x] 4.3: Only generate selected format when specified

- [x] Task 5: Handle output directory (AC: #5)
  - [x] 5.1: Default to `dist/` directory
  - [x] 5.2: Support `--output-dir` flag
  - [x] 5.3: Create directory if it doesn't exist
  - [x] 5.4: Use semantic filenames (e.g., `resume.pdf`, `resume.docx`)

- [x] Task 6: Atomic writes and cleanup (AC: #7)
  - [x] 6.1: Write to temp files first
  - [x] 6.2: Move to final location on success
  - [x] 6.3: Clean up temp files on failure
  - [x] 6.4: Never leave partial files

- [x] Task 7: Code quality verification
  - [x] 7.1: Run `ruff check src tests --fix`
  - [x] 7.2: Run `mypy src --strict` with zero errors
  - [x] 7.3: Add tests for build command
  - [x] 7.4: Test error scenarios and cleanup

## Dev Notes

### Architecture Compliance

This story implements the main build command that orchestrates plan loading, Work Unit retrieval, and output generation. Per Architecture Section 2.6.

**Source:** [epics.md#Story 5.4](_bmad-output/planning-artifacts/epics.md)

### Dependencies

This story REQUIRES:
- Story 4.6 (Plan Persistence) - SavedPlan model
- Story 5.1 (Resume Data Model) - ResumeData model
- Story 5.2 (PDF Provider) - PDFProvider
- Story 5.3 (DOCX Provider) - DOCXProvider

This story ENABLES:
- Story 5.5 (Manifest & Provenance)
- Story 5.6 (Output Configuration)

### Build Command Implementation

**`src/resume_as_code/commands/build.py`:**

```python
"""Build command for resume generation."""

from __future__ import annotations

import shutil
import tempfile
from pathlib import Path
from typing import TYPE_CHECKING

import click
from rich.console import Console

from resume_as_code.utils.errors import handle_errors
from resume_as_code.models.plan import SavedPlan
from resume_as_code.models.resume import ContactInfo, ResumeData
from resume_as_code.providers.docx import DOCXProvider
from resume_as_code.providers.pdf import PDFProvider
from resume_as_code.services.work_unit_loader import WorkUnitLoader

if TYPE_CHECKING:
    from resume_as_code.config import Config

console = Console()


@click.command("build")
@click.option(
    "--plan", "-p", "plan_path",
    type=click.Path(exists=True, path_type=Path),
    help="Path to saved plan file",
)
@click.option(
    "--jd", "-j", "jd_path",
    type=click.Path(exists=True, path_type=Path),
    help="Path to job description file (creates implicit plan)",
)
@click.option(
    "--format", "-f", "output_format",
    type=click.Choice(["pdf", "docx", "all"]),
    default="all",
    help="Output format(s) to generate",
)
@click.option(
    "--output-dir", "-o", "output_dir",
    type=click.Path(path_type=Path),
    default=Path("dist"),
    help="Output directory for generated files",
)
@click.option(
    "--template", "-t", "template_name",
    default="modern",
    help="Template to use for rendering",
)
@click.pass_context
@handle_errors
def build_command(
    ctx: click.Context,
    plan_path: Path | None,
    jd_path: Path | None,
    output_format: str,
    output_dir: Path,
    template_name: str,
) -> None:
    """Build resume from plan or job description."""
    config: Config = ctx.obj["config"]

    # Validate inputs
    if not plan_path and not jd_path:
        raise click.UsageError(
            "Either --plan or --jd is required.\n"
            "  Use --plan to build from a saved plan\n"
            "  Use --jd to generate an implicit plan from a job description"
        )

    # Get plan (load or generate)
    if plan_path:
        plan = SavedPlan.load(plan_path)
        console.print(f"[blue]Loaded plan from:[/] {plan_path}")
    else:
        # Generate implicit plan (same as `resume plan`)
        plan = _generate_implicit_plan(jd_path, config)
        console.print("[blue]Generated implicit plan from JD[/]")

    # Load Work Units from plan
    loader = WorkUnitLoader(config.work_units_dir)
    work_units = []
    for selected in plan.selected_work_units:
        wu = loader.load_by_id(selected.id)
        if wu:
            work_units.append(wu)

    if not work_units:
        raise click.ClickException("No Work Units found from plan")

    # Build ResumeData
    contact = _load_contact_info(config)
    resume = ResumeData.from_work_units(
        work_units=work_units,
        contact=contact,
        summary=config.default_summary,
    )

    # Generate outputs atomically
    _generate_outputs(
        resume=resume,
        output_format=output_format,
        output_dir=output_dir,
        template_name=template_name,
    )

    console.print(f"\n[green]✓ Build complete![/] Files in: {output_dir}")


def _generate_implicit_plan(jd_path: Path, config) -> SavedPlan:
    """Generate plan on-the-fly from JD."""
    from resume_as_code.services.jd_parser import JDParser
    from resume_as_code.services.ranker import HybridRanker
    from resume_as_code.services.work_unit_loader import WorkUnitLoader

    # Parse JD
    parser = JDParser()
    jd = parser.parse(jd_path.read_text())

    # Load Work Units
    loader = WorkUnitLoader(config.work_units_dir)
    work_units = loader.load_all()

    # Rank
    ranker = HybridRanker()
    ranking = ranker.rank(work_units, jd)

    # Create plan
    return SavedPlan.from_ranking(ranking, jd, jd_path, top_k=8)


def _load_contact_info(config) -> ContactInfo:
    """Load contact info from config."""
    return ContactInfo(
        name=config.contact_name or "Your Name",
        email=config.contact_email,
        phone=config.contact_phone,
        location=config.contact_location,
        linkedin=config.contact_linkedin,
        github=config.contact_github,
    )


def _generate_outputs(
    resume: ResumeData,
    output_format: str,
    output_dir: Path,
    template_name: str,
) -> None:
    """Generate output files atomically."""
    # Create temp directory for atomic writes
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        generated_files: list[tuple[Path, Path]] = []

        try:
            # Generate PDF
            if output_format in ("pdf", "all"):
                pdf_provider = PDFProvider(template_name=template_name)
                tmp_pdf = tmp_path / "resume.pdf"
                pdf_provider.render(resume, tmp_pdf)
                generated_files.append((tmp_pdf, output_dir / "resume.pdf"))
                console.print("[green]✓[/] Generated PDF")

            # Generate DOCX
            if output_format in ("docx", "all"):
                docx_provider = DOCXProvider()
                tmp_docx = tmp_path / "resume.docx"
                docx_provider.render(resume, tmp_docx)
                generated_files.append((tmp_docx, output_dir / "resume.docx"))
                console.print("[green]✓[/] Generated DOCX")

            # All succeeded - move to final location
            output_dir.mkdir(parents=True, exist_ok=True)
            for src, dst in generated_files:
                shutil.move(str(src), str(dst))

        except Exception:
            # Cleanup happens automatically with tempfile
            # No partial files left in output_dir
            raise
```

### CLI Registration

**Update `src/resume_as_code/cli.py`:**

```python
from resume_as_code.commands.build import build_command

# In CLI group setup
cli.add_command(build_command)
```

### Testing Requirements

**`tests/unit/test_build_command.py`:**

```python
"""Tests for build command."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from resume_as_code.cli import cli


@pytest.fixture
def runner():
    return CliRunner()


class TestBuildCommand:
    """Tests for build command."""

    def test_requires_plan_or_jd(self, runner):
        """Should error when neither --plan nor --jd provided."""
        result = runner.invoke(cli, ["build"])

        assert result.exit_code != 0
        assert "--plan" in result.output or "--jd" in result.output

    def test_builds_from_plan(self, runner, tmp_path):
        """Should build from saved plan file."""
        # Create minimal plan file
        plan_file = tmp_path / "plan.yaml"
        plan_file.write_text("""
version: "1.0.0"
jd_hash: "abc123"
selected_work_units: []
selection_count: 0
top_k: 8
ranker_version: "hybrid-rrf-v1"
""")

        with patch("resume_as_code.commands.build.SavedPlan.load") as mock_load:
            mock_plan = MagicMock()
            mock_plan.selected_work_units = []
            mock_load.return_value = mock_plan

            result = runner.invoke(cli, ["build", "--plan", str(plan_file)])

            # Should attempt to load plan
            mock_load.assert_called_once()

    def test_creates_output_directory(self, runner, tmp_path):
        """Should create output directory if needed."""
        output_dir = tmp_path / "new" / "nested" / "dir"

        # Would need full mocking for complete test
        # This demonstrates the test structure
        assert not output_dir.exists()

    def test_atomic_writes_no_partial_on_failure(self, runner, tmp_path):
        """Should not leave partial files on failure."""
        output_dir = tmp_path / "dist"
        output_dir.mkdir()

        # If PDF generation fails, no files should be in output
        # Implementation uses temp directory approach
        pass


class TestFormatSelection:
    """Tests for format selection."""

    def test_format_pdf_only(self):
        """--format pdf should only generate PDF."""
        pass

    def test_format_docx_only(self):
        """--format docx should only generate DOCX."""
        pass

    def test_format_all_default(self):
        """Default should generate both formats."""
        pass
```

### Verification Commands

```bash
# Build from saved plan
resume build --plan my-plan.yaml

# Build with implicit plan from JD
resume build --jd job-description.txt

# Build PDF only
resume build --jd job.txt --format pdf

# Build to custom directory
resume build --plan plan.yaml --output-dir ./applications/google/

# Check exit code
resume build --jd job.txt && echo "Success" || echo "Failed"
```

### References

- [Source: epics.md#Story 5.4](_bmad-output/planning-artifacts/epics.md)

## Dev Agent Record

### Agent Model Used

Claude Opus 4.5 (claude-opus-4-5-20251101)

### Debug Log References

N/A

### Completion Notes List

- Implemented `resume build` command with `--plan`, `--jd`, `--format`, `--output-dir`, `--template` flags
- Plan-based build loads SavedPlan and retrieves Work Units by ID
- JD-based build generates implicit plan on-the-fly using JDParser and HybridRanker
- Format selection supports pdf, docx, or all (default)
- Atomic writes using tempfile.TemporaryDirectory to prevent partial files on failure
- All 15 unit tests for build command pass
- Full test suite (886 tests) passes with no regressions
- ruff check passes with zero errors
- mypy --strict passes with zero errors
- Contact info uses placeholder defaults - documented as known limitation for Story 5.6

### Code Review Fixes

- **C1 (CRITICAL)**: Moved provider imports to lazy loading inside `_generate_outputs()` to prevent import-time WeasyPrint failures when system dependencies (pango, cairo) are not installed
- **H1/H2/M2**: Added `TestWorkUnitToResumeDataTransformation` test class with integration tests verifying Work Unit to ResumeData transformation and plan order preservation
- **H3**: Documented contact info limitation with TODO referencing Story 5.6 (Output Configuration)
- **M3**: Enhanced empty Work Units warning with actionable hint directing users to `resume plan` command

### File List

- src/resume_as_code/commands/build.py (new, modified for lazy imports)
- src/resume_as_code/cli.py (modified - added build_command registration)
- tests/unit/test_build_command.py (new, enhanced with transformation tests)

