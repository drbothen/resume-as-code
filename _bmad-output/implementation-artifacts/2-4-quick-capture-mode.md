# Story 2.4: Quick Capture Mode

Status: ready-for-dev

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

- [ ] Task 1: Add --from-memory flag (AC: #1, #2, #3)
  - [ ] 1.1: Update `commands/new.py` with `--from-memory` flag
  - [ ] 1.2: Skip archetype selection when `--from-memory` is set
  - [ ] 1.3: Use "minimal" archetype template

- [ ] Task 2: Create minimal archetype (AC: #2)
  - [ ] 2.1: Ensure `archetypes/minimal.yaml` has essential fields only
  - [ ] 2.2: Comment out optional fields
  - [ ] 2.3: Pre-set confidence to "medium"

- [ ] Task 3: Update work unit service (AC: #1, #2)
  - [ ] 3.1: Add parameter to set confidence level
  - [ ] 3.2: Handle minimal template specifically

- [ ] Task 4: Code quality verification
  - [ ] 4.1: Run `ruff check src tests --fix`
  - [ ] 4.2: Run `mypy src --strict` with zero errors
  - [ ] 4.3: Add tests for --from-memory flag

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
        if title is None and not ctx.obj.json_output:
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

{{agent_model_name_version}}

### Debug Log References

### Completion Notes List

### File List

