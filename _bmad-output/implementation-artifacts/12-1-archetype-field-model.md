# Story 12.1: Add Required Archetype Field with Inference Migration

Status: done

## Story

As a resume user,
I want all work units to have an archetype classification,
so that I can analyze achievement patterns, validate PAR structure, and enable archetype-aware features without any unclassified work units.

## Acceptance Criteria

1. **AC1**: A `WorkUnitArchetype` enum exists with all 9 archetype values: `greenfield`, `migration`, `optimization`, `incident`, `leadership`, `strategic`, `transformation`, `cultural`, `minimal`
2. **AC2**: The `WorkUnit` Pydantic model has a **required** `archetype` field of type `WorkUnitArchetype`
3. **AC3**: The JSON Schema (`work-unit.schema.json`) includes archetype as a **required** enum field
4. **AC4**: An `ArchetypeInferenceService` exists that can infer archetype from work unit content (tags, title, problem, actions, outcome)
5. **AC5**: A migration (`v3_to_v4.py`) runs inference to populate archetype for all existing work units
6. **AC6**: Schema version updates to `4.0.0` (breaking change - new required field)
7. **AC7**: The `resume migrate --dry-run` shows inferred archetypes before applying
8. **AC8**: The `resume show work-unit <id>` command displays the archetype
9. **AC9**: The `resume validate` command requires archetype field
10. **AC10**: Unit tests cover enum values, model validation, inference logic, and migration

## Tasks / Subtasks

- [x] Task 1: Create WorkUnitArchetype enum (AC: 1)
  - [x] 1.1: Add `WorkUnitArchetype(str, Enum)` class to `models/work_unit.py`
  - [x] 1.2: Define all 9 values with docstrings explaining each archetype's purpose
  - [x] 1.3: Ensure enum values match archetype template filenames exactly (lowercase)

- [x] Task 2: Create ArchetypeInferenceService (AC: 4)
  - [x] 2.1: Create `services/archetype_inference.py`
  - [x] 2.2: Implement rule-based inference using keyword patterns per archetype
  - [x] 2.3: Implement tag-based inference (tags like "leadership", "migration" map directly)
  - [x] 2.4: Implement confidence scoring (0.0-1.0) based on signal strength
  - [x] 2.5: Return `(archetype, confidence)` tuple
  - [x] 2.6: Default to `minimal` when confidence is below threshold (0.3)

- [x] Task 3: Add required archetype field to WorkUnit model (AC: 2)
  - [x] 3.1: Add `archetype: WorkUnitArchetype = Field(...)` to WorkUnit class (REQUIRED, no default)
  - [x] 3.2: Add field description for documentation
  - [x] 3.3: Update schema_version default to "4.0.0"

- [x] Task 4: Update JSON Schema (AC: 3, 9)
  - [x] 4.1: Add archetype property to `src/resume_as_code/schemas/work-unit.schema.json`
  - [x] 4.2: Use enum constraint with all 9 values
  - [x] 4.3: Add "archetype" to the `required` array

- [x] Task 5: Create migration v3_to_v4 (AC: 5, 6, 7)
  - [x] 5.1: Create `migrations/v3_to_v4.py`
  - [x] 5.2: Implement `check_applicable()` - detects work units without archetype
  - [x] 5.3: Implement `preview()` - shows inferred archetype + confidence for each work unit
  - [x] 5.4: Implement `apply()` - runs inference and writes archetype to each work unit YAML
  - [x] 5.5: Update CURRENT_SCHEMA_VERSION to "4.0.0" in `migrations/__init__.py`
  - [x] 5.6: Register migration in registry

- [x] Task 6: Verify show command displays archetype (AC: 8)
  - [x] 6.1: Confirm `commands/show.py` already handles archetype display
  - [x] 6.2: Test display shows archetype value

