# Story 4.3: Plan Command & Selection Display

Status: done

## Story

As a **user**,
I want **to run `resume plan` and see which Work Units will be included**,
So that **I know exactly what my resume will contain before generating it**.

## Acceptance Criteria

1. **Given** I run `resume plan --jd senior-engineer.txt`
   **When** the command executes
   **Then** I see a "SELECTED" section with Work Units that will be included
   **And** each selected Work Unit shows: ID, title, relevance score, match reasons

2. **Given** the plan displays selected Work Units
   **When** I review the output
   **Then** Work Units are ordered by relevance score (highest first)
   **And** scores are displayed as percentages (e.g., "87% match")

3. **Given** I run `resume plan --jd file.txt --top 5`
   **When** the command executes
   **Then** only the top 5 Work Units are selected

4. **Given** no `--top` flag is provided
   **When** the plan runs
   **Then** a sensible default is used (top 8)

5. **Given** I run the plan command
   **When** output is displayed
   **Then** Rich formatting makes selections easy to scan
   **And** match reasons are indented under each Work Unit

6. **Given** I run `resume plan --jd file.txt`
   **When** the plan displays content analysis
   **Then** I see total word count with optimal range comparison
   **And** I see estimated page count

7. **Given** I run `resume plan --jd file.txt`
   **When** the plan displays keyword analysis
   **Then** I see keyword coverage percentage
   **And** I see list of missing high-priority JD keywords

## Tasks / Subtasks

