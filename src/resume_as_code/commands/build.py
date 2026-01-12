"""Build command for resume generation."""

from __future__ import annotations

import shutil
import tempfile
from pathlib import Path
from typing import TYPE_CHECKING, Any

import click

from resume_as_code.config import get_config
from resume_as_code.models.plan import SavedPlan
from resume_as_code.models.resume import ContactInfo, ResumeData
from resume_as_code.services.work_unit_service import load_all_work_units
from resume_as_code.utils.console import console, info, success
from resume_as_code.utils.errors import handle_errors

if TYPE_CHECKING:
    from resume_as_code.models.config import ResumeConfig


@click.command("build")
@click.option(
    "--plan",
    "-p",
    "plan_path",
    type=click.Path(exists=True, path_type=Path),
    help="Path to saved plan file",
)
@click.option(
    "--jd",
    "-j",
    "jd_path",
    type=click.Path(exists=True, path_type=Path),
    help="Path to job description file (creates implicit plan)",
)
@click.option(
    "--format",
    "-f",
    "output_format",
    type=click.Choice(["pdf", "docx", "all"]),
    default=None,
    help="Output format(s) to generate (default: from config or 'all')",
)
@click.option(
    "--output-dir",
    "-o",
    "output_dir",
    type=click.Path(path_type=Path),
    default=None,
    help="Output directory for generated files (default: from config or 'dist')",
)
@click.option(
    "--template",
    "-t",
    "template_name",
    default=None,
    help="Template to use for rendering (default: from config or 'modern')",
)
@click.pass_context
@handle_errors
def build_command(
    ctx: click.Context,
    plan_path: Path | None,
    jd_path: Path | None,
    output_format: str | None,
    output_dir: Path | None,
    template_name: str | None,
) -> None:
    """Build resume from plan or job description.

    Generate PDF and/or DOCX resume files from a saved plan or by
    creating an implicit plan from a job description.

    Examples:

        # Build from saved plan
        resume build --plan my-plan.yaml

        # Build with implicit plan from JD
        resume build --jd job-description.txt

        # Build PDF only to custom directory
        resume build --jd job.txt --format pdf --output-dir ./applications/google/
    """
    config = get_config()

    # Apply config defaults when CLI flags not provided (Story 5.6: Output Configuration)
    # CLI flags override config values (AC: #1, #2)
    actual_output_dir = output_dir if output_dir is not None else config.output_dir
    actual_template = template_name if template_name is not None else config.default_template
    # Map config "both" to build "all" for consistency
    config_format = "all" if config.default_format == "both" else config.default_format
    actual_format = output_format if output_format is not None else config_format

    # Validate inputs (AC: #3)
    if not plan_path and not jd_path:
        raise click.UsageError(
            "Either --plan or --jd is required.\n"
            "  Use --plan to build from a saved plan\n"
            "  Use --jd to generate an implicit plan from a job description"
        )

    # Get plan (load or generate)
    if plan_path:
        plan = SavedPlan.load(plan_path)
        if not ctx.obj.quiet:
            info(f"Loaded plan from: {plan_path}")
    else:
        # Generate implicit plan (same as `resume plan`) (AC: #2)
        assert jd_path is not None  # Guaranteed by validation above
        plan = _generate_implicit_plan(jd_path, config)
        if not ctx.obj.quiet:
            info("Generated implicit plan from JD")

    # Load Work Units from plan (AC: #1)
    work_units = _load_work_units_from_plan(plan, config)

    if not work_units:
        # Explicit warning about empty resume - user should review plan
        console.print(
            "[yellow]Warning:[/yellow] No Work Units found from plan. "
            "The generated resume will be empty.\n"
            "  Hint: Run 'resume plan --jd <file>' to see Work Unit selection."
        )

    # Build ResumeData
    contact = _load_contact_info(config)
    resume = ResumeData.from_work_units(
        work_units=work_units,
        contact=contact,
        summary=config.profile.summary,  # Load from profile config
    )

    # Generate outputs atomically (AC: #4, #5, #7)
    _generate_outputs(
        resume=resume,
        plan=plan,
        work_units=work_units,
        output_format=actual_format,
        output_dir=actual_output_dir,
        template_name=actual_template,
    )

    # AC: #6 - Success exit code is 0 (automatic if no exception)
    if not ctx.obj.quiet:
        success(f"Build complete! Files in: {actual_output_dir}")


