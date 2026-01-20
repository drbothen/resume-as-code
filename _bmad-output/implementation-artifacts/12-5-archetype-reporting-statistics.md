# Story 12.5: Archetype Reporting & Statistics

## Status: Done

---

## Story

**As a** user managing my work unit collection,
**I want** to filter and view statistics by archetype,
**So that** I can understand the composition of my work history and identify gaps in coverage.

---

## Context & Background

### Epic 12 Goal

Add persistent archetype tracking to work units for categorization analysis, PAR validation, and improved resume generation.

### Previous Stories

- **12-1** (done): Added `WorkUnitArchetype` enum and required `archetype` field to model
- **12-2** (ready-for-dev): Persist archetype when using `--archetype` flag
- **12-3** (ready-for-dev): Inference service for classifying existing work units
- **12-4** (ready-for-dev): PAR structure validation matching archetype expectations

### Problem Statement

With archetype now a required field on all work units, users need visibility into:
1. How many work units exist per archetype category
2. Filtering list command by archetype (like existing `tag:` and `confidence:` filters)
3. Archetype distribution statistics for portfolio analysis

### Current List Command Patterns

From `src/resume_as_code/commands/list_cmd.py`:
- Filter syntax: `--filter/-f` with `tag:<value>`, `confidence:<value>` prefixes
- `_apply_filter()` function at line 688 handles filter prefix parsing
- `_output_table()` at line 808 handles Rich table display
- `_output_json()` at line 787 handles JSON output

---

## Acceptance Criteria

### AC1: Filter by Archetype

**Given** a user with work units having various archetypes
**When** user runs `resume list --filter archetype:incident`
**Then** only work units with `archetype: incident` are displayed

### AC2: Archetype Column in Table Output

**Given** a user runs `resume list` with verbose output
**When** the table renders
**Then** includes an "Archetype" column showing each work unit's archetype

### AC3: Archetype Statistics Summary

**Given** a user runs `resume list --stats` (new flag)
**When** output completes
**Then** shows archetype distribution summary (count per archetype)

### AC4: JSON Output Includes Archetype

**Given** a user runs `resume --json list`
**When** JSON output is generated
**Then** each work unit includes `archetype` field

### AC5: Case-Insensitive Archetype Filter

**Given** a user runs `resume list --filter archetype:INCIDENT` or `archetype:Incident`
**When** filter is applied
**Then** matches work units with `archetype: incident` (case-insensitive)

---

## Technical Implementation

### 1. Add Archetype Filter to `_apply_filter()`

Location: `src/resume_as_code/commands/list_cmd.py:688`

**Current implementation** handles `tag:` and `confidence:` prefixes. Add `archetype:` prefix:

```python
def _apply_filter(
    work_units: list[WorkUnit],
    filter_str: str,
) -> list[WorkUnit]:
    """Apply filter to work units list."""
    filter_lower = filter_str.lower()

    # Existing filters
    if filter_lower.startswith("tag:"):
        tag_value = filter_str[4:].strip()
        return [wu for wu in work_units if tag_value.lower() in [t.lower() for t in wu.tags]]

    if filter_lower.startswith("confidence:"):
        conf_value = filter_str[11:].strip().lower()
        return [wu for wu in work_units if wu.confidence.value.lower() == conf_value]

    # NEW: archetype filter
    if filter_lower.startswith("archetype:"):
        archetype_value = filter_str[10:].strip().lower()
        return [wu for wu in work_units if wu.archetype.value.lower() == archetype_value]

    # Free text search (existing)
    return [
        wu for wu in work_units
        if filter_lower in wu.title.lower()
        or filter_lower in " ".join(wu.tags).lower()
    ]
```

### 2. Add Archetype Column to Table Output

Location: `src/resume_as_code/commands/list_cmd.py:808` (`_output_table()`)

Add archetype column to the table:

```python
def _output_table(work_units: list[WorkUnit], verbose: bool = False) -> None:
    """Render work units as Rich table."""
    table = Table(title="Work Units", show_header=True)
    table.add_column("ID", style="cyan")
    table.add_column("Title", style="white")
    table.add_column("Date", style="dim")
    table.add_column("Archetype", style="yellow")  # NEW column
    table.add_column("Confidence", style="green")

    if verbose:
        table.add_column("Tags", style="dim")
        table.add_column("File", style="dim")

    for wu in work_units:
        row = [
            wu.id,
            wu.title[:60] + "..." if len(wu.title) > 60 else wu.title,
            wu.time_started.strftime("%Y-%m") if wu.time_started else "-",
            wu.archetype.value,  # NEW
            wu.confidence.value,
        ]
        if verbose:
            row.append(", ".join(wu.tags[:3]) + ("..." if len(wu.tags) > 3 else ""))
            row.append(f"work-units/{wu.id}.yaml")
        table.add_row(*row)

    console.print(table)
    console.print(f"\n[dim]Total: {len(work_units)} work units[/dim]")
```