- [x] Task 7: Write unit tests (AC: 10)
  - [x] 7.1: Test WorkUnitArchetype enum has exactly 9 values
  - [x] 7.2: Test WorkUnit model REQUIRES archetype (fails without it)
  - [x] 7.3: Test ArchetypeInferenceService with various content patterns
  - [x] 7.4: Test inference confidence scoring
  - [x] 7.5: Test migration preview output
  - [x] 7.6: Test migration apply updates YAML files correctly

- [x] Task 8: Run quality checks (AC: all)
  - [x] 8.1: Run `uv run ruff check src tests --fix`
  - [x] 8.2: Run `uv run ruff format src tests`
  - [x] 8.3: Run `uv run mypy src --strict`
  - [x] 8.4: Run `uv run pytest`

## Dev Notes

### Architecture Compliance

This story introduces a **breaking change** requiring migration. The pattern follows existing migration system in `migrations/`.

**Layer boundaries:**
- Model change: `models/work_unit.py`
- New service: `services/archetype_inference.py`
- Migration: `migrations/v3_to_v4.py`
- Schema: `schemas/work-unit.schema.json`

### Archetype Inference Rules

Based on Perplexity research, use **rule-based classification with confidence scoring**:

```python
ARCHETYPE_RULES: dict[str, dict] = {
    "greenfield": {
        "keywords": ["built", "created", "designed", "architected", "launched",
                     "new system", "from scratch", "greenfield", "platform"],
        "tags": ["greenfield", "architecture", "new-feature", "launch"],
        "problem_signals": ["need", "gap", "opportunity", "no existing"],
        "action_signals": ["designed", "built", "architected", "engineered"],
    },
    "migration": {
        "keywords": ["migrated", "upgraded", "transitioned", "converted",
                     "legacy", "modernized", "refactored"],
        "tags": ["migration", "upgrade", "modernization", "refactor"],
        "problem_signals": ["legacy", "outdated", "end of life", "technical debt"],
        "action_signals": ["migrated", "transitioned", "converted", "upgraded"],
    },
    "optimization": {
        "keywords": ["optimized", "improved", "reduced", "increased efficiency",
                     "performance", "cost reduction", "streamlined"],
        "tags": ["optimization", "performance", "cost-reduction", "efficiency"],
        "problem_signals": ["slow", "expensive", "inefficient", "bottleneck"],
        "action_signals": ["optimized", "reduced", "improved", "streamlined"],
    },
    "incident": {
        "keywords": ["incident", "outage", "vulnerability", "security",
                     "assessment", "penetration", "remediated", "responded"],
        "tags": ["incident", "security", "vulnerability", "oncall", "pentest"],
        "problem_signals": ["vulnerability", "breach", "outage", "attack"],
        "action_signals": ["assessed", "remediated", "responded", "discovered"],
    },
    "leadership": {
        "keywords": ["led", "mentored", "hired", "built team", "grew",
                     "managed", "coached", "developed talent"],
        "tags": ["leadership", "team", "hiring", "mentorship", "management"],
        "problem_signals": ["team gap", "capability", "talent", "growth"],
        "action_signals": ["led", "mentored", "hired", "built", "grew"],
    },
    "strategic": {
        "keywords": ["strategy", "roadmap", "architecture decision", "aligned",
                     "framework", "standards", "governance"],
        "tags": ["strategic", "architecture", "roadmap", "governance"],
        "problem_signals": ["alignment", "direction", "standards", "framework"],
        "action_signals": ["developed", "established", "defined", "aligned"],
    },
    "transformation": {
        "keywords": ["transformed", "revolutionized", "scaled", "enterprise",
                     "organization-wide", "digital transformation"],
        "tags": ["transformation", "digital", "enterprise", "scale"],
        "problem_signals": ["organizational", "enterprise", "transformation"],
        "action_signals": ["transformed", "revolutionized", "scaled"],
    },
    "cultural": {
        "keywords": ["culture", "dei", "engagement", "inclusion", "diversity",
                     "values", "employee experience"],
        "tags": ["culture", "dei", "engagement", "inclusion"],
        "problem_signals": ["culture", "engagement", "inclusion", "morale"],
        "action_signals": ["championed", "fostered", "cultivated"],
    },
    "minimal": {
        "keywords": [],  # Fallback - no specific signals
        "tags": ["minimal", "quick-capture"],
        "problem_signals": [],
        "action_signals": [],
    },
}
```

