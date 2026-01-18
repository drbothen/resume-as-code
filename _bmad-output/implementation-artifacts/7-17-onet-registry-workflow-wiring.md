# Story 7.17: O*NET & Registry Workflow Wiring

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a **job seeker**,
I want **skill normalization and O*NET lookup integrated into the plan and build workflow**,
So that **my skills are automatically standardized using industry terminology**.

## Acceptance Criteria

1. **Given** I run `resume plan --jd job.txt`
   **When** skills are curated from work units
   **Then** SkillRegistry normalizes aliases (k8s → Kubernetes)
   **And** JD keywords are expanded with aliases for better matching

2. **Given** O*NET is configured (ONET_API_KEY set)
   **When** an unknown skill is encountered during curation
   **Then** it is looked up via O*NET API
   **And** the result is cached for future use

3. **Given** O*NET is NOT configured
   **When** skill curation runs
   **Then** local registry normalization still works
   **And** unknown skills pass through unchanged (graceful degradation)

4. **Given** I run `resume build`
   **When** skills are rendered
   **Then** they use the same normalized names from the plan phase

5. **Given** O*NET discovers a new skill mapping
   **When** the skill is added to the registry
   **Then** it persists across sessions (cached locally)

## Tasks / Subtasks

- [x] Task 1: Create SkillRegistry factory with O*NET support (AC: #2, #3)
  - [x] 1.1 Add `SkillRegistry.load_with_onet(onet_config: ONetConfig | None)` class method
  - [x] 1.2 Factory creates ONetService when config.is_configured
  - [x] 1.3 Factory falls back to load_default() when O*NET unavailable
  - [x] 1.4 Add unit tests for factory method

- [x] Task 2: Wire SkillRegistry into plan.py (AC: #1)
  - [x] 2.1 Load registry using factory in `_curate_skills()` function
  - [x] 2.2 Pass registry to SkillCurator (currently missing)
  - [x] 2.3 Use config.onet if available for O*NET integration
  - [x] 2.4 Add integration test for plan with registry

- [x] Task 3: Wire O*NET lookup into curation flow (AC: #2, #5)
  - [x] 3.1 Modify SkillCurator._deduplicate() to call lookup_and_cache() for unknown skills
  - [x] 3.2 Only lookup if onet_service is configured on registry
  - [x] 3.3 Log discovered skills at INFO level
  - [x] 3.4 Add unit tests for O*NET lookup during curation

- [x] Task 4: Ensure consistency between plan and build (AC: #4)
  - [x] 4.1 Verify resume.py already uses registry (Story 7.4)
  - [x] 4.2 Update to use same factory method as plan.py
  - [x] 4.3 Add integration test: plan + build produce same skill names

- [x] Task 5: Add tests and documentation
  - [x] 5.1 Integration test: full workflow with mocked O*NET
  - [x] 5.2 Integration test: graceful degradation without O*NET
  - [x] 5.3 Update CLAUDE.md if new config options added (N/A - no new options)
  - [x] 5.4 Run `ruff check` and `mypy --strict`

## Dev Notes

### Current State Analysis

**What Story 7.4 delivered:**
- `SkillRegistry` with `normalize()` and `get_aliases()` methods
- `SkillCurator` accepts optional `registry` parameter
- `resume.py` (build phase) passes registry to curator ✅
- `plan.py` does NOT pass registry to curator ❌

**What Story 7.5 delivered:**
- `ONetConfig` model with API key from environment
- `ONetService` with `search_occupations()` and `get_occupation_skills()`
- `SkillRegistry.lookup_and_cache()` method for O*NET discovery
- `--show-onet-status` CLI command

**Gap:**
- No connection between ONetService and the plan/build workflow
- `plan.py` doesn't use SkillRegistry at all
- `resume.py` uses registry but not with O*NET

### Implementation Pattern

**Factory Method:**
```python
# src/resume_as_code/services/skill_registry.py

@classmethod
def load_with_onet(cls, onet_config: ONetConfig | None = None) -> SkillRegistry:
    """Load registry with optional O*NET service.

    Args:
        onet_config: O*NET configuration (from ResumeConfig.onet).

    Returns:
        SkillRegistry with O*NET service if configured.
    """
    from resume_as_code.services.onet_service import ONetService

    # Load base registry
    registry_data = cls._load_default_data()
    entries = [SkillEntry(**e) for e in registry_data.get("skills", [])]

    # Add O*NET service if configured
    onet_service = None
    if onet_config and onet_config.is_configured:
        onet_service = ONetService(onet_config)
        logger.info("O*NET service enabled for skill lookup")

    return cls(entries, onet_service=onet_service)
```

**Plan.py Integration:**
```python
# src/resume_as_code/commands/plan.py (in _curate_skills function)

from resume_as_code.services.skill_registry import SkillRegistry

# Load registry with O*NET if configured
registry = SkillRegistry.load_with_onet(config.onet)

curator = SkillCurator(
    max_count=config.skills.max_display,
    exclude=config.skills.exclude,
    prioritize=config.skills.prioritize,
    registry=registry,  # ← ADD THIS
)
```

**Curation with O*NET Lookup:**
```python
# src/resume_as_code/services/skill_curator.py (in _deduplicate)

def _deduplicate(self, skills: set[str]) -> dict[str, str]:
    normalized: dict[str, str] = {}
    for skill in skills:
        if not skill or not skill.strip():
            continue

        display = skill
        if self.registry:
            # Try local normalization first
            display = self.registry.normalize(skill)

            # If unchanged (not in registry) and O*NET available, try lookup
            if display == skill and self.registry._onet_service:
                entry = self.registry.lookup_and_cache(skill)
                if entry:
                    display = entry.canonical

        lower = display.lower()
        if lower not in normalized:
            normalized[lower] = display
        # ... rest of dedup logic
```

### Dependencies

- **Depends on:** Story 7.4 (SkillRegistry), Story 7.5 (ONetService)
- **Blocked by:** None (both dependencies complete)

### Testing Strategy

```python
# tests/integration/test_skill_workflow.py

@respx.mock
def test_plan_uses_registry_normalization(cli_runner, tmp_path):
    """Plan command normalizes skills via registry."""
    # Setup: work unit with "k8s" skill
    # Run: resume plan --jd job.txt
    # Assert: curated skills include "Kubernetes" not "k8s"

@respx.mock
def test_plan_with_onet_discovers_skills(cli_runner, tmp_path, monkeypatch):
    """Plan command discovers unknown skills via O*NET."""
    monkeypatch.setenv("ONET_API_KEY", "test-key")
    # Mock O*NET response
    # Setup: work unit with "python programming" skill
    # Run: resume plan --jd job.txt
    # Assert: skill normalized to O*NET canonical name

def test_plan_graceful_without_onet(cli_runner, tmp_path):
    """Plan works without O*NET configured."""
    # No ONET_API_KEY set
    # Run: resume plan --jd job.txt
    # Assert: succeeds with local registry only
```

### Project Context Rules

From `project-context.md`:
- Run `ruff check` and `mypy --strict` before completing
- Use Rich console for CLI output, never `print()`
- Type hints required on all public functions
- Use `|` union syntax (Python 3.10+)

### References

- [Depends: Story 7.4 - Skills Registry & Normalization]
- [Depends: Story 7.5 - O*NET API Integration]
- [Source: src/resume_as_code/commands/plan.py - _curate_skills function]
- [Source: src/resume_as_code/models/resume.py - from_work_units method]
- [Source: src/resume_as_code/services/skill_curator.py - _deduplicate method]

## Dev Agent Record

### Agent Model Used

claude-opus-4-5-20251101

### Debug Log References

N/A

### Completion Notes List

- Added `SkillRegistry.load_with_onet()` factory method to create registry with O*NET integration
- Updated `plan.py` to use `load_with_onet()` and pass registry to SkillCurator
- Modified `SkillCurator._deduplicate()` to call `lookup_and_cache()` for unknown skills
- Updated `resume.py` to accept `onet_config` parameter and use `load_with_onet()`
- Updated `build.py` to pass `config.onet` to `from_work_units()`
- Added comprehensive unit tests for new factory method (7 tests)
- Added unit tests for O*NET lookup during curation (4 tests)
- Added integration tests for plan command O*NET wiring (2 tests)
- All 116 related unit tests pass
- All 66 plan command integration tests pass
- Ruff and mypy --strict pass with no issues

### File List

- `src/resume_as_code/services/skill_registry.py` - Added load_with_onet() factory method
- `src/resume_as_code/services/skill_curator.py` - Modified _deduplicate() for O*NET lookup
- `src/resume_as_code/commands/plan.py` - Wired registry with O*NET into curation
- `src/resume_as_code/commands/build.py` - Pass onet_config to from_work_units()
- `src/resume_as_code/models/resume.py` - Added onet_config parameter, use load_with_onet()
- `tests/unit/test_skill_registry.py` - Added TestSkillRegistryLoadWithOnet class
- `tests/unit/test_skill_curator.py` - Added TestSkillCuratorONetLookup class
- `tests/unit/test_resume_model.py` - Updated test to verify load_with_onet() usage
- `tests/integration/test_plan_command.py` - Added TestPlanCommandONetWiring class
