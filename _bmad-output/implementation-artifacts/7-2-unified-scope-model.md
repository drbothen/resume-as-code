# Story 7.2: Unified Scope Model

Status: ready-for-dev

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a **resume builder**,
I want **a single Scope model used consistently across positions and work units**,
So that **executive metrics are reliable and don't conflict between data sources**.

## Acceptance Criteria

1. **Given** a position with scope data
   **When** I create work units for that position
   **Then** I don't need to duplicate scope in work units
   **And** scope from position is used for resume rendering

2. **Given** the unified Scope model
   **When** I inspect its fields
   **Then** it contains:
   - `revenue: str | None` - Revenue impact (e.g., "$500M")
   - `team_size: int | None` - Total team/org size
   - `direct_reports: int | None` - Direct reports count
   - `budget: str | None` - Budget managed
   - `pl_responsibility: str | None` - P&L responsibility
   - `geography: str | None` - Geographic reach
   - `customers: str | None` - Customer scope

3. **Given** existing work units with legacy scope fields
   **When** validation runs
   **Then** a deprecation warning is logged (not an error)
   **And** legacy fields are mapped to unified model internally

4. **Given** ResumeItem renders a position
   **When** scope data exists
   **Then** scope_line is formatted consistently using unified model

## Tasks / Subtasks

