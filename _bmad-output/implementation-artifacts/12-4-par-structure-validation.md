# Story 12.4: PAR Structure Validation by Archetype

Status: done

## Story

**As a** user maintaining a collection of work units,
**I want** validation that checks if my PAR (Problem-Action-Result) structure matches the archetype's expectations,
**So that** I can ensure my achievements are documented with archetype-appropriate content and improve resume generation quality.

---

## Context & Background

### Epic 12 Goal

Add persistent archetype tracking to work units for categorization analysis, PAR validation, and improved resume generation.

### Previous Stories

- **12-1** (done): Added `WorkUnitArchetype` enum and required `archetype` field to model with v4.0.0 migration
- **12-2** (ready-for-dev): Persist archetype when using `--archetype` flag
- **12-3** (ready-for-dev): Inference service to suggest archetypes based on content analysis

### Problem Statement

Each archetype has specific PAR framework expectations:

| Archetype | Problem Focus | Action Focus | Result Focus |
|-----------|--------------|--------------|--------------|
| **incident** | What failed? Impact scope? | Detect, triage, mitigate, resolve | MTTR, prevented impact |
| **greenfield** | What need/opportunity? | Design, build, integrate, deploy | Delivered capability, business value |
| **migration** | Legacy limitations? | Plan, execute, validate, cutover | Successful transition, improvements |
| **optimization** | Performance/cost baseline? | Profile, identify, implement | % improvement, cost savings |
| **leadership** | Team/capability gap? | Mentor, align, champion | Team growth, retention |
| **strategic** | Market/competitive position? | Research, position, partner | Market share, competitive advantage |
| **transformation** | Organizational challenge? | Vision, execute, change manage | Enterprise-wide impact |
| **cultural** | Culture/engagement issue? | Cultivate, program, measure | Engagement scores, retention |
| **minimal** | (No specific validation) | (No specific validation) | (No specific validation) |

Currently, validation only checks schema compliance. This story adds content-aware validation that:
1. Checks if PAR content contains archetype-appropriate keywords/patterns
2. Warns when content doesn't match archetype expectations
3. Suggests potential archetype misclassification

### Relationship to Existing Validation

The `resume validate` command already checks:
- Schema validation (via JSON Schema)
- Content quality (weak verbs, quantification) with `--content-quality`
- Content density (bullet length) with `--content-density`
- Position references with `--check-positions`

This story adds a NEW flag `--check-archetype` that validates PAR structure against archetype expectations.

---

## Acceptance Criteria

### AC1: Archetype Validation Service Exists

**Given** a work unit with `archetype` field
**When** `validate_archetype_alignment()` is called
**Then** returns list of validation warnings/suggestions based on PAR content vs archetype expectations

### AC2: Incident Archetype Validation

**Given** a work unit with `archetype: incident`
**When** validation runs
**Then** checks for:
- Problem contains incident indicators (outage, failure, breach, alert, impact scope)
- Actions contain response patterns (detected, triaged, mitigated, resolved, communicated)
- Outcome contains resolution metrics (MTTR, prevented impact, restored)

### AC3: Greenfield Archetype Validation

**Given** a work unit with `archetype: greenfield`
**When** validation runs
**Then** checks for:
- Problem describes need/opportunity (needed, gap, opportunity, no existing)
- Actions contain build patterns (designed, built, architected, launched, deployed)
- Outcome contains delivery indicators (delivered, launched, enabled, created)

### AC4: All Archetypes Have Validation Rules

**Given** any non-minimal archetype (8 total: incident, greenfield, migration, optimization, leadership, strategic, transformation, cultural)
**When** validation rules are defined
**Then** each archetype has problem_patterns, action_patterns, and outcome_patterns

### AC5: CLI Flag `--check-archetype` Added

**Given** user runs `resume validate work-units --check-archetype`
**When** validation completes
**Then** shows archetype alignment warnings alongside schema validation results

### AC6: Warnings Are Suggestions, Not Errors

**Given** archetype validation finds mismatches
**When** displaying results
**Then** shows as warnings (yellow) not errors (red), and does NOT fail validation

### AC7: Unit Tests for Each Archetype

