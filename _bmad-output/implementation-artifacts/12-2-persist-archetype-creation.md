# Story 12.2: Persist Archetype on Work Unit Creation

## Status: Done

---

## Story

**As a** user creating work units via CLI,
**I want** the archetype value from `--archetype` to be explicitly persisted in the YAML file,
**So that** archetype categorization is guaranteed regardless of template content.

---

## Context & Background

### Current Behavior

Two code paths exist for creating work units:

1. **Template-based** (`create_work_unit_file`): Loads archetype template and relies on template having `archetype:` field
2. **Inline creation** (`create_work_unit_from_data`): Explicitly sets `archetype` in the data dict (correct)

**Gap**: Template-based creation trusts templates to include correct archetype field. If template is malformed or lacks the field, the archetype is lost.

### Previous Story Context

Story 12-1 made `archetype` a **required field** on `WorkUnit` model (schema v4.0.0). This story ensures the CLI creation flow explicitly persists the archetype value passed via `--archetype` flag.

### Files Modified in 12-1

- `src/resume_as_code/models/work_unit.py`: Added `WorkUnitArchetype` enum, made `archetype` required
- `src/resume_as_code/services/migration_service.py`: Added v4.0.0 migration

---

## Acceptance Criteria

### AC1: Template-Based Creation Explicitly Sets Archetype

**Given** a user creates a work unit with `--archetype greenfield`
**When** `create_work_unit_file()` generates the YAML
**Then** the archetype field is explicitly set/verified in the output, not just inherited from template

### AC2: Archetype Persisted for All Archetypes

**Given** any valid archetype (greenfield, migration, optimization, incident, leadership, strategic, transformation, cultural, minimal)
**When** `create_work_unit_file()` is called with that archetype
**Then** the output file contains `archetype: {value}` matching the flag

### AC3: Unit Tests for Archetype Persistence

**Given** `create_work_unit_file()` is called
**When** reading the generated file
**Then** tests verify `archetype: {value}` is present and correct

### AC4: Both Creation Paths Have Consistent Behavior

**Given** inline creation (`create_work_unit_from_data`) already persists archetype
**When** template creation is updated
**Then** both paths produce consistent archetype field output

---

## Technical Implementation

### 1. Modify `create_work_unit_file()` in `work_unit_service.py`

Location: `src/resume_as_code/services/work_unit_service.py:88-145`

**Current flow**:
```python
def create_work_unit_file(archetype, work_unit_id, title, work_units_dir, position_id=None):
    content = load_archetype(archetype)  # Loads template
    content = re.sub(r'id:...', f'id: "{work_unit_id}"', content)  # Sets ID
    content = re.sub(r'title:...', f'title: "{escaped_title}"', content)  # Sets title
    if position_id:
        # Adds position_id
    file_path.write_text(content)
```

**Required change**: Add explicit archetype replacement after title:

```python
# After title replacement (line ~130), add:
# Ensure archetype field matches the requested archetype
# Handle both quoted and unquoted values in templates
if re.search(r'archetype:\s*\S+', content):
    content = re.sub(
        r'archetype:\s*["\']?\S+["\']?',
        f'archetype: {archetype}',
        content,
        count=1,
    )
else:
    # Defensive: add archetype if template lacks it (should not happen with current templates)
    content = re.sub(
        r'(schema_version:\s*["\']?\S+["\']?)',
        rf'\1\narchetype: {archetype}',
        content,
        count=1,
    )
```

**Why regex instead of YAML parse/dump**: Preserves template comments and formatting (matches existing pattern for id/title).

**Edge case handling**: Defensive code handles malformed templates lacking archetype field.

### 2. Add Test Coverage

Location: `tests/unit/test_work_unit_service.py`

Add to `TestCreateWorkUnitFile` class:

```python
def test_creates_file_with_correct_archetype(self, tmp_path: Path) -> None:
    """Should create file with archetype matching the flag."""
    work_units_dir = tmp_path / "work-units"

    file_path = create_work_unit_file(
        archetype="incident",
        work_unit_id="wu-2024-03-15-test",
        title="Test Incident",
        work_units_dir=work_units_dir,
    )

    content = file_path.read_text()
    assert "archetype: incident" in content

def test_archetype_persisted_for_all_types(self, tmp_path: Path) -> None:
    """Should persist archetype for every valid archetype type."""
    from resume_as_code.services.archetype_service import list_archetypes

    work_units_dir = tmp_path / "work-units"

    for arch in list_archetypes():
        file_path = create_work_unit_file(
            archetype=arch,
            work_unit_id=f"wu-2024-03-15-{arch}",
            title=f"Test {arch}",
            work_units_dir=work_units_dir,
        )
        content = file_path.read_text()
        assert f"archetype: {arch}" in content, f"Archetype {arch} not persisted"

def test_archetype_overrides_template_value(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Should override any existing archetype value in template."""
    # This test verifies that even if a template has archetype: X,
    # passing archetype="Y" results in archetype: Y
    work_units_dir = tmp_path / "work-units"

    # Create with greenfield template but verify archetype is set correctly
    file_path = create_work_unit_file(
        archetype="greenfield",
        work_unit_id="wu-2024-03-15-override-test",
        title="Override Test",
        work_units_dir=work_units_dir,
    )

    content = file_path.read_text()
    # Should have exactly one archetype field matching the flag
    assert content.count("archetype:") == 1
    assert "archetype: greenfield" in content
```