- [ ] Task 1: Create unified Scope model (AC: #2)
  - [ ] 1.1 Create `src/resume_as_code/models/scope.py` with unified Scope class
  - [ ] 1.2 Add proper docstrings and Field descriptions
  - [ ] 1.3 Export from `models/__init__.py`
  - [ ] 1.4 Add unit tests for Scope model validation

- [ ] Task 2: Update Position to use unified Scope (AC: #1, #4)
  - [ ] 2.1 Replace `PositionScope` with unified `Scope` in position.py
  - [ ] 2.2 Update `format_scope_line()` in position_service.py if needed
  - [ ] 2.3 Update any imports/references to PositionScope

- [ ] Task 3: Deprecate WorkUnit.scope (AC: #3)
  - [ ] 3.1 Add `@deprecated` decorator or deprecation warning to WorkUnit.scope
  - [ ] 3.2 Create migration helper to map legacy fields to unified model
  - [ ] 3.3 Log warning when legacy scope is used (not error)
  - [ ] 3.4 Update WorkUnit model validator to emit deprecation warning

- [ ] Task 4: Update ResumeItem scope handling (AC: #4)
  - [ ] 4.1 Refactor ResumeItem to use Position.scope instead of separate scope_* fields
  - [ ] 4.2 Keep scope_line as computed property
  - [ ] 4.3 Update resume builder to derive scope from Position only

- [ ] Task 5: Update schema generation and tests
  - [ ] 5.1 Regenerate schemas after model changes
  - [ ] 5.2 Update all tests referencing PositionScope or WorkUnit.scope
  - [ ] 5.3 Add integration test verifying scope flows from Position to ResumeItem

## Dev Notes

### Technical Debt Being Addressed

**Current State: THREE incompatible Scope models:**

| Location | Model | Fields |
|----------|-------|--------|
| `models/position.py:17` | `PositionScope` | revenue, team_size, direct_reports, budget, pl_responsibility, geography, customers |
| `models/work_unit.py:179` | `Scope` | budget_managed, team_size, revenue_influenced, geographic_reach |
| `models/resume.py:41` | `ResumeItem` (inline) | scope_budget, scope_team_size, scope_revenue, scope_line |

**Field Mapping Conflicts:**
- Position: `budget` vs WorkUnit: `budget_managed`
- Position: `revenue` vs WorkUnit: `revenue_influenced`
- Position: `geography` vs WorkUnit: `geographic_reach`
- Position has: `direct_reports`, `pl_responsibility`, `customers` (WorkUnit doesn't)

### Migration Strategy

**Phase 1: Create Unified Model** (this story)
```python
# src/resume_as_code/models/scope.py (new file)
from pydantic import BaseModel, ConfigDict, Field

class Scope(BaseModel):
    """Unified scope model for executive-level positions.

    Captures leadership scale indicators: P&L, revenue, team size,
    budget, geography, customers. Used by Position and inherited
    by work units via position reference.
    """

    model_config = ConfigDict(extra="forbid")

    revenue: str | None = Field(default=None, description="Revenue impact, e.g., '$500M'")
    team_size: int | None = Field(default=None, ge=0, description="Total team/org size")
    direct_reports: int | None = Field(default=None, ge=0, description="Direct reports count")
    budget: str | None = Field(default=None, description="Budget managed, e.g., '$50M'")
    pl_responsibility: str | None = Field(default=None, description="P&L responsibility")
    geography: str | None = Field(default=None, description="Geographic reach, e.g., 'Global'")
    customers: str | None = Field(default=None, description="Customer scope, e.g., 'Fortune 500'")
```

**Phase 2: Update Position**
```python
# models/position.py
from resume_as_code.models.scope import Scope

class Position(BaseModel):
    # ... existing fields ...
    scope: Scope | None = Field(
        default=None, description="Scope indicators for executive positions"
    )
    # DELETE: PositionScope class (replaced by unified Scope)
```

**Phase 3: Deprecate WorkUnit.scope**
```python
# models/work_unit.py
import warnings

class WorkUnit(BaseModel):
    # ... existing fields ...

    # DEPRECATED: Use position.scope instead
    scope: Scope | None = Field(
        default=None,
        deprecated="Use position.scope instead. WorkUnit.scope will be removed in v1.0",
    )

    @model_validator(mode="after")
    def warn_deprecated_scope(self) -> WorkUnit:
        if self.scope is not None:
            warnings.warn(
                "WorkUnit.scope is deprecated. Set scope on the Position instead.",
                DeprecationWarning,
                stacklevel=2,
            )
        return self
```

**Phase 4: Update ResumeItem**
```python
# models/resume.py
class ResumeItem(BaseModel):
    title: str
    organization: str | None = None
    # ... other fields ...

    # Keep scope_line as the formatted display string
    scope_line: str | None = None  # Computed from Position.scope

    # REMOVE: Individual scope_* fields (scope_budget, scope_team_size, scope_revenue)
```

### Legacy Field Mapping

When migrating existing WorkUnit.scope data:

| Legacy Field (WorkUnit.Scope) | Maps To (Unified Scope) |
|-------------------------------|-------------------------|
| `budget_managed` | `budget` |
| `team_size` | `team_size` |
| `revenue_influenced` | `revenue` |
| `geographic_reach` | `geography` |

### Existing format_scope_line Function

Location: `services/position_service.py:20-56`

Already correctly uses Position.scope - no changes needed to the function itself, just ensure the import changes.

### Project Context Rules

From `project-context.md`:
- Run `ruff check` and `mypy --strict` before completing
- Use Rich console for CLI output, never `print()`
- Type hints required on all public functions
- Use `|` union syntax (Python 3.10+)
- Use `model_config = ConfigDict(extra="forbid")` on all Pydantic models

### Testing Standards

```python
# tests/unit/models/test_scope.py
def test_scope_all_fields_optional():
    """Scope model allows all fields to be None."""
    scope = Scope()
    assert scope.revenue is None
    assert scope.team_size is None

def test_scope_team_size_validates_non_negative():
    """team_size must be >= 0."""
    with pytest.raises(ValidationError):
        Scope(team_size=-1)

def test_scope_forbids_extra_fields():
    """Extra fields raise ValidationError."""
    with pytest.raises(ValidationError):
        Scope(extra_field="value")
```

```python
# tests/unit/models/test_work_unit.py
def test_work_unit_scope_deprecated_warning():
    """Setting WorkUnit.scope emits deprecation warning."""
    with pytest.warns(DeprecationWarning, match="deprecated"):
        WorkUnit(
            id="wu-2024-01-01-test",
            title="Test work unit",
            problem=Problem(statement="Test problem statement here"),
            actions=["Action one here"],
            outcome=Outcome(result="Test result here"),
            scope=Scope(team_size=10),  # Deprecated usage
        )
```

### Research Findings (2026-01-15)

**Pydantic v2 Field Deprecation (v2.7+):**

Three ways to mark a field as deprecated:

```python
from typing import Annotated
from pydantic import BaseModel, Field

# Option 1: Boolean (simplest)
class Model(BaseModel):
    old_field: Annotated[int, Field(deprecated=True)]

# Option 2: Custom message string (recommended)
class Model(BaseModel):
    old_field: Annotated[int, Field(deprecated="Use new_field instead")]

# Option 3: warnings.deprecated decorator
from typing_extensions import deprecated

class Model(BaseModel):
    old_field: Annotated[int, deprecated("Use new_field instead")]
```

**Effects of `deprecated=True`:**
1. Runtime warning emitted when field is accessed/set
2. JSON schema includes `"deprecated": true`
3. IDE hints may show strikethrough

**Best Practice for Model Deprecation:**
- Use `Field(deprecated="message")` with clear migration path
- Set `stacklevel=2` in manual `warnings.warn()` calls
- Test with `PYTHONWARNINGS=error` to catch deprecation issues

**Recommended Implementation Pattern:**

```python
# Use Annotated with Field(deprecated=...) for Pydantic-native deprecation
from typing import Annotated
from pydantic import BaseModel, ConfigDict, Field

class WorkUnit(BaseModel):
    model_config = ConfigDict(extra="forbid")

    # ... existing fields ...

    # DEPRECATED: scope field with clear message
    scope: Annotated[
        Scope | None,
        Field(
            default=None,
            deprecated="WorkUnit.scope is deprecated. Set scope on Position instead. "
                       "Will be removed in v1.0.",
        ),
    ] = None
```

**JSON Schema Output:**
```json
{
  "properties": {
    "scope": {
      "deprecated": true,
      "title": "Scope",
      "anyOf": [{"$ref": "#/$defs/Scope"}, {"type": "null"}]
    }
  }
}
```

**Sources:**
- Pydantic v2.7 release notes: https://pydantic.dev/articles/pydantic-v2-7-release
- PEP 565 (Python warning handling): https://peps.python.org/pep-0565/

### References

- [Source: _bmad-output/planning-artifacts/architecture.md#3.2 Data Architecture]
- [Source: _bmad-output/planning-artifacts/epics/epic-7-schema-data-model-refactoring.md#Story 7.2]
- [Source: src/resume_as_code/models/position.py:17-36 - PositionScope class]
- [Source: src/resume_as_code/models/work_unit.py:179-188 - Scope class]
- [Source: src/resume_as_code/models/resume.py:52-55 - ResumeItem scope_* fields]
- [Source: src/resume_as_code/services/position_service.py:20-56 - format_scope_line]

## Dev Agent Record

### Agent Model Used

{{agent_model_name_version}}

### Debug Log References

### Completion Notes List

### File List

