# Story 12.3: Archetype Inference Service

## Status: Done

---

## Story

**As a** user with existing work units that lack archetype metadata,
**I want** an inference service that suggests archetypes based on content analysis,
**So that** I can efficiently categorize my work history without manual classification.

---

## Context & Background

### Epic 12 Goal

Add persistent archetype tracking to work units for categorization analysis, PAR validation, and improved resume generation.

### Previous Stories

- **12-1** (done): Added `WorkUnitArchetype` enum and required `archetype` field to model
- **12-2** (ready-for-dev): Persist archetype when using `--archetype` flag

### Problem Statement

Users with existing work units (pre-v4.0.0 schema) or work units created without explicit archetype selection need a way to:
1. Automatically infer archetype from content
2. Batch-classify multiple work units
3. Review suggestions before applying

### Archetype Distinguishing Characteristics

| Archetype | Key Signals (Keywords, Patterns) |
|-----------|----------------------------------|
| **incident** | P1/P2, outage, breach, resolved, detected, triaged, mitigated, MTTR, incident-response tag |
| **greenfield** | built, designed, architected, launched, new system, from scratch, pioneered |
| **migration** | migrated, migration, upgraded, transitioned, legacy replacement, cloud migration |
| **optimization** | optimized, reduced latency, cost reduction, performance, profiled, metrics.baseline present |
| **leadership** | mentored, coached, aligned stakeholders, championed, unified teams, organizational |
| **strategic** | strategy, market analysis, competitive, positioned, partnership, market share |
| **transformation** | transformation, digital, enterprise-wide, board-level, organizational change |
| **cultural** | culture, talent development, engagement, attrition, retention, cultivated |
| **minimal** | Fallback when confidence < threshold; short content with no strong signals |

---

## Acceptance Criteria

### AC1: Inference Service Returns Archetype with Confidence

**Given** a work unit dictionary or `WorkUnit` object
**When** `infer_archetype()` is called
**Then** returns `(archetype: WorkUnitArchetype, confidence: float)` tuple where confidence is 0.0-1.0

### AC2: Inference Uses Multiple Signals

**Given** a work unit with title, problem, actions, outcome, and tags
**When** inference analyzes the content
**Then** combines signals from all fields (not just title) for accurate classification

### AC3: Returns `minimal` When Uncertain

**Given** a work unit with ambiguous or insufficient content
**When** confidence score < 0.5 threshold
**Then** returns `(WorkUnitArchetype.MINIMAL, confidence)` as safe fallback

### AC4: CLI Command for Batch Inference

**Given** work units directory with multiple YAML files
**When** user runs `resume infer-archetypes [--apply] [--min-confidence 0.5]`
**Then** displays suggested archetypes for each work unit, optionally applying them

### AC5: Dry-Run by Default

**Given** user runs `resume infer-archetypes` without `--apply`
**When** inference completes
**Then** shows suggestions only, does NOT modify files

---

## Technical Implementation

### 1. Create Inference Service

Location: `src/resume_as_code/services/archetype_inference_service.py`