### 3. Add `--stats` Flag for Archetype Distribution

Location: Add to list command options

```python
@click.option(
    "--stats",
    is_flag=True,
    help="Show archetype distribution statistics",
)
```

Add statistics rendering function:

```python
def _output_archetype_stats(work_units: list[WorkUnit]) -> None:
    """Display archetype distribution statistics."""
    from collections import Counter

    archetype_counts = Counter(wu.archetype.value for wu in work_units)

    console.print("\n[bold]Archetype Distribution[/bold]\n")

    # Sort by count descending
    for archetype, count in sorted(archetype_counts.items(), key=lambda x: -x[1]):
        pct = count / len(work_units) * 100 if work_units else 0
        bar = "█" * int(pct / 5)  # 20 chars max for 100%
        console.print(f"  {archetype:<14} {count:>3} ({pct:5.1f}%) {bar}")

    console.print(f"\n[dim]Total: {len(work_units)} work units[/dim]")
```

### 4. Update JSON Output to Include Archetype

Location: `src/resume_as_code/commands/list_cmd.py:787` (`_output_json()`)

Ensure archetype is included in JSON serialization:

```python
def _output_json(work_units: list[WorkUnit]) -> None:
    """Output work units as JSON."""
    response = JSONResponse(
        status="success",
        command="list",
        data={
            "work_units": [
                {
                    "id": wu.id,
                    "title": wu.title,
                    "archetype": wu.archetype.value,  # Ensure included
                    "confidence": wu.confidence.value,
                    "tags": wu.tags,
                    "time_started": wu.time_started.isoformat() if wu.time_started else None,
                    "time_ended": wu.time_ended.isoformat() if wu.time_ended else None,
                    "position_id": wu.position_id,
                }
                for wu in work_units
            ],
            "total": len(work_units),
        },
    )
    click.echo(response.to_json())
```

### 5. Add Unit Tests

Location: `tests/unit/commands/test_list_cmd.py`

```python
class TestArchetypeFilter:
    """Tests for archetype filtering."""

    def test_filter_by_archetype(self, sample_work_units: list[WorkUnit]) -> None:
        """Should filter work units by archetype."""
        # Assume sample_work_units has mix of archetypes
        filtered = _apply_filter(sample_work_units, "archetype:incident")
        assert all(wu.archetype.value == "incident" for wu in filtered)

    def test_archetype_filter_case_insensitive(self, sample_work_units: list[WorkUnit]) -> None:
        """Should match archetypes case-insensitively."""
        filtered_lower = _apply_filter(sample_work_units, "archetype:incident")
        filtered_upper = _apply_filter(sample_work_units, "archetype:INCIDENT")
        filtered_mixed = _apply_filter(sample_work_units, "archetype:Incident")
        assert filtered_lower == filtered_upper == filtered_mixed

    def test_archetype_filter_invalid_returns_empty(self, sample_work_units: list[WorkUnit]) -> None:
        """Should return empty list for invalid archetype."""
        filtered = _apply_filter(sample_work_units, "archetype:nonexistent")
        assert filtered == []


class TestArchetypeStats:
    """Tests for archetype statistics."""

    def test_stats_counts_archetypes(self, sample_work_units: list[WorkUnit]) -> None:
        """Should count work units per archetype."""
        from collections import Counter
        counts = Counter(wu.archetype.value for wu in sample_work_units)
        # Verify counts are correct
        assert sum(counts.values()) == len(sample_work_units)
```

---

## Implementation Checklist

- [x] Add `archetype:` filter support to `_apply_filter()` in `list_cmd.py`
- [x] Add "Archetype" column to table output in `_output_table()`
- [x] Add `--stats` flag to list command
- [x] Add `_output_archetype_stats()` function
- [x] Ensure JSON output includes `archetype` field
- [x] Add unit tests for archetype filtering
- [x] Add unit tests for archetype statistics
- [x] Run `ruff check src tests --fix`
- [x] Run `ruff format src tests`
- [x] Run `mypy src --strict`
- [x] Run `pytest -v`

---

## Files to Modify

| File | Change |
|------|--------|
| `src/resume_as_code/commands/list_cmd.py` | Add archetype filter, column, stats flag |
| `tests/unit/commands/test_list_cmd.py` | Add archetype filtering tests |

