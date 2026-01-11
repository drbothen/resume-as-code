# Story 3.3: List Command & Filtering

Status: done

## Story

As a **user with many Work Units**,
I want **to browse and filter my collection**,
So that **I can find specific accomplishments quickly**.

## Acceptance Criteria

1. **Given** I run `resume list`
   **When** the command executes
   **Then** all Work Units are listed in a table format
   **And** columns include: ID, Title, Date, Confidence, Tags (truncated)

2. **Given** I run `resume list --json`
   **When** the command executes
   **Then** output is a JSON array of Work Unit summaries

3. **Given** I run `resume list --filter "tag:python"`
   **When** the command executes
   **Then** only Work Units with the `python` tag are shown

4. **Given** I run `resume list --filter "confidence:high"`
   **When** the command executes
   **Then** only Work Units with high confidence are shown

5. **Given** I run `resume list --filter "2024"`
   **When** the command executes
   **Then** Work Units matching "2024" in ID, title, or date are shown

6. **Given** no Work Units exist
   **When** I run `resume list`
   **Then** a helpful message is shown: "No Work Units found. Run `resume new work-unit` to create one."

7. **Given** I run `resume list --sort date`
   **When** the command executes
   **Then** Work Units are sorted by date (newest first by default)

## Tasks / Subtasks