```python
"""Archetype inference service for classifying work units."""

from __future__ import annotations

import re
from typing import Any

from resume_as_code.models.work_unit import WorkUnit, WorkUnitArchetype

# Keyword patterns for each archetype (case-insensitive)
ARCHETYPE_PATTERNS: dict[WorkUnitArchetype, list[str]] = {
    WorkUnitArchetype.INCIDENT: [
        r"\bp[12]\b", r"outage", r"incident", r"breach", r"detected",
        r"triaged", r"mitigated", r"resolved.*production", r"mttr",
        r"security\s+event", r"escalation", r"on-?call",
    ],
    WorkUnitArchetype.GREENFIELD: [
        r"built\s+(?:new|a)", r"designed\s+(?:and\s+)?(?:built|implemented)",
        r"architected", r"launched", r"from\s+scratch", r"pioneered",
        r"new\s+(?:system|feature|product|platform)", r"ground-?up",
    ],
    WorkUnitArchetype.MIGRATION: [
        r"migrat(?:ed|ion)", r"upgraded", r"transitioned",
        r"legacy\s+(?:replacement|system)", r"cloud\s+migration",
        r"database\s+migration", r"platform\s+(?:upgrade|migration)",
    ],
    WorkUnitArchetype.OPTIMIZATION: [
        r"optimiz(?:ed|ation)", r"reduced\s+(?:latency|cost|time)",
        r"improv(?:ed|ing)\s+performance", r"profiled",
        r"cost\s+(?:reduction|savings)", r"latency\s+reduction",
        r"resource\s+(?:optimization|rightsizing)",
    ],
    WorkUnitArchetype.LEADERSHIP: [
        r"mentor(?:ed|ing)", r"coach(?:ed|ing)", r"aligned\s+stakeholders",
        r"championed", r"unified\s+teams", r"cross-?team",
        r"organizational\s+(?:change|impact)", r"built\s+(?:the\s+)?team",
    ],
    WorkUnitArchetype.STRATEGIC: [
        r"strateg(?:y|ic)", r"market\s+(?:analysis|positioning)",
        r"competitive", r"positioned", r"partnership",
        r"market\s+share", r"business\s+development",
    ],
    WorkUnitArchetype.TRANSFORMATION: [
        r"transformation", r"digital\s+transformation",
        r"enterprise-?wide", r"board-?level", r"organizational\s+change",
        r"company-?wide", r"global\s+(?:initiative|rollout)",
    ],
    WorkUnitArchetype.CULTURAL: [
        r"culture", r"talent\s+development", r"engagement",
        r"attrition", r"retention", r"cultivated",
        r"dei|diversity", r"employee\s+experience",
    ],
}

# Minimum confidence to suggest non-minimal archetype
MIN_CONFIDENCE_THRESHOLD = 0.5


def extract_text_content(work_unit: WorkUnit | dict[str, Any]) -> str:
    """Extract all text content from work unit for analysis."""
    if isinstance(work_unit, WorkUnit):
        parts = [
            work_unit.title,
            work_unit.problem.statement,
            " ".join(work_unit.actions),
            work_unit.outcome.result,
            " ".join(work_unit.tags),
        ]
        if work_unit.outcome.quantified_impact:
            parts.append(work_unit.outcome.quantified_impact)
        if work_unit.outcome.business_value:
            parts.append(work_unit.outcome.business_value)
    else:
        # Handle dict (raw YAML)
        parts = [
            str(work_unit.get("title", "")),
            str(work_unit.get("problem", {}).get("statement", "")),
            " ".join(work_unit.get("actions", [])),
            str(work_unit.get("outcome", {}).get("result", "")),
            " ".join(work_unit.get("tags", [])),
        ]
    return " ".join(parts).lower()


def score_archetype(text: str, archetype: WorkUnitArchetype) -> float:
    """Score how well text matches an archetype's patterns."""
    patterns = ARCHETYPE_PATTERNS.get(archetype, [])
    if not patterns:
        return 0.0

    matches = sum(1 for p in patterns if re.search(p, text, re.IGNORECASE))
    return matches / len(patterns)


def infer_archetype(
    work_unit: WorkUnit | dict[str, Any],
    threshold: float = MIN_CONFIDENCE_THRESHOLD,
) -> tuple[WorkUnitArchetype, float]:
    """Infer archetype from work unit content.

    Args:
        work_unit: WorkUnit object or raw dict from YAML.
        threshold: Minimum confidence to return non-minimal archetype.

    Returns:
        Tuple of (archetype, confidence) where confidence is 0.0-1.0.
    """
    text = extract_text_content(work_unit)

    scores: dict[WorkUnitArchetype, float] = {}
    for archetype in WorkUnitArchetype:
        if archetype == WorkUnitArchetype.MINIMAL:
            continue  # Don't score minimal - it's the fallback
        scores[archetype] = score_archetype(text, archetype)

    if not scores:
        return (WorkUnitArchetype.MINIMAL, 0.0)

    best_archetype = max(scores, key=lambda k: scores[k])
    best_score = scores[best_archetype]

    if best_score < threshold:
        return (WorkUnitArchetype.MINIMAL, best_score)

    return (best_archetype, best_score)
```

### 2. Add CLI Command

Location: `src/resume_as_code/commands/infer.py`