- [x] Task 1: Create plan command module (AC: #1, #2, #3, #4)
  - [x] 1.1: Create `src/resume_as_code/commands/plan.py`
  - [x] 1.2: Implement `resume plan` command with Click
  - [x] 1.3: Add `--jd` option (required) for job description file
  - [x] 1.4: Add `--top` option with default of 8
  - [x] 1.5: Register command in `cli.py`

- [x] Task 2: Wire up ranking pipeline (AC: #1, #2)
  - [x] 2.1: Load Work Units from configured directory
  - [x] 2.2: Parse JD file using jd_parser
  - [x] 2.3: Run hybrid ranking
  - [x] 2.4: Select top N Work Units

- [x] Task 3: Implement Rich output display (AC: #1, #2, #5)
  - [x] 3.1: Create "SELECTED" section with Rich Panel
  - [x] 3.2: Display Work Unit ID, title, score as percentage
  - [x] 3.3: Display match reasons indented under each Work Unit
  - [x] 3.4: Use color coding (green for high scores, yellow for medium)

- [x] Task 4: Implement content analysis (AC: #6)
  - [x] 4.1: Calculate total word count of selected Work Units
  - [x] 4.2: Compare against optimal ranges (475-600 for 1-page, 800-1200 for 2-page)
  - [x] 4.3: Estimate page count
  - [x] 4.4: Display in Content Analysis section

- [x] Task 5: Implement keyword analysis (AC: #7)
  - [x] 5.1: Calculate keyword coverage percentage
  - [x] 5.2: Identify missing high-priority JD keywords
  - [x] 5.3: Display in Keyword Analysis section

- [x] Task 6: Implement JSON output (AC: #1)
  - [x] 6.1: Support `--json` flag for machine-readable output
  - [x] 6.2: Include all selection data in JSON

- [x] Task 7: Code quality verification
  - [x] 7.1: Run `ruff check src tests --fix`
  - [x] 7.2: Run `ruff format src tests`
  - [x] 7.3: Run `mypy src --strict` with zero errors
  - [x] 7.4: Add integration tests for plan command

## Dev Notes

### Architecture Compliance

This story implements the "Terraform-style preview" - the killer feature that differentiates Resume as Code from other tools.

**Source:** [epics.md#Story 4.3](_bmad-output/planning-artifacts/epics.md)

### Dependencies

This story REQUIRES:
- Story 4.1 (Job Description Parser)
- Story 4.2 (BM25 Ranking Engine)
- Story 1.2 (Rich Console)

### Plan Command Implementation

**`src/resume_as_code/commands/plan.py`:**

```python
"""Plan command for resume preview."""

from __future__ import annotations

from pathlib import Path

import click
from rich.panel import Panel
from rich.table import Table

from resume_as_code.config import get_config
from resume_as_code.models.output import JSONResponse
from resume_as_code.services.jd_parser import parse_jd_file
from resume_as_code.services.ranker import HybridRanker
from resume_as_code.services.work_unit_service import load_all_work_units
from resume_as_code.utils.console import console, success, warning, info
from resume_as_code.utils.errors import handle_errors


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
    help="Show excluded Work Units with reasons",
)
@click.pass_context
@handle_errors
def plan_command(
    ctx: click.Context,
    jd_path: Path,
    top: int,
    show_excluded: bool,
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
        _output_json(ctx, ranking, jd, top)
    else:
        _output_rich(ranking, jd, top, show_excluded)


def _output_rich(ranking, jd, top: int, show_excluded: bool) -> None:
    """Display plan with Rich formatting."""
    selected = ranking.results[:top]
    excluded = ranking.results[top:]

    # Header
    console.print()
    console.print(Panel(
        f"[bold]Resume Plan[/bold]\n"
        f"JD: {jd.title or 'Untitled'}\n"
        f"Experience Level: {jd.experience_level.value}",
        title="📋 Plan Preview",
        border_style="blue",
    ))

    # Selected Work Units
    console.print("\n[bold green]✓ SELECTED[/bold green] "
                  f"({len(selected)} Work Units)\n")

    for i, result in enumerate(selected, 1):
        score_color = "green" if result.score >= 0.7 else "yellow" if result.score >= 0.4 else "red"
        console.print(
            f"  [{score_color}]{result.score:.0%}[/{score_color}] "
            f"[bold]{result.work_unit['title']}[/bold]"
        )
        console.print(f"       [dim]{result.work_unit_id}[/dim]")
        if result.match_reasons:
            for reason in result.match_reasons:
                console.print(f"       [cyan]↳[/cyan] {reason}")
        console.print()

    # Content Analysis
    _display_content_analysis(selected)

    # Keyword Analysis
    _display_keyword_analysis(selected, jd)

    # Excluded (if requested)
    if show_excluded and excluded:
        _display_excluded(excluded[:5])


def _display_content_analysis(selected: list) -> None:
    """Display content analysis section."""
    # Calculate word count
    total_words = sum(
        len(_extract_text(r.work_unit).split())
        for r in selected
    )

    # Estimate pages (roughly 500 words per page)
    estimated_pages = total_words / 500

    # Determine optimal range
    if estimated_pages <= 1.5:
        optimal = "475-600"
        status = "✓" if 475 <= total_words <= 600 else "⚠"
    else:
        optimal = "800-1,200"
        status = "✓" if 800 <= total_words <= 1200 else "⚠"

    console.print(Panel(
        f"Word Count: {total_words} (optimal: {optimal}) {status}\n"
        f"Estimated Pages: {estimated_pages:.1f}",
        title="📊 Content Analysis",
        border_style="cyan",
    ))


def _display_keyword_analysis(selected: list, jd) -> None:
    """Display keyword analysis section."""
    # Get all text from selected Work Units
    all_text = " ".join(
        _extract_text(r.work_unit).lower()
        for r in selected
    )

    # Check JD keywords
    found = [kw for kw in jd.keywords if kw.lower() in all_text]
    missing = [kw for kw in jd.keywords if kw.lower() not in all_text]

    coverage = len(found) / len(jd.keywords) * 100 if jd.keywords else 100

    status = "✓" if coverage >= 60 else "⚠"

    content = f"Coverage: {coverage:.0f}% ({len(found)}/{len(jd.keywords)} keywords) {status}"
    if missing[:5]:
        content += f"\nMissing: {', '.join(missing[:5])}"

    console.print(Panel(
        content,
        title="🔑 Keyword Analysis",
        border_style="yellow",
    ))


def _display_excluded(excluded: list) -> None:
    """Display excluded Work Units."""
    console.print("\n[bold red]✗ EXCLUDED[/bold red] (top 5 shown)\n")

    for result in excluded:
        console.print(
            f"  [dim]{result.score:.0%}[/dim] {result.work_unit['title']}"
        )
        console.print(f"       [dim]Below selection threshold[/dim]")


def _extract_text(work_unit: dict) -> str:
    """Extract text from Work Unit."""
    parts = [
        work_unit.get("title", ""),
        work_unit.get("problem", {}).get("statement", ""),
        " ".join(work_unit.get("actions", [])),
        work_unit.get("outcome", {}).get("result", ""),
    ]
    return " ".join(filter(None, parts))


def _output_json(ctx, ranking, jd, top: int) -> None:
    """Output plan as JSON."""
    selected = ranking.results[:top]

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
        },
    )
    print(response.to_json())
```

### Verification Commands

```bash
# Create sample JD
cat > sample-jd.txt << 'EOF'
Senior Software Engineer - Platform

Requirements:
- 5+ years Python experience
- AWS cloud infrastructure
- Kubernetes deployment
- API design
EOF

# Run plan
resume plan --jd sample-jd.txt

# With top N
resume plan --jd sample-jd.txt --top 5

# With excluded
resume plan --jd sample-jd.txt --show-excluded

# JSON output
resume --json plan --jd sample-jd.txt
```

### References

- [Source: epics.md#Story 4.3](_bmad-output/planning-artifacts/epics.md)

## Dev Agent Record

### Agent Model Used

Claude Opus 4.5 (claude-opus-4-5-20251101)

### Debug Log References

None

### Completion Notes List

- Implemented `resume plan` command following the "terraform plan" pattern for resume previews
- Created `src/resume_as_code/commands/plan.py` with all required functionality
- Added `load_all_work_units()` to `work_unit_service.py` for reusability
- Registered command in `cli.py`
- All 7 Acceptance Criteria met:
  - AC1: Shows "SELECTED" section with Work Units, ID, title, relevance score, match reasons
  - AC2: Work Units ordered by relevance score (highest first), scores as percentages
  - AC3: `--top` option limits results
  - AC4: Default top is 8
  - AC5: Rich formatting with indented match reasons
  - AC6: Content analysis shows word count, optimal range comparison, page estimate
  - AC7: Keyword analysis shows coverage percentage and missing keywords
- Added 15 integration tests for plan command
- All 684 tests pass (no regressions)
- Code quality verified: ruff lint, ruff format, mypy strict all pass

### File List

- `src/resume_as_code/commands/plan.py` (new)
- `src/resume_as_code/cli.py` (modified - registered plan_command)
- `src/resume_as_code/services/work_unit_service.py` (modified - added load_all_work_units)
- `tests/integration/test_plan_command.py` (new)

## Change Log

- 2026-01-11: Code Review PASSED - all 7 issues fixed (3 MEDIUM, 4 LOW)
  - M1: Reverted formatting-only change to jd_parser.py (not part of story)
  - M2: Fixed weak test assertion in test_plan_top_option_limits_results
  - M3: Fixed weak test assertion in test_plan_default_top_is_8
  - L1: Fixed incomplete assertion in test_plan_shows_match_reasons_indented
  - L2: Staged new files in git
  - L3: Fixed silent exception in work_unit_service.py (catch YAMLError, OSError)
  - L4: Extracted magic numbers to constants in plan.py
- 2026-01-11: Implemented Story 4.3 - Plan Command & Selection Display (all ACs met)

