"""New command for creating Work Units and Positions."""

from __future__ import annotations

import re
from datetime import date, datetime
from typing import Any, cast

import click
from pydantic import HttpUrl

from resume_as_code.config import get_config
from resume_as_code.models.board_role import BoardRole, BoardRoleType
from resume_as_code.models.certification import Certification
from resume_as_code.models.education import Education
from resume_as_code.models.errors import NotFoundError
from resume_as_code.models.output import JSONResponse
from resume_as_code.models.position import EmploymentType, Position, PositionScope
from resume_as_code.models.publication import Publication, PublicationType
from resume_as_code.services.archetype_service import list_archetypes
from resume_as_code.services.board_role_service import BoardRoleService
from resume_as_code.services.certification_service import CertificationService
from resume_as_code.services.education_service import EducationService
from resume_as_code.services.highlight_service import HighlightService
from resume_as_code.services.position_service import PositionService
from resume_as_code.services.publication_service import PublicationService
from resume_as_code.services.work_unit_service import (
    create_work_unit_file,
    create_work_unit_from_data,
    generate_id,
)
from resume_as_code.utils.console import console, info, success, warning
from resume_as_code.utils.editor import get_editor, open_in_editor
from resume_as_code.utils.errors import handle_errors
from resume_as_code.utils.slugify import generate_unique_position_id

EMPLOYMENT_TYPES: list[EmploymentType] = [
    "full-time",
    "part-time",
    "contract",
    "consulting",
    "freelance",
]

BOARD_ROLE_TYPES: list[BoardRoleType] = [
    "director",
    "advisory",
    "committee",
]

PUBLICATION_TYPES: list[PublicationType] = [
    "conference",
    "article",
    "whitepaper",
    "book",
    "podcast",
    "webinar",
]


def parse_position_flag(value: str) -> dict[str, str | None]:
    """Parse --position flag value.

    Format: "Employer|Title|StartDate|EndDate"
    EndDate is optional (can be omitted for current position).

    Args:
        value: The position flag value in pipe-separated format.

    Returns:
        Dictionary with employer, title, start_date, end_date keys.

    Raises:
        click.BadParameter: If format is invalid.
    """
    parts = value.split("|")
    if len(parts) < 3 or len(parts) > 4:
        raise click.BadParameter(
            "Position must be in format: 'Employer|Title|StartDate|EndDate' (EndDate optional)"
        )

    employer = parts[0].strip()
    title = parts[1].strip()
    start_date = parts[2].strip()
    end_date = parts[3].strip() if len(parts) > 3 else None

    if not employer:
        raise click.BadParameter("Employer cannot be empty")
    if not title:
        raise click.BadParameter("Title cannot be empty")
    if not start_date:
        raise click.BadParameter("StartDate cannot be empty")

    return {
        "employer": employer,
        "title": title,
        "start_date": start_date,
        "end_date": end_date or None,
    }


def parse_certification_flag(value: str) -> dict[str, str | None]:
    """Parse --certification flag value.

    Format: "Name|Issuer|Date|Expires"
    Issuer, Date, and Expires can be empty.

    Args:
        value: The certification flag value in pipe-separated format.

    Returns:
        Dictionary with name, issuer, date, expires keys.

    Raises:
        click.BadParameter: If format is invalid.
    """
    parts = value.split("|")
    if len(parts) < 1 or len(parts) > 4:
        raise click.BadParameter(
            "Certification must be in format: 'Name|Issuer|Date|Expires' "
            "(Issuer, Date, Expires optional)"
        )

    name = parts[0].strip()
    if not name:
        raise click.BadParameter("Certification name cannot be empty")

    issuer = parts[1].strip() if len(parts) > 1 else None
    cert_date = parts[2].strip() if len(parts) > 2 else None
    expires = parts[3].strip() if len(parts) > 3 else None

    return {
        "name": name,
        "issuer": issuer or None,
        "date": cert_date or None,
        "expires": expires or None,
    }


def parse_education_flag(value: str) -> dict[str, str | None]:
    """Parse --education flag value.

    Format: "Degree|Institution|Year|Honors"
    Year and Honors can be empty.

    Args:
        value: The education flag value in pipe-separated format.

    Returns:
        Dictionary with degree, institution, year, honors keys.

    Raises:
        click.BadParameter: If format is invalid.
    """
    parts = value.split("|")
    if len(parts) < 2 or len(parts) > 4:
        raise click.BadParameter(
            "Education must be in format: 'Degree|Institution|Year|Honors' (Year, Honors optional)"
        )

    degree = parts[0].strip()
    institution = parts[1].strip()

    if not degree:
        raise click.BadParameter("Degree cannot be empty")
    if not institution:
        raise click.BadParameter("Institution cannot be empty")

    year = parts[2].strip() if len(parts) > 2 else None
    honors = parts[3].strip() if len(parts) > 3 else None

    return {
        "degree": degree,
        "institution": institution,
        "year": year or None,
        "honors": honors or None,
    }


def parse_board_role_flag(value: str) -> dict[str, str | None]:
    """Parse pipe-separated board role value.

    Format: "Organization|Role|Type|StartDate|EndDate|Focus"
    Type defaults to 'advisory', EndDate and Focus are optional.

    Args:
        value: The board role flag value in pipe-separated format.

    Returns:
        Dictionary with organization, role, type, start_date, end_date, focus keys.

    Raises:
        click.BadParameter: If format is invalid.
    """
    parts = value.split("|")
    if len(parts) < 4 or len(parts) > 6:
        raise click.BadParameter(
            "Board role must be in format: "
            "'Organization|Role|Type|StartDate|EndDate|Focus' "
            "(EndDate and Focus optional)"
        )

    organization = parts[0].strip()
    role = parts[1].strip()
    role_type = parts[2].strip() if parts[2].strip() else "advisory"
    start_date = parts[3].strip()
    end_date = parts[4].strip() if len(parts) > 4 else None
    focus = parts[5].strip() if len(parts) > 5 else None

    if not organization:
        raise click.BadParameter("Organization cannot be empty")
    if not role:
        raise click.BadParameter("Role cannot be empty")
    if role_type not in BOARD_ROLE_TYPES:
        raise click.BadParameter(f"Type must be one of: {', '.join(BOARD_ROLE_TYPES)}")
    if not start_date:
        raise click.BadParameter("StartDate cannot be empty")

    return {
        "organization": organization,
        "role": role,
        "type": role_type,
        "start_date": start_date,
        "end_date": end_date or None,
        "focus": focus or None,
    }