**Given** the archetype validation service
**When** tested with sample work units
**Then** correctly identifies alignment/misalignment for each archetype type

---

## Technical Implementation

### 1. Create Archetype Validation Service

Location: `src/resume_as_code/services/archetype_validation_service.py`

```python
"""Archetype-aware PAR structure validation service."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from resume_as_code.models.work_unit import WorkUnit, WorkUnitArchetype


@dataclass
class ArchetypeValidationResult:
    """Result of archetype alignment validation."""

    archetype: WorkUnitArchetype
    is_aligned: bool
    problem_score: float  # 0.0-1.0
    action_score: float   # 0.0-1.0
    outcome_score: float  # 0.0-1.0
    warnings: list[str]
    suggestions: list[str]


# Validation patterns for each archetype
ARCHETYPE_PAR_PATTERNS: dict[WorkUnitArchetype, dict[str, list[str]]] = {
    WorkUnitArchetype.INCIDENT: {
        "problem_patterns": [
            r"outage", r"incident", r"failure", r"breach", r"alert",
            r"degraded", r"affecting", r"impact", r"down", r"critical",
        ],
        "action_patterns": [
            r"detect", r"triage", r"mitigat", r"resolv", r"respond",
            r"diagnos", r"communic", r"escalat", r"contain", r"restor",
        ],
        "outcome_patterns": [
            r"mttr", r"restor", r"prevent", r"reduc.*time",
            r"minutes", r"hours", r"avoided", r"resolved in",
        ],
    },
    WorkUnitArchetype.GREENFIELD: {
        "problem_patterns": [
            r"need", r"gap", r"opportunit", r"no existing", r"lack",
            r"require", r"demand", r"missing", r"enable",
        ],
        "action_patterns": [
            r"design", r"built", r"architect", r"launch", r"deploy",
            r"implement", r"engineer", r"pioneer", r"create", r"develop",
        ],
        "outcome_patterns": [
            r"deliver", r"launch", r"enabl", r"creat", r"achiev",
            r"support", r"serving", r"processing", r"scale",
        ],
    },
    WorkUnitArchetype.MIGRATION: {
        "problem_patterns": [
            r"legacy", r"outdat", r"end of life", r"unsupport",
            r"technical debt", r"old", r"deprecat", r"compatibility",
        ],
        "action_patterns": [
            r"migrat", r"transition", r"upgrad", r"convert",
            r"port", r"refactor", r"plan", r"cutover", r"parallel",
        ],
        "outcome_patterns": [
            r"complet", r"success", r"zero downtime", r"no data loss",
            r"modern", r"reduc.*cost", r"improv", r"decommission",
        ],
    },
    WorkUnitArchetype.OPTIMIZATION: {
        "problem_patterns": [
            r"slow", r"expensive", r"inefficient", r"bottleneck",
            r"latency", r"cost", r"resource", r"baseline",
        ],
        "action_patterns": [
            r"optimiz", r"profil", r"analyz", r"identif", r"implement",
            r"cache", r"refactor", r"streamlin", r"tune", r"rightsize",
        ],
        "outcome_patterns": [
            r"\d+%", r"reduc", r"improv", r"faster", r"cheaper",
            r"cost sav", r"latency", r"throughput", r"efficiency",
        ],
    },
    WorkUnitArchetype.LEADERSHIP: {
        "problem_patterns": [
            r"team", r"capability", r"talent", r"skill gap",
            r"growth", r"retention", r"hiring", r"alignment",
        ],
        "action_patterns": [
            r"mentor", r"coach", r"align", r"champion", r"built.*team",
            r"hired", r"develop", r"lead", r"unified", r"cultivat",
        ],
        "outcome_patterns": [
            r"promot", r"retent", r"grew", r"hired", r"engag",
            r"team", r"capability", r"culture", r"develop",
        ],
    },
    WorkUnitArchetype.STRATEGIC: {
        "problem_patterns": [
            r"market", r"competit", r"position", r"direction",
            r"strateg", r"opportunit", r"partner", r"growth",
        ],
        "action_patterns": [
            r"research", r"analyz", r"position", r"develop.*strateg",
            r"establish", r"partner", r"align", r"define", r"framework",
        ],
        "outcome_patterns": [
            r"market share", r"competit", r"position", r"partner",
            r"revenue", r"growth", r"advantage", r"influence",
        ],
    },
    WorkUnitArchetype.TRANSFORMATION: {
        "problem_patterns": [
            r"enterprise", r"organization", r"company-wide", r"scale",
            r"transform", r"digital", r"legacy", r"moderniz",
        ],
        "action_patterns": [
            r"transform", r"lead", r"execut", r"change manag",
            r"vision", r"align", r"rollout", r"global", r"enterprise",
        ],
        "outcome_patterns": [
            r"transform", r"enterprise", r"company-wide", r"scale",
            r"million", r"organization", r"global", r"adopted",
        ],
    },
    WorkUnitArchetype.CULTURAL: {
        "problem_patterns": [
            r"culture", r"engagement", r"retention", r"attrition",
            r"morale", r"satisfaction", r"diversity", r"inclusion",
        ],
        "action_patterns": [
            r"cultivat", r"program", r"initiative", r"champion",
            r"foster", r"measur", r"survey", r"implement",
        ],
        "outcome_patterns": [
            r"engagement", r"retention", r"nps", r"satisfaction",
            r"attrition", r"score", r"improv", r"culture",
        ],
    },
}


def extract_par_text(work_unit: WorkUnit | dict[str, Any]) -> tuple[str, str, str]:
    """Extract Problem, Actions, Result text from work unit."""
    if isinstance(work_unit, WorkUnit):
        problem_text = work_unit.problem.statement
        if work_unit.problem.context:
            problem_text += " " + work_unit.problem.context
        action_text = " ".join(work_unit.actions)
        outcome_text = work_unit.outcome.result
        if work_unit.outcome.quantified_impact:
            outcome_text += " " + work_unit.outcome.quantified_impact
        if work_unit.outcome.business_value:
            outcome_text += " " + work_unit.outcome.business_value
    else:
        problem = work_unit.get("problem", {})
        problem_text = str(problem.get("statement", ""))
        if problem.get("context"):
            problem_text += " " + str(problem.get("context", ""))
        action_text = " ".join(work_unit.get("actions", []))
        outcome = work_unit.get("outcome", {})
        outcome_text = str(outcome.get("result", ""))
        if outcome.get("quantified_impact"):
            outcome_text += " " + str(outcome.get("quantified_impact", ""))
        if outcome.get("business_value"):
            outcome_text += " " + str(outcome.get("business_value", ""))

    return problem_text.lower(), action_text.lower(), outcome_text.lower()


def score_par_section(text: str, patterns: list[str]) -> float:
    """Score how well text matches expected patterns (0.0-1.0)."""
    if not patterns or not text:
        return 0.0

    matches = sum(1 for p in patterns if re.search(p, text, re.IGNORECASE))
    return min(1.0, matches / max(3, len(patterns) // 2))  # Expect at least 3 matches for 1.0


def validate_archetype_alignment(
    work_unit: WorkUnit | dict[str, Any],
    archetype: WorkUnitArchetype | None = None,
) -> ArchetypeValidationResult:
    """Validate work unit PAR structure against archetype expectations.

    Args:
        work_unit: WorkUnit object or raw dict from YAML.
        archetype: Override archetype (uses work_unit.archetype if not provided).

    Returns:
        ArchetypeValidationResult with scores and suggestions.
    """
    if archetype is None:
        if isinstance(work_unit, WorkUnit):
            archetype = work_unit.archetype
        else:
            arch_str = work_unit.get("archetype", "minimal")
            archetype = WorkUnitArchetype(arch_str)

    # Minimal archetype has no specific validation
    if archetype == WorkUnitArchetype.MINIMAL:
        return ArchetypeValidationResult(
            archetype=archetype,
            is_aligned=True,
            problem_score=1.0,
            action_score=1.0,
            outcome_score=1.0,
            warnings=[],
            suggestions=["Consider classifying with a specific archetype for better resume targeting"],
        )

    patterns = ARCHETYPE_PAR_PATTERNS.get(archetype, {})
    problem_text, action_text, outcome_text = extract_par_text(work_unit)

    # Score each PAR section
    problem_score = score_par_section(problem_text, patterns.get("problem_patterns", []))
    action_score = score_par_section(action_text, patterns.get("action_patterns", []))
    outcome_score = score_par_section(outcome_text, patterns.get("outcome_patterns", []))

    warnings: list[str] = []
    suggestions: list[str] = []

    # Generate warnings for low scores
    ALIGNMENT_THRESHOLD = 0.3

    if problem_score < ALIGNMENT_THRESHOLD:
        warnings.append(
            f"Problem section may not align with {archetype.value} archetype "
            f"(score: {problem_score:.0%})"
        )
        suggestions.append(
            f"For {archetype.value}, problem should describe: "
            f"{_get_problem_guidance(archetype)}"
        )

    if action_score < ALIGNMENT_THRESHOLD:
        warnings.append(
            f"Actions may not align with {archetype.value} archetype "
            f"(score: {action_score:.0%})"
        )
        suggestions.append(
            f"For {archetype.value}, actions should include: "
            f"{_get_action_guidance(archetype)}"
        )

    if outcome_score < ALIGNMENT_THRESHOLD:
        warnings.append(
            f"Outcome may not align with {archetype.value} archetype "
            f"(score: {outcome_score:.0%})"
        )
        suggestions.append(
            f"For {archetype.value}, outcome should demonstrate: "
            f"{_get_outcome_guidance(archetype)}"
        )

    # Overall alignment check
    avg_score = (problem_score + action_score + outcome_score) / 3
    is_aligned = avg_score >= ALIGNMENT_THRESHOLD

    if not is_aligned:
        suggestions.append(
            f"Consider if '{archetype.value}' is the best archetype for this work unit. "
            f"Run 'resume infer-archetypes' to see suggestions."
        )

    return ArchetypeValidationResult(
        archetype=archetype,
        is_aligned=is_aligned,
        problem_score=problem_score,
        action_score=action_score,
        outcome_score=outcome_score,
        warnings=warnings,
        suggestions=suggestions,
    )


def _get_problem_guidance(archetype: WorkUnitArchetype) -> str:
    """Get human-readable guidance for problem section."""
    guidance = {
        WorkUnitArchetype.INCIDENT: "the incident/outage, impact scope, and severity",
        WorkUnitArchetype.GREENFIELD: "the need, gap, or opportunity that drove the project",
        WorkUnitArchetype.MIGRATION: "legacy system limitations and modernization drivers",
        WorkUnitArchetype.OPTIMIZATION: "performance baseline, costs, or inefficiencies",
        WorkUnitArchetype.LEADERSHIP: "team/capability gaps or growth opportunities",
        WorkUnitArchetype.STRATEGIC: "market position, competitive challenges, or strategic needs",
        WorkUnitArchetype.TRANSFORMATION: "enterprise-wide challenges requiring transformation",
        WorkUnitArchetype.CULTURAL: "culture, engagement, or retention challenges",
    }
    return guidance.get(archetype, "the challenge or problem")


def _get_action_guidance(archetype: WorkUnitArchetype) -> str:
    """Get human-readable guidance for action section."""
    guidance = {
        WorkUnitArchetype.INCIDENT: "detect, triage, mitigate, resolve, communicate",
        WorkUnitArchetype.GREENFIELD: "design, build, architect, launch, deploy",
        WorkUnitArchetype.MIGRATION: "plan, migrate, transition, validate, cutover",
        WorkUnitArchetype.OPTIMIZATION: "profile, analyze, optimize, implement improvements",
        WorkUnitArchetype.LEADERSHIP: "mentor, coach, align, champion, build team",
        WorkUnitArchetype.STRATEGIC: "research, analyze, position, establish partnerships",
        WorkUnitArchetype.TRANSFORMATION: "lead transformation, execute change, align organization",
        WorkUnitArchetype.CULTURAL: "cultivate, program, measure, foster change",
    }
    return guidance.get(archetype, "relevant actions")


def _get_outcome_guidance(archetype: WorkUnitArchetype) -> str:
    """Get human-readable guidance for outcome section."""
    guidance = {
        WorkUnitArchetype.INCIDENT: "MTTR, restored service, prevented impact",
        WorkUnitArchetype.GREENFIELD: "delivered capability, launched product, enabled users",
        WorkUnitArchetype.MIGRATION: "successful transition, zero downtime, decommissioned legacy",
        WorkUnitArchetype.OPTIMIZATION: "% improvement, cost savings, latency reduction",
        WorkUnitArchetype.LEADERSHIP: "team growth, promotions, retention, capability building",
        WorkUnitArchetype.STRATEGIC: "market share, competitive position, partnerships",
        WorkUnitArchetype.TRANSFORMATION: "enterprise-wide adoption, organizational change",
        WorkUnitArchetype.CULTURAL: "engagement scores, retention rates, culture metrics",
    }
    return guidance.get(archetype, "measurable results")
```

