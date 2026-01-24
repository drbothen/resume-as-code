"""Build command for resume generation."""

from __future__ import annotations

import shutil
import tempfile
from pathlib import Path
from typing import TYPE_CHECKING, Any

import click

from resume_as_code.config import get_config
from resume_as_code.data_loader import (
    load_board_roles,
    load_certifications,
    load_education,
    load_highlights,
    load_profile,
    load_publications,
)
from resume_as_code.models.config import DEFAULT_TAILORED_NOTICE
from resume_as_code.models.plan import SavedPlan
from resume_as_code.models.resume import ContactInfo, ResumeData
from resume_as_code.services.position_service import PositionService
from resume_as_code.services.work_unit_loader import WorkUnitLoader
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
@click.option(
    "--strict-positions",
    is_flag=True,
    help="Validate position_id references exist before building (fail on invalid refs)",
)
@click.option(
    "--name",
    "-n",
    "output_name",
    default=None,
    help="Base filename for output (default: 'resume'). E.g., --name john-doe-cto",
)
@click.option(
    "--tailored-notice/--no-tailored-notice",
    default=None,
    help="Include/exclude tailored resume footer notice (overrides config)",
)
@click.option(
    "--allow-gaps/--no-allow-gaps",
    "allow_gaps",
    default=None,
    help="Override employment_continuity mode: --allow-gaps for pure relevance filtering, "
    "--no-allow-gaps to guarantee at least one bullet per position (Story 7.20)",
)
@click.option(
    "--years",
    "-y",
    "years",
    type=int,
    default=None,
    help="Limit work history to last N years (overrides config history_years)",
)
@click.option(
    "--templates-dir",
    "templates_dir",
    type=click.Path(exists=True, file_okay=False, dir_okay=True, path_type=Path),
    default=None,
    help="Path to custom templates directory (supplements built-in templates) (Story 11.3)",
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
    strict_positions: bool,
    output_name: str | None,
    tailored_notice: bool | None,
    allow_gaps: bool | None,
    years: int | None,
    templates_dir: Path | None,
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

        # Build with custom filename
        resume build --jd job.txt --name john-doe-cto
    """
    config = get_config()

    # Apply config defaults when CLI flags not provided (Story 5.6: Output Configuration)
    # CLI flags override config values (AC: #1, #2)
    actual_output_dir = output_dir if output_dir is not None else config.output_dir
    actual_template = template_name if template_name is not None else config.default_template
    # Map config "both" to build "all" for consistency
    config_format = "all" if config.default_format == "both" else config.default_format
    actual_format = output_format if output_format is not None else config_format
    # CLI --templates-dir overrides config templates_dir (Story 11.3)
    actual_templates_dir = templates_dir if templates_dir is not None else config.templates_dir

    # Validate inputs (AC: #3)
    if not plan_path and not jd_path:
        raise click.UsageError(
            "Either --plan or --jd is required.\n"
            "  Use --plan to build from a saved plan\n"
            "  Use --jd to generate an implicit plan from a job description"
        )

    # Get plan (load or generate) and JD keywords for skill curation
    jd_keywords: set[str] = set()
    if plan_path:
        plan = SavedPlan.load(plan_path)
        jd_keywords = _get_jd_keywords_from_plan(plan)
        if not ctx.obj.quiet:
            info(f"Loaded plan from: {plan_path}")
    else:
        # Generate implicit plan (same as `resume plan`) (AC: #2)
        assert jd_path is not None  # Guaranteed by validation above
        plan, jd_keywords = _generate_implicit_plan(
            jd_path, config, strict_positions, allow_gaps, years
        )
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

    # Build ResumeData with skill curation (Story 6.3) and position grouping (Story 6.7)
    contact = _load_contact_info()
    positions_path = config.positions_path

    # Load data via data_loader (Story 9.2)
    project_path = Path.cwd()
    profile = load_profile(project_path)
    publications = load_publications(project_path)
    education = load_education(project_path)
    certifications = load_certifications(project_path)
    career_highlights = load_highlights(project_path)
    board_roles = load_board_roles(project_path)

    # Get full JD for action-level scoring (Story 7.18)
    jd_for_scoring = _get_jd_for_scoring(plan_path, jd_path)

    resume = ResumeData.from_work_units(
        work_units=work_units,
        contact=contact,
        summary=profile.summary,  # Load from profile via data_loader (Story 9.2)
        skills_config=config.skills,  # Pass skills curation config
        jd_keywords=jd_keywords if jd_keywords else None,  # Pass JD keywords for prioritization
        positions_path=positions_path if positions_path.exists() else None,  # Position grouping
        onet_config=config.onet,  # O*NET skill discovery (Story 7.17)
        curation_config=config.curation,  # Action-level scoring config (Story 7.18)
        jd=jd_for_scoring,  # Full JD for action scoring (Story 7.18)
    )
    # Resolve tailored notice (Story 7.19)
    # Do this BEFORE constructing final ResumeData so it's included
    # CLI flag takes precedence over config
    show_tailored_notice = (
        tailored_notice if tailored_notice is not None else config.tailored_notice
    )
    actual_tailored_notice_text: str | None = None
    if show_tailored_notice:
        # Use custom text from config, or fall back to default
        actual_tailored_notice_text = config.tailored_notice_text or DEFAULT_TAILORED_NOTICE

    # Curate publications for JD relevance (Story 8.2)
    curated_publications = list(publications)  # Default: all publications
    if jd_for_scoring and publications:
        from resume_as_code.services.content_curator import ContentCurator
        from resume_as_code.services.embedder import EmbeddingService
        from resume_as_code.services.skill_registry import SkillRegistry

        embedder = EmbeddingService()
        curator = ContentCurator(embedder=embedder, config=config.curation)
        registry = SkillRegistry.load_default()

        pub_curation = curator.curate_publications(
            publications=list(publications),
            jd=jd_for_scoring,
            registry=registry,
        )
        curated_publications = pub_curation.selected
        if not ctx.obj.quiet and pub_curation.excluded:
            console.print(
                f"[dim]Publications: {len(pub_curation.selected)} selected, "
                f"{len(pub_curation.excluded)} excluded by JD relevance[/dim]"
            )

    # Curate career highlights for JD relevance (Bug fix: highlights curation)
    curated_highlights = list(career_highlights)  # Default: all highlights
    if jd_for_scoring and career_highlights:
        from resume_as_code.services.content_curator import ContentCurator
        from resume_as_code.services.embedder import EmbeddingService

        embedder = EmbeddingService()
        curator = ContentCurator(embedder=embedder, config=config.curation)

        highlights_curation = curator.curate_highlights(
            highlights=list(career_highlights),
            jd=jd_for_scoring,
        )
        curated_highlights = highlights_curation.selected
        if not ctx.obj.quiet and highlights_curation.excluded:
            console.print(
                f"[dim]Highlights: {len(highlights_curation.selected)} selected, "
                f"{len(highlights_curation.excluded)} excluded by JD relevance[/dim]"
            )

    # Add config data to ResumeData (Story 6.2, 6.6, 6.13, 6.14, 6.15, 7.19, 8.2)
    # Set publications_curated=True when JD was used for curation (Story 8.2 Task 6)
    publications_were_curated = bool(jd_for_scoring and publications)
    resume = ResumeData(
        contact=resume.contact,
        summary=resume.summary,
        sections=resume.sections,
        skills=resume.skills,
        education=list(education),
        certifications=list(certifications),
        career_highlights=curated_highlights,
        board_roles=list(board_roles),
        publications=curated_publications,
        publications_curated=publications_were_curated,
        tailored_notice_text=actual_tailored_notice_text,
    )

    # Generate outputs atomically (AC: #4, #5, #7)
    actual_name = output_name if output_name else "resume"

    # Story 13.1: Resolve DOCX-specific template
    # Priority: CLI --template > config.docx.template > config.default_template
    actual_docx_template = template_name  # CLI flag takes precedence
    if actual_docx_template is None and config.docx and config.docx.template:
        actual_docx_template = config.docx.template
    if actual_docx_template is None:
        actual_docx_template = actual_template  # Falls back to default_template

    _generate_outputs(
        resume=resume,
        plan=plan,
        work_units=work_units,
        output_format=actual_format,
        output_dir=actual_output_dir,
        template_name=actual_template,
        docx_template_name=actual_docx_template,
        output_name=actual_name,
        templates_dir=actual_templates_dir,
    )

    # AC: #6 - Success exit code is 0 (automatic if no exception)
    if not ctx.obj.quiet:
        success(f"Build complete! Files in: {actual_output_dir}")


def _generate_implicit_plan(
    jd_path: Path,
    config: ResumeConfig,
    strict_positions: bool = False,
    allow_gaps: bool | None = None,
    years: int | None = None,
) -> tuple[SavedPlan, set[str]]:
    """Generate plan on-the-fly from JD.

    Args:
        jd_path: Path to job description file.
        config: Application configuration.
        strict_positions: If True, validate position_id references before planning.
        allow_gaps: Override employment_continuity mode (None = use config).
        years: Limit work history to last N years (None = use config or unlimited).

    Returns:
        Tuple of (SavedPlan created from ranking results, JD keywords set).
    """
    from resume_as_code.services.employment_continuity import EmploymentContinuityService
    from resume_as_code.services.jd_parser import parse_jd_file
    from resume_as_code.services.ranker import HybridRanker

    # Parse JD
    jd = parse_jd_file(jd_path)

    # Load Work Units
    work_units = load_all_work_units(config.work_units_dir)

    # Load positions for seniority inference (Story 7.12)
    position_service = PositionService(config.positions_path)
    positions = position_service.load_positions()

    # Apply work history duration filter (Story 13.2)
    # CLI --years flag overrides config.history_years
    effective_years = years if years is not None else config.history_years
    if effective_years is not None and positions:
        positions_list = list(positions.values())
        filtered_list = PositionService.filter_by_years(positions_list, effective_years)
        positions = {pos.id: pos for pos in filtered_list}

        # Also filter work units to exclude those referencing filtered-out positions
        work_units = [
            wu
            for wu in work_units
            if wu.get("position_id") is None or wu.get("position_id") in positions
        ]

    # Validate position references if strict mode enabled (Story 7.6)
    if strict_positions:
        # Always validate - even if positions dict is empty, work units
        # with position_id references should fail validation
        loader = WorkUnitLoader(config.work_units_dir)
        try:
            # This validates and raises on invalid refs
            loader.load_with_positions(positions)
        except Exception as e:
            from resume_as_code.models.errors import ValidationError

            raise ValidationError(
                message=f"Position reference validation failed: {e}",
                suggestion=("Fix invalid position_ids or run 'resume validate --check-positions'"),
            ) from e

    # Rank with scoring weights from config (AC: #3)
    # Pass positions for seniority inference from position title/scope (Story 7.12)
    ranker = HybridRanker()
    ranking = ranker.rank(
        work_units,
        jd,
        top_k=config.default_top_k,
        scoring_weights=config.scoring_weights,
        positions=positions,
    )

    # Apply employment continuity (Story 7.20)
    # Resolve mode: CLI flag > config

    from resume_as_code.models.config import EmploymentContinuityMode
    from resume_as_code.models.work_unit import WorkUnit

    if allow_gaps is True:
        continuity_mode: EmploymentContinuityMode = "allow_gaps"
    elif allow_gaps is False:
        continuity_mode = "minimum_bullet"
    else:
        continuity_mode = config.employment_continuity

    continuity_service = EmploymentContinuityService(mode=continuity_mode)

    # Convert work unit dicts to WorkUnit objects for continuity service
    all_wu_objects = [WorkUnit.model_validate(wu) for wu in work_units]

    # Get selected work units from ranking
    selected_wu_ids = {result.work_unit_id for result in ranking.results[: config.default_top_k]}
    selected_wu_objects = [wu for wu in all_wu_objects if wu.id in selected_wu_ids]
    scores = {result.work_unit_id: result.score for result in ranking.results}

    # Ensure continuity (adds missing position work units in minimum_bullet mode)
    position_list = list(positions.values())
    enhanced_work_units = continuity_service.ensure_continuity(
        positions=position_list,
        selected_work_units=selected_wu_objects,
        all_work_units=all_wu_objects,
        scores=scores,
    )

    # Get IDs of enhanced work units
    enhanced_wu_ids = {wu.id for wu in enhanced_work_units}

    # Create plan from ranking, including enhanced selection
    # The ranking already contains the original results; we need to add continuity additions
    plan = SavedPlan.from_ranking(ranking, jd, jd_path, top_k=config.default_top_k)

    # If continuity service added work units, update the plan
    added_wu_ids = enhanced_wu_ids - selected_wu_ids
    if added_wu_ids:
        # Add missing work units to the plan's selected list
        from resume_as_code.models.plan import SelectedWorkUnit

        for wu in enhanced_work_units:
            if wu.id in added_wu_ids:
                plan.selected_work_units.append(
                    SelectedWorkUnit(
                        id=wu.id,
                        title=wu.title,
                        score=scores.get(wu.id, 0.0),
                        match_reasons=["Added for employment continuity"],
                    )
                )
        plan.selection_count = len(plan.selected_work_units)

    # Return both plan and JD keywords for skill curation
    return plan, set(jd.keywords)


def _get_jd_keywords_from_plan(plan: SavedPlan) -> set[str]:
    """Extract JD keywords from saved plan by re-parsing JD file.

    Args:
        plan: SavedPlan with jd_path.

    Returns:
        Set of JD keywords, or empty set if JD file not accessible.
    """
    if not plan.jd_path:
        return set()

    jd_file = Path(plan.jd_path)
    if not jd_file.exists():
        return set()

    try:
        from resume_as_code.services.jd_parser import parse_jd_file

        jd = parse_jd_file(jd_file)
        return set(jd.keywords)
    except Exception:
        # If JD parsing fails, continue without keywords
        return set()


def _get_jd_for_scoring(
    plan_path: Path | None,
    jd_path: Path | None,
) -> Any:
    """Get full JobDescription for action-level scoring (Story 7.18).

    Args:
        plan_path: Path to saved plan file (has jd_path embedded).
        jd_path: Direct path to JD file.

    Returns:
        JobDescription object, or None if JD not available.
    """
    from resume_as_code.services.jd_parser import parse_jd_file

    # Direct JD path takes precedence
    if jd_path and jd_path.exists():
        try:
            return parse_jd_file(jd_path)
        except Exception:
            return None

    # Try to get JD from plan
    if plan_path and plan_path.exists():
        try:
            plan = SavedPlan.load(plan_path)
            if plan.jd_path:
                jd_file = Path(plan.jd_path)
                if jd_file.exists():
                    return parse_jd_file(jd_file)
        except Exception:
            pass

    return None


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


def _load_contact_info() -> ContactInfo:
    """Load contact info from profile via data_loader.

    Returns:
        ContactInfo populated from profile, with warnings for missing data.
    """
    # Load profile via data_loader (Story 9.2)
    profile = load_profile(Path.cwd())

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
    docx_template_name: str | None = None,
    output_name: str = "resume",
    templates_dir: Path | None = None,
) -> None:
    """Generate output files atomically.

    Uses temporary directory for writes, only moving to final location
    if all generation succeeds. This prevents partial files on failure (AC: #7).

    Args:
        resume: ResumeData to render (includes tailored_notice_text if set).
        plan: SavedPlan used for the build.
        work_units: List of Work Unit dictionaries included in build.
        output_format: Format to generate (pdf, docx, all).
        output_dir: Target output directory.
        template_name: Name of template to use for PDF.
        docx_template_name: Name of template to use for DOCX (Story 13.1).
            Defaults to template_name if not specified.
        output_name: Base filename for output files (default: 'resume').
        templates_dir: Optional path to custom templates directory (Story 11.3).

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
            pdf_page_count: int | None = None
            if output_format in ("pdf", "all"):
                pdf_provider = PDFProvider(
                    template_name=template_name,
                    templates_dir=templates_dir,
                )
                tmp_pdf = tmp_path / f"{output_name}.pdf"
                result = pdf_provider.render(resume, tmp_pdf)
                pdf_page_count = result.page_count
                generated_files.append((tmp_pdf, output_dir / f"{output_name}.pdf"))
                formats_generated.append("pdf")
                console.print("[green]\u2713[/green] Generated PDF")

                # Story 6.17 AC #6: Warn if CTO template exceeds 2 pages
                if template_name == "cto" and pdf_page_count > 2:
                    console.print(
                        f"[yellow]Warning:[/yellow] CTO resumes should be 2 pages maximum "
                        f"(generated {pdf_page_count} pages). Consider trimming content."
                    )

            # Generate DOCX (AC: #4, Story 13.1: template support)
            if output_format in ("docx", "all"):
                # Use DOCX-specific template (resolved in build_command, Story 13.1)
                effective_docx_template = docx_template_name or template_name
                docx_provider = DOCXProvider(
                    template_name=effective_docx_template,
                    templates_dir=templates_dir,
                )
                tmp_docx = tmp_path / f"{output_name}.docx"
                docx_provider.render(resume, tmp_docx)
                generated_files.append((tmp_docx, output_dir / f"{output_name}.docx"))
                formats_generated.append("docx")
                console.print("[green]\u2713[/green] Generated DOCX")

            # Generate manifest (Story 5.5 - Provenance)
            manifest_provider = ManifestProvider()
            tmp_manifest = tmp_path / f"{output_name}-manifest.yaml"
            manifest_provider.generate(
                plan=plan,
                work_units=work_units,
                template=template_name,
                output_formats=formats_generated,
                output_path=tmp_manifest,
            )
            generated_files.append((tmp_manifest, output_dir / f"{output_name}-manifest.yaml"))
            console.print("[green]\u2713[/green] Generated manifest")

            # All succeeded - move to final location (AC: #5)
            output_dir.mkdir(parents=True, exist_ok=True)
            for src, dst in generated_files:
                shutil.move(str(src), str(dst))

        except Exception:
            # Cleanup happens automatically with tempfile
            # No partial files left in output_dir (AC: #7)
            raise