def parse_publication_flag(value: str) -> dict[str, str | list[str] | None]:
    """Parse pipe-separated publication value.

    Format: "Title|Type|Venue|Date|URL|Topics|Abstract"
    URL, Topics, and Abstract are optional.
    Topics should be comma-separated: "kubernetes,security,devops"

    Args:
        value: The publication flag value in pipe-separated format.

    Returns:
        Dictionary with title, type, venue, date, url, topics, abstract keys.

    Raises:
        click.BadParameter: If format is invalid.
    """
    parts = value.split("|")
    if len(parts) < 4 or len(parts) > 7:
        raise click.BadParameter(
            "Publication must be in format: 'Title|Type|Venue|Date|URL|Topics|Abstract' "
            "(URL, Topics, Abstract optional)"
        )

    title = parts[0].strip()
    pub_type = parts[1].strip()
    venue = parts[2].strip()
    pub_date = parts[3].strip()
    url = parts[4].strip() if len(parts) > 4 else None
    topics_str = parts[5].strip() if len(parts) > 5 else None
    abstract = parts[6].strip() if len(parts) > 6 else None

    if not title:
        raise click.BadParameter("Title cannot be empty")
    if not pub_type:
        raise click.BadParameter("Type cannot be empty")
    if pub_type not in PUBLICATION_TYPES:
        raise click.BadParameter(f"Type must be one of: {', '.join(PUBLICATION_TYPES)}")
    if not venue:
        raise click.BadParameter("Venue cannot be empty")
    if not pub_date:
        raise click.BadParameter("Date cannot be empty")

    # Parse comma-separated topics
    topics: list[str] = []
    if topics_str:
        topics = [t.strip() for t in topics_str.split(",") if t.strip()]

    return {
        "title": title,
        "type": pub_type,
        "venue": venue,
        "date": pub_date,
        "url": url or None,
        "topics": topics,
        "abstract": abstract or None,
    }


def find_existing_position(
    employer: str,
    title: str,
    positions: dict[str, Position],
) -> Position | None:
    """Find existing position by employer and title.

    Case-insensitive, whitespace-normalized matching.

    Args:
        employer: Employer name to search for.
        title: Job title to search for.
        positions: Dictionary of existing positions.

    Returns:
        Matching Position if found, None otherwise.
    """
    employer_lower = employer.lower().strip()
    title_lower = title.lower().strip()

    for pos in positions.values():
        if (
            pos.employer.lower().strip() == employer_lower
            and pos.title.lower().strip() == title_lower
        ):
            return pos

    return None


def _get_archetype_choices() -> list[str]:
    """Get available archetype choices for the CLI option."""
    archetypes = list_archetypes()
    if not archetypes:
        warning("No archetypes found; using 'greenfield' as fallback")
        return ["greenfield"]  # Fallback default
    return archetypes


@click.group("new")
def new_group() -> None:
    """Create new resources."""


