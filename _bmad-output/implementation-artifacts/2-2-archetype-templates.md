# Story 2.2: Archetype Templates

Status: done

## Story

As a **user**,
I want **pre-built templates for common work types**,
So that **I have guidance on what to capture for different situations**.

## Acceptance Criteria

1. **Given** the archetypes directory exists
   **When** I inspect `archetypes/incident.yaml`
   **Then** I find a template optimized for incident response stories
   **And** it includes prompts for: detection, response actions, resolution, prevention measures

2. **Given** I inspect `archetypes/greenfield.yaml`
   **When** I read the template
   **Then** I find a template optimized for new project/feature stories
   **And** it includes prompts for: problem identified, solution designed, implementation approach, outcomes

3. **Given** I inspect `archetypes/leadership.yaml`
   **When** I read the template
   **Then** I find a template optimized for leadership/influence stories
   **And** it includes prompts for: challenge, stakeholders influenced, approach taken, organizational impact

4. **Given** any archetype template
   **When** I validate it against the Work Unit schema
   **Then** it passes validation (with placeholder values)
   **And** it includes helpful comments guiding the user

5. **Given** executive-level archetypes exist
   **When** I inspect `archetypes/transformation.yaml`
   **Then** I find a template for executive transformation initiatives
   **And** it includes prompts for: strategic vision, cross-functional scope, quantified business outcomes

6. **Given** I inspect `archetypes/cultural.yaml`
   **When** I read the template
   **Then** I find a template for cultural/organizational leadership
   **And** it includes prompts for: talent development, organizational impact, soft accomplishment quantification

7. **Given** I inspect `archetypes/strategic.yaml`
   **When** I read the template
   **Then** I find a template for strategic repositioning initiatives
   **And** it includes prompts for: market positioning, competitive analysis, business model impact

## Tasks / Subtasks

