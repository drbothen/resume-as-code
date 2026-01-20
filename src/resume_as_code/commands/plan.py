"""Plan command for resume preview."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any

import click

if TYPE_CHECKING:
    from resume_as_code.models.board_role import BoardRole
    from resume_as_code.models.certification import Certification
    from resume_as_code.models.config import ResumeConfig
from rich.panel import Panel

from resume_as_code.config import get_config
from resume_as_code.data_loader import (
    load_board_roles,
    load_certifications,
    load_education,
    load_highlights,
    load_profile,
    load_publications,
)
from resume_as_code.models.exclusion import get_exclusion_reason
from resume_as_code.models.output import JSONResponse
from resume_as_code.models.plan import SavedPlan
from resume_as_code.services.certification_matcher import (
    CertificationMatcher,
    CertificationMatchResult,
)
from resume_as_code.services.content_curator import (
    ContentCurator,
    is_executive_level,
)
from resume_as_code.services.content_curator import (
    CurationResult as ContentCurationResult,
)
from resume_as_code.services.coverage_analyzer import (
    CoverageLevel,
    CoverageReport,
    analyze_coverage,
)
from resume_as_code.services.education_matcher import (
    EducationMatcher,
    EducationMatchResult,
)
from resume_as_code.services.employment_continuity import (
    EmploymentContinuityService,
    EmploymentGap,
)
from resume_as_code.services.jd_parser import parse_jd_file
from resume_as_code.services.position_service import PositionService
from resume_as_code.services.ranker import HybridRanker, RankingResult
from resume_as_code.services.skill_curator import CurationResult, SkillCurator
from resume_as_code.services.work_unit_loader import WorkUnitLoader
from resume_as_code.services.work_unit_service import load_all_work_units
from resume_as_code.utils.console import console, info, json_output, success, warning
from resume_as_code.utils.errors import handle_errors
from resume_as_code.utils.work_unit_text import extract_work_unit_text

# Content analysis thresholds
WORDS_PER_PAGE = 500
ONE_PAGE_MIN_WORDS = 475
ONE_PAGE_MAX_WORDS = 600
TWO_PAGE_MIN_WORDS = 800
TWO_PAGE_MAX_WORDS = 1200
ONE_PAGE_THRESHOLD = 1.5  # Pages


# Position grouping dataclasses
@dataclass(frozen=True)
class PositionSummary:
    """Summary of a position for plan display."""

    id: str
    title: str
    dates: str
    work_unit_count: int


@dataclass(frozen=True)
class EmployerGroup:
    """Group of positions for a single employer."""

    name: str
    positions: list[PositionSummary]
    work_unit_count: int


@dataclass(frozen=True)
class PositionGroupingResult:
    """Result of grouping work units by position/employer."""

    employers: list[EmployerGroup]
    ungrouped_count: int
    has_positions: bool


@dataclass(frozen=True)
class ProfilePreview:
    """Profile completeness preview for plan display.

    Attributes:
        name: User's name.
        title: Professional title.
        contact_complete: Whether all contact fields are filled.
        missing_fields: List of missing contact field names.
        summary_words: Word count of summary.
        summary_status: "optimal", "too_short", or "too_long".
    """

    name: str | None
    title: str | None
    contact_complete: bool
    missing_fields: list[str]
    summary_words: int
    summary_status: str  # "optimal", "too_short", "too_long"


@dataclass(frozen=True)
class CareerHighlightsPreview:
    """Career highlights preview for plan display.

    Attributes:
        highlights: List of career highlight strings.
        count: Number of highlights configured.
        has_highlights: Whether any highlights are configured.
    """

    highlights: list[str]
    count: int
    has_highlights: bool


@dataclass(frozen=True)
class BoardRoleSummary:
    """Summary of a board role for plan display."""

    organization: str
    role: str
    role_type: str
    dates: str
    is_current: bool


@dataclass(frozen=True)
class BoardRolesPreview:
    """Board roles preview for plan display.

    Attributes:
        roles: List of board role summaries.
        count: Number of roles configured.
        current_count: Number of current/active roles.
        has_roles: Whether any roles are configured.
    """

    roles: list[BoardRoleSummary]
    count: int
    current_count: int
    has_roles: bool


@dataclass(frozen=True)
class PublicationSummary:
    """Summary of a publication for plan display."""

    title: str
    pub_type: str
    venue: str
    year: str
    is_speaking: bool


@dataclass(frozen=True)
class PublicationsPreview:
    """Publications preview for plan display.

    Attributes:
        publications: List of publication summaries.
        count: Number of publications configured.
        speaking_count: Number of speaking engagements.
        written_count: Number of written works.
        has_publications: Whether any publications are configured.
    """

    publications: list[PublicationSummary]
    count: int
    speaking_count: int
    written_count: int
    has_publications: bool


@dataclass(frozen=True)
class CurationPreview:
    """JD-relevant content curation preview for plan display.

    Shows which items were curated and their relevance scores.
    """

    highlights_result: ContentCurationResult[str] | None
    certifications_result: ContentCurationResult[Certification] | None
    board_roles_result: ContentCurationResult[BoardRole] | None
    is_executive: bool


@click.command("plan")
@click.option(
    "--jd",
    "-j",
    "jd_path",
    type=click.Path(exists=True, path_type=Path),
    help="Path to job description file",
)
@click.option(
    "--output",
    "-o",
    "output_path",
    type=click.Path(path_type=Path),
    help="Save plan to file",
)
@click.option(
    "--load",
    "-l",
    "load_path",
    type=click.Path(exists=True, path_type=Path),
    help="Load and display saved plan",
)
@click.option(
    "--top",
    "-t",
    default=8,
    help="Number of top Work Units to select (default: 8)",
)
@click.option(
    "--show-excluded",
    is_flag=True,
    help="Show top 5 excluded Work Units with reasons",
)
@click.option(
    "--show-all-excluded",
    is_flag=True,
    help="Show all excluded Work Units with reasons",
)
@click.option(
    "--strict-positions",
    is_flag=True,
    help="Validate position_id references exist before planning (fail on invalid refs)",
)
@click.option(
    "--allow-gaps/--no-allow-gaps",
    "allow_gaps",
    default=None,
    help="Override employment_continuity mode: --allow-gaps for pure relevance, "
    "--no-allow-gaps for minimum_bullet (default from config)",
)
@click.option(
    "--years",
    "-y",
    "years",
    type=int,
    default=None,
    help="Limit work history to last N years (overrides config history_years)",
)
@click.pass_context
@handle_errors
def plan_command(
    ctx: click.Context,
    jd_path: Path | None,
    output_path: Path | None,
    load_path: Path | None,
    top: int,
    show_excluded: bool,
    show_all_excluded: bool,
    strict_positions: bool,
    allow_gaps: bool | None,
    years: int | None,
) -> None:
    """Preview which Work Units will be included in a resume.

    This is the "terraform plan" for your resume - see exactly what
    will be selected before generating output.
    """
    # Handle loading saved plan
    if load_path:
        plan = SavedPlan.load(load_path)
        _display_saved_plan(plan, ctx.obj.json_output if ctx.obj else False)
        return

    # Require --jd if not loading
    if not jd_path:
        raise click.UsageError("Either --jd or --load is required")

    config = get_config()

    # Load Work Units
    work_units = load_all_work_units(config.work_units_dir)
    if not work_units:
        warning("No Work Units found. Run `resume new work-unit` to create some.")
        return

    # Load positions for seniority inference (Story 7.12)
    position_service = PositionService(config.positions_path)
    positions = position_service.load_positions()

    # Apply work history duration filter (Story 13.2)
    # CLI --years flag overrides config.history_years
    effective_years = years if years is not None else config.history_years
    if effective_years is not None and positions:
        original_count = len(positions)
        positions_list = list(positions.values())
        filtered_list = PositionService.filter_by_years(positions_list, effective_years)
        positions = {pos.id: pos for pos in filtered_list}
        filtered_count = original_count - len(positions)
        if filtered_count > 0 and not ctx.obj.quiet:
            info(f"Filtered to last {effective_years} years ({filtered_count} positions excluded)")

        # Also filter work units to exclude those referencing filtered-out positions
        original_wu_count = len(work_units)
        work_units = [
            wu
            for wu in work_units
            if wu.get("position_id") is None or wu.get("position_id") in positions
        ]
        filtered_wu_count = original_wu_count - len(work_units)
        if filtered_wu_count > 0 and not ctx.obj.quiet:
            info(f"Excluded {filtered_wu_count} work units from filtered positions")

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

    # Parse JD
    jd = parse_jd_file(jd_path)
    if not ctx.obj.quiet:
        info(f"Analyzing: {jd.title or jd_path.name}")

    # Run ranking with scoring weights from config (AC: #3)
    # Pass positions for seniority inference from position title/scope (Story 7.12)
    ranker = HybridRanker()
    ranking = ranker.rank(
        work_units, jd, top_k=top, scoring_weights=config.scoring_weights, positions=positions
    )

    # Determine employment continuity mode (Story 7.20)
    # CLI flag overrides config when set
    if allow_gaps is None:
        continuity_mode = config.employment_continuity
    else:
        continuity_mode = "allow_gaps" if allow_gaps else "minimum_bullet"

    # Apply employment continuity (Story 7.20)
    continuity_service = EmploymentContinuityService(mode=continuity_mode)
    position_list = list(positions.values())

    # Build scores dict for tiebreaking
    scores = {r.work_unit_id: r.score for r in ranking.results}

    # Get initial selection
    selected = ranking.results[:top]
    selected_wu_dicts = [r.work_unit for r in selected]

    # Convert selected work units to WorkUnit objects for continuity service
    from resume_as_code.models.work_unit import WorkUnit

    selected_wus = [WorkUnit.model_validate(wu) for wu in selected_wu_dicts]
    all_wus = [WorkUnit.model_validate(wu) for wu in work_units]

    # Ensure continuity - may add work units from missing positions
    enhanced_wus = continuity_service.ensure_continuity(
        position_list, selected_wus, all_wus, scores
    )

    # Detect gaps in the enhanced selection (only relevant in allow_gaps mode,
    # since minimum_bullet mode ensures all positions have coverage)
    employment_gaps = continuity_service.detect_gaps(position_list, enhanced_wus)

    # Rebuild selected_wu_dicts from enhanced work units
    selected_wu_dicts = [wu.model_dump() for wu in enhanced_wus]

    # Run coverage analysis on selected Work Units
    coverage = analyze_coverage(jd.skills, selected_wu_dicts)

    # Lowercase JD keywords once for reuse in curation and display
    jd_keywords_lower = {k.lower() for k in jd.keywords}

    # Run skills curation
    skills_curation = _curate_skills_from_work_units(selected_wu_dicts, config, jd_keywords_lower)

    # Get position grouping for selected work units
    # Pass filtered positions to avoid re-loading (Story 13.2)
    position_grouping = _get_position_grouping(selected_wu_dicts, config, positions)

    # Get certifications analysis (AC2)
    certs_analysis = _get_certifications_analysis(jd.raw_text, config)

    # Get education analysis (AC3)
    education_analysis = _get_education_analysis(jd.raw_text, config)

    # Get profile preview (AC4)
    profile_preview = _get_profile_preview(config)

    # Get career highlights preview (AC9)
    career_highlights_preview = _get_career_highlights_preview(config)

    # Get board roles preview (AC10)
    board_roles_preview = _get_board_roles_preview(config)

    # Get publications preview (AC11)
    publications_preview = _get_publications_preview(config)

    # Get JD-relevant content curation preview (Story 7.14 AC7)
    curation_preview = _get_curation_preview(config, jd)

    # Save plan if requested
    if output_path:
        plan = SavedPlan.from_ranking(ranking, jd, jd_path, top)
        plan.save(output_path)
        success(f"Plan saved to: {output_path}")

    # Output
    if ctx.obj.json_output:
        _output_json(
            ranking.results,
            jd,
            top,
            coverage,
            skills_curation,
            position_grouping,
            certs_analysis,
            education_analysis,
            profile_preview,
            career_highlights_preview,
            board_roles_preview,
            publications_preview,
            curation_preview,
            employment_gaps=employment_gaps,
            continuity_mode=continuity_mode,
        )
    else:
        _output_rich(
            ranking.results,
            jd,
            top,
            show_excluded or show_all_excluded,
            show_all_excluded,
            coverage,
            skills_curation,
            jd_keywords_lower,
            position_grouping,
            certs_analysis,
            education_analysis,
            profile_preview,
            career_highlights_preview,
            board_roles_preview,
            publications_preview,
            curation_preview,
            employment_gaps=employment_gaps,
            continuity_mode=continuity_mode,
            positions=positions,
        )


def _curate_skills_from_work_units(
    work_units: list[dict[str, Any]],
    config: ResumeConfig,
    jd_keywords_lower: set[str] | None = None,
) -> CurationResult:
    """Extract and curate skills from selected Work Units.

    Args:
        work_units: List of selected Work Unit dictionaries.
        config: Resume configuration with skills settings.
        jd_keywords_lower: Lowercased keywords from job description.

    Returns:
        CurationResult with curated skills.
    """
    from resume_as_code.services.skill_registry import SkillRegistry

    # Extract all skills from work units
    all_skills: set[str] = set()
    for wu in work_units:
        # Filter out empty/whitespace tags
        for tag in wu.get("tags", []):
            if tag and tag.strip():
                all_skills.add(tag)
        # Handle skills_demonstrated which may be list of dicts or strings
        for skill in wu.get("skills_demonstrated", []):
            if isinstance(skill, dict):
                skill_name = skill.get("name", "")
                if skill_name and skill_name.strip():
                    all_skills.add(skill_name)
            else:
                skill_str = str(skill)
                if skill_str and skill_str.strip():
                    all_skills.add(skill_str)

    # Load registry with O*NET support if configured (Story 7.17)
    registry = SkillRegistry.load_with_onet(config.onet)

    # Create curator with config settings and registry
    curator = SkillCurator(
        max_count=config.skills.max_display,
        exclude=config.skills.exclude,
        prioritize=config.skills.prioritize,
        registry=registry,
    )

    return curator.curate(all_skills, jd_keywords_lower or set())


def _get_position_grouping(
    selected_work_units: list[dict[str, Any]],
    config: ResumeConfig,
    positions: dict[str, Any] | None = None,
) -> PositionGroupingResult:
    """Group selected work units by position/employer.

    Args:
        selected_work_units: List of selected Work Unit dictionaries.
        config: Resume configuration with positions path.
        positions: Optional pre-filtered positions dict. If None, loads from file.

    Returns:
        PositionGroupingResult with employer groups and ungrouped count.
    """
    # Always create position_service for group_by_employer method
    position_service = PositionService(config.positions_path)
    if positions is None:
        positions = position_service.load_positions()

    # If no positions file, return empty result
    if not positions:
        return PositionGroupingResult(
            employers=[],
            ungrouped_count=len(selected_work_units),
            has_positions=False,
        )

    # Group work units by position_id
    grouped: dict[str, list[str]] = {}  # position_id -> work_unit_ids
    ungrouped: list[str] = []

    for wu in selected_work_units:
        pos_id = wu.get("position_id")
        if pos_id and pos_id in positions:
            if pos_id not in grouped:
                grouped[pos_id] = []
            grouped[pos_id].append(wu.get("id", "unknown"))
        else:
            ungrouped.append(wu.get("id", "unknown"))

    # Group positions by employer
    employer_groups = position_service.group_by_employer([positions[pid] for pid in grouped])

    # Build result
    employers: list[EmployerGroup] = []
    for employer, pos_list in employer_groups.items():
        position_summaries = [
            PositionSummary(
                id=pos.id,
                title=pos.title,
                dates=pos.format_date_range(),
                work_unit_count=len(grouped.get(pos.id, [])),
            )
            for pos in pos_list
        ]
        employer_wu_count = sum(ps.work_unit_count for ps in position_summaries)
        employers.append(
            EmployerGroup(
                name=employer,
                positions=position_summaries,
                work_unit_count=employer_wu_count,
            )
        )

    return PositionGroupingResult(
        employers=employers,
        ungrouped_count=len(ungrouped),
        has_positions=True,
    )


def _get_certifications_analysis(
    jd_text: str,
    config: ResumeConfig,
) -> CertificationMatchResult:
    """Analyze user certifications against JD requirements.

    Args:
        jd_text: Raw job description text.
        config: Resume configuration (unused, data loaded via data_loader).

    Returns:
        CertificationMatchResult with matched, gaps, and additional certs.
    """
    matcher = CertificationMatcher()

    # Extract JD certification requirements
    jd_certs = matcher.extract_jd_requirements(jd_text)

    # Load certifications via data_loader (Story 9.2)
    certifications = load_certifications(Path.cwd())

    # Match against user's certifications
    return matcher.match_certifications(certifications, jd_certs)


def _get_education_analysis(
    jd_text: str,
    config: ResumeConfig,
) -> EducationMatchResult:
    """Analyze user education against JD requirements.

    Args:
        jd_text: Raw job description text.
        config: Resume configuration (unused, data loaded via data_loader).

    Returns:
        EducationMatchResult with degree match and field relevance.
    """
    matcher = EducationMatcher()

    # Extract JD education requirements
    jd_req = matcher.extract_jd_requirements(jd_text)

    # Load education via data_loader (Story 9.2)
    education = load_education(Path.cwd())

    # Match against user's education
    return matcher.match_education(education, jd_req)


def _get_profile_preview(config: ResumeConfig) -> ProfilePreview:
    """Generate profile preview with completeness check.

    Args:
        config: Resume configuration (unused, data loaded via data_loader).

    Returns:
        ProfilePreview with contact completeness and summary analysis.
    """
    # Load profile via data_loader (Story 9.2)
    profile = load_profile(Path.cwd())
    missing: list[str] = []

    # Check required contact fields
    if not profile.name:
        missing.append("name")
    if not profile.email:
        missing.append("email")
    if not profile.phone:
        missing.append("phone")
    if not profile.location:
        missing.append("location")
    if not profile.linkedin:
        missing.append("linkedin")

    # Analyze summary word count (optimal: 45-75 words per AC4)
    summary_words = len(profile.summary.split()) if profile.summary else 0
    if summary_words < 45:
        summary_status = "too_short"
    elif summary_words > 75:
        summary_status = "too_long"
    else:
        summary_status = "optimal"

    return ProfilePreview(
        name=profile.name,
        title=profile.title,
        contact_complete=len(missing) == 0,
        missing_fields=missing,
        summary_words=summary_words,
        summary_status=summary_status,
    )


def _get_career_highlights_preview(config: ResumeConfig) -> CareerHighlightsPreview:
    """Generate career highlights preview.

    Args:
        config: Resume configuration (unused, data loaded via data_loader).

    Returns:
        CareerHighlightsPreview with highlights data.
    """
    # Load highlights via data_loader (Story 9.2)
    highlights = load_highlights(Path.cwd())
    return CareerHighlightsPreview(
        highlights=highlights,
        count=len(highlights),
        has_highlights=len(highlights) > 0,
    )


def _get_board_roles_preview(config: ResumeConfig) -> BoardRolesPreview:
    """Generate board roles preview.

    Args:
        config: Resume configuration (unused, data loaded via data_loader).

    Returns:
        BoardRolesPreview with roles data.
    """
    # Load board roles via data_loader (Story 9.2)
    roles = load_board_roles(Path.cwd())
    display_roles = [r for r in roles if r.display]

    role_summaries = [
        BoardRoleSummary(
            organization=role.organization,
            role=role.role,
            role_type=role.type,
            dates=role.format_date_range(),
            is_current=role.is_current,
        )
        for role in display_roles
    ]

    current_count = sum(1 for role in display_roles if role.is_current)

    return BoardRolesPreview(
        roles=role_summaries,
        count=len(display_roles),
        current_count=current_count,
        has_roles=len(display_roles) > 0,
    )


def _get_publications_preview(config: ResumeConfig) -> PublicationsPreview:
    """Generate publications preview.

    Args:
        config: Resume configuration (unused, data loaded via data_loader).

    Returns:
        PublicationsPreview with publications data.
    """
    # Load publications via data_loader (Story 9.2)
    pubs = load_publications(Path.cwd())
    display_pubs = [p for p in pubs if p.display]

    pub_summaries = [
        PublicationSummary(
            title=pub.title,
            pub_type=pub.type,
            venue=pub.venue,
            year=pub.year,
            is_speaking=pub.is_speaking,
        )
        for pub in display_pubs
    ]

    speaking_count = sum(1 for pub in display_pubs if pub.is_speaking)
    written_count = len(display_pubs) - speaking_count

    return PublicationsPreview(
        publications=pub_summaries,
        count=len(display_pubs),
        speaking_count=speaking_count,
        written_count=written_count,
        has_publications=len(display_pubs) > 0,
    )


def _get_curation_preview(
    config: ResumeConfig,
    jd: Any,
) -> CurationPreview | None:
    """Generate JD-relevant content curation preview.

    Uses ContentCurator to curate career highlights, certifications,
    and board roles based on JD relevance with scores.

    Args:
        config: Resume configuration with curation settings.
        jd: Parsed job description.

    Returns:
        CurationPreview with curated content and scores, or None if no content.
    """
    from resume_as_code.services.embedder import EmbeddingService

    # Load data via data_loader (Story 9.2)
    career_highlights = load_highlights(Path.cwd())
    certifications = load_certifications(Path.cwd())
    board_roles = load_board_roles(Path.cwd())

    # Check if there's any content to curate
    has_content = career_highlights or certifications or board_roles
    if not has_content:
        return None

    # Initialize curator with config
    embedder = EmbeddingService()
    curator = ContentCurator(
        embedder=embedder,
        config=config.curation,
        quantified_boost=config.scoring_weights.quantified_boost,
    )

    # Determine if executive role for board role limits
    is_executive = is_executive_level(jd.experience_level)

    # Curate highlights
    highlights_result = None
    if career_highlights:
        highlights_result = curator.curate_highlights(
            career_highlights,
            jd,
        )

    # Curate certifications
    certs_result = None
    if certifications:
        certs_result = curator.curate_certifications(
            certifications,
            jd,
        )

    # Curate board roles
    board_roles_result = None
    if board_roles:
        board_roles_result = curator.curate_board_roles(
            board_roles,
            jd,
            is_executive_role=is_executive,
        )

    return CurationPreview(
        highlights_result=highlights_result,
        certifications_result=certs_result,
        board_roles_result=board_roles_result,
        is_executive=is_executive,
    )


def _display_saved_plan(plan: SavedPlan, json_mode: bool = False) -> None:
    """Display a loaded SavedPlan."""
    # Check for Work Unit changes (Task 3.4)
    config = get_config()
    current_work_units = load_all_work_units(config.work_units_dir)
    current_wu_ids = {wu.get("id") for wu in current_work_units}
    saved_wu_ids = {wu.id for wu in plan.selected_work_units}
    missing_wu_ids = saved_wu_ids - current_wu_ids

    if json_mode:
        response = JSONResponse(
            status="success",
            command="plan",
            data={
                "loaded_from": plan.jd_path,
                "jd_hash": plan.jd_hash,
                "jd_title": plan.jd_title,
                "created_at": plan.created_at.strftime("%Y-%m-%dT%H:%M:%S"),
                "selected": [
                    {
                        "id": wu.id,
                        "title": wu.title,
                        "score": wu.score,
                        "match_reasons": wu.match_reasons,
                    }
                    for wu in plan.selected_work_units
                ],
                "selection_count": plan.selection_count,
                "top_k": plan.top_k,
                "version": plan.version,
                "missing_work_units": list(missing_wu_ids),
            },
        )
        json_output(response.to_json())
        return

    # Rich output for saved plan
    console.print()
    console.print(
        Panel(
            f"[bold]Saved Resume Plan[/bold]\n"
            f"JD: {plan.jd_title or 'Untitled'}\n"
            f"Created: {plan.created_at.strftime('%Y-%m-%d %H:%M')}\n"
            f"Hash: {plan.jd_hash}",
            title="Plan Preview (Loaded)",
            border_style="blue",
        )
    )

    # Warn if Work Units have changed (Task 3.4)
    if missing_wu_ids:
        warning(
            f"⚠️  {len(missing_wu_ids)} Work Unit(s) from this plan no longer exist: "
            f"{', '.join(sorted(missing_wu_ids))}"
        )
        console.print()

    # Selected Work Units
    console.print(
        f"\n[bold green]SELECTED[/bold green] ({len(plan.selected_work_units)} Work Units)\n"
    )

    for wu in plan.selected_work_units:
        score_color = "green" if wu.score >= 0.7 else "yellow" if wu.score >= 0.4 else "red"
        # Mark missing Work Units
        missing_marker = " [red][MISSING][/red]" if wu.id in missing_wu_ids else ""
        title_display = f"[bold]{wu.title}[/bold]{missing_marker}"
        console.print(f"  [{score_color}]{wu.score:.0%}[/{score_color}] {title_display}")
        console.print(f"       [dim]{wu.id}[/dim]")
        if wu.match_reasons:
            for reason in wu.match_reasons:
                console.print(f"       [cyan]>[/cyan] {reason}")
        console.print()


def _output_rich(
    results: list[RankingResult],
    jd: Any,
    top: int,
    show_excluded: bool,
    show_all: bool = False,
    coverage: CoverageReport | None = None,
    skills_curation: CurationResult | None = None,
    jd_keywords_lower: set[str] | None = None,
    position_grouping: PositionGroupingResult | None = None,
    certs_analysis: CertificationMatchResult | None = None,
    education_analysis: EducationMatchResult | None = None,
    profile_preview: ProfilePreview | None = None,
    career_highlights_preview: CareerHighlightsPreview | None = None,
    board_roles_preview: BoardRolesPreview | None = None,
    publications_preview: PublicationsPreview | None = None,
    curation_preview: CurationPreview | None = None,
    employment_gaps: list[EmploymentGap] | None = None,
    continuity_mode: str | None = None,
    positions: dict[str, Any] | None = None,
) -> None:
    """Display plan with Rich formatting."""
    selected = results[:top]
    excluded = results[top:]

    # Header
    console.print()
    console.print(
        Panel(
            f"[bold]Resume Plan[/bold]\n"
            f"JD: {jd.title or 'Untitled'}\n"
            f"Experience Level: {jd.experience_level.value}",
            title="Plan Preview",
            border_style="blue",
        )
    )

    # Profile Preview (AC4: first section after header)
    if profile_preview:
        _display_profile_preview(profile_preview)

    # Position Grouping Preview (AC1: before selected work units)
    if position_grouping:
        _display_position_grouping(position_grouping)

    # Selected Work Units
    console.print(f"\n[bold green]SELECTED[/bold green] ({len(selected)} Work Units)\n")

    for result in selected:
        score_color = "green" if result.score >= 0.7 else "yellow" if result.score >= 0.4 else "red"
        console.print(
            f"  [{score_color}]{result.score:.0%}[/{score_color}] "
            f"[bold]{result.work_unit.get('title', 'Untitled')}[/bold]"
        )
        console.print(f"       [dim]{result.work_unit_id}[/dim]")
        if result.match_reasons:
            for reason in result.match_reasons:
                console.print(f"       [cyan]>[/cyan] {reason}")
        console.print()

    # Employment Gap Warning (Story 7.20 AC4)
    # Only show in allow_gaps mode when gaps exist
    if continuity_mode == "allow_gaps" and employment_gaps:
        from resume_as_code.services.employment_continuity import (
            EmploymentContinuityService,
        )

        service = EmploymentContinuityService()
        gap_warning = service.format_gap_warning(employment_gaps)
        if gap_warning:
            console.print()
            console.print(gap_warning)
            console.print()

    # Content Analysis
    _display_content_analysis(selected)

    # Keyword Analysis
    _display_keyword_analysis(selected, jd)

    # Skill Coverage Analysis
    if coverage:
        _display_coverage(coverage)

    # Skills Curation
    if skills_curation:
        _display_skills_curation(skills_curation, jd_keywords_lower or set())

    # Certifications Analysis (AC2)
    if certs_analysis:
        _display_certifications_analysis(certs_analysis)

    # Education Analysis (AC3)
    if education_analysis:
        _display_education_analysis(education_analysis)

    # Career Highlights Preview (AC9)
    if career_highlights_preview:
        _display_career_highlights_preview(career_highlights_preview)

    # Board Roles Preview (AC10)
    if board_roles_preview:
        _display_board_roles_preview(board_roles_preview)

    # Publications Preview (AC11)
    if publications_preview:
        _display_publications_preview(publications_preview)

    # JD-Relevant Content Curation (Story 7.14 AC7)
    if curation_preview:
        _display_curation_preview(curation_preview)

    # Excluded (if requested)
    if show_excluded and excluded:
        # Calculate selected position IDs for gap flagging (Story 7.20 AC7)
        selected_position_ids: set[str] = set()
        for r in selected:
            pos_id = r.work_unit.get("position_id")
            if pos_id and isinstance(pos_id, str):
                selected_position_ids.add(pos_id)
        _display_excluded(
            excluded,
            show_all=show_all,
            selected_position_ids=selected_position_ids,
            positions=positions,
        )


def _display_position_grouping(grouping: PositionGroupingResult) -> None:
    """Display position grouping preview section.

    Shows how work units will be grouped by employer/position on the resume.

    Args:
        grouping: Position grouping result with employer groups.
    """
    # AC6: Handle no positions gracefully
    if not grouping.has_positions:
        console.print(
            Panel(
                "[dim]No positions configured[/dim]\n"
                "[yellow]Consider adding positions.yaml for employer grouping[/yellow]",
                title="Position Grouping",
                border_style="dim",
            )
        )
        return

    # Build content for panel
    lines: list[str] = []

    for employer_group in grouping.employers:
        wu_count = employer_group.work_unit_count
        lines.append(f"[bold]{employer_group.name}[/bold] ({wu_count} work units)")
        for pos in employer_group.positions:
            lines.append(f"  • {pos.title} ({pos.dates})")
            if pos.work_unit_count > 0:
                lines.append(f"    [dim]{pos.work_unit_count} work unit(s)[/dim]")

    if grouping.ungrouped_count > 0:
        ungrouped = grouping.ungrouped_count
        lines.append(f"\n[yellow]⚠ {ungrouped} work unit(s) not linked to positions[/yellow]")

    console.print(
        Panel(
            "\n".join(lines),
            title="Position Grouping Preview",
            border_style="cyan",
        )
    )


def _display_profile_preview(preview: ProfilePreview) -> None:
    """Display profile preview section.

    Shows contact completeness and summary word count status.

    Args:
        preview: Profile preview with completeness data.
    """
    lines: list[str] = []

    # AC8: Handle missing/incomplete profile
    if not preview.name and not preview.title:
        console.print(
            Panel(
                "[dim]Profile not configured[/dim]\n"
                "[yellow]Configure profile in .resume.yaml[/yellow]",
                title="Profile Preview",
                border_style="dim",
            )
        )
        return

    # Name and title
    if preview.name:
        lines.append(f"[bold]Name:[/bold] {preview.name}")
    if preview.title:
        lines.append(f"[bold]Title:[/bold] {preview.title}")

    # Contact completeness
    if preview.contact_complete:
        lines.append("\n[green]✓ Contact info complete[/green]")
    else:
        lines.append(f"\n[yellow]⚠ Missing:[/yellow] {', '.join(preview.missing_fields)}")

    # Summary word count with status indicator
    summary_colors = {
        "optimal": "green",
        "too_short": "yellow",
        "too_long": "yellow",
    }
    summary_color = summary_colors.get(preview.summary_status, "dim")

    summary_label = {
        "optimal": "optimal",
        "too_short": "too short (aim for 45-75 words)",
        "too_long": "too long (aim for 45-75 words)",
    }.get(preview.summary_status, preview.summary_status)

    lines.append(
        f"\n[bold]Summary:[/bold] {preview.summary_words} words "
        f"[{summary_color}]({summary_label})[/{summary_color}]"
    )

    console.print(
        Panel(
            "\n".join(lines),
            title="Profile Preview",
            border_style="green",
        )
    )


def _display_certifications_analysis(analysis: CertificationMatchResult) -> None:
    """Display certifications analysis section.

    Shows matched certifications (green), gaps (red), and additional (dim).

    Args:
        analysis: Certification match result from CertificationMatcher.
    """
    lines: list[str] = []

    # Check if no certifications at all (AC7)
    if not analysis.matched and not analysis.additional:
        console.print(
            Panel(
                "[dim]No certifications configured[/dim]\n"
                "[yellow]Add certifications to .resume.yaml[/yellow]",
                title="Certifications Analysis",
                border_style="dim",
            )
        )
        # Still show gaps if JD mentions certs
        if analysis.gaps:
            console.print("[dim]JD mentions these certifications:[/dim]")
            for cert in analysis.gaps:
                console.print(f"  [red]✗[/red] {cert}")
        return

    # Matched certifications (green) - AC2
    if analysis.matched:
        lines.append("[bold green]Matched:[/bold green]")
        for cert in analysis.matched:
            lines.append(f"  [green]✓[/green] {cert}")

    # Gaps (red) - certifications JD wants but user doesn't have
    if analysis.gaps:
        lines.append("\n[bold red]Gaps (JD requirements):[/bold red]")
        for cert in analysis.gaps:
            lines.append(f"  [red]✗[/red] {cert}")

    # Additional (dim) - user certs not mentioned in JD
    if analysis.additional:
        lines.append("\n[dim]Additional (not in JD):[/dim]")
        for cert in analysis.additional:
            lines.append(f"  [dim]○[/dim] {cert}")

    # Summary line
    lines.append(f"\n[dim]Match rate: {analysis.match_percentage}%[/dim]")

    console.print(
        Panel(
            "\n".join(lines),
            title="Certifications Analysis",
            border_style="magenta",
        )
    )


def _display_education_analysis(analysis: EducationMatchResult) -> None:
    """Display education analysis section.

    Shows degree match status and field relevance.

    Args:
        analysis: Education match result from EducationMatcher.
    """
    lines: list[str] = []

    # Check if no education configured
    if not analysis.best_match_education:
        console.print(
            Panel(
                "[dim]No education configured[/dim]\n"
                "[yellow]Add education to .resume.yaml[/yellow]",
                title="Education Analysis",
                border_style="dim",
            )
        )
        # Show JD requirement if any
        if analysis.jd_requirement_text:
            console.print(f"[dim]JD requirement: {analysis.jd_requirement_text}[/dim]")
        return

    # Your education
    lines.append(f"[bold]Your Education:[/bold] {analysis.best_match_education}")

    # JD Requirement
    if analysis.jd_requirement_text:
        lines.append(f"[bold]JD Requirement:[/bold] {analysis.jd_requirement_text}")
    else:
        lines.append("[bold]JD Requirement:[/bold] [dim]None specified[/dim]")

    # Degree match status with color coding
    degree_colors = {
        "exceeds": "green",
        "meets": "green",
        "below": "red",
        "unknown": "yellow",
    }
    degree_color = degree_colors.get(analysis.degree_match, "yellow")
    degree_match = analysis.degree_match
    lines.append(f"\n[bold]Degree Level:[/bold] [{degree_color}]{degree_match}[/{degree_color}]")

    # Field relevance with color coding
    field_colors = {
        "direct": "green",
        "related": "yellow",
        "unrelated": "red",
        "unknown": "dim",
    }
    field_color = field_colors.get(analysis.field_relevance, "dim")
    field_rel = analysis.field_relevance
    lines.append(f"[bold]Field Relevance:[/bold] [{field_color}]{field_rel}[/{field_color}]")

    # Overall status
    status_color = "green" if analysis.meets_requirements else "red"
    status_icon = "✓" if analysis.meets_requirements else "✗"
    status_text = "Meets requirements" if analysis.meets_requirements else "Below requirements"
    lines.append(f"\n[{status_color}]{status_icon} {status_text}[/{status_color}]")

    console.print(
        Panel(
            "\n".join(lines),
            title="Education Analysis",
            border_style="blue",
        )
    )


def _display_career_highlights_preview(preview: CareerHighlightsPreview) -> None:
    """Display career highlights preview section.

    Shows configured career highlights for executive/hybrid resumes.

    Args:
        preview: Career highlights preview data.
    """
    # Handle no highlights configured
    if not preview.has_highlights:
        console.print(
            Panel(
                "[dim]No career highlights configured[/dim]\n"
                "[yellow]Add career_highlights to .resume.yaml for executive resumes[/yellow]",
                title="Career Highlights",
                border_style="dim",
            )
        )
        return

    lines: list[str] = []
    for i, highlight in enumerate(preview.highlights, 1):
        lines.append(f"  {i}. {highlight}")

    # Add count indicator
    count_color = "green" if preview.count <= 4 else "yellow"
    lines.append(f"\n[{count_color}]{preview.count} highlight(s) configured[/{count_color}]")
    if preview.count > 4:
        lines.append("[yellow]⚠ Research suggests max 4 highlights for optimal impact[/yellow]")

    console.print(
        Panel(
            "\n".join(lines),
            title="Career Highlights",
            border_style="cyan",
        )
    )


def _display_board_roles_preview(preview: BoardRolesPreview) -> None:
    """Display board roles preview section.

    Shows configured board and advisory roles.

    Args:
        preview: Board roles preview data.
    """
    # Handle no roles configured
    if not preview.has_roles:
        console.print(
            Panel(
                "[dim]No board roles configured[/dim]\n"
                "[yellow]Add board_roles to .resume.yaml for executive resumes[/yellow]",
                title="Board & Advisory Roles",
                border_style="dim",
            )
        )
        return

    lines: list[str] = []
    for role in preview.roles:
        current_marker = " [green](current)[/green]" if role.is_current else ""
        role_type_label = f"[dim]({role.role_type})[/dim]"
        role_line = f"  • [bold]{role.organization}[/bold] - {role.role}"
        lines.append(f"{role_line} {role_type_label}{current_marker}")
        lines.append(f"    [dim]{role.dates}[/dim]")

    # Summary
    if preview.current_count > 0:
        current_text = f"{preview.current_count} current"
    else:
        current_text = "none current"
    lines.append(f"\n[dim]{preview.count} role(s) ({current_text})[/dim]")

    console.print(
        Panel(
            "\n".join(lines),
            title="Board & Advisory Roles",
            border_style="magenta",
        )
    )


def _display_publications_preview(preview: PublicationsPreview) -> None:
    """Display publications preview section.

    Shows configured publications and speaking engagements.

    Args:
        preview: Publications preview data.
    """
    # Handle no publications configured
    if not preview.has_publications:
        console.print(
            Panel(
                "[dim]No publications configured[/dim]\n"
                "[yellow]Add publications to .resume.yaml for thought leadership[/yellow]",
                title="Publications & Speaking",
                border_style="dim",
            )
        )
        return

    lines: list[str] = []

    # Group by type
    speaking = [p for p in preview.publications if p.is_speaking]
    written = [p for p in preview.publications if not p.is_speaking]

    if speaking:
        lines.append("[bold]Speaking Engagements:[/bold]")
        for pub in speaking:
            lines.append(f"  • {pub.venue} ({pub.year}) - {pub.title}")
            lines.append(f"    [dim]{pub.pub_type}[/dim]")

    if written:
        if speaking:
            lines.append("")
        lines.append("[bold]Written Works:[/bold]")
        for pub in written:
            lines.append(f"  • {pub.title}")
            lines.append(f"    [dim]{pub.venue} ({pub.year}) - {pub.pub_type}[/dim]")

    # Summary
    summary = (
        f"{preview.count} publication(s): "
        f"{preview.speaking_count} speaking, {preview.written_count} written"
    )
    lines.append(f"\n[dim]{summary}[/dim]")

    console.print(
        Panel(
            "\n".join(lines),
            title="Publications & Speaking",
            border_style="yellow",
        )
    )


def _display_curation_preview(preview: CurationPreview) -> None:
    """Display JD-relevant content curation preview section.

    Shows which items were selected and their relevance scores for:
    - Career highlights (Story 7.14 AC7)
    - Certifications with priority
    - Board roles (with executive limit adjustment)

    Args:
        preview: Curation preview with curated results.
    """
    lines: list[str] = []

    # Career highlights curation
    if preview.highlights_result:
        hr = preview.highlights_result
        lines.append("[bold cyan]Career Highlights[/bold cyan] (by JD relevance):")
        for highlight in hr.selected:
            # Use content-based key for score lookup
            key = ContentCurator._highlight_key(highlight)
            score = hr.scores.get(key, 0.0)
            score_color = "green" if score >= 0.5 else "yellow"
            lines.append(f"  [{score_color}]{score:.0%}[/{score_color}] {highlight[:60]}...")
        if hr.excluded:
            lines.append(f"  [dim]({len(hr.excluded)} excluded below threshold)[/dim]")
        lines.append("")

    # Certifications curation
    if preview.certifications_result:
        cr = preview.certifications_result
        lines.append("[bold cyan]Certifications[/bold cyan] (by JD relevance):")
        for cert in cr.selected:
            has_priority = getattr(cert, "priority", None) == "always"
            priority_marker = " [magenta]★[/magenta]" if has_priority else ""
            score = cr.scores.get(cert.name, 0.0)
            score_color = "green" if score >= 0.5 else "yellow"
            if score > 0:
                score_display = f"[{score_color}]{score:.0%}[/{score_color}]"
            else:
                score_display = "[dim]priority[/dim]"
            lines.append(f"  {score_display} {cert.name}{priority_marker}")
        if cr.excluded:
            lines.append(f"  [dim]({len(cr.excluded)} excluded)[/dim]")
        lines.append("")

    # Board roles curation
    if preview.board_roles_result:
        br = preview.board_roles_result
        role_limit = "5 max (executive)" if preview.is_executive else "3 max"
        lines.append(f"[bold cyan]Board Roles[/bold cyan] ({role_limit}):")
        for role in br.selected:
            has_priority = getattr(role, "priority", None) == "always"
            priority_marker = " [magenta]★[/magenta]" if has_priority else ""
            score = br.scores.get(role.organization, 0.0)
            score_color = "green" if score >= 0.5 else "yellow"
            if score > 0:
                score_display = f"[{score_color}]{score:.0%}[/{score_color}]"
            else:
                score_display = "[dim]priority[/dim]"
            lines.append(f"  {score_display} {role.organization} - {role.role}{priority_marker}")
        if br.excluded:
            lines.append(f"  [dim]({len(br.excluded)} excluded)[/dim]")

    if lines:
        console.print(
            Panel(
                "\n".join(lines),
                title="Content Curation (JD-Relevant)",
                border_style="cyan",
            )
        )


def _display_content_analysis(selected: list[RankingResult]) -> None:
    """Display content analysis section."""
    # Calculate word count
    total_words = sum(len(extract_work_unit_text(r.work_unit).split()) for r in selected)

    # Estimate pages
    estimated_pages = total_words / WORDS_PER_PAGE

    # Determine optimal range
    if estimated_pages <= ONE_PAGE_THRESHOLD:
        optimal = f"{ONE_PAGE_MIN_WORDS}-{ONE_PAGE_MAX_WORDS}"
        in_range = ONE_PAGE_MIN_WORDS <= total_words <= ONE_PAGE_MAX_WORDS
    else:
        optimal = f"{TWO_PAGE_MIN_WORDS:,}-{TWO_PAGE_MAX_WORDS:,}"
        in_range = TWO_PAGE_MIN_WORDS <= total_words <= TWO_PAGE_MAX_WORDS

    status = "[green]OK[/green]" if in_range else "[yellow]![/yellow]"

    console.print(
        Panel(
            f"Word Count: {total_words} (optimal: {optimal}) {status}\n"
            f"Estimated Pages: {estimated_pages:.1f}",
            title="Content Analysis",
            border_style="cyan",
        )
    )


def _display_keyword_analysis(selected: list[RankingResult], jd: Any) -> None:
    """Display keyword analysis section."""
    # Get all text from selected Work Units
    all_text = " ".join(extract_work_unit_text(r.work_unit).lower() for r in selected)

    # Check JD keywords
    found = [kw for kw in jd.keywords if kw.lower() in all_text]
    missing = [kw for kw in jd.keywords if kw.lower() not in all_text]

    coverage = len(found) / len(jd.keywords) * 100 if jd.keywords else 100

    status = "[green]OK[/green]" if coverage >= 60 else "[yellow]![/yellow]"

    content = f"Coverage: {coverage:.0f}% ({len(found)}/{len(jd.keywords)} keywords) {status}"
    if missing[:5]:
        content += f"\nMissing: {', '.join(missing[:5])}"

    console.print(
        Panel(
            content,
            title="Keyword Analysis",
            border_style="yellow",
        )
    )


def _display_coverage(report: CoverageReport) -> None:
    """Display skill coverage analysis with Rich formatting."""
    if not report.items:
        return

    # Header with summary
    summary = (
        f"Coverage: {report.coverage_percentage:.0f}%\n"
        f"Strong: {report.strong_count} | Weak: {report.weak_count} | Gaps: {report.gap_count}"
    )

    console.print(
        Panel(
            summary,
            title="🎯 Skill Coverage",
            border_style="magenta",
        )
    )

    # Show each skill with its coverage status
    for item in report.items:
        wu_info = ""
        if item.matching_work_units:
            # Show up to 2 Work Unit IDs
            wu_ids = item.matching_work_units[:2]
            wu_info = f" ({', '.join(wu_ids)})"
            if len(item.matching_work_units) > 2:
                wu_info = f" ({', '.join(wu_ids)}, +{len(item.matching_work_units) - 2})"

        # Add "Weak signal" indicator for weak matches per AC3
        weak_label = " [dim]Weak signal[/dim]" if item.level == CoverageLevel.WEAK else ""
        line = f"  [{item.color}]{item.symbol}[/{item.color}] {item.skill}{weak_label}{wu_info}"
        console.print(line)


def _display_skills_curation(
    curation_result: CurationResult,
    jd_keywords_lower: set[str],
) -> None:
    """Display skills curation in plan output.

    Args:
        curation_result: Result from SkillCurator.
        jd_keywords_lower: Lowercased keywords from job description.
    """
    console.print("\n[bold]Skills Curation:[/bold]")

    if not curation_result.included:
        console.print("  [dim]No skills extracted from selected Work Units[/dim]")
        return

    # Build skills display with JD match indicators
    skill_lines = []
    for skill in curation_result.included:
        match_indicator = " [green]✓[/green]" if skill.lower() in jd_keywords_lower else ""
        skill_lines.append(f"  {skill}{match_indicator}")

    for line in skill_lines:
        console.print(line)

    # Stats
    stats = curation_result.stats
    console.print(
        f"\n[dim]Curated {stats['included']} from {stats['total_raw']} total skills[/dim]"
    )

    # Excluded count (if any)
    if curation_result.excluded:
        console.print(f"[dim]Excluded: {len(curation_result.excluded)} skills[/dim]")


def _display_excluded(
    excluded: list[RankingResult],
    show_all: bool = False,
    selected_position_ids: set[str] | None = None,
    positions: dict[str, Any] | None = None,
) -> None:
    """Display excluded Work Units with reasons.

    Args:
        excluded: List of excluded ranking results.
        show_all: If True, show all excluded work units.
        selected_position_ids: Set of position IDs that have work units in the selection.
        positions: Dictionary of position_id -> Position for gap duration calculation.
    """
    from resume_as_code.services.employment_continuity import EmploymentContinuityService

    total_excluded = len(excluded)
    to_show = excluded if show_all else excluded[:5]

    if show_all:
        console.print(f"\n[bold dim]EXCLUDED[/bold dim] ({total_excluded} total)\n")
    else:
        console.print(
            f"\n[bold dim]EXCLUDED[/bold dim] ({total_excluded} total, showing {len(to_show)})\n"
        )

    # Create continuity service for gap duration calculation
    continuity_service = EmploymentContinuityService()

    for result in to_show:
        title = result.work_unit.get("title", "Untitled")
        reason = get_exclusion_reason(result.score)
        position_id = result.work_unit.get("position_id")

        console.print(f"  [dim]{result.score:.0%}[/dim] [dim]{title}[/dim]")
        console.print(f"       [dim italic]{reason.message}[/dim italic]")

        # Story 7.20 AC7: Flag excluded work units that would cause gaps
        if (
            position_id
            and selected_position_ids is not None
            and positions is not None
            and position_id not in selected_position_ids
        ):
            # This excluded work unit is from a position with no representation
            position = positions.get(position_id)
            if position:
                # Calculate gap duration from position dates
                start_date = continuity_service._parse_date(position.start_date)
                end_date = continuity_service._parse_date(position.end_date)
                if start_date:
                    from datetime import date

                    if end_date is None:
                        end_date = date.today()
                    gap_months = continuity_service._months_between(start_date, end_date)
                    if gap_months >= 3:
                        gap_msg = f"⚠️ Excluding this creates {gap_months}-month gap"
                        console.print(f"       [yellow]{gap_msg}[/yellow]")

        if reason.suggestion:
            console.print(f"       [blue]💡 {reason.suggestion}[/blue]")

    if not show_all and total_excluded > 5:
        console.print(
            f"\n  [dim]... and {total_excluded - 5} more. Use --show-all-excluded to see all.[/dim]"
        )


def _output_json(
    results: list[RankingResult],
    jd: Any,
    top: int,
    coverage: CoverageReport | None = None,
    skills_curation: CurationResult | None = None,
    position_grouping: PositionGroupingResult | None = None,
    certs_analysis: CertificationMatchResult | None = None,
    education_analysis: EducationMatchResult | None = None,
    profile_preview: ProfilePreview | None = None,
    career_highlights_preview: CareerHighlightsPreview | None = None,
    board_roles_preview: BoardRolesPreview | None = None,
    publications_preview: PublicationsPreview | None = None,
    curation_preview: CurationPreview | None = None,
    employment_gaps: list[EmploymentGap] | None = None,
    continuity_mode: str | None = None,
) -> None:
    """Output plan as JSON."""
    selected = results[:top]
    excluded = results[top:]

    # Build skills_curation data for JSON
    skills_curation_data = None
    if skills_curation:
        skills_curation_data = {
            "included": skills_curation.included,
            "excluded": [
                {"skill": skill, "reason": reason} for skill, reason in skills_curation.excluded
            ],
            "stats": skills_curation.stats,
        }

    # Build position_grouping data for JSON (AC5)
    position_grouping_data = None
    if position_grouping and position_grouping.has_positions:
        position_grouping_data = {
            "employers": [
                {
                    "name": eg.name,
                    "positions": [
                        {
                            "id": ps.id,
                            "title": ps.title,
                            "dates": ps.dates,
                        }
                        for ps in eg.positions
                    ],
                    "work_unit_count": eg.work_unit_count,
                }
                for eg in position_grouping.employers
            ],
            "ungrouped_count": position_grouping.ungrouped_count,
        }

    # Build certifications_analysis data for JSON (AC5)
    certs_analysis_data = None
    if certs_analysis:
        certs_analysis_data = {
            "matched": certs_analysis.matched,
            "gaps": certs_analysis.gaps,
            "additional": certs_analysis.additional,
            "match_percentage": certs_analysis.match_percentage,
        }

    # Build education_analysis data for JSON (AC5)
    education_analysis_data = None
    if education_analysis:
        education_analysis_data = {
            "meets_requirements": education_analysis.meets_requirements,
            "degree_match": education_analysis.degree_match,
            "field_relevance": education_analysis.field_relevance,
            "jd_requirement": education_analysis.jd_requirement_text,
            "user_education": education_analysis.best_match_education,
        }

    # Build profile_preview data for JSON (AC5)
    profile_preview_data = None
    if profile_preview:
        profile_preview_data = {
            "name": profile_preview.name,
            "title": profile_preview.title,
            "contact_complete": profile_preview.contact_complete,
            "missing_fields": profile_preview.missing_fields,
            "summary_words": profile_preview.summary_words,
            "summary_status": profile_preview.summary_status,
        }

    # Build career_highlights data for JSON (AC9)
    career_highlights_data = None
    if career_highlights_preview and career_highlights_preview.has_highlights:
        career_highlights_data = {
            "highlights": career_highlights_preview.highlights,
            "count": career_highlights_preview.count,
        }

    # Build board_roles data for JSON (AC10)
    board_roles_data = None
    if board_roles_preview and board_roles_preview.has_roles:
        board_roles_data = {
            "roles": [
                {
                    "organization": role.organization,
                    "role": role.role,
                    "type": role.role_type,
                    "dates": role.dates,
                    "is_current": role.is_current,
                }
                for role in board_roles_preview.roles
            ],
            "count": board_roles_preview.count,
            "current_count": board_roles_preview.current_count,
        }

    # Build publications data for JSON (AC11)
    publications_data = None
    if publications_preview and publications_preview.has_publications:
        publications_data = {
            "publications": [
                {
                    "title": pub.title,
                    "type": pub.pub_type,
                    "venue": pub.venue,
                    "year": pub.year,
                    "is_speaking": pub.is_speaking,
                }
                for pub in publications_preview.publications
            ],
            "count": publications_preview.count,
            "speaking_count": publications_preview.speaking_count,
            "written_count": publications_preview.written_count,
        }

    # Build curation preview data for JSON (Story 7.14 AC7)
    curation_preview_data: dict[str, Any] | None = None
    if curation_preview:
        curation_preview_data = {
            "is_executive_role": curation_preview.is_executive,
            "highlights": None,
            "certifications": None,
            "board_roles": None,
        }
        if curation_preview.highlights_result:
            hr = curation_preview.highlights_result
            curation_preview_data["highlights"] = {
                "selected": hr.selected,
                "excluded": hr.excluded,
                "scores": hr.scores,
                "reason": hr.reason,
            }
        if curation_preview.certifications_result:
            cr = curation_preview.certifications_result
            curation_preview_data["certifications"] = {
                "selected": [c.name for c in cr.selected],
                "excluded": [c.name for c in cr.excluded],
                "scores": cr.scores,
                "reason": cr.reason,
            }
        if curation_preview.board_roles_result:
            br = curation_preview.board_roles_result
            curation_preview_data["board_roles"] = {
                "selected": [r.organization for r in br.selected],
                "excluded": [r.organization for r in br.excluded],
                "scores": br.scores,
                "reason": br.reason,
            }

    response = JSONResponse(
        status="success",
        command="plan",
        data={
            "jd": {
                "title": jd.title,
                "skills": jd.skills,
                "experience_level": jd.experience_level.value,
            },
            "selected": [
                {
                    "id": r.work_unit_id,
                    "title": r.work_unit.get("title"),
                    "score": r.score,
                    "match_reasons": r.match_reasons,
                }
                for r in selected
            ],
            "selection_count": len(selected),
            "excluded": [
                {
                    "id": r.work_unit_id,
                    "title": r.work_unit.get("title"),
                    "score": r.score,
                    "exclusion_reason": get_exclusion_reason(r.score).to_dict(),
                }
                for r in excluded
            ],
            "excluded_count": len(excluded),
            "coverage": coverage.to_dict() if coverage else None,
            "skills_curation": skills_curation_data,
            "position_grouping": position_grouping_data,
            "certifications_analysis": certs_analysis_data,
            "education_analysis": education_analysis_data,
            "profile_preview": profile_preview_data,
            "career_highlights": career_highlights_data,
            "board_roles": board_roles_data,
            "publications": publications_data,
            "content_curation": curation_preview_data,
            "employment_continuity": {
                "mode": continuity_mode,
                "gaps": [
                    {
                        "position_id": gap.missing_position_id,
                        "employer": gap.missing_employer,
                        "start_date": gap.start_date.isoformat(),
                        "end_date": gap.end_date.isoformat(),
                        "duration_months": gap.duration_months,
                    }
                    for gap in (employment_gaps or [])
                ],
            }
            if continuity_mode
            else None,
        },
    )
    json_output(response.to_json())