@new_group.command("work-unit")
@click.option(
    "--archetype",
    "-a",
    type=click.Choice(_get_archetype_choices()),
    help="Archetype template to use",
)
@click.option(
    "--title",
    "-t",
    help="Work Unit title (used to generate ID slug)",
)
@click.option(
    "--position",
    "position_spec",
    help="Create/reuse position: 'Employer|Title|StartDate|EndDate'",
)
@click.option(
    "--position-id",
    "-p",
    help="Position ID to associate with this work unit",
)
@click.option(
    "--problem",
    help="Problem statement (min 20 chars) - enables inline creation",
)
@click.option(
    "--action",
    "actions",
    multiple=True,
    help="Action taken (repeatable, min 10 chars each)",
)
@click.option(
    "--result",
    help="Outcome result (min 10 chars)",
)
@click.option(
    "--impact",
    help="Quantified impact (optional)",
)
@click.option(
    "--skill",
    "skills",
    multiple=True,
    help="Skill demonstrated (repeatable)",
)
@click.option(
    "--tag",
    "tags",
    multiple=True,
    help="Tag for filtering (repeatable)",
)
@click.option(
    "--start-date",
    help="Start date (YYYY-MM-DD or YYYY-MM)",
)
@click.option(
    "--end-date",
    help="End date (YYYY-MM-DD or YYYY-MM)",
)
@click.option(
    "--from-memory",
    is_flag=True,
    help="Quick capture mode with minimal template",
)
@click.option(
    "--no-edit",
    is_flag=True,
    help="Don't open editor after creation",
)
@click.pass_context
@handle_errors
def new_work_unit(
    ctx: click.Context,
    archetype: str | None,
    title: str | None,
    position_spec: str | None,
    position_id: str | None,
    problem: str | None,
    actions: tuple[str, ...],
    result: str | None,
    impact: str | None,
    skills: tuple[str, ...],
    tags: tuple[str, ...],
    start_date: str | None,
    end_date: str | None,
    from_memory: bool,
    no_edit: bool,
) -> None:
    """Create a new Work Unit from an archetype template or inline data.

    For full inline creation (LLM-optimized), provide:
    --title, --problem, --action (at least one), and --result.
    """
    config = get_config()
    position_service = PositionService(config.positions_path)
    position_created = False
    actual_position_id: str | None = None

    # Validate mutually exclusive flags
    if position_spec and position_id:
        raise click.UsageError("Cannot use both --position and --position-id")

    # Handle --position-id flag
    if position_id:
        if not position_service.position_exists(position_id):
            raise NotFoundError(f"Position not found: {position_id}")
        actual_position_id = position_id

    # Handle --position flag (inline position creation/reuse)
    elif position_spec:
        try:
            pos_data = parse_position_flag(position_spec)
        except click.BadParameter as e:
            raise click.UsageError(str(e)) from e

        positions = position_service.load_positions()
        existing = find_existing_position(
            str(pos_data["employer"]),
            str(pos_data["title"]),
            positions,
        )

        if existing:
            actual_position_id = existing.id
        else:
            # Create new position
            existing_ids = set(positions.keys())
            new_position_id = generate_unique_position_id(
                str(pos_data["employer"]),
                str(pos_data["title"]),
                existing_ids,
            )
            new_pos = Position(
                id=new_position_id,
                employer=str(pos_data["employer"]),
                title=str(pos_data["title"]),
                start_date=str(pos_data["start_date"]),
                end_date=pos_data["end_date"] if pos_data["end_date"] else None,
            )
            position_service.save_position(new_pos)
            actual_position_id = new_pos.id
            position_created = True

    # Validate partial inline flags - if any inline-specific flag is provided,
    # require all of them to avoid silent fallback to template mode
    has_inline_flags = problem is not None or len(actions) > 0 or result is not None
    if has_inline_flags:
        missing = []
        if title is None:
            missing.append("--title")
        if problem is None:
            missing.append("--problem")
        if len(actions) == 0:
            missing.append("--action")
        if result is None:
            missing.append("--result")
        if missing:
            raise click.UsageError(
                f"Inline creation requires all of: --title, --problem, --action, --result. "
                f"Missing: {', '.join(missing)}"
            )

    # Determine if we're in full inline creation mode
    # (all required fields provided: title, problem, actions, result)
    inline_mode = (
        title is not None and problem is not None and len(actions) > 0 and result is not None
    )

    if inline_mode:
        # Validate inline data
        assert title is not None
        assert problem is not None
        assert result is not None

        if len(problem) < 20:
            raise click.UsageError(
                f"Problem statement must be at least 20 characters (got {len(problem)})"
            )
        if len(result) < 10:
            raise click.UsageError(f"Result must be at least 10 characters (got {len(result)})")
        for i, action in enumerate(actions):
            if len(action) < 10:
                raise click.UsageError(
                    f"Action {i + 1} must be at least 10 characters (got {len(action)})"
                )

        # Generate ID and create file from data
        work_unit_id = generate_id(title, date.today())
        # Default to 'minimal' archetype for inline mode (like --from-memory)
        inline_archetype = archetype or "minimal"
        file_path = create_work_unit_from_data(
            work_unit_id=work_unit_id,
            title=title,
            problem_statement=problem,
            actions=list(actions),
            result=result,
            work_units_dir=config.work_units_dir,
            archetype=inline_archetype,
            position_id=actual_position_id,
            quantified_impact=impact,
            skills=list(skills) if skills else None,
            tags=list(tags) if tags else None,
            start_date=start_date,
            end_date=end_date,
        )

        # Output result for inline mode
        if ctx.obj.json_output:
            data: dict[str, Any] = {
                "id": work_unit_id,
                "file": str(file_path),
                "archetype": inline_archetype,
                "inline_created": True,
                "position_created": position_created,
            }
            if actual_position_id:
                data["position_id"] = actual_position_id
            if skills:
                data["skills_count"] = len(skills)
            if tags:
                data["tags_count"] = len(tags)
            response = JSONResponse(
                status="success",
                command="new work-unit",
                data=data,
            )
            click.echo(response.to_json())
        elif not ctx.obj.quiet:
            success(f"Created Work Unit: {work_unit_id}")
            info(f"File: {file_path}")
            info(f"Archetype: {inline_archetype}")
            info(f"Actions: {len(actions)}")
            if skills:
                info(f"Skills: {len(skills)}")
            if tags:
                info(f"Tags: {len(tags)}")
            if position_created:
                success(f"Position created: {actual_position_id}")
            elif actual_position_id:
                info(f"Using position: {actual_position_id}")

        return  # Exit early for inline mode

    # Template-based creation mode (original behavior)
    # Quick capture mode - use minimal archetype, skip archetype selection
    if from_memory:
        if archetype is not None and archetype != "minimal" and not ctx.obj.quiet:
            warning(f"--from-memory overrides --archetype={archetype}, using 'minimal'")
        archetype = "minimal"
        if title is None and not ctx.obj.json_output and not ctx.obj.quiet:
            title = click.prompt("Quick title")
        elif title is None:
            title = "quick-capture"
    else:
        # Select archetype (interactive if not provided)
        if archetype is None:
            archetype = _select_archetype_interactive(ctx)

        # Get title (interactive if not provided)
        if title is None:
            title = _prompt_title_interactive(ctx)

    # Position selection (interactive if not provided and not in quiet/json mode)
    # Only prompt if no position was specified via --position or --position-id
    if actual_position_id is None and not ctx.obj.json_output and not ctx.obj.quiet:
        actual_position_id = _prompt_position_interactive(ctx, config, from_memory=from_memory)

    # Generate ID and create file
    work_unit_id = generate_id(title, date.today())
    file_path = create_work_unit_file(
        archetype=archetype,
        work_unit_id=work_unit_id,
        title=title,
        work_units_dir=config.work_units_dir,
        position_id=actual_position_id,
    )

    # Output result
    if ctx.obj.json_output:
        template_data: dict[str, str | bool] = {
            "id": work_unit_id,
            "file": str(file_path),
            "archetype": archetype,
            "position_created": position_created,
        }
        if actual_position_id:
            template_data["position_id"] = actual_position_id
        response = JSONResponse(
            status="success",
            command="new work-unit",
            data=template_data,
        )
        click.echo(response.to_json())
    elif not ctx.obj.quiet:
        success(f"Created Work Unit: {work_unit_id}")
        info(f"File: {file_path}")
        if position_created:
            success(f"Position created: {actual_position_id}")
        elif actual_position_id:
            info(f"Using position: {actual_position_id}")

    # Open in editor
    if not no_edit and not ctx.obj.json_output and not ctx.obj.quiet:
        editor = get_editor(config)
        if editor:
            open_in_editor(file_path, editor)
        else:
            info("Set $EDITOR or $VISUAL to auto-open files")


def _select_archetype_interactive(ctx: click.Context) -> str:
    """Interactively select an archetype."""
    if ctx.obj.json_output or ctx.obj.quiet:
        # Non-interactive mode - use default
        return "greenfield"

    archetypes = list_archetypes()
    if not archetypes:
        return "greenfield"

    console.print("\n[bold]Select an archetype:[/bold]\n")

    for i, name in enumerate(archetypes, 1):
        console.print(f"  {i}. {name}")

    default_idx = archetypes.index("greenfield") + 1 if "greenfield" in archetypes else 1
    console.print(f"\n  [dim]Default: {archetypes[default_idx - 1]}[/dim]")

    choice: int = click.prompt(
        "Choice",
        type=click.IntRange(1, len(archetypes)),
        default=default_idx,
        show_default=False,
    )

    return archetypes[choice - 1]


def _prompt_title_interactive(ctx: click.Context) -> str:
    """Interactively prompt for title."""
    if ctx.obj.json_output or ctx.obj.quiet:
        # Non-interactive mode - use placeholder
        return "untitled-work-unit"

    title: str = click.prompt("Work Unit title")
    return title