---

## Anti-Patterns to Avoid

1. **DO NOT** create a separate command - integrate with existing `list` command
2. **DO NOT** break existing filter syntax (`tag:`, `confidence:`) - additive only
3. **DO NOT** make archetype column always visible - use existing column pattern
4. **DO NOT** require WorkUnit model changes - archetype field already exists from 12-1

---

## Verification Commands

```bash
# Filter by archetype
uv run resume list --filter archetype:incident
uv run resume list --filter archetype:greenfield

# Show archetype statistics
uv run resume list --stats

# Combine filter and stats
uv run resume list --filter archetype:incident --stats

# JSON output with archetype
uv run resume --json list | jq '.data.work_units[0].archetype'

# Run tests
uv run pytest tests/unit/commands/test_list_cmd.py -v -k archetype

# Full quality check
uv run ruff check src tests --fix && uv run ruff format src tests && uv run mypy src --strict && uv run pytest
```

---

## UI Examples

### Table Output with Archetype Column

```
                     Work Units
┏━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━┳━━━━━━━━━━━━━━━┳━━━━━━━━━━━━┓
┃ ID                       ┃ Title                               ┃ Date    ┃ Archetype     ┃ Confidence ┃
┡━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━╇━━━━━━━━━━━━━━━╇━━━━━━━━━━━━┩
│ wu-2024-01-15-p1-outage  │ Resolved P1 database outage         │ 2024-01 │ incident      │ high       │
│ wu-2024-02-20-analytics  │ Built real-time analytics pipeline  │ 2024-02 │ greenfield    │ high       │
│ wu-2024-03-10-cloud-mig  │ Migrated legacy system to AWS       │ 2024-03 │ migration     │ medium     │
└──────────────────────────┴─────────────────────────────────────┴─────────┴───────────────┴────────────┘

Total: 3 work units
```

### Archetype Statistics Output

```
Archetype Distribution

  incident        5 (25.0%) █████
  greenfield      4 (20.0%) ████
  migration       3 (15.0%) ███
  optimization    3 (15.0%) ███
  leadership      2 (10.0%) ██
  strategic       2 (10.0%) ██
  cultural        1 ( 5.0%) █

Total: 20 work units
```

---

## Story Points: 3

**Rationale**: Extends existing list command with additive features. No new files, clear patterns to follow from existing filter implementation. Well-scoped with straightforward tests.

---

## Dev Agent Record

### Implementation Plan

1. Add `archetype:` prefix filter to `_apply_filter()` following existing `tag:` and `confidence:` patterns
2. Add "Archetype" column to table output in `_output_table()` with magenta style
3. Add `--stats` flag to list command and `_output_archetype_stats()` function
4. Update `_output_json()` to include archetype field and optional stats
5. Write comprehensive unit tests for filtering and statistics
6. Fix integration tests affected by table column layout change

### Completion Notes

**Implementation completed successfully:**
- Added `archetype:` filter with case-insensitive matching (AC1, AC5)
- Added "Archetype" column to table output between Date and Confidence (AC2)
- Added `--stats` flag showing distribution bar chart with percentages (AC3)
- Updated JSON output to include `archetype` field and optional `archetype_stats` (AC4)
- Added 11 new unit tests covering all acceptance criteria
- Fixed 3 integration tests that failed due to table wrapping with new column

**Key decisions:**
- Used magenta style for Archetype column to differentiate from other columns
- Stats output uses Unicode block character (█) for visual bars
- JSON stats are sorted by count descending for consistency with table output
- Work units missing archetype field display as "unknown" in stats

---

## File List

| File | Change |
|------|--------|
| `src/resume_as_code/commands/list_cmd.py` | Added archetype filter, column, stats flag, stats function, JSON archetype field; CR: Added missing Total line to stats output |
| `tests/unit/test_list_filtering.py` | Added TestFilterByArchetype (6 tests) and TestArchetypeStats (5 tests) |
| `tests/integration/test_list_command.py` | Fixed 3 tests for table wrapping with new column; CR: Added 6 new tests for archetype filter, stats, and JSON output |
| `CLAUDE.md` | CR: Updated List Command Options with --stats flag and archetype filter documentation |

---

## Change Log

| Date | Change |
|------|--------|
| 2026-01-19 | Implemented Story 12.5: Archetype Reporting & Statistics - AC1-AC5 complete |
| 2026-01-19 | Code Review: Fixed missing Total line in stats output, added 6 integration tests, updated CLAUDE.md documentation |