```python
"""Infer archetypes for work units."""

from __future__ import annotations

from pathlib import Path

import click
from ruamel.yaml import YAML

from resume_as_code.config import get_config
from resume_as_code.models.output import JSONResponse
from resume_as_code.services.archetype_inference_service import (
    MIN_CONFIDENCE_THRESHOLD,
    infer_archetype,
)
from resume_as_code.utils.console import console, info, success, warning
from resume_as_code.utils.errors import handle_errors


@click.command("infer-archetypes")
@click.option(
    "--apply",
    is_flag=True,
    help="Apply inferred archetypes to work unit files (default: dry-run)",
)
@click.option(
    "--min-confidence",
    type=float,
    default=MIN_CONFIDENCE_THRESHOLD,
    help=f"Minimum confidence to suggest archetype (default: {MIN_CONFIDENCE_THRESHOLD})",
)
@click.option(
    "--include-assigned",
    is_flag=True,
    help="Re-infer even for work units that already have archetypes",
)
@click.pass_context
@handle_errors
def infer_archetypes_command(
    ctx: click.Context,
    apply: bool,
    min_confidence: float,
    include_assigned: bool,
) -> None:
    """Infer archetypes for work units based on content analysis.

    By default, shows suggestions without modifying files.
    Use --apply to update work unit files with inferred archetypes.
    """
    config = get_config()
    work_units_dir = config.work_units_dir

    if not work_units_dir.exists():
        warning("No work-units directory found")
        return

    yaml = YAML()
    yaml.preserve_quotes = True

    results: list[dict] = []

    for yaml_file in sorted(work_units_dir.glob("*.yaml")):
        with yaml_file.open() as f:
            data = yaml.load(f)

        if not data:
            continue

        existing_archetype = data.get("archetype")

        # Skip if already has archetype (unless --include-assigned)
        if existing_archetype and not include_assigned:
            continue

        archetype, confidence = infer_archetype(data, min_confidence)

        result = {
            "file": yaml_file.name,
            "id": data.get("id", "unknown"),
            "inferred": archetype.value,
            "confidence": round(confidence, 2),
            "existing": existing_archetype,
        }
        results.append(result)

        if apply and confidence >= min_confidence:
            data["archetype"] = archetype.value
            with yaml_file.open("w") as f:
                yaml.dump(data, f)
            result["applied"] = True

    # Output results
    if ctx.obj.json_output:
        response = JSONResponse(
            status="success",
            command="infer-archetypes",
            data={
                "results": results,
                "total": len(results),
                "applied": apply,
                "min_confidence": min_confidence,
            },
        )
        click.echo(response.to_json())
    else:
        if not results:
            info("No work units to analyze (all have archetypes assigned)")
            return

        console.print(f"\n[bold]Archetype Inference Results[/bold]\n")

        for r in results:
            status = "[green]APPLIED[/green]" if r.get("applied") else "[dim]suggested[/dim]"
            conf_color = "green" if r["confidence"] >= 0.7 else "yellow" if r["confidence"] >= 0.5 else "red"
            console.print(
                f"  {r['file']}: "
                f"[{conf_color}]{r['inferred']}[/{conf_color}] "
                f"({r['confidence']:.0%}) {status}"
            )

        console.print(f"\n[dim]Total: {len(results)} | Min confidence: {min_confidence}[/dim]")

        if not apply:
            console.print("\n[dim]Use --apply to update files[/dim]")
```

### 3. Register CLI Command

Location: `src/resume_as_code/cli.py`

Add import and registration:
```python
from resume_as_code.commands.infer import infer_archetypes_command

# In cli setup:
cli.add_command(infer_archetypes_command)
```

### 4. Add Unit Tests

Location: `tests/unit/services/test_archetype_inference_service.py`

```python
"""Tests for archetype inference service."""

from __future__ import annotations

import pytest

from resume_as_code.models.work_unit import WorkUnitArchetype
from resume_as_code.services.archetype_inference_service import (
    extract_text_content,
    infer_archetype,
    score_archetype,
)


class TestExtractTextContent:
    """Tests for text extraction."""

    def test_extracts_from_dict(self) -> None:
        """Should extract all text fields from dict."""
        data = {
            "title": "Resolved P1 outage",
            "problem": {"statement": "Database failed"},
            "actions": ["Diagnosed issue", "Fixed config"],
            "outcome": {"result": "Restored in 30 min"},
            "tags": ["incident-response"],
        }
        text = extract_text_content(data)
        assert "resolved p1 outage" in text
        assert "database failed" in text
        assert "incident-response" in text


class TestScoreArchetype:
    """Tests for archetype scoring."""

    def test_incident_keywords_score_high(self) -> None:
        """Incident keywords should score high for INCIDENT archetype."""
        text = "resolved p1 outage, detected, triaged, mitigated incident"
        score = score_archetype(text, WorkUnitArchetype.INCIDENT)
        assert score > 0.3

    def test_migration_keywords_score_high(self) -> None:
        """Migration keywords should score high for MIGRATION archetype."""
        text = "migrated legacy database to cloud"
        score = score_archetype(text, WorkUnitArchetype.MIGRATION)
        assert score > 0.2


class TestInferArchetype:
    """Tests for archetype inference."""

    def test_infers_incident_from_p1_keywords(self) -> None:
        """Should infer INCIDENT from P1/outage keywords."""
        data = {
            "title": "Resolved P1 database outage affecting 10K users",
            "problem": {"statement": "Production database failed"},
            "actions": ["Detected via alerts", "Triaged impact", "Mitigated"],
            "outcome": {"result": "Restored service in 45 minutes"},
            "tags": ["incident-response"],
        }
        archetype, confidence = infer_archetype(data)
        assert archetype == WorkUnitArchetype.INCIDENT
        assert confidence >= 0.5

    def test_infers_greenfield_from_build_keywords(self) -> None:
        """Should infer GREENFIELD from new system keywords."""
        data = {
            "title": "Built new real-time analytics pipeline from scratch",
            "problem": {"statement": "No analytics capability existed"},
            "actions": ["Designed architecture", "Built data pipeline"],
            "outcome": {"result": "Launched analytics platform"},
            "tags": ["new-system"],
        }
        archetype, confidence = infer_archetype(data)
        assert archetype == WorkUnitArchetype.GREENFIELD
        assert confidence >= 0.3

    def test_returns_minimal_for_ambiguous_content(self) -> None:
        """Should return MINIMAL when content is ambiguous."""
        data = {
            "title": "Did some work",
            "problem": {"statement": "There was a problem"},
            "actions": ["Fixed it"],
            "outcome": {"result": "It worked"},
            "tags": [],
        }
        archetype, confidence = infer_archetype(data)
        assert archetype == WorkUnitArchetype.MINIMAL
        assert confidence < 0.5
```