@new_group.command("position")
@click.argument("position_spec", required=False)
@click.option("--employer", help="Employer name")
@click.option("--title", "job_title", help="Job title")
@click.option("--location", help="Location (city, state)")
@click.option("--start-date", help="Start date (YYYY-MM)")
@click.option("--end-date", help="End date (YYYY-MM) or blank for current")
@click.option(
    "--employment-type",
    type=click.Choice(EMPLOYMENT_TYPES),
    help="Employment type",
)
@click.option("--promoted-from", help="Position ID this was promoted from")
# Scope indicators for executive positions (AC #6, #7)
@click.option("--scope-revenue", help="Revenue impact (e.g., '$500M')")
@click.option("--scope-team-size", type=int, help="Team size (number)")
@click.option("--scope-direct-reports", type=int, help="Direct reports count")
@click.option("--scope-budget", help="Budget managed (e.g., '$50M')")
@click.option("--scope-pl", help="P&L responsibility (e.g., '$100M')")
@click.option("--scope-geography", help="Geographic reach (e.g., 'Global', 'EMEA')")
@click.option("--scope-customers", help="Customer scope (e.g., '500K users', 'Fortune 500')")
@click.pass_context
@handle_errors
def new_position(
    ctx: click.Context,
    position_spec: str | None,
    employer: str | None,
    job_title: str | None,
    location: str | None,
    start_date: str | None,
    end_date: str | None,
    employment_type: EmploymentType | None,
    promoted_from: str | None,
    scope_revenue: str | None,
    scope_team_size: int | None,
    scope_direct_reports: int | None,
    scope_budget: str | None,
    scope_pl: str | None,
    scope_geography: str | None,
    scope_customers: str | None,
) -> None:
    """Create a new employment position.

    Can be used in three ways:
    1. Pipe-separated: resume new position "Employer|Title|StartDate|EndDate"
    2. Flags: resume new position --employer "X" --title "Y" --start-date "2022-01"
    3. Interactive: resume new position

    For executive positions, add scope indicators:
      --scope-revenue "$500M"
      --scope-team-size 200
      --scope-budget "$50M"
      --scope-pl "$100M"
      --scope-geography "Global (15 countries)"
      --scope-customers "Fortune 500 clients"
    """
    config = get_config()
    service = PositionService(config.positions_path)

    # Parse pipe-separated format if provided
    if position_spec:
        try:
            parsed = parse_position_flag(position_spec)
            employer = employer or parsed["employer"]
            job_title = job_title or parsed["title"]
            start_date = start_date or parsed["start_date"]
            end_date = end_date or parsed["end_date"]
        except click.BadParameter as e:
            raise click.UsageError(str(e)) from e

    # Determine interactive vs non-interactive mode
    non_interactive = employer is not None and job_title is not None and start_date is not None

    if non_interactive:
        # Non-interactive mode - use provided values directly
        # These are guaranteed non-None due to the non_interactive condition above
        assert employer is not None
        assert job_title is not None
        assert start_date is not None

        # Validate date format
        if not _validate_date_format(start_date):
            raise click.UsageError("Invalid start-date format. Use YYYY-MM.")
        if end_date and not _validate_date_format(end_date):
            raise click.UsageError("Invalid end-date format. Use YYYY-MM.")

        # Validate promoted_from if provided
        if promoted_from and not service.position_exists(promoted_from):
            raise NotFoundError(f"Position not found: {promoted_from}")

        # Generate unique ID
        existing_ids = set(service.load_positions().keys())
        position_id = generate_unique_position_id(employer, job_title, existing_ids)

        # Build scope from flags (AC #6)
        scope = _build_position_scope(
            revenue=scope_revenue,
            team_size=scope_team_size,
            direct_reports=scope_direct_reports,
            budget=scope_budget,
            pl=scope_pl,
            geography=scope_geography,
            customers=scope_customers,
        )

        # Create position
        position = Position(
            id=position_id,
            employer=employer,
            title=job_title,
            location=location,
            start_date=start_date,
            end_date=end_date,
            employment_type=employment_type,
            promoted_from=promoted_from,
            scope=scope,
        )

    else:
        # Interactive mode - prompt for values
        console.print("[bold]Create New Position[/bold]\n")

        # Required fields
        employer = employer or click.prompt("Employer name")
        job_title = job_title or click.prompt("Job title")

        # Optional location
        if location is None:
            location_input: str = click.prompt("Location (city, state/country)", default="")
            location = location_input if location_input else None

        # Date prompts
        default_date = datetime.now().strftime("%Y-%m")
        if start_date is None:
            start_date = click.prompt("Start date (YYYY-MM)", default=default_date)

        # Validate date format
        if not _validate_date_format(start_date):
            console.print("[red]✗ Invalid date format. Use YYYY-MM.[/red]")
            raise SystemExit(1)

        if end_date is None:
            is_current: bool = click.confirm("Is this your current position?", default=True)
            if not is_current:
                end_date_input: str = click.prompt("End date (YYYY-MM)")
                if not _validate_date_format(end_date_input):
                    console.print("[red]✗ Invalid date format. Use YYYY-MM.[/red]")
                    raise SystemExit(1)
                end_date = end_date_input

        # Employment type selection
        if employment_type is None:
            console.print("\n[bold]Employment Type:[/bold]")
            for i, emp_type in enumerate(EMPLOYMENT_TYPES, 1):
                console.print(f"  {i}. {emp_type}")

            type_choice: int = click.prompt(
                "Select type",
                type=click.IntRange(1, len(EMPLOYMENT_TYPES)),
                default=1,
            )
            employment_type = EMPLOYMENT_TYPES[type_choice - 1]

        # Promotion check
        if promoted_from is None and click.confirm(
            "\nWas this a promotion from a previous position?", default=False
        ):
            positions = service.load_positions()
            if positions:
                console.print("\n[bold]Select previous position:[/bold]")
                pos_list = list(positions.values())
                for i, pos in enumerate(pos_list, 1):
                    console.print(f"  {i}. {pos.title} at {pos.employer}")

                prev_choice: int = click.prompt(
                    "Select position",
                    type=click.IntRange(1, len(pos_list)),
                )
                promoted_from = pos_list[prev_choice - 1].id
            else:
                console.print("[dim]No existing positions to link as promotion source.[/dim]")

        # Scope indicators for executive positions (AC #6)
        scope = None
        if click.confirm("\nAdd scope indicators (for executive roles)?", default=False):
            console.print("\n[bold]Scope Indicators[/bold]")
            console.print("[dim]Leave blank to skip any field.[/dim]\n")

            scope_pl_input: str = click.prompt("P&L responsibility (e.g., $100M)", default="")
            scope_revenue_input: str = click.prompt("Revenue impact (e.g., $500M)", default="")
            scope_team_input: str = click.prompt("Team size (number)", default="")
            scope_direct_input: str = click.prompt("Direct reports (number)", default="")
            scope_budget_input: str = click.prompt("Budget managed (e.g., $50M)", default="")
            scope_geo_input: str = click.prompt("Geography (e.g., Global, EMEA)", default="")
            scope_customers_input: str = click.prompt(
                "Customer scope (e.g., 500K users)", default=""
            )

            scope = _build_position_scope(
                revenue=scope_revenue_input or None,
                team_size=int(scope_team_input) if scope_team_input else None,
                direct_reports=int(scope_direct_input) if scope_direct_input else None,
                budget=scope_budget_input or None,
                pl=scope_pl_input or None,
                geography=scope_geo_input or None,
                customers=scope_customers_input or None,
            )

        # Generate unique ID
        existing_ids = set(service.load_positions().keys())
        position_id = generate_unique_position_id(employer, job_title, existing_ids)

        # Create position
        position = Position(
            id=position_id,
            employer=employer,
            title=job_title,
            location=location,
            start_date=start_date,
            end_date=end_date,
            employment_type=employment_type,
            promoted_from=promoted_from,
            scope=scope,
        )

    service.save_position(position)

    # Output result
    if ctx.obj.json_output:
        data: dict[str, Any] = {
            "position_id": position.id,
            "employer": position.employer,
            "title": position.title,
            "file": str(config.positions_path),
        }
        if position.scope:
            data["has_scope"] = True
        response = JSONResponse(
            status="success",
            command="new position",
            data=data,
        )
        click.echo(response.to_json())
    else:
        success(f"Position created: {position.id}")
        info(f"Use this ID in work units: position_id: {position.id}")
        if position.scope:
            # Import format_scope_line to display the formatted scope
            from resume_as_code.services.position_service import format_scope_line

            scope_line = format_scope_line(position)
            if scope_line:
                info(f"Scope: {scope_line}")


