"""New command for creating Work Units and Positions."""

from __future__ import annotations

import re
from datetime import date, datetime
from pathlib import Path
from typing import Any

import click
from pydantic import HttpUrl

from resume_as_code.config import get_config
from resume_as_code.models.certification import Certification
from resume_as_code.models.education import Education
from resume_as_code.models.errors import NotFoundError
from resume_as_code.models.output import JSONResponse
from resume_as_code.models.position import EmploymentType, Position
from resume_as_code.services.archetype_service import list_archetypes
from resume_as_code.services.certification_service import CertificationService
from resume_as_code.services.education_service import EducationService
from resume_as_code.services.position_service import PositionService
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


def parse_position_flag(value: str) -> dict[str, str | None]:
    """Parse --position flag value.

    Format: "Employer|Title|StartDate|EndDate"
    EndDate can be empty for current position.

    Args:
        value: The position flag value in pipe-separated format.

    Returns:
        Dictionary with employer, title, start_date, end_date keys.

    Raises:
        click.BadParameter: If format is invalid.
    """
    parts = value.split("|")
    if len(parts) != 4:
        raise click.BadParameter("Position must be in format: 'Employer|Title|StartDate|EndDate'")

    employer, title, start_date, end_date = parts
    return {
        "employer": employer.strip(),
        "title": title.strip(),
        "start_date": start_date.strip(),
        "end_date": end_date.strip() or None,
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
        title is not None
        and problem is not None
        and len(actions) > 0
        and result is not None
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
            raise click.UsageError(
                f"Result must be at least 10 characters (got {len(result)})"
            )
        for i, action in enumerate(actions):
            if len(action) < 10:
                raise click.UsageError(
                    f"Action {i + 1} must be at least 10 characters (got {len(action)})"
                )

        # Generate ID and create file from data
        work_unit_id = generate_id(title, date.today())
        file_path = create_work_unit_from_data(
            work_unit_id=work_unit_id,
            title=title,
            problem_statement=problem,
            actions=list(actions),
            result=result,
            work_units_dir=config.work_units_dir,
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
@click.pass_context
@handle_errors
def new_position(
    ctx: click.Context,
    employer: str | None,
    job_title: str | None,
    location: str | None,
    start_date: str | None,
    end_date: str | None,
    employment_type: EmploymentType | None,
    promoted_from: str | None,
) -> None:
    """Create a new employment position.

    Can be used interactively (no flags) or non-interactively (with flags).
    For non-interactive mode, provide at least --employer, --title, and --start-date.
    """
    config = get_config()
    service = PositionService(config.positions_path)

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
        )

    service.save_position(position)

    # Output result
    if ctx.obj.json_output:
        response = JSONResponse(
            status="success",
            command="new position",
            data={
                "position_id": position.id,
                "employer": position.employer,
                "title": position.title,
                "file": str(config.positions_path),
            },
        )
        click.echo(response.to_json())
    else:
        success(f"Position created: {position.id}")
        info(f"Use this ID in work units: position_id: {position.id}")


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
    """Validate YYYY-MM date format."""
    return bool(re.match(r"^\d{4}-\d{2}$", date_str))


def _validate_year_format(year_str: str) -> bool:
    """Validate YYYY year format."""
    return bool(re.match(r"^\d{4}$", year_str))


@new_group.command("certification")
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
    name: str | None,
    issuer: str | None,
    cert_date: str | None,
    expires: str | None,
    credential_id: str | None,
    url: str | None,
) -> None:
    """Create a new certification record.

    Can be used interactively (no flags) or non-interactively (with --name).
    For non-interactive mode, at minimum provide --name.
    """
    # Use Path.cwd() for config location (certifications stored in .resume.yaml)
    service = CertificationService(config_path=Path.cwd() / ".resume.yaml")

    # Determine interactive vs non-interactive mode
    non_interactive = name is not None

    if non_interactive:
        # Non-interactive mode - use provided values directly
        assert name is not None

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
@click.option("--degree", required=False, help="Degree name")
@click.option("--institution", required=False, help="Institution name")
@click.option("--year", help="Graduation year (YYYY)")
@click.option("--honors", help="Honors/distinction")
@click.option("--gpa", help="GPA (e.g., 3.8/4.0)")
@click.pass_context
@handle_errors
def new_education(
    ctx: click.Context,
    degree: str | None,
    institution: str | None,
    year: str | None,
    honors: str | None,
    gpa: str | None,
) -> None:
    """Create a new education record.

    Can be used interactively (no flags) or non-interactively (with --degree and --institution).
    For non-interactive mode, provide at least --degree and --institution.
    """
    # Use Path.cwd() for config location (education stored in .resume.yaml)
    service = EducationService(config_path=Path.cwd() / ".resume.yaml")

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
            year=year,
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
            year=year,
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