### 2. Integrate with Validate Command

Location: `src/resume_as_code/commands/validate.py`

Add to the `validate_work_units_command` function:

```python
# Add option
@click.option(
    "--check-archetype",
    is_flag=True,
    help="Validate PAR structure matches archetype expectations",
)
```

After existing validation, add:

```python
# Archetype validation (warnings only, doesn't fail validation)
if check_archetype:
    from resume_as_code.services.archetype_validation_service import (
        validate_archetype_alignment,
    )

    for wu in work_units:
        result = validate_archetype_alignment(wu)
        if not result.is_aligned or result.warnings:
            has_warnings = True
            if not ctx.obj.json_output:
                console.print(
                    f"\n[yellow]Archetype alignment warnings for {wu.id}:[/yellow]"
                )
                for warning in result.warnings:
                    console.print(f"  [yellow]![/yellow] {warning}")
                for suggestion in result.suggestions:
                    console.print(f"  [dim]{suggestion}[/dim]")

            # Add to JSON warnings if applicable
            if ctx.obj.json_output:
                for warning in result.warnings:
                    warnings.append({
                        "file": f"work-units/{wu.id}.yaml",
                        "type": "archetype_alignment",
                        "message": warning,
                        "suggestion": result.suggestions[0] if result.suggestions else None,
                    })
```