def _prompt_position_interactive(
    ctx: click.Context, config: Any, from_memory: bool = False
) -> str | None:
    """Prompt user to select or create a position.

    Args:
        ctx: Click context.
        config: Application configuration.
        from_memory: If True, suggest position based on current date (AC#5).

    Returns:
        Position ID if selected, None if skipped or no positions exist.
    """
    service = PositionService(config.positions_path)
    positions = service.load_positions()

    # Only prompt if positions exist - skip for new projects
    if not positions:
        return None

    # AC#5: Date-based position suggestion for --from-memory mode
    if from_memory:
        today = datetime.now().strftime("%Y-%m")
        suggested = service.suggest_position_for_date(today)
        if suggested:
            console.print(
                f"\n[cyan]Suggested position:[/cyan] {suggested.title} at {suggested.employer}"
            )
            if click.confirm("Use this position?", default=True):
                return suggested.id
            # User declined, fall through to full selection

    options: list[tuple[str, str]] = []

    # Add existing positions sorted by start_date descending
    sorted_positions = sorted(
        positions.values(),
        key=lambda p: p.start_date,
        reverse=True,
    )
    for pos in sorted_positions:
        options.append((pos.id, f"{pos.title} at {pos.employer}"))

    # Add special options
    options.append(("__new__", "Create new position..."))
    options.append(("__none__", "No position (personal project)"))

    console.print("\n[bold]Select Position:[/bold]")
    for i, (_, label) in enumerate(options, 1):
        console.print(f"  {i}. {label}")

    choice: int = click.prompt(
        "Select option",
        type=click.IntRange(1, len(options)),
        default=len(options),  # Default to "No position"
    )
    selected_id, _ = options[choice - 1]

    if selected_id == "__new__":
        # Inline create new position - call the position creation logic
        console.print("\n[bold]Create New Position[/bold]\n")
        return _create_position_inline(ctx, config, service)
    elif selected_id == "__none__":
        return None
    else:
        return selected_id


def _create_position_inline(ctx: click.Context, config: Any, service: PositionService) -> str:
    """Create a position inline during work unit creation."""
    # Required fields
    employer: str = click.prompt("Employer name")
    title: str = click.prompt("Job title")

    # Optional location (consistent with main new position command)
    location_input: str = click.prompt("Location (city, state/country)", default="")
    location: str | None = location_input if location_input else None

    # Date prompts
    default_date = datetime.now().strftime("%Y-%m")
    start_date: str = click.prompt("Start date (YYYY-MM)", default=default_date)

    is_current: bool = click.confirm("Is this your current position?", default=True)
    end_date: str | None = None
    if not is_current:
        end_date = click.prompt("End date (YYYY-MM)")

    # Employment type selection
    console.print("\n[bold]Employment Type:[/bold]")
    for i, emp_type in enumerate(EMPLOYMENT_TYPES, 1):
        console.print(f"  {i}. {emp_type}")

    type_choice: int = click.prompt(
        "Select type",
        type=click.IntRange(1, len(EMPLOYMENT_TYPES)),
        default=1,
    )
    employment_type = EMPLOYMENT_TYPES[type_choice - 1]

    # Generate unique ID
    existing_ids = set(service.load_positions().keys())
    position_id = generate_unique_position_id(employer, title, existing_ids)

    # Create and save position
    position = Position(
        id=position_id,
        employer=employer,
        title=title,
        location=location,
        start_date=start_date,
        end_date=end_date,
        employment_type=employment_type,
    )

    service.save_position(position)
    success(f"Position created: {position_id}")

    return position_id


def _validate_date_format(date_str: str) -> bool:
    """Validate YYYY-MM date format for CLI input.

    Note: This intentionally duplicates validation from models.types.YearMonth.
    CLI-layer validation provides immediate user feedback before model creation,
    enabling clearer error messages and interactive prompts for correction.
    """
    return bool(re.match(r"^\d{4}-\d{2}$", date_str))


def _build_position_scope(
    revenue: str | None,
    team_size: int | None,
    direct_reports: int | None,
    budget: str | None,
    pl: str | None,
    geography: str | None,
    customers: str | None = None,
) -> PositionScope | None:
    """Build PositionScope from individual scope flags.

    Returns None if no scope fields are populated.
    """
    if not any([revenue, team_size, direct_reports, budget, pl, geography, customers]):
        return None

    return PositionScope(
        revenue=revenue,
        team_size=team_size,
        direct_reports=direct_reports,
        budget=budget,
        pl_responsibility=pl,
        geography=geography,
        customers=customers,
    )


def _validate_year_format(year_str: str) -> bool:
    """Validate YYYY year format for CLI input.

    Note: This intentionally duplicates validation from models.types.Year.
    CLI-layer validation provides immediate user feedback before model creation,
    enabling clearer error messages and interactive prompts for correction.
    """
    return bool(re.match(r"^\d{4}$", year_str))