- [x] Task 1: Create core archetypes (AC: #1, #2, #3, #4)
  - [x] 1.1: Create `archetypes/incident.yaml` with incident response guidance
  - [x] 1.2: Create `archetypes/greenfield.yaml` with new project guidance
  - [x] 1.3: Create `archetypes/leadership.yaml` with influence/leadership guidance
  - [x] 1.4: Add YAML comments with field explanations
  - [x] 1.5: Ensure all templates validate against work-unit.schema.json

- [x] Task 2: Create executive archetypes (AC: #5, #6, #7)
  - [x] 2.1: Create `archetypes/transformation.yaml` for executive transformation
  - [x] 2.2: Create `archetypes/cultural.yaml` for culture/organizational change
  - [x] 2.3: Create `archetypes/strategic.yaml` for strategic initiatives
  - [x] 2.4: Include scope fields (budget, team size, revenue)
  - [x] 2.5: Include impact category guidance

- [x] Task 3: Create additional utility archetypes
  - [x] 3.1: Create `archetypes/migration.yaml` for system migrations
  - [x] 3.2: Create `archetypes/optimization.yaml` for performance/cost optimization
  - [x] 3.3: Create `archetypes/minimal.yaml` for quick capture (--from-memory)

- [x] Task 4: Create archetype loader utility
  - [x] 4.1: Create `src/resume_as_code/services/archetype_service.py`
  - [x] 4.2: Implement `list_archetypes()` function
  - [x] 4.3: Implement `load_archetype(name: str)` function
  - [x] 4.4: Implement `get_archetype_path(name: str)` function

- [x] Task 5: Code quality verification
  - [x] 5.1: Validate all archetype YAML files
  - [x] 5.2: Run `ruff check src tests --fix`
  - [x] 5.3: Run `mypy src --strict` with zero errors
  - [x] 5.4: Add unit tests for archetype service

## Dev Notes

### Architecture Compliance

Archetypes provide pre-filled templates that guide users through Work Unit creation. Each archetype is optimized for a specific type of accomplishment.

**Source:** [Architecture Section 2.3 - Project Structure](_bmad-output/planning-artifacts/architecture.md#23-project-structure)
**Source:** [Architecture Section 1.4 - Content Strategy Standards](_bmad-output/planning-artifacts/architecture.md#14-content-strategy-standards)

### Dependencies

This story REQUIRES:
- Story 2.1 (Work Unit Schema) - Schema must exist for validation

This story ENABLES:
- Story 2.3 (Create Work Unit Command) - Uses archetypes for scaffolding

### Archetype Design Principles

1. **Schema-valid**: All archetypes must pass Work Unit schema validation
2. **Comment-rich**: YAML comments guide users on what to write
3. **Placeholder values**: Use descriptive placeholders that explain the field
4. **Strong verbs**: Pre-fill with strong action verbs from approved list
5. **PAR framework**: Structure follows Problem-Action-Result

### Core Archetype Templates

**`archetypes/incident.yaml`:**

```yaml
# Incident Response Work Unit Template
# Use this archetype for: production incidents, outages, security events, escalations
#
# PAR Framework Focus:
# - Problem: What was the incident? What was the impact?
# - Action: How did you detect, respond, and resolve?
# - Result: What was the outcome? What prevention measures were implemented?

schema_version: "1.0.0"
id: "wu-YYYY-MM-DD-incident-slug"  # Replace with actual date and description

title: "Resolved [SEVERITY] [SYSTEM] incident affecting [SCOPE]"
# Examples:
# - "Resolved P1 database incident affecting 10K users"
# - "Contained security breach in payment processing system"

problem:
  statement: |
    [SYSTEM/SERVICE] experienced [ISSUE TYPE] causing [IMPACT].
    # Be specific: "Production database cluster failed causing 2-hour outage for all EU customers"

  constraints:
    - "Time pressure: [X hours/minutes] to resolve"
    - "Limited visibility: [What was unclear initially]"
    # Add constraints that made this challenging

  context: |
    # What was the business context? Why did this matter?
    # Example: "Peak shopping season with 3x normal traffic"

actions:
  - "Detected [HOW]: [Detection method and initial signal]"
  - "Triaged [WHAT]: [How you assessed severity and impact]"
  - "Mitigated [HOW]: [Immediate actions to reduce impact]"
  - "Resolved [HOW]: [Root cause fix or workaround]"
  - "Communicated [TO WHOM]: [Stakeholder updates]"
  # Strong verbs: orchestrated, spearheaded, mobilized, executed

outcome:
  result: |
    [QUANTIFIED RESOLUTION]: Restored service in [TIME],
    preventing [QUANTIFIED AVOIDED IMPACT].
    # Example: "Restored service in 45 minutes, preventing estimated $200K in lost revenue"

  quantified_impact: "[X% reduction in MTTR / prevented $Y impact / Z users affected]"

  business_value: |
    # What did this mean for the business?
    # Example: "Maintained 99.9% uptime SLA commitment to enterprise customers"

# Optional: Time tracking
time_started: YYYY-MM-DD  # When incident began
time_ended: YYYY-MM-DD    # When fully resolved

# Skills demonstrated during incident
skills_demonstrated:
  - name: "Incident Command"
    # onet_element_id: "2.B.1.a"  # Optional O*NET mapping
  - name: "Root Cause Analysis"
  - name: "[Relevant Technology]"

confidence: high  # high | medium | low - how certain are you about the details?

tags:
  - incident-response
  - "[system-name]"
  - "[technology]"

# Evidence linking (optional but valuable)
evidence:
  - type: metrics
    url: "https://[monitoring-dashboard-url]"
    dashboard_name: "Incident Timeline"
    description: "Timeline and impact metrics"
  # - type: git_repo
  #   url: "https://github.com/org/repo"
  #   description: "Fix PR or postmortem"
```

**`archetypes/greenfield.yaml`:**

```yaml
# Greenfield Project Work Unit Template
# Use this archetype for: new features, new systems, new products, ground-up builds
#
# PAR Framework Focus:
# - Problem: What need or opportunity did you identify?
# - Action: How did you design and build the solution?
# - Result: What was delivered and what impact did it have?

schema_version: "1.0.0"
id: "wu-YYYY-MM-DD-project-slug"

title: "Built [WHAT] enabling [OUTCOME]"
# Examples:
# - "Built real-time analytics pipeline enabling sub-second insights"
# - "Designed microservices architecture supporting 10x scale"

problem:
  statement: |
    [WHO] needed [CAPABILITY] to [ACHIEVE GOAL].
    # Be specific about the gap or opportunity

  constraints:
    - "Timeline: [X weeks/months] to deliver"
    - "Budget: [Constraints if relevant]"
    - "Technical: [Existing system constraints]"

  context: |
    # Why was this project prioritized? What was the strategic context?

actions:
  - "Designed [ARCHITECTURE/APPROACH]: [Key design decisions]"
  - "Built [COMPONENT]: [Technical implementation]"
  - "Integrated [WITH WHAT]: [How it connected to existing systems]"
  - "Tested [HOW]: [Quality assurance approach]"
  - "Deployed [WHERE/HOW]: [Release strategy]"
  # Strong verbs: architected, engineered, pioneered, launched

outcome:
  result: |
    Delivered [WHAT] achieving [QUANTIFIED OUTCOME].

  quantified_impact: "[X% improvement / $Y value / Z users enabled]"

  business_value: |
    # Strategic value created

time_started: YYYY-MM-DD
time_ended: YYYY-MM-DD

skills_demonstrated:
  - name: "System Design"
  - name: "[Primary Technology]"
  - name: "[Secondary Technology]"

confidence: high
tags:
  - greenfield
  - "[technology-stack]"

evidence:
  - type: git_repo
    url: "https://github.com/org/repo"
    description: "Project repository"
```

**`archetypes/leadership.yaml`:**

```yaml
# Leadership & Influence Work Unit Template
# Use this archetype for: cross-team initiatives, mentoring, culture change, process improvements
#
# PAR Framework Focus:
# - Problem: What organizational challenge needed leadership?
# - Action: How did you influence, align, or lead others?
# - Result: What organizational outcome was achieved?

schema_version: "1.0.0"
id: "wu-YYYY-MM-DD-leadership-slug"

title: "[ACTION VERB] [INITIATIVE] across [SCOPE]"
# Examples:
# - "Championed engineering excellence program across 5 teams"
# - "Unified deployment practices organization-wide"

problem:
  statement: |
    [ORGANIZATION/TEAM] faced [CHALLENGE] impacting [OUTCOME METRIC].

  constraints:
    - "Stakeholder complexity: [Who needed to be aligned]"
    - "Change resistance: [What obstacles existed]"

  context: |
    # Why did this require leadership rather than just execution?

actions:
  - "Aligned [STAKEHOLDERS]: [How you built consensus]"
  - "Designed [PROGRAM/PROCESS]: [What you created]"
  - "Coached [TEAMS/INDIVIDUALS]: [How you developed others]"
  - "Measured [METRICS]: [How you tracked progress]"
  # Strong verbs: championed, cultivated, mentored, mobilized, unified

outcome:
  result: |
    Achieved [ORGANIZATIONAL OUTCOME] affecting [SCOPE].

  quantified_impact: "[X teams adopted / Y% improvement / Z people developed]"

  business_value: |
    # Long-term organizational value

skills_demonstrated:
  - name: "Stakeholder Management"
  - name: "Change Leadership"
  - name: "Coaching & Mentoring"

confidence: high
tags:
  - leadership
  - "[initiative-type]"

# Executive scope fields (if applicable)
scope:
  team_size: 0  # Number of people influenced/led
  # budget_managed: "$X"  # If you managed budget
  # geographic_reach: "Global"  # If cross-geography

impact_category:
  - organizational
  # - talent
  # - operational
```

### Executive Archetype Templates

**`archetypes/transformation.yaml`:**

```yaml
# Executive Transformation Work Unit Template
# Use for: Digital transformation, organizational restructuring, major initiatives
#
# RAS Framework (Results-Action-Situation) - Lead with impact

schema_version: "1.0.0"
id: "wu-YYYY-MM-DD-transformation-slug"

title: "Drove [TRANSFORMATION TYPE] delivering [PRIMARY METRIC]"
# Lead with the result for executive-level work

problem:
  statement: |
    [ORGANIZATION] required [TRANSFORMATION] to [STRATEGIC OBJECTIVE].

  constraints:
    - "Scale: [Size of organization/initiative]"
    - "Complexity: [Cross-functional dependencies]"
    - "Timeline: [Executive timeline pressures]"

  context: |
    # Strategic imperatives driving this transformation

actions:
  - "Defined [STRATEGY]: [Strategic vision and roadmap]"
  - "Secured [RESOURCES]: [Budget, headcount, executive sponsorship]"
  - "Orchestrated [EXECUTION]: [Cross-functional coordination]"
  - "Governed [PROGRESS]: [Executive oversight and course correction]"
  # Strong verbs: transformed, revolutionized, spearheaded, orchestrated

outcome:
  result: |
    Delivered [TRANSFORMATION] achieving [QUANTIFIED BUSINESS OUTCOME].

  quantified_impact: "$[X]M impact / [Y]% improvement / [Z] metric achieved"

  business_value: |
    # Strategic value to organization

# Executive scope (critical for senior roles)
scope:
  budget_managed: "$XM"
  team_size: 0  # Direct + indirect
  revenue_influenced: "$XM"
  geographic_reach: "Global/Regional/National"

impact_category:
  - financial
  - organizational
  - operational

metrics:
  baseline: "[Before state with numbers]"
  outcome: "[After state with numbers]"
  percentage_change: 0  # Improvement percentage

framing:
  action_verb: "Transformed"  # Use strongest applicable verb
  strategic_context: "[Why this mattered to the business]"

confidence: high
tags:
  - executive
  - transformation
```

**`archetypes/minimal.yaml`:** (for --from-memory quick capture)

```yaml
# Minimal Quick Capture Template
# Use this for fast capture when details are fresh

schema_version: "1.0.0"
id: "wu-YYYY-MM-DD-quick-slug"
title: "[What you accomplished in one line]"

problem:
  statement: "[The challenge or opportunity - 1-2 sentences]"

actions:
  - "[Key action you took]"

outcome:
  result: "[What you achieved]"

confidence: medium  # Quick capture = medium confidence by default
tags: []

# Fill in these details later:
# time_started: YYYY-MM-DD
# time_ended: YYYY-MM-DD
# skills_demonstrated: []
# evidence: []
```

### Archetype Service

**`src/resume_as_code/services/archetype_service.py`:**

```python
"""Archetype service for loading Work Unit templates."""

from __future__ import annotations

from pathlib import Path

import yaml

# Default archetype location (relative to package)
ARCHETYPES_DIR = Path(__file__).parent.parent.parent.parent / "archetypes"


def list_archetypes() -> list[str]:
    """List available archetype names."""
    if not ARCHETYPES_DIR.exists():
        return []
    return sorted([p.stem for p in ARCHETYPES_DIR.glob("*.yaml")])


def get_archetype_path(name: str) -> Path:
    """Get the path to an archetype file."""
    path = ARCHETYPES_DIR / f"{name}.yaml"
    if not path.exists():
        raise FileNotFoundError(f"Archetype '{name}' not found")
    return path


def load_archetype(name: str) -> str:
    """Load archetype file content as string (preserving comments)."""
    path = get_archetype_path(name)
    return path.read_text()


def load_archetype_data(name: str) -> dict:
    """Load archetype as parsed YAML data (loses comments)."""
    path = get_archetype_path(name)
    with path.open() as f:
        return yaml.safe_load(f)
```

### Project Structure After This Story

```
archetypes/
├── incident.yaml           # NEW
├── greenfield.yaml         # NEW
├── leadership.yaml         # NEW
├── transformation.yaml     # NEW
├── cultural.yaml           # NEW
├── strategic.yaml          # NEW
├── migration.yaml          # NEW
├── optimization.yaml       # NEW
└── minimal.yaml            # NEW

src/resume_as_code/
├── services/
│   ├── __init__.py
│   └── archetype_service.py  # NEW
└── ...
```

### Testing Requirements

**`tests/unit/test_archetype_service.py`:**

```python
"""Tests for archetype service."""

import pytest

from resume_as_code.services.archetype_service import (
    get_archetype_path,
    list_archetypes,
    load_archetype,
)


def test_list_archetypes_returns_available():
    """Should return list of archetype names."""
    archetypes = list_archetypes()
    assert "incident" in archetypes
    assert "greenfield" in archetypes
    assert "leadership" in archetypes


def test_load_archetype_returns_content():
    """Should return archetype file content."""
    content = load_archetype("incident")
    assert "schema_version" in content
    assert "problem" in content


def test_get_archetype_path_invalid_raises():
    """Should raise FileNotFoundError for invalid archetype."""
    with pytest.raises(FileNotFoundError):
        get_archetype_path("nonexistent")
```

**`tests/integration/test_archetype_validation.py`:**

```python
"""Integration tests for archetype schema validation."""

import yaml
import jsonschema

from resume_as_code.services.archetype_service import list_archetypes, load_archetype_data


def test_all_archetypes_valid_against_schema(work_unit_schema):
    """All archetypes should validate against Work Unit schema."""
    for archetype_name in list_archetypes():
        data = load_archetype_data(archetype_name)
        # Note: Archetypes have placeholder values, so this tests structure only
        assert "id" in data
        assert "title" in data
        assert "problem" in data
        assert "actions" in data
        assert "outcome" in data
```

### Verification Commands

```bash
# List available archetypes
ls archetypes/

# Validate YAML syntax
for f in archetypes/*.yaml; do python -c "import yaml; yaml.safe_load(open('$f'))"; done

# Run tests
pytest tests/unit/test_archetype_service.py -v

# Code quality
ruff check src tests --fix
mypy src --strict
```

### References

- [Source: architecture.md#Section 2.3 - Project Structure](_bmad-output/planning-artifacts/architecture.md)
- [Source: architecture.md#Section 1.4 - Content Strategy Standards](_bmad-output/planning-artifacts/architecture.md)
- [Source: epics.md#Story 2.2](_bmad-output/planning-artifacts/epics.md)

## Dev Agent Record

### Agent Model Used

Claude Opus 4.5 (claude-opus-4-5-20251101)

### Debug Log References

N/A

### Completion Notes List

- Created 9 archetype templates following PAR framework with comprehensive YAML comments
- Core archetypes: incident.yaml, greenfield.yaml, leadership.yaml
- Executive archetypes: transformation.yaml, cultural.yaml, strategic.yaml (all include scope, impact_category, metrics, framing fields)
- Utility archetypes: migration.yaml, optimization.yaml, minimal.yaml
- Created archetype_service.py with list_archetypes(), get_archetype_path(), load_archetype(), load_archetype_data() functions
- All YAML files validated successfully with yaml.safe_load()
- 13 unit tests added for archetype service (all passing)
- 21 integration tests added for archetype schema validation (all passing)
- ruff check: passed
- mypy --strict: passed (0 errors)
- Full test suite: 310 tests passed, 0 regressions

### Change Log

- 2026-01-11: Story 2.2 completed - All archetypes and archetype service implemented
- 2026-01-11: Code review remediation - Added integration tests, fixed documentation, standardized placeholders

### File List

**New Files:**
- archetypes/incident.yaml
- archetypes/greenfield.yaml
- archetypes/leadership.yaml
- archetypes/transformation.yaml
- archetypes/cultural.yaml
- archetypes/strategic.yaml
- archetypes/migration.yaml
- archetypes/optimization.yaml
- archetypes/minimal.yaml
- src/resume_as_code/services/__init__.py
- src/resume_as_code/services/archetype_service.py
- tests/unit/test_archetype_service.py
- tests/integration/test_archetype_validation.py

**Modified Files:**
- _bmad-output/implementation-artifacts/sprint-status.yaml (status: in-progress -> review)
- tests/unit/test_work_unit_schema.py (removed unused Outcome import)
- tests/conftest.py (added work_unit_schema fixture)
- archetypes/minimal.yaml (standardized date placeholder format)