### 3. Add Unit Tests

Location: `tests/unit/services/test_archetype_validation_service.py`

```python
"""Tests for archetype validation service."""

from __future__ import annotations

import pytest

from resume_as_code.models.work_unit import WorkUnitArchetype
from resume_as_code.services.archetype_validation_service import (
    extract_par_text,
    score_par_section,
    validate_archetype_alignment,
)


class TestExtractParText:
    """Tests for PAR text extraction."""

    def test_extracts_from_dict(self) -> None:
        """Should extract problem, actions, outcome from dict."""
        data = {
            "problem": {
                "statement": "Database crashed",
                "context": "During peak hours",
            },
            "actions": ["Diagnosed issue", "Restored service"],
            "outcome": {
                "result": "Resolved in 30 min",
                "quantified_impact": "Prevented $10K loss",
            },
        }
        problem, actions, outcome = extract_par_text(data)
        assert "database crashed" in problem
        assert "peak hours" in problem
        assert "diagnosed issue" in actions
        assert "resolved in 30 min" in outcome
        assert "prevented" in outcome


class TestScoreParSection:
    """Tests for PAR section scoring."""

    def test_high_score_with_many_matches(self) -> None:
        """Should score high when text contains many pattern matches."""
        text = "detected outage, triaged impact, mitigated damage, resolved incident"
        patterns = ["detect", "triage", "mitigat", "resolv", "incident"]
        score = score_par_section(text, patterns)
        assert score >= 0.8

    def test_low_score_with_no_matches(self) -> None:
        """Should score low when text has no pattern matches."""
        text = "did some work on the project"
        patterns = ["detect", "triage", "mitigat", "resolv"]
        score = score_par_section(text, patterns)
        assert score < 0.3

    def test_zero_score_for_empty_patterns(self) -> None:
        """Should return 0 for empty patterns."""
        score = score_par_section("some text", [])
        assert score == 0.0


class TestValidateArchetypeAlignment:
    """Tests for archetype alignment validation."""

    def test_incident_aligned_work_unit(self) -> None:
        """Well-formed incident work unit should be aligned."""
        data = {
            "archetype": "incident",
            "problem": {
                "statement": "Production database outage affecting 10K users",
                "context": "Critical P1 incident during peak hours",
            },
            "actions": [
                "Detected via monitoring alerts",
                "Triaged impact across services",
                "Mitigated by failing over to replica",
                "Resolved root cause in connection pool",
                "Communicated status to stakeholders",
            ],
            "outcome": {
                "result": "Restored service in 45 minutes",
                "quantified_impact": "MTTR reduced, prevented $50K impact",
            },
        }
        result = validate_archetype_alignment(data)
        assert result.is_aligned
        assert result.problem_score >= 0.3
        assert result.action_score >= 0.3
        assert result.outcome_score >= 0.3
        assert len(result.warnings) == 0

    def test_greenfield_aligned_work_unit(self) -> None:
        """Well-formed greenfield work unit should be aligned."""
        data = {
            "archetype": "greenfield",
            "problem": {
                "statement": "Team needed real-time analytics capability",
                "context": "Gap in observability for customer behavior",
            },
            "actions": [
                "Designed event-driven architecture",
                "Built streaming data pipeline",
                "Deployed to production with CI/CD",
                "Launched beta to internal teams",
            ],
            "outcome": {
                "result": "Delivered analytics platform serving 1M events/day",
                "quantified_impact": "Enabled product team to make data-driven decisions",
            },
        }
        result = validate_archetype_alignment(data)
        assert result.is_aligned
        assert len(result.warnings) == 0

    def test_misaligned_work_unit_generates_warnings(self) -> None:
        """Work unit with wrong archetype should generate warnings."""
        data = {
            "archetype": "incident",  # Wrong archetype for this content
            "problem": {
                "statement": "Team needed new feature",  # Not incident-like
            },
            "actions": ["Built new system", "Deployed to production"],
            "outcome": {
                "result": "Launched new product",  # Not incident-like
            },
        }
        result = validate_archetype_alignment(data)
        assert not result.is_aligned
        assert len(result.warnings) > 0
        assert any("incident" in w.lower() for w in result.warnings)

    def test_minimal_archetype_always_aligned(self) -> None:
        """Minimal archetype should always be aligned (no validation)."""
        data = {
            "archetype": "minimal",
            "problem": {"statement": "stuff"},
            "actions": ["did things"],
            "outcome": {"result": "it worked"},
        }
        result = validate_archetype_alignment(data)
        assert result.is_aligned
        assert result.problem_score == 1.0
        assert len(result.warnings) == 0
        assert any("specific archetype" in s for s in result.suggestions)

    def test_optimization_checks_for_metrics(self) -> None:
        """Optimization archetype should check for quantified improvements."""
        data = {
            "archetype": "optimization",
            "problem": {
                "statement": "API was slow with high latency",
                "context": "Baseline response time 500ms",
            },
            "actions": [
                "Profiled application to identify bottlenecks",
                "Optimized database queries",
                "Implemented caching layer",
            ],
            "outcome": {
                "result": "Reduced latency by 60%",
                "quantified_impact": "Response time improved from 500ms to 200ms",
            },
        }
        result = validate_archetype_alignment(data)
        assert result.is_aligned
        assert result.outcome_score >= 0.3  # Should detect % improvement

    def test_all_archetypes_have_patterns(self) -> None:
        """Every non-minimal archetype should have validation patterns."""
        from resume_as_code.services.archetype_validation_service import (
            ARCHETYPE_PAR_PATTERNS,
        )

        for archetype in WorkUnitArchetype:
            if archetype == WorkUnitArchetype.MINIMAL:
                continue
            assert archetype in ARCHETYPE_PAR_PATTERNS, f"Missing patterns for {archetype}"
            patterns = ARCHETYPE_PAR_PATTERNS[archetype]
            assert "problem_patterns" in patterns
            assert "action_patterns" in patterns
            assert "outcome_patterns" in patterns
```