**Confidence Calculation:**
```python
def infer_archetype(work_unit: dict) -> tuple[WorkUnitArchetype, float]:
    """Infer archetype from work unit content.

    Returns (archetype, confidence) where confidence is 0.0-1.0.
    """
    scores: dict[str, float] = {}

    text = _combine_text(work_unit)  # title + problem + actions + outcome
    tags = work_unit.get("tags", [])

    for archetype, rules in ARCHETYPE_RULES.items():
        if archetype == "minimal":
            continue  # Skip minimal in scoring, use as fallback

        score = 0.0

        # Keyword matches (40% weight)
        keyword_hits = sum(1 for kw in rules["keywords"] if kw.lower() in text.lower())
        score += (keyword_hits / max(len(rules["keywords"]), 1)) * 0.4

        # Tag matches (40% weight) - direct tag match is strong signal
        tag_hits = sum(1 for t in rules["tags"] if t in tags)
        score += (tag_hits / max(len(rules["tags"]), 1)) * 0.4

        # Problem/action signal matches (20% weight)
        signal_hits = sum(1 for s in rules["problem_signals"] + rules["action_signals"]
                         if s.lower() in text.lower())
        total_signals = len(rules["problem_signals"]) + len(rules["action_signals"])
        score += (signal_hits / max(total_signals, 1)) * 0.2

        scores[archetype] = score

    # Select highest scoring archetype
    if not scores or max(scores.values()) < 0.3:
        return (WorkUnitArchetype.MINIMAL, 0.1)  # Low confidence fallback

    best = max(scores.items(), key=lambda x: x[1])
    return (WorkUnitArchetype(best[0]), best[1])
```

### Migration Pattern

Follow existing migration patterns in `migrations/v2_to_v3.py`:

```python
class MigrationV3ToV4(Migration):
    """Add required archetype field to work units via inference."""

    from_version = "3.0.0"
    to_version = "4.0.0"

    def check_applicable(self, context: MigrationContext) -> bool:
        """Check if any work units lack archetype field."""
        work_units_dir = context.project_path / "work-units"
        if not work_units_dir.exists():
            return False
        for wu_file in work_units_dir.glob("*.yaml"):
            data = load_yaml(wu_file)
            if "archetype" not in data:
                return True
        return False

    def preview(self, context: MigrationContext) -> list[str]:
        """Show inferred archetypes for each work unit."""
        changes = []
        work_units_dir = context.project_path / "work-units"
        for wu_file in work_units_dir.glob("*.yaml"):
            data = load_yaml(wu_file)
            if "archetype" not in data:
                archetype, confidence = infer_archetype(data)
                changes.append(
                    f"{wu_file.name}: archetype={archetype.value} (confidence={confidence:.2f})"
                )
        return changes

    def apply(self, context: MigrationContext) -> MigrationResult:
        """Add inferred archetype to each work unit YAML."""
        # Implementation uses ruamel.yaml to preserve comments
        ...
```

### File Locations

| File | Change Type |
|------|-------------|
| `src/resume_as_code/models/work_unit.py` | Add enum + required field |
| `src/resume_as_code/services/archetype_inference.py` | NEW - inference service |
| `src/resume_as_code/schemas/work-unit.schema.json` | Add required property |
| `src/resume_as_code/migrations/__init__.py` | Update version constant |
| `src/resume_as_code/migrations/v3_to_v4.py` | NEW - migration |
| `tests/unit/test_work_unit.py` | Add model tests |
| `tests/unit/test_archetype_inference.py` | NEW - inference tests |
| `tests/unit/test_migrations.py` | Add migration tests |

### Schema Version Change

**Breaking change**: `3.0.0` → `4.0.0`

Per semver:
- Major version bump for breaking change (new required field)
- All existing work units will fail validation until migrated
- Migration MUST run before any other commands work