@new_group.command("certification")
@click.argument("certification_spec", required=False)
@click.option("--name", required=False, help="Certification name")
@click.option("--issuer", help="Issuing organization")
@click.option("--date", "cert_date", help="Date obtained (YYYY-MM)")
@click.option("--expires", help="Expiration date (YYYY-MM)")
@click.option("--credential-id", help="Credential ID")
@click.option("--url", help="Verification URL")
@click.pass_context
@handle_errors
def new_certification(
    ctx: click.Context,
    certification_spec: str | None,
    name: str | None,
    issuer: str | None,
    cert_date: str | None,
    expires: str | None,
    credential_id: str | None,
    url: str | None,
) -> None:
    """Create a new certification record.

    Can be used in three ways:
    1. Pipe-separated: resume new certification "Name|Issuer|Date|Expires"
    2. Flags: resume new certification --name "Name" --issuer "Issuer"
    3. Interactive: resume new certification
    """
    # Use Path.cwd() for config location (certifications stored in .resume.yaml)
    service = CertificationService(config_path=ctx.obj.effective_config_path)

    # Parse pipe-separated format if provided
    if certification_spec:
        try:
            parsed = parse_certification_flag(certification_spec)
            name = name or parsed["name"]
            issuer = issuer or parsed["issuer"]
            cert_date = cert_date or parsed["date"]
            expires = expires or parsed["expires"]
        except click.BadParameter as e:
            raise click.UsageError(str(e)) from e

    # Determine interactive vs non-interactive mode
    non_interactive = name is not None

    if non_interactive:
        # Non-interactive mode - use provided values directly
        assert name is not None

        # Validate name is not empty
        if not name.strip():
            raise click.UsageError("Certification name cannot be empty")

        # Validate date formats if provided
        if cert_date and not _validate_date_format(cert_date):
            raise click.UsageError("Invalid date format. Use YYYY-MM.")
        if expires and not _validate_date_format(expires):
            raise click.UsageError("Invalid expires format. Use YYYY-MM.")

        # Check for duplicate
        existing = service.find_certification(name, issuer)
        if existing:
            if ctx.obj.json_output:
                response = JSONResponse(
                    status="success",
                    command="new certification",
                    data={
                        "certification_created": False,
                        "message": f"Certification '{name}' already exists",
                    },
                )
                click.echo(response.to_json())
            else:
                info(f"Certification '{name}' already exists")
            return

        # Create certification
        certification = Certification(
            name=name,
            issuer=issuer,
            date=cert_date,
            expires=expires,
            credential_id=credential_id,
            url=HttpUrl(url) if url else None,
        )

    else:
        # Interactive mode - prompt for values
        console.print("[bold]Create New Certification[/bold]\n")

        # Required fields
        name = click.prompt("Certification name")

        # Optional fields
        issuer_input: str = click.prompt("Issuing organization", default="")
        issuer = issuer_input if issuer_input else None

        cert_date_input: str = click.prompt("Date obtained (YYYY-MM)", default="")
        if cert_date_input and not _validate_date_format(cert_date_input):
            console.print("[red]✗ Invalid date format. Use YYYY-MM.[/red]")
            raise SystemExit(1)
        cert_date = cert_date_input if cert_date_input else None

        expires_input: str = click.prompt("Expiration date (YYYY-MM)", default="")
        if expires_input and not _validate_date_format(expires_input):
            console.print("[red]✗ Invalid date format. Use YYYY-MM.[/red]")
            raise SystemExit(1)
        expires = expires_input if expires_input else None

        credential_id_input: str = click.prompt("Credential ID", default="")
        credential_id = credential_id_input if credential_id_input else None

        url_input: str = click.prompt("Verification URL", default="")
        url = url_input if url_input else None

        # Create certification
        certification = Certification(
            name=name,
            issuer=issuer,
            date=cert_date,
            expires=expires,
            credential_id=credential_id,
            url=HttpUrl(url) if url else None,
        )

    service.save_certification(certification)

    # Output result
    if ctx.obj.json_output:
        response = JSONResponse(
            status="success",
            command="new certification",
            data={
                "certification_created": True,
                "name": certification.name,
                "issuer": certification.issuer,
                "file": str(service.config_path),
            },
        )
        click.echo(response.to_json())
    else:
        success(f"Certification created: {certification.name}")
        if certification.issuer:
            info(f"Issuer: {certification.issuer}")


@new_group.command("education")
@click.argument("education_spec", required=False)
@click.option("--degree", required=False, help="Degree name")
@click.option("--institution", required=False, help="Institution name")
@click.option("--year", help="Graduation year (YYYY)")
@click.option("--honors", help="Honors/distinction")
@click.option("--gpa", help="GPA (e.g., 3.8/4.0)")
@click.pass_context
@handle_errors
def new_education(
    ctx: click.Context,
    education_spec: str | None,
    degree: str | None,
    institution: str | None,
    year: str | None,
    honors: str | None,
    gpa: str | None,
) -> None:
    """Create a new education record.

    Can be used in three ways:
    1. Pipe-separated: resume new education "Degree|Institution|Year|Honors"
    2. Flags: resume new education --degree "BS CS" --institution "MIT"
    3. Interactive: resume new education
    """
    # Use Path.cwd() for config location (education stored in .resume.yaml)
    service = EducationService(config_path=ctx.obj.effective_config_path)

    # Parse pipe-separated format if provided
    if education_spec:
        try:
            parsed = parse_education_flag(education_spec)
            degree = degree or parsed["degree"]
            institution = institution or parsed["institution"]
            year = year or parsed["year"]
            honors = honors or parsed["honors"]
        except click.BadParameter as e:
            raise click.UsageError(str(e)) from e

    # Determine interactive vs non-interactive mode
    non_interactive = degree is not None and institution is not None

    if non_interactive:
        # Non-interactive mode - use provided values directly
        assert degree is not None
        assert institution is not None

        # Validate year format if provided
        if year and not _validate_year_format(year):
            raise click.UsageError("Invalid year format. Use YYYY.")

        # Check for duplicate
        existing = service.find_education(degree, institution)
        if existing:
            if ctx.obj.json_output:
                response = JSONResponse(
                    status="success",
                    command="new education",
                    data={
                        "education_created": False,
                        "message": f"Education '{degree}' from '{institution}' already exists",
                    },
                )
                click.echo(response.to_json())
            else:
                info(f"Education '{degree}' from '{institution}' already exists")
            return

        # Create education
        education = Education(
            degree=degree,
            institution=institution,
            graduation_year=year,
            honors=honors,
            gpa=gpa,
        )

    else:
        # Interactive mode - prompt for values
        console.print("[bold]Create New Education Record[/bold]\n")

        # Required fields
        degree = degree or click.prompt("Degree (e.g., BS Computer Science)")
        institution = institution or click.prompt("Institution")

        # Optional fields
        year_input: str = click.prompt("Graduation year (YYYY)", default="")
        if year_input and not _validate_year_format(year_input):
            console.print("[red]✗ Invalid year format. Use YYYY.[/red]")
            raise SystemExit(1)
        year = year_input if year_input else None

        honors_input: str = click.prompt("Honors/distinction", default="")
        honors = honors_input if honors_input else None

        gpa_input: str = click.prompt("GPA (e.g., 3.8/4.0)", default="")
        gpa = gpa_input if gpa_input else None

        # Create education
        education = Education(
            degree=degree,
            institution=institution,
            graduation_year=year,
            honors=honors,
            gpa=gpa,
        )

    service.save_education(education)

    # Output result
    if ctx.obj.json_output:
        response = JSONResponse(
            status="success",
            command="new education",
            data={
                "education_created": True,
                "degree": education.degree,
                "institution": education.institution,
                "file": str(service.config_path),
            },
        )
        click.echo(response.to_json())
    else:
        success(f"Education created: {education.degree}")
        info(f"Institution: {education.institution}")