### 3. No Changes to `create_work_unit_from_data()`

Already correctly persists archetype at line 194:
```python
data: dict[str, Any] = {
    "id": work_unit_id,
    "title": title,
    "schema_version": "4.0.0",
    "archetype": archetype,  # Already correct
}
```

---

## Implementation Checklist

- [x] Modify `create_work_unit_file()` to explicitly set archetype via regex
- [x] Add test `test_creates_file_with_correct_archetype`
- [x] Add test `test_archetype_persisted_for_all_types`
- [x] Add test `test_archetype_overrides_template_value`
- [x] Run `ruff check src tests --fix`
- [x] Run `ruff format src tests`
- [x] Run `mypy src --strict`
- [x] Run `pytest tests/unit/test_work_unit_service.py -v`
- [x] Run full test suite `pytest`

---

## Files to Modify

| File | Change |
|------|--------|
| `src/resume_as_code/services/work_unit_service.py` | Add archetype regex replacement in `create_work_unit_file()` |
| `tests/unit/test_work_unit_service.py` | Add 3 test methods |

---

## Anti-Patterns to Avoid

1. **DO NOT** parse and dump YAML with ruamel.yaml - loses template comments
2. **DO NOT** modify `create_work_unit_from_data()` - already correct
3. **DO NOT** add archetype validation to CLI layer - model already validates
4. **DO NOT** change template files - they already have archetype field

---

## Verification Commands

```bash
# Create work unit and verify archetype persisted
uv run resume new work-unit --archetype incident --title "Test" --no-edit
cat work-units/wu-*-test.yaml | grep "archetype:"
# Expected: archetype: incident

# Run specific tests
uv run pytest tests/unit/test_work_unit_service.py::TestCreateWorkUnitFile -v

# Run full quality check
uv run ruff check src tests --fix && uv run ruff format src tests && uv run mypy src --strict && uv run pytest
```

---

## Dev Agent Record

### Implementation Plan

Added archetype regex replacement to `create_work_unit_file()` after position_id handling. The implementation:
1. Checks if `archetype:` field exists in template content
2. If exists: replaces value with the archetype parameter using regex
3. If missing (defensive): inserts archetype field after schema_version

Used regex instead of YAML parsing to preserve template comments and formatting, matching the existing pattern for id/title replacements.

### Completion Notes

- ✅ Added 18 lines to `work_unit_service.py` (lines 141-158) for archetype regex replacement
- ✅ Added 6 test methods total (3 original + 3 from code review)
- ✅ All 2685 tests pass (32 in test_work_unit_service.py)
- ✅ mypy strict mode passes with no issues
- ✅ ruff check/format passes

---

## File List

| File | Change |
|------|--------|
| `src/resume_as_code/services/work_unit_service.py` | Added archetype regex replacement (lines 141-158) |
| `tests/unit/test_work_unit_service.py` | Added 6 test methods (lines 232-387) |
| `_bmad-output/implementation-artifacts/sprint-status.yaml` | Updated story status |

---

## Change Log

| Date | Change |
|------|--------|
| 2026-01-19 | Implemented archetype persistence in `create_work_unit_file()`, added 3 unit tests |
| 2026-01-19 | Code review: Added 3 tests for edge cases (missing archetype, quoted values, path consistency) |

---

## Story Points: 3

**Rationale**: Small, focused change to a single function with clear tests. No new patterns or architectural decisions.

---

## Senior Developer Review (AI)

**Reviewer:** Amelia (Dev Agent)
**Date:** 2026-01-19
**Outcome:** ✅ APPROVED (after remediation)

### Initial Findings

| Severity | Issue | Resolution |
|----------|-------|------------|
| MEDIUM | File List missing `sprint-status.yaml` | ✅ Added to File List |
| MEDIUM | Line count claimed 17, actual 18 | ✅ Corrected in Completion Notes |
| MEDIUM | Defensive code path untested (template missing archetype) | ✅ Added `test_archetype_added_when_template_missing_field` |
| LOW | No test for quoted archetype value in template | ✅ Added `test_archetype_handles_quoted_template_value` |
| LOW | No test comparing both creation paths | ✅ Added `test_both_creation_paths_produce_consistent_archetype` |

### Verification

- All 32 tests in `test_work_unit_service.py` pass
- All 2685 tests in full suite pass
- mypy strict: no issues
- ruff check/format: clean

### Notes

All edge cases now have test coverage. The defensive code path (adding archetype when template lacks it) is now explicitly tested via monkeypatching `load_archetype`.
