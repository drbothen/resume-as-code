# Story 2.4: Quick Capture Mode

Status: done

## Story

As a **user in a hurry**,
I want **a minimal capture mode for when I just need to jot something down**,
So that **friction doesn't stop me from capturing important work**.

## Acceptance Criteria

1. **Given** I run `resume new work-unit --from-memory`
   **When** the command executes
   **Then** a minimal template is used (fewer fields, less guidance)
   **And** the `confidence` field is pre-set to `medium`

2. **Given** I use `--from-memory` mode
   **When** the file is created
   **Then** only essential fields are scaffolded: `title`, `problem.statement`, `actions`, `outcome.result`
   **And** optional fields are present but commented out

3. **Given** I run `resume new work-unit --from-memory --title "Quick win"`
   **When** the command executes
   **Then** the title is pre-filled
   **And** the editor opens immediately without prompts

## Tasks / Subtasks

- [x] Task 1: Add --from-memory flag (AC: #1, #2, #3)
  - [x] 1.1: Update `commands/new.py` with `--from-memory` flag
  - [x] 1.2: Skip archetype selection when `--from-memory` is set
  - [x] 1.3: Use "minimal" archetype template

- [x] Task 2: Verify minimal archetype (AC: #2) - *Pre-existed from Story 2.2*
  - [x] 2.1: Verified `archetypes/minimal.yaml` has essential fields only
  - [x] 2.2: Verified optional fields are commented out
  - [x] 2.3: Verified confidence pre-set to "medium"
  - *Note: No changes needed - archetype created in Story 2.2*

- [N/A] Task 3: ~~Update work unit service~~ - *Not needed*
  - Confidence is set via template, not code parameter
  - Minimal template handled identically to other archetypes

- [x] Task 4: Code quality verification
  - [x] 4.1: Run `ruff check src tests --fix`
  - [x] 4.2: Run `mypy src --strict` with zero errors
  - [x] 4.3: Add tests for --from-memory flag

## Dev Notes

### Architecture Compliance

Quick capture mode reduces friction for fast capture when details are fresh.

**Source:** [epics.md#Story 2.4](_bmad-output/planning-artifacts/epics.md)

### Dependencies

This story REQUIRES:
- Story 2.2 (Archetype Templates) - minimal.yaml archetype
- Story 2.3 (Create Work Unit Command) - base command

### Implementation

**Update `src/resume_as_code/commands/new.py`:**

```python
@new_group.command("work-unit")
@click.option(
    "--archetype",
    "-a",
    type=click.Choice(list_archetypes()),
    help="Archetype template to use",
)
@click.option(
    "--title",
    "-t",
    help="Work Unit title",
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
    from_memory: bool,
    no_edit: bool,
) -> None:
    """Create a new Work Unit."""
    config = get_config()

    # Quick capture mode
    if from_memory:
        archetype = "minimal"
        if title is None and not ctx.obj.json_output and not ctx.obj.quiet:
            title = click.prompt("Quick title")
        elif title is None:
            title = "quick-capture"

    # ... rest of implementation
```

### Minimal Archetype

**`archetypes/minimal.yaml`:** (from Story 2.2)

```yaml
# Quick Capture - Fill in details later
schema_version: "1.0.0"
id: "wu-YYYY-MM-DD-quick-slug"
title: "[What you accomplished]"

problem:
  statement: "[The challenge - 1-2 sentences]"

actions:
  - "[Key action]"

outcome:
  result: "[What you achieved]"

confidence: medium  # Quick capture = medium confidence

# --- Fill in later ---
# time_started: YYYY-MM-DD
# time_ended: YYYY-MM-DD
# tags: []
# skills_demonstrated: []
# evidence: []
```

### Testing Requirements

```python
def test_from_memory_uses_minimal_archetype(tmp_path, monkeypatch):
    """--from-memory should use minimal archetype."""
    monkeypatch.chdir(tmp_path)
    runner = CliRunner()
    result = runner.invoke(
        main,
        ["new", "work-unit", "--from-memory", "--title", "Quick win", "--no-edit"],
    )
    assert result.exit_code == 0

    files = list((tmp_path / "work-units").glob("*.yaml"))
    content = files[0].read_text()
    assert "confidence: medium" in content
```

### Verification Commands

```bash
# Quick capture
resume new work-unit --from-memory --title "Quick win" --no-edit

# Verify minimal template used
cat work-units/wu-*.yaml | grep "confidence: medium"
```

### References

- [Source: epics.md#Story 2.4](_bmad-output/planning-artifacts/epics.md)

## Dev Agent Record

### Agent Model Used

Claude Opus 4.5 (claude-opus-4-5-20251101)

### Debug Log References

N/A - No debug issues encountered.

### Completion Notes List

- Implemented `--from-memory` flag in `commands/new.py` that uses the minimal archetype and skips interactive archetype selection
- When `--from-memory` is used without `--title`, prompts for "Quick title" instead of "Work Unit title"
- When `--from-memory` is used in JSON/quiet mode without title, defaults to "quick-capture"
- The minimal archetype (`archetypes/minimal.yaml`) was already present from Story 2.2 with correct structure (essential fields only, optional fields commented out, confidence: medium)
- Added 8 comprehensive tests covering all acceptance criteria
- All 370 tests pass, ruff check passes, mypy strict passes

### Code Review Fixes (2026-01-11)

- **C1/C2 Fixed**: Updated Tasks 2 & 3 to reflect reality (archetype pre-existed, no service changes needed)
- **M2 Fixed**: Added warning when `--from-memory` overrides `--archetype` flag
- **M3 Fixed**: Updated Dev Notes code example to include `and not ctx.obj.quiet` check
- **M1 Fixed**: Added test `test_from_memory_opens_editor_by_default` to verify AC #3 editor opening
- **L1 Fixed**: Added test `test_from_memory_missing_archetype_error` for edge case handling
- All 373 tests pass, ruff check passes, mypy strict passes

### File List

- src/resume_as_code/commands/new.py (modified: added --from-memory flag and quick capture logic)
- tests/integration/test_new_command.py (modified: added TestFromMemoryMode class with 8 tests)

### Change Log

- 2026-01-11: Implemented Story 2.4 Quick Capture Mode - added --from-memory flag for minimal template quick capture
- 2026-01-11: Code review fixes - added archetype override warning, 3 new tests, fixed story documentation