---

## Implementation Checklist

- [x] Create `src/resume_as_code/services/archetype_validation_service.py`
- [x] Add `--check-archetype` flag to validate command
- [x] Integrate archetype validation in validate.py work-units subcommand
- [x] Create `tests/unit/services/test_archetype_validation_service.py`
- [x] Add CLI integration test for `--check-archetype` flag
- [x] Run `ruff check src tests --fix`
- [x] Run `ruff format src tests`
- [x] Run `mypy src --strict`
- [x] Run `pytest -v`

---

## Files to Create/Modify

| File | Change |
|------|--------|
| `src/resume_as_code/services/archetype_validation_service.py` | **NEW** - Validation service |
| `src/resume_as_code/commands/validate.py` | Add `--check-archetype` flag and integration |
| `tests/unit/services/test_archetype_validation_service.py` | **NEW** - Unit tests |
| `tests/test_cli.py` | Add CLI integration test |

---

## Anti-Patterns to Avoid

1. **DO NOT** fail validation on archetype misalignment - these are warnings/suggestions only
2. **DO NOT** use ML/embeddings - simple regex patterns are sufficient and deterministic
3. **DO NOT** modify work unit files - this is read-only validation
4. **DO NOT** add archetype validation to schema (JSON Schema) - it's content-aware validation
5. **DO NOT** require --check-archetype by default - it's opt-in