- [x] Task 1: Create list command module (AC: #1, #2)
  - [x] 1.1: Create `src/resume_as_code/commands/list_cmd.py` (avoid `list` keyword)
  - [x] 1.2: Implement `resume list` command with Click
  - [x] 1.3: Register command in `cli.py`
  - [x] 1.4: Load all Work Units from configured directory

- [x] Task 2: Implement table output (AC: #1)
  - [x] 2.1: Create Rich Table with columns: ID, Title, Date, Confidence, Tags
  - [x] 2.2: Truncate long titles (max 40 chars)
  - [x] 2.3: Truncate tags list (show first 3 + "...")
  - [x] 2.4: Extract date from Work Unit ID

- [x] Task 3: Implement JSON output (AC: #2)
  - [x] 3.1: Add `--json` flag support (via global flag)
  - [x] 3.2: Output Work Unit summaries as JSON array
  - [x] 3.3: Include all fields in JSON (no truncation)

- [x] Task 4: Implement filtering (AC: #3, #4, #5)
  - [x] 4.1: Add `--filter` option accepting filter string
  - [x] 4.2: Parse `tag:<value>` filter syntax
  - [x] 4.3: Parse `confidence:<value>` filter syntax
  - [x] 4.4: Implement free-text search across ID, title, date
  - [x] 4.5: Support multiple filters (AND logic)

- [x] Task 5: Implement sorting (AC: #7)
  - [x] 5.1: Add `--sort` option with choices: date, title, confidence
  - [x] 5.2: Add `--reverse` flag for ascending order
  - [x] 5.3: Default to date descending (newest first)

- [x] Task 6: Handle empty state (AC: #6)
  - [x] 6.1: Detect when no Work Units exist
  - [x] 6.2: Display helpful message with `resume new work-unit` suggestion
  - [x] 6.3: Return empty array in JSON mode

- [x] Task 7: Code quality verification
  - [x] 7.1: Run `ruff check src tests --fix`
  - [x] 7.2: Run `ruff format src tests`
  - [x] 7.3: Run `mypy src --strict` with zero errors
  - [x] 7.4: Add unit tests for filtering logic
  - [x] 7.5: Add integration tests for list command

## Dev Notes

### Architecture Compliance

This story implements FR8 (list all Work Units). It provides discovery capabilities for the Work Unit collection, enabling users to find and filter their accomplishments.

**Source:** [epics.md#Story 3.3](_bmad-output/planning-artifacts/epics.md)
**Source:** [Architecture Section 3.3 - CLI Interface Design](_bmad-output/planning-artifacts/architecture.md)

### Dependencies

This story REQUIRES:
- Story 1.1 (Project Scaffolding) - CLI skeleton
- Story 1.2 (Rich Console) - Table output formatting
- Story 2.1 (Work Unit Schema) - Pydantic models for loading
- Story 2.5 (Metadata & Evidence) - Confidence and tags fields

### Command Implementation

> **Note:** The sample code below was planning guidance. See the actual implementation at
> `src/resume_as_code/commands/list_cmd.py` for the final, reviewed version which includes:
> - Multiple filter support with AND logic (`--filter` is repeatable)
> - Named sort key functions (not lambdas, per ruff E731)
> - Proper type hints with `tuple[str, ...]` for filter args

<details>
<summary>Original planning sample (outdated - click to expand)</summary>

**`src/resume_as_code/commands/list_cmd.py`:**

```python
"""List command for browsing Work Units."""

from __future__ import annotations

from pathlib import Path
from typing import Literal

import click
from rich.table import Table

from resume_as_code.config import get_config
from resume_as_code.models.output import JSONResponse
from resume_as_code.services.work_unit_service import load_all_work_units
from resume_as_code.utils.console import console, info
from resume_as_code.utils.errors import handle_errors


SortField = Literal["date", "title", "confidence"]


@click.command("list")
@click.option(
    "--filter",
    "-f",
    "filter_str",
    help="Filter Work Units (tag:value, confidence:value, or free text)",
)
@click.option(
    "--sort",
    "-s",
    type=click.Choice(["date", "title", "confidence"]),
    default="date",
    help="Sort field (default: date)",
)
@click.option(
    "--reverse",
    "-r",
    is_flag=True,
    help="Reverse sort order (ascending)",
)
@click.pass_context
@handle_errors
def list_command(
    ctx: click.Context,
    filter_str: str | None,
    sort: SortField,
    reverse: bool,
) -> None:
    """List all Work Units with optional filtering.

    Filter syntax:
      tag:<value>        - Filter by tag
      confidence:<value> - Filter by confidence level
      <text>             - Free text search in ID, title, date
    """
    config = get_config()

    # Load all Work Units
    work_units = load_all_work_units(config.work_units_dir)

    # Handle empty state
    if not work_units:
        if ctx.obj.json_output:
            response = JSONResponse(
                status="success",
                command="list",
                data={"work_units": [], "count": 0},
            )
            print(response.to_json())
        else:
            info("No Work Units found. Run `resume new work-unit` to create one.")
        return

    # Apply filter
    if filter_str:
        work_units = _apply_filter(work_units, filter_str)

    # Apply sort
    work_units = _apply_sort(work_units, sort, reverse)

    # Output
    if ctx.obj.json_output:
        _output_json(ctx, work_units)
    else:
        _output_table(work_units)


def _apply_filter(work_units: list[dict], filter_str: str) -> list[dict]:
    """Apply filter to Work Units.

    Supports:
      - tag:<value> - Filter by tag
      - confidence:<value> - Filter by confidence
      - <text> - Free text search
    """
    filtered = []

    for wu in work_units:
        # Parse filter
        if filter_str.startswith("tag:"):
            tag_value = filter_str[4:].lower()
            tags = [t.lower() for t in wu.get("tags", [])]
            if tag_value in tags:
                filtered.append(wu)

        elif filter_str.startswith("confidence:"):
            conf_value = filter_str[11:].lower()
            if wu.get("confidence", "").lower() == conf_value:
                filtered.append(wu)

        else:
            # Free text search
            search_text = filter_str.lower()
            searchable = " ".join([
                wu.get("id", ""),
                wu.get("title", ""),
                str(wu.get("time_started", "")),
                str(wu.get("time_ended", "")),
            ]).lower()

            if search_text in searchable:
                filtered.append(wu)

    return filtered


def _apply_sort(
    work_units: list[dict],
    sort_field: SortField,
    reverse: bool,
) -> list[dict]:
    """Sort Work Units by field."""
    if sort_field == "date":
        # Extract date from ID (wu-YYYY-MM-DD-slug)
        def get_date(wu: dict) -> str:
            wu_id = wu.get("id", "")
            if wu_id.startswith("wu-") and len(wu_id) > 13:
                return wu_id[3:13]  # YYYY-MM-DD
            return ""
        key_func = get_date
        default_reverse = True  # Newest first

    elif sort_field == "title":
        key_func = lambda wu: wu.get("title", "").lower()
        default_reverse = False

    elif sort_field == "confidence":
        # Order: high > medium > low
        conf_order = {"high": 0, "medium": 1, "low": 2, None: 3}
        key_func = lambda wu: conf_order.get(wu.get("confidence"), 3)
        default_reverse = False

    # Apply reverse flag (inverts default)
    actual_reverse = not reverse if sort_field == "date" else reverse

    return sorted(work_units, key=key_func, reverse=actual_reverse)


def _output_json(ctx: click.Context, work_units: list[dict]) -> None:
    """Output Work Units as JSON."""
    summaries = [
        {
            "id": wu.get("id"),
            "title": wu.get("title"),
            "date": _extract_date(wu),
            "confidence": wu.get("confidence"),
            "tags": wu.get("tags", []),
        }
        for wu in work_units
    ]

    response = JSONResponse(
        status="success",
        command="list",
        data={"work_units": summaries, "count": len(summaries)},
    )
    print(response.to_json())


def _output_table(work_units: list[dict]) -> None:
    """Output Work Units as Rich table."""
    table = Table(title="Work Units", show_lines=False)

    table.add_column("ID", style="cyan", no_wrap=True)
    table.add_column("Title", style="white")
    table.add_column("Date", style="green")
    table.add_column("Confidence", style="yellow")
    table.add_column("Tags", style="blue")

    for wu in work_units:
        table.add_row(
            _truncate(wu.get("id", ""), 30),
            _truncate(wu.get("title", ""), 40),
            _extract_date(wu),
            wu.get("confidence") or "-",
            _format_tags(wu.get("tags", [])),
        )

    console.print(table)
    console.print(f"\n[dim]{len(work_units)} Work Unit(s)[/dim]")


def _truncate(text: str, max_len: int) -> str:
    """Truncate text with ellipsis."""
    if len(text) <= max_len:
        return text
    return text[:max_len - 3] + "..."


def _extract_date(wu: dict) -> str:
    """Extract date from Work Unit ID or time_started."""
    # Try time_started first
    if wu.get("time_started"):
        return str(wu["time_started"])[:10]

    # Fall back to ID
    wu_id = wu.get("id", "")
    if wu_id.startswith("wu-") and len(wu_id) > 13:
        return wu_id[3:13]  # YYYY-MM-DD

    return "-"


def _format_tags(tags: list[str]) -> str:
    """Format tags for display (truncate if too many)."""
    if not tags:
        return "-"
    if len(tags) <= 3:
        return ", ".join(tags)
    return ", ".join(tags[:3]) + f" +{len(tags) - 3}"
```

### Work Unit Loading Service

**Update `src/resume_as_code/services/work_unit_service.py`:**

```python
# Add imports at top of file
from resume_as_code.models.errors import NotFoundError, ValidationError

# Add these functions:

def load_all_work_units(work_units_dir: Path) -> list[dict]:
    """Load all Work Units from directory.

    Args:
        work_units_dir: Path to work-units directory.

    Returns:
        List of Work Unit dictionaries.
    """
    if not work_units_dir.exists():
        return []

    yaml = YAML()
    work_units = []

    for yaml_file in sorted(work_units_dir.glob("*.yaml")):
        try:
            with open(yaml_file) as f:
                data = yaml.load(f)
                if data:
                    work_units.append(data)
        except Exception:
            # Skip invalid files (they'll be caught by validate)
            continue

    return work_units


def load_work_unit(path: Path) -> dict:
    """Load a single Work Unit.

    Args:
        path: Path to the Work Unit YAML file.

    Returns:
        Work Unit dictionary.

    Raises:
        NotFoundError: If file doesn't exist.
        ValidationError: If file is invalid YAML.
    """
    if not path.exists():
        raise NotFoundError(f"Work Unit not found: {path}")

    yaml = YAML()
    try:
        with open(path) as f:
            return yaml.load(f)
    except Exception as e:
        raise ValidationError(f"Invalid YAML in {path}: {e}")
```

### CLI Registration

**Update `src/resume_as_code/cli.py`:**

```python
# Add import
from resume_as_code.commands.list_cmd import list_command

# Register command after main
main.add_command(list_command)
```

### Testing Requirements

**`tests/unit/test_list_filtering.py`:**

```python
"""Tests for list command filtering logic."""

import pytest

# Import the filter function (adjust path as needed)
from resume_as_code.commands.list_cmd import _apply_filter, _apply_sort


@pytest.fixture
def sample_work_units() -> list[dict]:
    """Sample Work Units for testing."""
    return [
        {
            "id": "wu-2026-01-10-project-a",
            "title": "Project A",
            "confidence": "high",
            "tags": ["python", "aws"],
        },
        {
            "id": "wu-2025-06-15-project-b",
            "title": "Project B",
            "confidence": "medium",
            "tags": ["java", "gcp"],
        },
        {
            "id": "wu-2024-03-20-project-c",
            "title": "Project C",
            "confidence": "low",
            "tags": ["python", "azure"],
        },
    ]


class TestFilterByTag:
    """Tests for tag filtering."""

    def test_filter_by_tag(self, sample_work_units):
        """Should filter by tag."""
        result = _apply_filter(sample_work_units, "tag:python")
        assert len(result) == 2
        assert all("python" in wu["tags"] for wu in result)

    def test_filter_by_tag_case_insensitive(self, sample_work_units):
        """Should be case-insensitive."""
        result = _apply_filter(sample_work_units, "tag:PYTHON")
        assert len(result) == 2

    def test_filter_by_nonexistent_tag(self, sample_work_units):
        """Should return empty for nonexistent tag."""
        result = _apply_filter(sample_work_units, "tag:rust")
        assert len(result) == 0


class TestFilterByConfidence:
    """Tests for confidence filtering."""

    def test_filter_by_confidence(self, sample_work_units):
        """Should filter by confidence level."""
        result = _apply_filter(sample_work_units, "confidence:high")
        assert len(result) == 1
        assert result[0]["confidence"] == "high"


class TestFreeTextSearch:
    """Tests for free text search."""

    def test_search_in_id(self, sample_work_units):
        """Should search in ID."""
        result = _apply_filter(sample_work_units, "2026")
        assert len(result) == 1

    def test_search_in_title(self, sample_work_units):
        """Should search in title."""
        result = _apply_filter(sample_work_units, "Project B")
        assert len(result) == 1


class TestSorting:
    """Tests for sorting."""

    def test_sort_by_date_newest_first(self, sample_work_units):
        """Should sort by date, newest first by default."""
        result = _apply_sort(sample_work_units, "date", reverse=False)
        assert result[0]["id"].startswith("wu-2026")

    def test_sort_by_title(self, sample_work_units):
        """Should sort by title alphabetically."""
        result = _apply_sort(sample_work_units, "title", reverse=False)
        assert result[0]["title"] == "Project A"

    def test_sort_by_confidence(self, sample_work_units):
        """Should sort by confidence (high first)."""
        result = _apply_sort(sample_work_units, "confidence", reverse=False)
        assert result[0]["confidence"] == "high"
```

**`tests/integration/test_list_command.py`:**

```python
"""Integration tests for list command."""

from pathlib import Path

from click.testing import CliRunner

from resume_as_code.cli import main


def _create_work_unit(path: Path, wu_id: str, title: str, tags: list[str] = None) -> None:
    """Helper to create a Work Unit file."""
    tags_str = ", ".join(tags or [])
    content = f'''
schema_version: "1.0.0"
id: "{wu_id}"
title: "{title}"
problem:
  statement: "Test problem"
actions:
  - "Test action"
outcome:
  result: "Test result"
tags: [{tags_str}]
confidence: high
'''
    path.write_text(content)


def test_list_shows_all_work_units(tmp_path: Path, monkeypatch):
    """Should list all Work Units."""
    monkeypatch.chdir(tmp_path)

    work_units = tmp_path / "work-units"
    work_units.mkdir()
    _create_work_unit(work_units / "wu-a.yaml", "wu-2026-01-01-a", "Project A")
    _create_work_unit(work_units / "wu-b.yaml", "wu-2026-01-02-b", "Project B")

    runner = CliRunner()
    result = runner.invoke(main, ["list"])

    assert result.exit_code == 0
    assert "Project A" in result.output
    assert "Project B" in result.output
    assert "2 Work Unit(s)" in result.output


def test_list_empty_state(tmp_path: Path, monkeypatch):
    """Should show helpful message when no Work Units exist."""
    monkeypatch.chdir(tmp_path)

    runner = CliRunner()
    result = runner.invoke(main, ["list"])

    assert result.exit_code == 0
    assert "No Work Units found" in result.output
    assert "resume new work-unit" in result.output


def test_list_filter_by_tag(tmp_path: Path, monkeypatch):
    """Should filter by tag."""
    monkeypatch.chdir(tmp_path)

    work_units = tmp_path / "work-units"
    work_units.mkdir()
    _create_work_unit(work_units / "wu-a.yaml", "wu-2026-01-01-a", "Python Project", ["python"])
    _create_work_unit(work_units / "wu-b.yaml", "wu-2026-01-02-b", "Java Project", ["java"])

    runner = CliRunner()
    result = runner.invoke(main, ["list", "--filter", "tag:python"])

    assert result.exit_code == 0
    assert "Python Project" in result.output
    assert "Java Project" not in result.output


def test_list_json_output(tmp_path: Path, monkeypatch):
    """Should output valid JSON."""
    monkeypatch.chdir(tmp_path)

    work_units = tmp_path / "work-units"
    work_units.mkdir()
    _create_work_unit(work_units / "wu-a.yaml", "wu-2026-01-01-a", "Project A")

    runner = CliRunner()
    result = runner.invoke(main, ["--json", "list"])

    assert result.exit_code == 0
    assert '"work_units"' in result.output
    assert '"count": 1' in result.output
```

### Verification Commands

```bash
# Create sample Work Units
mkdir -p work-units

cat > work-units/wu-2026-01-10-python-api.yaml << 'EOF'
schema_version: "1.0.0"
id: "wu-2026-01-10-python-api"
title: "Built Python REST API"
problem:
  statement: "Needed API for mobile app"
actions:
  - "Designed OpenAPI spec"
  - "Implemented with FastAPI"
outcome:
  result: "API serving 10K req/sec"
tags: [python, api, fastapi]
confidence: high
EOF

cat > work-units/wu-2025-06-15-java-service.yaml << 'EOF'
schema_version: "1.0.0"
id: "wu-2025-06-15-java-service"
title: "Migrated Java Service"
problem:
  statement: "Legacy service needed update"
actions:
  - "Upgraded to Java 17"
outcome:
  result: "Reduced memory by 30%"
tags: [java, migration]
confidence: medium
EOF

# List all
resume list

# List with JSON output
resume --json list

# Filter by tag
resume list --filter "tag:python"

# Filter by confidence
resume list --filter "confidence:high"

# Free text search
resume list --filter "2026"

# Sort by title
resume list --sort title

# Empty state (with no work-units dir)
rm -rf work-units && resume list

# Code quality
ruff check src tests --fix
mypy src --strict
pytest tests/unit/test_list_filtering.py tests/integration/test_list_command.py -v
```

</details>

### References

- [Source: epics.md#Story 3.3](_bmad-output/planning-artifacts/epics.md)
- [Source: architecture.md](_bmad-output/planning-artifacts/architecture.md)
- [Source: project-context.md](_bmad-output/project-context.md)

## Dev Agent Record

### Agent Model Used

Claude Opus 4.5 (claude-opus-4-5-20251101)

### Debug Log References

- Initial implementation completed following red-green-refactor cycle
- All 42 list command tests passing (27 unit + 15 integration) after code review fixes
- Full regression suite passing

### Completion Notes List

- Created `src/resume_as_code/commands/list_cmd.py` with full list command implementation
- Implemented Rich table output with columns: ID, Title, Date, Confidence, Tags
- Implemented JSON output via global `--json` flag with `JSONResponse` model
- Implemented filtering with `--filter` option supporting:
  - `tag:<value>` - filter by tag (case-insensitive)
  - `confidence:<value>` - filter by confidence level (case-insensitive)
  - Free text search across ID, title, date fields
  - Multiple `--filter` options with AND logic (all filters must match)
- Implemented sorting with `--sort` option (date, title, confidence)
- Implemented `--reverse` flag for ascending order
- Default sort is date descending (newest first)
- Empty state displays helpful message with `resume new work-unit` suggestion
- JSON mode returns empty array with count: 0 for empty state
- All code passes ruff linting and mypy strict type checking
- Tests cover all 7 acceptance criteria

### File List

**New files:**
- src/resume_as_code/commands/list_cmd.py
- tests/unit/test_list_filtering.py
- tests/integration/test_list_command.py

**Modified files:**
- src/resume_as_code/cli.py (registered list_command)
- src/resume_as_code/commands/validate.py (ruff formatting)
- tests/integration/test_validate_command.py (ruff formatting)
- tests/unit/test_content_validator.py (ruff formatting)

## Change Log

- 2026-01-11: Code review fixes - added multiple filter AND logic (Task 4.5), edge case tests
- 2026-01-11: Implemented Story 3.3 - List Command & Filtering (all ACs satisfied)