def _generate_implicit_plan(jd_path: Path, config: ResumeConfig) -> SavedPlan:
    """Generate plan on-the-fly from JD.

    Args:
        jd_path: Path to job description file.
        config: Application configuration.

    Returns:
        SavedPlan created from ranking results.
    """
    from resume_as_code.services.jd_parser import parse_jd_file
    from resume_as_code.services.ranker import HybridRanker

    # Parse JD
    jd = parse_jd_file(jd_path)

    # Load Work Units
    work_units = load_all_work_units(config.work_units_dir)

    # Rank with scoring weights from config (AC: #3)
    ranker = HybridRanker()
    ranking = ranker.rank(
        work_units, jd, top_k=config.default_top_k, scoring_weights=config.scoring_weights
    )

    # Create plan
    return SavedPlan.from_ranking(ranking, jd, jd_path, top_k=config.default_top_k)


def _load_work_units_from_plan(plan: SavedPlan, config: ResumeConfig) -> list[dict[str, Any]]:
    """Load Work Units by IDs from plan.

    Args:
        plan: SavedPlan with selected Work Unit IDs.
        config: Application configuration.

    Returns:
        List of Work Unit dictionaries.
    """
    # Load all Work Units
    all_work_units = load_all_work_units(config.work_units_dir)

    # Create lookup by ID
    wu_by_id = {wu.get("id"): wu for wu in all_work_units}

    # Get Work Units from plan in order
    work_units: list[dict[str, Any]] = []
    for selected in plan.selected_work_units:
        wu = wu_by_id.get(selected.id)
        if wu:
            work_units.append(wu)

    return work_units


def _load_contact_info(config: ResumeConfig) -> ContactInfo:
    """Load contact info from config profile.

    Args:
        config: Application configuration.

    Returns:
        ContactInfo populated from profile, with warnings for missing data.
    """
    profile = config.profile

    # Warn if name not configured (AC: #3)
    if not profile.name:
        console.print(
            "[yellow]Warning:[/yellow] No profile configured. "
            "Run `resume config profile.name 'Your Name'` to set."
        )

    return ContactInfo(
        name=profile.name or "Your Name",
        title=profile.title,
        email=profile.email,
        phone=profile.phone,
        location=profile.location,
        linkedin=str(profile.linkedin) if profile.linkedin else None,
        github=str(profile.github) if profile.github else None,
        website=str(profile.website) if profile.website else None,
    )


def _generate_outputs(
    resume: ResumeData,
    plan: SavedPlan,
    work_units: list[dict[str, Any]],
    output_format: str,
    output_dir: Path,
    template_name: str,
) -> None:
    """Generate output files atomically.

    Uses temporary directory for writes, only moving to final location
    if all generation succeeds. This prevents partial files on failure (AC: #7).

    Args:
        resume: ResumeData to render.
        plan: SavedPlan used for the build.
        work_units: List of Work Unit dictionaries included in build.
        output_format: Format to generate (pdf, docx, all).
        output_dir: Target output directory.
        template_name: Name of template to use.

    Raises:
        RenderError: If generation fails.
    """
    # Lazy imports to avoid import-time failures when WeasyPrint
    # system dependencies (pango, cairo) are not installed.
    # This allows the CLI to start even without PDF generation capability.
    from resume_as_code.providers.docx import DOCXProvider
    from resume_as_code.providers.manifest import ManifestProvider
    from resume_as_code.providers.pdf import PDFProvider

    # Track which formats are generated for manifest
    formats_generated: list[str] = []

    # Create temp directory for atomic writes
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        generated_files: list[tuple[Path, Path]] = []

        try:
            # Generate PDF (AC: #4)
            if output_format in ("pdf", "all"):
                pdf_provider = PDFProvider(template_name=template_name)
                tmp_pdf = tmp_path / "resume.pdf"
                pdf_provider.render(resume, tmp_pdf)
                generated_files.append((tmp_pdf, output_dir / "resume.pdf"))
                formats_generated.append("pdf")
                console.print("[green]\u2713[/green] Generated PDF")

            # Generate DOCX (AC: #4)
            if output_format in ("docx", "all"):
                docx_provider = DOCXProvider()
                tmp_docx = tmp_path / "resume.docx"
                docx_provider.render(resume, tmp_docx)
                generated_files.append((tmp_docx, output_dir / "resume.docx"))
                formats_generated.append("docx")
                console.print("[green]\u2713[/green] Generated DOCX")

            # Generate manifest (Story 5.5 - Provenance)
            manifest_provider = ManifestProvider()
            tmp_manifest = tmp_path / "manifest.yaml"
            manifest_provider.generate(
                plan=plan,
                work_units=work_units,
                template=template_name,
                output_formats=formats_generated,
                output_path=tmp_manifest,
            )
            generated_files.append((tmp_manifest, output_dir / "manifest.yaml"))
            console.print("[green]\u2713[/green] Generated manifest")

            # All succeeded - move to final location (AC: #5)
            output_dir.mkdir(parents=True, exist_ok=True)
            for src, dst in generated_files:
                shutil.move(str(src), str(dst))

        except Exception:
            # Cleanup happens automatically with tempfile
            # No partial files left in output_dir (AC: #7)
            raise