### Testing Patterns

```python
# Test required field
def test_work_unit_requires_archetype():
    """WorkUnit without archetype should fail validation."""
    yaml_content = """
    id: wu-2024-01-01-test
    title: "Test work unit without archetype"
    problem:
      statement: "Test problem statement here"
    actions:
      - "Test action here"
    outcome:
      result: "Test result"
    """
    data = yaml.safe_load(yaml_content)
    with pytest.raises(ValidationError, match="archetype"):
        WorkUnit(**data)

# Test inference
def test_infer_greenfield_from_keywords():
    """Work unit with 'built new system' should infer greenfield."""
    work_unit = {
        "title": "Built new authentication platform",
        "problem": {"statement": "Needed secure identity management"},
        "actions": ["Designed OAuth2 architecture", "Built microservices"],
        "outcome": {"result": "Launched platform serving 1M users"},
        "tags": ["architecture"],
    }
    archetype, confidence = infer_archetype(work_unit)
    assert archetype == WorkUnitArchetype.GREENFIELD
    assert confidence >= 0.5

# Test migration preview
def test_migration_preview_shows_inference(tmp_path):
    """Migration preview should show inferred archetypes."""
    # Create work unit without archetype
    wu_dir = tmp_path / "work-units"
    wu_dir.mkdir()
    (wu_dir / "wu-2024-01-01-test.yaml").write_text("""
id: wu-2024-01-01-test
title: "Migrated legacy system to cloud"
problem:
  statement: "Legacy on-prem system was expensive"
actions:
  - "Migrated to AWS"
outcome:
  result: "Reduced costs 40%"
tags:
  - migration
""")

    migration = MigrationV3ToV4()
    context = MigrationContext(project_path=tmp_path, dry_run=True)
    preview = migration.preview(context)

    assert len(preview) == 1
    assert "migration" in preview[0].lower()
```

### Project Structure Notes

- Inference service follows existing service patterns
- Migration follows existing `migrations/v2_to_v3.py` structure
- Enum placed in same file as WorkUnit model (matches existing pattern)

### References

- [Source: _bmad-output/planning-artifacts/architecture.md#3.8-Schema-Migration-System] - Migration patterns
- [Source: src/resume_as_code/migrations/v2_to_v3.py] - Existing migration example
- [Source: src/resume_as_code/models/work_unit.py] - Existing model structure
- [Source: src/resume_as_code/data/archetypes/] - Archetype template files for rule definitions

## Dev Agent Record

### Agent Model Used

Claude Opus 4.5 (claude-opus-4-5-20251101)

### Debug Log References

- Commit: `284a740 feat(schema): add required archetype field with v4.0.0 migration`

### Completion Notes List

- All 9 archetypes implemented in enum matching template filenames
- Inference service uses multi-signal scoring: 40% keywords, 40% tags, 20% problem/action signals
- Confidence threshold of 0.3 triggers minimal fallback
- Migration registered in registry with full path support (v1→v2→v3→v4)
- 127 archetype/migration tests added, 2679 total tests passing
- Show command displays archetype at `show.py:252-253`
- Validation enforced via Pydantic model required field

### File List

**Modified:**
- `src/resume_as_code/models/work_unit.py` - Added WorkUnitArchetype enum and required field
- `src/resume_as_code/migrations/__init__.py` - Updated CURRENT_SCHEMA_VERSION to 4.0.0
- `src/resume_as_code/schemas/work-unit.schema.json` - Added archetype to required array
- `src/resume_as_code/commands/show.py` - Displays archetype in work unit details
- `tests/unit/test_migrations.py` - Added v3→v4 migration tests

**Created:**
- `src/resume_as_code/services/archetype_inference.py` - Inference service with rule-based scoring
- `src/resume_as_code/migrations/v3_to_v4.py` - Migration adding archetype via inference
- `tests/unit/test_archetype.py` - 45 tests for enum, model, and inference
- `tests/integration/test_archetype_validation.py` - Schema validation tests
