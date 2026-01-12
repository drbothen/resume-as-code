"""Plan command for resume preview."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any

import click

if TYPE_CHECKING:
    from resume_as_code.models.config import ResumeConfig
from rich.panel import Panel

from resume_as_code.config import get_config
from resume_as_code.models.exclusion import get_exclusion_reason
from resume_as_code.models.output import JSONResponse
from resume_as_code.models.plan import SavedPlan
from resume_as_code.services.coverage_analyzer import (
    CoverageLevel,
    CoverageReport,
    analyze_coverage,
)
from resume_as_code.services.jd_parser import parse_jd_file
from resume_as_code.services.ranker import HybridRanker, RankingResult
from resume_as_code.services.skill_curator import CurationResult, SkillCurator
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

    # Parse JD
    jd = parse_jd_file(jd_path)
    if not ctx.obj.quiet:
        info(f"Analyzing: {jd.title or jd_path.name}")

    # Run ranking with scoring weights from config (AC: #3)
    ranker = HybridRanker()
    ranking = ranker.rank(work_units, jd, top_k=top, scoring_weights=config.scoring_weights)

    # Run coverage analysis on selected Work Units
    selected = ranking.results[:top]
    selected_wu_dicts = [r.work_unit for r in selected]
    coverage = analyze_coverage(jd.skills, selected_wu_dicts)

    # Lowercase JD keywords once for reuse in curation and display
    jd_keywords_lower = {k.lower() for k in jd.keywords}

    # Run skills curation
    skills_curation = _curate_skills_from_work_units(
        selected_wu_dicts, config, jd_keywords_lower
    )

    # Save plan if requested
    if output_path:
        plan = SavedPlan.from_ranking(ranking, jd, jd_path, top)
        plan.save(output_path)
        success(f"Plan saved to: {output_path}")

    # Output
    if ctx.obj.json_output:
        _output_json(ranking.results, jd, top, coverage, skills_curation)
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

    # Create curator with config settings
    curator = SkillCurator(
        max_count=config.skills.max_display,
        exclude=config.skills.exclude,
        prioritize=config.skills.prioritize,
    )

    return curator.curate(all_skills, jd_keywords_lower or set())


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

    # Excluded (if requested)
    if show_excluded and excluded:
        _display_excluded(excluded, show_all=show_all)


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


def _display_excluded(excluded: list[RankingResult], show_all: bool = False) -> None:
    """Display excluded Work Units with reasons."""
    total_excluded = len(excluded)
    to_show = excluded if show_all else excluded[:5]

    if show_all:
        console.print(f"\n[bold dim]EXCLUDED[/bold dim] ({total_excluded} total)\n")
    else:
        console.print(
            f"\n[bold dim]EXCLUDED[/bold dim] ({total_excluded} total, showing {len(to_show)})\n"
        )

    for result in to_show:
        title = result.work_unit.get("title", "Untitled")
        reason = get_exclusion_reason(result.score)

        console.print(f"  [dim]{result.score:.0%}[/dim] [dim]{title}[/dim]")
        console.print(f"       [dim italic]{reason.message}[/dim italic]")

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
                {"skill": skill, "reason": reason}
                for skill, reason in skills_curation.excluded
            ],
            "stats": skills_curation.stats,
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
        },
    )
    json_output(response.to_json())