---

## Verification Commands

```bash
# Run archetype validation on work units
uv run resume validate work-units --check-archetype

# With verbose output
uv run resume -v validate work-units --check-archetype

# JSON output for programmatic use
uv run resume --json validate work-units --check-archetype

# Run specific tests
uv run pytest tests/unit/services/test_archetype_validation_service.py -v

# Run full quality check
uv run ruff check src tests --fix && uv run ruff format src tests && uv run mypy src --strict && uv run pytest
```

---

## Project Structure Notes

- New service follows existing service patterns (`services/archetype_inference_service.py` from 12-3)
- Validation flag follows existing pattern (`--check-positions` from 11-5)
- Uses dataclass for result (matches existing patterns in codebase)
- Regex patterns reuse some from `archetype_inference_service.py` where appropriate

---

## References

- [Source: _bmad-output/implementation-artifacts/12-1-archetype-field-model.md] - Archetype enum and field
- [Source: _bmad-output/implementation-artifacts/12-3-archetype-inference-service.md] - Inference patterns
- [Source: src/resume_as_code/data/archetypes/*.yaml] - Archetype PAR templates
- [Source: _bmad-output/planning-artifacts/architecture.md#Content-Strategy-Standards] - PAR framework standards
- [Source: _bmad-output/project-context.md] - Project patterns and rules

---

## Dev Agent Record

### Agent Model Used

Claude Opus 4.5 (claude-opus-4-5-20251101)

### Debug Log References

N/A

### Completion Notes List

- Created archetype validation service with PAR pattern matching for all 8 non-minimal archetypes
- Service uses regex-based scoring (not ML) for deterministic results
- Added `--check-archetype` flag to `validate work-units` subcommand
- Warnings displayed in yellow (Rich) - do not fail validation per AC6
- JSON output includes archetype_warnings array
- 22 unit tests covering all archetypes and edge cases
- 5 integration tests for CLI flag behavior
- All 2748 tests pass with ruff, mypy clean

**Code Review Fixes Applied (2026-01-19):**
- Added module-level constants: `ALIGNMENT_THRESHOLD` and `MIN_MATCHES_FOR_FULL_SCORE` (replaced magic numbers)
- Added full docstring documentation to `extract_par_text()` and `score_par_section()`
- Fixed `_validate_archetype()` suggestion mapping bug - now pairs each warning with its corresponding suggestion by index
- Fixed edge case in `extract_par_text()` to handle None values and missing sections gracefully
- Added 4 new edge case tests for malformed work unit data
- All 2460 tests pass with ruff and mypy clean

### File List

| File | Action |
|------|--------|
| `src/resume_as_code/services/archetype_validation_service.py` | Created, then modified (review fixes) |
| `src/resume_as_code/commands/validate.py` | Modified, then modified (review fixes) |
| `tests/unit/services/test_archetype_validation_service.py` | Created, then modified (review fixes) |
| `tests/integration/test_validate_command.py` | Modified |

---

## Story Points: 5

**Rationale**: Medium complexity with new service, CLI integration, and comprehensive test coverage. Pattern matching logic requires careful design but builds on existing archetype inference patterns.