---

## Implementation Checklist

- [x] Create `src/resume_as_code/services/archetype_inference_service.py`
- [x] Create `src/resume_as_code/commands/infer.py`
- [x] Register command in `src/resume_as_code/cli.py`
- [x] Create `tests/unit/services/test_archetype_inference_service.py`
- [x] Add test for CLI command `tests/test_cli.py`
- [x] Run `ruff check src tests --fix`
- [x] Run `ruff format src tests`
- [x] Run `mypy src --strict`
- [x] Run `pytest -v`

---

## Files to Create/Modify

| File | Change |
|------|--------|
| `src/resume_as_code/services/archetype_inference_service.py` | **NEW** - Inference logic |
| `src/resume_as_code/commands/infer.py` | **NEW** - CLI command |
| `src/resume_as_code/cli.py` | Register new command |
| `tests/unit/services/__init__.py` | **NEW** - Package init |
| `tests/unit/services/test_archetype_inference_service.py` | **NEW** - Unit tests (25 tests after review) |
| `tests/test_cli.py` | **MODIFIED** - CLI integration tests (11 tests after review) |

**Note:** The following files were also modified in the same commit (Story 12-2 bundled changes):
| `src/resume_as_code/services/work_unit_service.py` | Archetype persistence in template creation |
| `tests/unit/test_work_unit_service.py` | Tests for archetype persistence |

---

## Anti-Patterns to Avoid

1. **DO NOT** use ML/embeddings - simple regex patterns are sufficient for this domain
2. **DO NOT** modify work units by default - dry-run first
3. **DO NOT** overwrite user's explicit archetype choice unless `--include-assigned`
4. **DO NOT** skip validation - inferred archetype must still pass WorkUnitArchetype enum

---

## Verification Commands

```bash
# Run inference in dry-run mode
uv run resume infer-archetypes

# Apply inferred archetypes
uv run resume infer-archetypes --apply

# Lower confidence threshold
uv run resume infer-archetypes --min-confidence 0.3 --apply

# JSON output for programmatic use
uv run resume --json infer-archetypes

# Run tests
uv run pytest tests/unit/services/test_archetype_inference_service.py -v
```

---

## Future Enhancements (Out of Scope)

- Semantic similarity using embeddings (currently regex-based)
- Training on user's classification choices
- Multiple archetype suggestions (top-3)
- Integration with migration command for v4.0.0 upgrades

---

## Story Points: 8

**Rationale**: New service module, new CLI command, comprehensive test coverage, regex pattern design. Medium complexity with clear boundaries.

---

## Dev Agent Record

**Completed**: 2026-01-19

**Implementation Notes**:
- Created inference service with regex-based pattern matching (no ML/embeddings per anti-patterns)
- Service uses 0.5 confidence threshold (vs 0.3 in archetype_inference.py for migration use case)
- CLI command is dry-run by default; `--apply` updates files using ruamel.yaml to preserve comments
- Full test coverage: 25 unit tests + 11 CLI integration tests (after review)
- All quality checks pass: ruff, mypy --strict, pytest

**Note on archetype_inference.py**: Existing `archetype_inference.py` (Story 12.1) is NOT redundant - it serves migration use case with lower 0.3 threshold and simpler interface. The new `archetype_inference_service.py` serves CLI use case with 0.5 threshold and richer API.

---

## Code Review Record

**Reviewed**: 2026-01-19

**Issues Fixed**:
1. **HIGH**: Changed `infer.py` to use `config.work_units_dir` instead of hardcoded `Path.cwd() / "work-units"` for consistency with all other commands
2. **MEDIUM**: Added 3 tests for WorkUnit object branch in `extract_text_content()` (was only testing dict branch)
3. **MEDIUM**: Documented bundled Story 12-2 files in File List section
4. **LOW**: Removed redundant `re.IGNORECASE` flag (text already lowercased), added clarifying comment
5. **LOW**: Added negative test `test_infer_archetypes_apply_skips_low_confidence` to verify `--apply` doesn't modify files when confidence < threshold