@new_group.command("highlight")
@click.option("--text", "-t", required=False, help="Highlight text (single-line achievement)")
@click.pass_context
@handle_errors
def new_highlight(
    ctx: click.Context,
    text: str | None,
) -> None:
    """Create a new career highlight.

    Career highlights appear prominently on CTO/executive resumes,
    showcasing top achievements with business impact metrics.

    Examples:
        # Non-interactive (LLM mode)
        resume new highlight --text "$50M revenue growth through digital transformation"

        # Interactive
        resume new highlight
    """
    # Use Path.cwd() for config location (highlights stored in .resume.yaml)
    service = HighlightService(config_path=ctx.obj.effective_config_path)

    # Non-interactive mode if --text provided
    if text is not None:
        # Validate text is not empty
        if not text.strip():
            raise click.UsageError("Highlight text cannot be empty")

        # Validate length (max 150 chars per config validation)
        if len(text) > 150:
            raise click.UsageError(
                f"Highlight exceeds 150 characters ({len(text)} chars). Keep highlights concise."
            )

        # Check for duplicates
        existing = service.load_highlights()
        if text in existing:
            if ctx.obj.json_output:
                response = JSONResponse(
                    status="success",
                    command="new highlight",
                    data={
                        "highlight_created": False,
                        "message": "Highlight already exists",
                    },
                )
                click.echo(response.to_json())
            else:
                info("Highlight already exists")
            return

        # Warn if exceeding recommended 4
        if len(existing) >= 4 and not ctx.obj.quiet and not ctx.obj.json_output:
            warning(
                f"You have {len(existing)} highlights. "
                "Research suggests 4 is optimal for executive resumes."
            )

        service.save_highlight(text)

        if ctx.obj.json_output:
            response = JSONResponse(
                status="success",
                command="new highlight",
                data={
                    "highlight_created": True,
                    "text": text,
                    "count": len(existing) + 1,
                    "file": str(service.config_path),
                },
            )
            click.echo(response.to_json())
        else:
            success("Highlight created")
            info(f"Total highlights: {len(existing) + 1}")

    else:
        # Interactive mode
        console.print("[bold]Create New Career Highlight[/bold]\n")
        console.print("[dim]Career highlights showcase your top achievements with metrics.[/dim]")
        console.print("[dim]Keep them concise (max 150 characters).[/dim]\n")

        text = click.prompt("Highlight text")

        if len(text) > 150:
            console.print("[red]✗ Highlight exceeds 150 characters. Please shorten.[/red]")
            raise SystemExit(1)

        service.save_highlight(text)
        success("Highlight created")
        info(f"Total highlights: {len(service.load_highlights())}")


@new_group.command("board-role")
@click.argument("board_role_spec", required=False)
@click.option("--organization", "-o", required=False, help="Organization name")
@click.option("--role", "-r", required=False, help="Role title (e.g., Board Advisor)")
@click.option(
    "--type",
    "role_type",
    type=click.Choice(BOARD_ROLE_TYPES),
    default="advisory",
    help="Role type (default: advisory)",
)
@click.option("--start-date", required=False, help="Start date (YYYY-MM)")
@click.option("--end-date", required=False, help="End date (YYYY-MM) or blank for current")
@click.option("--focus", required=False, help="Focus area or description")
@click.pass_context
@handle_errors
def new_board_role(
    ctx: click.Context,
    board_role_spec: str | None,
    organization: str | None,
    role: str | None,
    role_type: BoardRoleType,
    start_date: str | None,
    end_date: str | None,
    focus: str | None,
) -> None:
    """Create a new board or advisory role.

    Can be used in three ways:
    1. Pipe-separated: resume new board-role "Org|Role|Type|StartDate|EndDate|Focus"
    2. Flags: resume new board-role --organization "X" --role "Y" --start-date "2022-01"
    3. Interactive: resume new board-role
    """
    # Use Path.cwd() for config location (board roles stored in .resume.yaml)
    service = BoardRoleService(config_path=ctx.obj.effective_config_path)

    # Parse pipe-separated format if provided
    if board_role_spec:
        try:
            parsed = parse_board_role_flag(board_role_spec)
            organization = organization or parsed["organization"]
            role = role or parsed["role"]
            role_type = parsed["type"] or role_type  # type: ignore[assignment]
            start_date = start_date or parsed["start_date"]
            end_date = end_date or parsed["end_date"]
            focus = focus or parsed["focus"]
        except click.BadParameter as e:
            raise click.UsageError(str(e)) from e

    # Determine interactive vs non-interactive mode
    non_interactive = organization is not None and role is not None and start_date is not None

    if non_interactive:
        # Non-interactive mode - use provided values directly
        assert organization is not None
        assert role is not None
        assert start_date is not None

        # Validate date formats
        if not _validate_date_format(start_date):
            raise click.UsageError("Invalid start-date format. Use YYYY-MM.")
        if end_date and not _validate_date_format(end_date):
            raise click.UsageError("Invalid end-date format. Use YYYY-MM.")

        # Check for duplicate
        existing = service.find_board_role(organization, role)
        if existing:
            if ctx.obj.json_output:
                response = JSONResponse(
                    status="success",
                    command="new board-role",
                    data={
                        "board_role_created": False,
                        "message": f"Board role '{role}' at '{organization}' already exists",
                    },
                )
                click.echo(response.to_json())
            else:
                info(f"Board role '{role}' at '{organization}' already exists")
            return

        # Create board role
        board_role = BoardRole(
            organization=organization,
            role=role,
            type=role_type,
            start_date=start_date,
            end_date=end_date,
            focus=focus,
        )

    else:
        # Interactive mode - prompt for values
        console.print("[bold]Create New Board/Advisory Role[/bold]\n")

        # Required fields
        organization = organization or click.prompt("Organization name")
        role = role or click.prompt("Role title (e.g., Board Advisor)")

        # Role type selection
        if role_type == "advisory":  # default, ask for confirmation
            console.print("\n[bold]Role Type:[/bold]")
            for i, rt in enumerate(BOARD_ROLE_TYPES, 1):
                console.print(f"  {i}. {rt}")

            type_choice: int = click.prompt(
                "Select type",
                type=click.IntRange(1, len(BOARD_ROLE_TYPES)),
                default=2,  # advisory
            )
            role_type = BOARD_ROLE_TYPES[type_choice - 1]

        # Date prompts
        default_date = datetime.now().strftime("%Y-%m")
        if start_date is None:
            start_date = click.prompt("Start date (YYYY-MM)", default=default_date)

        # Validate date format
        if not _validate_date_format(start_date):
            console.print("[red]✗ Invalid date format. Use YYYY-MM.[/red]")
            raise SystemExit(1)

        if end_date is None:
            is_current: bool = click.confirm("Is this a current role?", default=True)
            if not is_current:
                end_date_input: str = click.prompt("End date (YYYY-MM)")
                if not _validate_date_format(end_date_input):
                    console.print("[red]✗ Invalid date format. Use YYYY-MM.[/red]")
                    raise SystemExit(1)
                end_date = end_date_input

        # Optional focus
        if focus is None:
            focus_input: str = click.prompt("Focus area (optional)", default="")
            focus = focus_input if focus_input else None

        # Create board role
        board_role = BoardRole(
            organization=organization,
            role=role,
            type=role_type,
            start_date=start_date,
            end_date=end_date,
            focus=focus,
        )

    service.save_board_role(board_role)

    # Output result
    if ctx.obj.json_output:
        response = JSONResponse(
            status="success",
            command="new board-role",
            data={
                "board_role_created": True,
                "organization": board_role.organization,
                "role": board_role.role,
                "type": board_role.type,
                "file": str(service.config_path),
            },
        )
        click.echo(response.to_json())
    else:
        success(f"Board role created: {board_role.role}")
        info(f"Organization: {board_role.organization}")
        info(f"Type: {board_role.type}")


