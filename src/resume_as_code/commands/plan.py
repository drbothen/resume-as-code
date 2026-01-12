"""Plan command for resume preview."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import click
from rich.panel import Panel

from resume_as_code.config import get_config
from resume_as_code.models.exclusion import get_exclusion_reason
from resume_as_code.models.output import JSONResponse
from resume_as_code.services.jd_parser import parse_jd_file
from resume_as_code.services.ranker import HybridRanker, RankingResult
from resume_as_code.services.work_unit_service import load_all_work_units
from resume_as_code.utils.console import console, info, json_output, warning
from resume_as_code.utils.errors import handle_errors

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
    required=True,
    help="Path to job description file",
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
    jd_path: Path,
    top: int,
    show_excluded: bool,
    show_all_excluded: bool,
) -> None:
    """Preview which Work Units will be included in a resume.

    This is the "terraform plan" for your resume - see exactly what
    will be selected before generating output.
    """
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

    # Run ranking
    ranker = HybridRanker()
    ranking = ranker.rank(work_units, jd, top_k=top)

    # Output
    if ctx.obj.json_output:
        _output_json(ranking.results, jd, top)
    else:
        _output_rich(
            ranking.results, jd, top, show_excluded or show_all_excluded, show_all_excluded
        )


def _output_rich(
    results: list[RankingResult],
    jd: Any,
    top: int,
    show_excluded: bool,
    show_all: bool = False,
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

    # Excluded (if requested)
    if show_excluded and excluded:
        _display_excluded(excluded, show_all=show_all)


def _display_content_analysis(selected: list[RankingResult]) -> None:
    """Display content analysis section."""
    # Calculate word count
    total_words = sum(len(_extract_text(r.work_unit).split()) for r in selected)

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
    all_text = " ".join(_extract_text(r.work_unit).lower() for r in selected)

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


def _extract_text(work_unit: dict[str, Any]) -> str:
    """Extract text from Work Unit."""
    parts: list[str] = []

    # Title
    if title := work_unit.get("title"):
        parts.append(title)

    # Problem
    if problem := work_unit.get("problem"):
        if isinstance(problem, dict):
            if stmt := problem.get("statement"):
                parts.append(stmt)
        elif isinstance(problem, str):
            parts.append(problem)

    # Actions
    if actions := work_unit.get("actions"):
        if isinstance(actions, list):
            parts.extend(str(a) for a in actions)
        elif isinstance(actions, str):
            parts.append(actions)

    # Outcome
    if outcome := work_unit.get("outcome"):
        if isinstance(outcome, dict):
            if result := outcome.get("result"):
                parts.append(result)
        elif isinstance(outcome, str):
            parts.append(outcome)

    return " ".join(filter(None, parts))


def _output_json(results: list[RankingResult], jd: Any, top: int) -> None:
    """Output plan as JSON."""
    selected = results[:top]
    excluded = results[top:]

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
        },
    )
    json_output(response.to_json())