@new_group.command("publication")
@click.argument("publication_spec", required=False)
@click.option("--title", required=False, help="Publication title")
@click.option(
    "--type",
    "pub_type",
    type=click.Choice(PUBLICATION_TYPES),
    help="Publication type",
)
@click.option("--venue", help="Venue/publisher name")
@click.option("--date", "pub_date", help="Publication date (YYYY-MM)")
@click.option("--url", help="Publication URL")
@click.option(
    "--topic",
    "-t",
    "topics",
    multiple=True,
    help="Topic tag for JD matching (repeatable)",
)
@click.option("--abstract", "-a", help="Brief description for semantic matching")
@click.pass_context
@handle_errors
def new_publication(
    ctx: click.Context,
    publication_spec: str | None,
    title: str | None,
    pub_type: str | None,
    venue: str | None,
    pub_date: str | None,
    url: str | None,
    topics: tuple[str, ...],
    abstract: str | None,
) -> None:
    """Create a new publication or speaking engagement record.

    Can be used in three ways:
    1. Pipe-separated: resume new publication "Title|Type|Venue|Date|URL|Topics|Abstract"
    2. Flags: resume new publication --title "Title" --type conference --venue "Conf"
       --topic "kubernetes" --topic "security"
    3. Interactive: resume new publication

    Types: conference, article, whitepaper, book, podcast, webinar
    Topics: Used for JD-relevance matching (comma-separated in pipe format)
    """
    # Use Path.cwd() for config location (publications stored in .resume.yaml)
    service = PublicationService(config_path=ctx.obj.effective_config_path)

    # Convert topics tuple to list for merging with parsed topics
    topics_list: list[str] = list(topics)

    # Parse pipe-separated format if provided
    if publication_spec:
        try:
            parsed = parse_publication_flag(publication_spec)
            title = title or str(parsed["title"]) if parsed["title"] else title
            pub_type = pub_type or str(parsed["type"]) if parsed["type"] else pub_type
            venue = venue or str(parsed["venue"]) if parsed["venue"] else venue
            pub_date = pub_date or str(parsed["date"]) if parsed["date"] else pub_date
            url = url or (str(parsed["url"]) if parsed["url"] else None)
            # Merge topics from pipe with topics from flags
            parsed_topics = parsed.get("topics", [])
            if isinstance(parsed_topics, list) and not topics_list:
                topics_list = parsed_topics
            abstract = abstract or (str(parsed["abstract"]) if parsed["abstract"] else None)
        except click.BadParameter as e:
            raise click.UsageError(str(e)) from e

    # Determine interactive vs non-interactive mode
    non_interactive = title is not None

    if non_interactive:
        # Non-interactive mode - use provided values directly
        assert title is not None

        # Validate required fields
        if not title.strip():
            raise click.UsageError("Publication title cannot be empty")
        if not pub_type:
            raise click.UsageError("Publication type is required")
        if not venue:
            raise click.UsageError("Venue is required")
        if not pub_date:
            raise click.UsageError("Date is required")

        # Validate date format
        if not _validate_date_format(pub_date):
            raise click.UsageError("Invalid date format. Use YYYY-MM.")

        # Check for duplicate
        existing = service.find_publication(title)
        if existing:
            if ctx.obj.json_output:
                response = JSONResponse(
                    status="success",
                    command="new publication",
                    data={
                        "publication_created": False,
                        "message": f"Publication '{title}' already exists",
                    },
                )
                click.echo(response.to_json())
            else:
                info(f"Publication '{title}' already exists")
            return

        # Create publication with new fields
        publication = Publication(
            title=title,
            type=cast(PublicationType, pub_type),
            venue=venue,
            date=pub_date,
            url=HttpUrl(url) if url else None,
            topics=topics_list,
            abstract=abstract,
        )

    else:
        # Interactive mode - prompt for values
        console.print("[bold]Create New Publication / Speaking Engagement[/bold]\n")

        # Required fields
        title = click.prompt("Title")

        # Type selection
        console.print("\nPublication types:")
        for i, t in enumerate(PUBLICATION_TYPES, 1):
            console.print(f"  {i}. {t}")
        type_idx_str: str = click.prompt("Select type (number)", default="1")
        try:
            type_idx = int(type_idx_str) - 1
            if type_idx < 0 or type_idx >= len(PUBLICATION_TYPES):
                console.print("[red]✗ Invalid selection.[/red]")
                raise SystemExit(1)
            pub_type = PUBLICATION_TYPES[type_idx]
        except ValueError:
            console.print("[red]✗ Invalid selection.[/red]")
            raise SystemExit(1) from None

        venue = click.prompt("Venue/Publisher")

        pub_date_input: str = click.prompt("Date (YYYY-MM)")
        if not _validate_date_format(pub_date_input):
            console.print("[red]✗ Invalid date format. Use YYYY-MM.[/red]")
            raise SystemExit(1)
        pub_date = pub_date_input

        url_input: str = click.prompt("URL (optional)", default="")
        url = url_input if url_input else None

        # New fields for JD-relevant curation (Story 8.2)
        topics_input: str = click.prompt("Topics (comma-separated, for JD matching)", default="")
        topics_list = (
            [t.strip() for t in topics_input.split(",") if t.strip()] if topics_input else []
        )

        abstract_input: str = click.prompt("Abstract (for semantic matching)", default="")
        abstract = abstract_input if abstract_input else None

        # Create publication with new fields
        publication = Publication(
            title=title,
            type=pub_type,
            venue=venue,
            date=pub_date,
            url=HttpUrl(url) if url else None,
            topics=topics_list,
            abstract=abstract,
        )

    service.save_publication(publication)

    # Output result
    if ctx.obj.json_output:
        data: dict[str, Any] = {
            "publication_created": True,
            "title": publication.title,
            "type": publication.type,
            "venue": publication.venue,
            "file": str(service.config_path),
        }
        if publication.topics:
            data["topics"] = publication.topics
        if publication.abstract:
            data["abstract"] = publication.abstract
        response = JSONResponse(
            status="success",
            command="new publication",
            data=data,
        )
        click.echo(response.to_json())
    else:
        success(f"Publication created: {publication.title}")
        info(f"Type: {publication.type}")
        info(f"Venue: {publication.venue}")
        if publication.topics:
            info(f"Topics: {', '.join(publication.topics)}")
