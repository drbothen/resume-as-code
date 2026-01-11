# Story 3.2: Actionable Validation Feedback

Status: completed

## Story

As a **user who made a mistake**,
I want **clear, specific error messages that tell me how to fix the problem**,
So that **I can correct issues without guessing**.

## Acceptance Criteria

1. **Given** a Work Unit is missing a required field
   **When** validation fails
   **Then** the error message includes the field path (e.g., `problem.statement`)
   **And** the message states "Missing required field"
   **And** a suggestion is provided (e.g., "Add a problem statement describing the challenge")

2. **Given** a Work Unit has an invalid field type
   **When** validation fails
   **Then** the error message includes what was expected vs what was found
   **And** example of correct format is shown

3. **Given** a Work Unit has an invalid enum value (e.g., `confidence: super-high`)
   **When** validation fails
   **Then** the error lists valid options: `high`, `medium`, `low`

4. **Given** multiple validation errors exist in one file
   **When** validation runs
   **Then** all errors are reported (not just the first one)
   **And** errors are grouped by file

5. **Given** validation fails
   **When** Rich output is used (not `--json`)
   **Then** errors are color-coded and formatted for readability
   **And** file paths are clickable in supported terminals

6. **Given** content quality validation is enabled
   **When** I run `resume validate --content-quality`
   **Then** weak action verbs are flagged (managed, handled, helped, worked on, was responsible for)
   **And** missing quantification is warned (outcomes without metrics)
   **And** action verb repetition is flagged (same verb used multiple times)

7. **Given** a Work Unit uses a weak action verb
   **When** content quality validation runs
   **Then** the warning includes strong verb alternatives (orchestrated, spearheaded, championed, transformed)

8. **Given** content density validation is enabled
   **When** I run `resume validate --content-density`
   **Then** warning if bullet character count is outside 100-160 range

## Tasks / Subtasks

- [x] Task 1: Enhance error message mapping (AC: #1, #2, #3)
  - [x] 1.1: Create `utils/validation_messages.py` with error mappings
  - [x] 1.2: Map "required" schema errors to field-specific suggestions
  - [x] 1.3: Map "type" schema errors with expected vs actual
  - [x] 1.4: Map "enum" schema errors with valid options list
  - [x] 1.5: Add contextual suggestions for each Work Unit field

- [x] Task 2: Implement comprehensive error collection (AC: #4)
  - [x] 2.1: Update validator to collect ALL errors per file
  - [x] 2.2: Group errors by file path
  - [x] 2.3: Sort errors by field path for consistency
  - [x] 2.4: Limit to reasonable max errors per file (e.g., 20)

- [x] Task 3: Enhance Rich output formatting (AC: #5)
  - [x] 3.1: Color-code errors (red), warnings (yellow), info (blue)
  - [x] 3.2: Make file paths clickable using Rich's file link syntax
  - [x] 3.3: Add line numbers when available (via ruamel.yaml)
  - [x] 3.4: Use Rich Tree or Panel for grouped errors
  - [x] 3.5: Add icons/symbols for error types

- [x] Task 4: Implement content quality validation (AC: #6, #7)
  - [x] 4.1: Add `--content-quality` flag to validate command
  - [x] 4.2: Create `services/content_validator.py`
  - [x] 4.3: Implement weak verb detection with alternatives
  - [x] 4.4: Implement missing quantification detection
  - [x] 4.5: Implement verb repetition detection
  - [x] 4.6: Define weak verbs list and strong alternatives

- [x] Task 5: Implement content density validation (AC: #8)
  - [x] 5.1: Add `--content-density` flag to validate command
  - [x] 5.2: Implement bullet/action character count validation
  - [x] 5.3: Warn if outside 100-160 character range

- [x] Task 6: Code quality verification
  - [x] 6.1: Run `ruff check src tests --fix`
  - [x] 6.2: Run `ruff format src tests`
  - [x] 6.3: Run `mypy src --strict` with zero errors
  - [x] 6.4: Add unit tests for validation message mapping
  - [x] 6.5: Add unit tests for content quality validation
  - [x] 6.6: Add integration tests for enhanced error output

## Dev Notes

### Architecture Compliance

This story implements FR7 (actionable validation feedback). It enhances the basic validation from Story 3.1 with user-friendly error messages and content quality checks.

**Source:** [epics.md#Story 3.2](_bmad-output/planning-artifacts/epics.md)
**Source:** [Architecture Section 1.4 - Content Strategy](_bmad-output/planning-artifacts/architecture.md)

### Dependencies

This story REQUIRES:
- Story 3.1 (Validate Command) - Base validation infrastructure
- Story 1.2 (Rich Console) - Output formatting utilities

### Weak Action Verbs Reference

Based on resume best practices, these verbs should be flagged with alternatives:

| Weak Verb | Strong Alternatives |
|-----------|---------------------|
| managed | orchestrated, directed, coordinated, oversaw |
| handled | resolved, processed, executed, administered |
| helped | enabled, facilitated, supported, empowered |
| worked on | developed, built, created, implemented |
| was responsible for | owned, led, drove, championed |
| did | executed, delivered, accomplished, achieved |
| made | produced, generated, crafted, designed |
| got | secured, acquired, obtained, earned |
| used | leveraged, utilized, applied, employed |
| assisted | supported, enabled, contributed to, facilitated |

### Validation Message Mapping

**`src/resume_as_code/utils/validation_messages.py`:**

```python
"""Validation error message mappings with suggestions."""

from __future__ import annotations

# Field-specific suggestions for missing required fields
FIELD_SUGGESTIONS: dict[str, str] = {
    "title": "Add a concise title describing your accomplishment (e.g., 'Reduced API latency by 40%')",
    "problem": "Add a problem section describing the challenge you faced",
    "problem.statement": "Describe the challenge or problem you were solving",
    "actions": "List the specific actions you took to solve the problem",
    "outcome": "Add an outcome section describing the results",
    "outcome.result": "Describe what you achieved or the impact of your work",
    "id": "Add a unique ID in format: wu-YYYY-MM-DD-slug",
    "schema_version": "Add schema_version: '1.0.0' at the top of the file",
}

# Type error examples
TYPE_EXAMPLES: dict[str, str] = {
    "string": '"example text"',
    "array": '["item1", "item2"]',
    "object": "key: value",
    "number": "42 or 3.14",
    "boolean": "true or false",
    "integer": "42",
}

# Enum field valid values (for clearer messages)
ENUM_FIELDS: dict[str, list[str]] = {
    "confidence": ["high", "medium", "low"],
    "evidence.type": ["git_repo", "metrics", "document", "artifact", "other"],
}


def get_suggestion_for_field(field_path: str) -> str:
    """Get a helpful suggestion for a missing/invalid field."""
    # Try exact match first
    if field_path in FIELD_SUGGESTIONS:
        return FIELD_SUGGESTIONS[field_path]

    # Try partial match (e.g., "problem.statement" matches "statement")
    for key, suggestion in FIELD_SUGGESTIONS.items():
        if field_path.endswith(key):
            return suggestion

    return "Check the Work Unit schema for the correct format"


def get_type_example(expected_type: str) -> str:
    """Get an example for the expected type."""
    return TYPE_EXAMPLES.get(expected_type, f"a valid {expected_type}")


def get_enum_values(field_path: str) -> list[str] | None:
    """Get valid enum values for a field."""
    for key, values in ENUM_FIELDS.items():
        if field_path.endswith(key):
            return values
    return None
```

### Content Quality Validator

**`src/resume_as_code/services/content_validator.py`:**

```python
"""Content quality validation for Work Units."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any


# Weak verbs with strong alternatives
WEAK_VERBS: dict[str, list[str]] = {
    "managed": ["orchestrated", "directed", "coordinated", "oversaw"],
    "handled": ["resolved", "processed", "executed", "administered"],
    "helped": ["enabled", "facilitated", "supported", "empowered"],
    "worked on": ["developed", "built", "created", "implemented"],
    "was responsible for": ["owned", "led", "drove", "championed"],
    "did": ["executed", "delivered", "accomplished", "achieved"],
    "made": ["produced", "generated", "crafted", "designed"],
    "got": ["secured", "acquired", "obtained", "earned"],
    "used": ["leveraged", "utilized", "applied", "employed"],
    "assisted": ["supported", "enabled", "contributed to", "facilitated"],
}

# Optimal bullet character range
BULLET_CHAR_MIN = 100
BULLET_CHAR_MAX = 160


@dataclass
class ContentWarning:
    """A content quality warning (not an error)."""

    code: str
    message: str
    path: str
    suggestion: str
    severity: str = field(default="warning")  # warning or info


def validate_content_quality(work_unit: dict[str, Any], file_path: str) -> list[ContentWarning]:
    """Validate content quality of a Work Unit.

    Returns warnings (not errors) for content improvements.
    """
    warnings: list[ContentWarning] = []

    # Check actions for weak verbs
    actions = work_unit.get("actions", [])
    verb_usage: dict[str, int] = {}

    for i, action in enumerate(actions):
        if not isinstance(action, str):
            continue

        # Check for weak verbs
        action_lower = action.lower()
        for weak_verb, alternatives in WEAK_VERBS.items():
            if re.search(rf"\b{re.escape(weak_verb)}\b", action_lower):
                warnings.append(
                    ContentWarning(
                        code="WEAK_ACTION_VERB",
                        message=f"Action {i + 1} uses weak verb '{weak_verb}'",
                        path=f"{file_path}:actions[{i}]",
                        suggestion=f"Consider stronger verbs: {', '.join(alternatives[:3])}",
                    )
                )

        # Track verb usage for repetition (first word of action)
        words = action.split()
        if words:
            first_word = words[0].lower()
            verb_usage[first_word] = verb_usage.get(first_word, 0) + 1

    # Check for verb repetition
    for verb, count in verb_usage.items():
        if count > 1 and verb not in ("the", "a", "an", "to", "and", "or", "for", "with", "of"):
            warnings.append(
                ContentWarning(
                    code="VERB_REPETITION",
                    message=f"Verb '{verb}' used {count} times in actions",
                    path=f"{file_path}:actions",
                    suggestion="Vary your action verbs for stronger impact",
                )
            )

    # Check outcome for quantification
    outcome = work_unit.get("outcome", {})
    if isinstance(outcome, dict):
        result = outcome.get("result", "")
        if result and isinstance(result, str) and not _has_quantification(result):
            warnings.append(
                ContentWarning(
                    code="MISSING_QUANTIFICATION",
                    message="Outcome result lacks quantification",
                    path=f"{file_path}:outcome.result",
                    suggestion="Add metrics (%, $, time saved, etc.) to strengthen impact",
                    severity="info",
                )
            )

    return warnings


def validate_content_density(work_unit: dict[str, Any], file_path: str) -> list[ContentWarning]:
    """Validate content density (character counts, etc.)."""
    warnings: list[ContentWarning] = []

    actions = work_unit.get("actions", [])
    for i, action in enumerate(actions):
        if not isinstance(action, str):
            continue

        char_count = len(action)
        if char_count < BULLET_CHAR_MIN:
            warnings.append(
                ContentWarning(
                    code="BULLET_TOO_SHORT",
                    message=f"Action {i + 1} is {char_count} chars (min: {BULLET_CHAR_MIN})",
                    path=f"{file_path}:actions[{i}]",
                    suggestion="Expand with more detail about impact or method",
                )
            )
        elif char_count > BULLET_CHAR_MAX:
            warnings.append(
                ContentWarning(
                    code="BULLET_TOO_LONG",
                    message=f"Action {i + 1} is {char_count} chars (max: {BULLET_CHAR_MAX})",
                    path=f"{file_path}:actions[{i}]",
                    suggestion="Consider splitting into multiple focused bullets",
                )
            )

    return warnings


def _has_quantification(text: str) -> bool:
    """Check if text contains quantification.

    Looks for:
    - Percentages (40%)
    - Currency ($50,000)
    - Multipliers (3x)
    - Time units (30 min, 5 hours)
    - Abbreviations (50K, 2M)
    - Impact words with metrics (reduced by X, improved X%)
    """
    patterns = [
        r"\d+%",  # Percentages
        r"\$[\d,]+",  # Currency
        r"\d+x",  # Multipliers
        r"\d+\s*(?:ms|secs?|mins?|hours?|days?)",  # Time (with plurals)
        r"\d+[KMB]",  # Abbreviations
        # Impact words must be near numbers/metrics to count as quantification
        r"(?:reduced|increased|improved|saved|generated)\s+(?:by\s+)?\d",
        # Or just any number that looks metric-like
        r"\b\d+(?:\.\d+)?\s*(?:%|x|\$|K|M|B|ms|sec|min|hour|day)\b",
    ]
    return any(re.search(pattern, text, re.IGNORECASE) for pattern in patterns)
```

### Enhanced Validate Command

**Update `src/resume_as_code/commands/validate.py`:**

```python
@click.command("validate")
@click.argument("path", type=click.Path(exists=True, path_type=Path), required=False)
@click.option(
    "--content-quality",
    is_flag=True,
    help="Check content quality (weak verbs, quantification)",
)
@click.option(
    "--content-density",
    is_flag=True,
    help="Check content density (bullet length)",
)
@click.pass_context
@handle_errors
def validate_command(
    ctx: click.Context,
    path: Path | None,
    content_quality: bool,
    content_density: bool,
) -> None:
    """Validate Work Units against schema and content guidelines."""
    # ... existing validation ...

    # Content quality checks (warnings, not errors)
    if content_quality or content_density:
        for result in summary.results:
            if result.valid:
                data = _load_yaml(result.file_path)
                if content_quality:
                    warnings = validate_content_quality(data, str(result.file_path))
                    _display_warnings(warnings)
                if content_density:
                    warnings = validate_content_density(data, str(result.file_path))
                    _display_warnings(warnings)
```

### Rich Output Formatting

**Update `_output_rich` function:**

```python
from rich.panel import Panel
from rich.tree import Tree


def _output_rich(summary: ValidationSummary) -> None:
    """Output validation results with Rich formatting."""
    for result in summary.results:
        if result.valid:
            console.print(f"[green]✓[/green] {result.file_path}")
        else:
            # Create error tree for this file
            tree = Tree(f"[red]✗[/red] [link=file://{result.file_path}]{result.file_path}[/link]")

            for err in result.errors:
                error_node = tree.add(f"[red]{err.code}[/red]: {err.message}")
                if err.suggestion:
                    error_node.add(f"[dim]💡 {err.suggestion}[/dim]")

            console.print(tree)

    # Summary panel
    console.print()
    if summary.invalid_count == 0:
        console.print(Panel(
            f"[green]✓ All {summary.valid_count} Work Unit(s) passed validation[/green]",
            title="Validation Complete",
            border_style="green",
        ))
    else:
        console.print(Panel(
            f"[red]✗ {summary.invalid_count} of {summary.total_count} Work Unit(s) "
            f"failed validation[/red]",
            title="Validation Failed",
            border_style="red",
        ))
```

### Testing Requirements

**`tests/unit/test_validation_messages.py`:**

```python
"""Tests for validation message mappings."""

from resume_as_code.utils.validation_messages import (
    get_suggestion_for_field,
    get_type_example,
    get_enum_values,
)


class TestFieldSuggestions:
    """Tests for field suggestion lookup."""

    def test_exact_match(self):
        """Should return suggestion for exact field match."""
        assert "title" in get_suggestion_for_field("title").lower()

    def test_nested_field(self):
        """Should return suggestion for nested field."""
        suggestion = get_suggestion_for_field("problem.statement")
        assert "challenge" in suggestion.lower() or "problem" in suggestion.lower()

    def test_unknown_field(self):
        """Should return generic suggestion for unknown fields."""
        suggestion = get_suggestion_for_field("unknown.field")
        assert "schema" in suggestion.lower()


class TestEnumValues:
    """Tests for enum value lookup."""

    def test_confidence_values(self):
        """Should return confidence enum values."""
        values = get_enum_values("confidence")
        assert values == ["high", "medium", "low"]

    def test_evidence_type_values(self):
        """Should return evidence type enum values."""
        values = get_enum_values("evidence.type")
        assert "git_repo" in values
```

**`tests/unit/test_content_validator.py`:**

```python
"""Tests for content quality validation."""

from resume_as_code.services.content_validator import (
    validate_content_quality,
    validate_content_density,
)


class TestContentQuality:
    """Tests for content quality validation."""

    def test_detects_weak_verb(self):
        """Should detect weak action verbs."""
        work_unit = {
            "actions": ["Managed a team of engineers"],
        }
        warnings = validate_content_quality(work_unit, "test.yaml")
        assert any(w.code == "WEAK_ACTION_VERB" for w in warnings)

    def test_suggests_alternatives(self):
        """Should suggest strong verb alternatives."""
        work_unit = {
            "actions": ["Handled customer complaints"],
        }
        warnings = validate_content_quality(work_unit, "test.yaml")
        assert any("resolved" in w.suggestion.lower() for w in warnings)

    def test_detects_verb_repetition(self):
        """Should detect repeated verbs."""
        work_unit = {
            "actions": [
                "Implemented new feature",
                "Implemented another feature",
            ],
        }
        warnings = validate_content_quality(work_unit, "test.yaml")
        assert any(w.code == "VERB_REPETITION" for w in warnings)

    def test_detects_missing_quantification(self):
        """Should warn about missing metrics."""
        work_unit = {
            "outcome": {"result": "Improved system performance"},
        }
        warnings = validate_content_quality(work_unit, "test.yaml")
        assert any(w.code == "MISSING_QUANTIFICATION" for w in warnings)

    def test_accepts_quantified_outcome(self):
        """Should not warn when outcome has metrics."""
        work_unit = {
            "outcome": {"result": "Improved system performance by 40%"},
        }
        warnings = validate_content_quality(work_unit, "test.yaml")
        assert not any(w.code == "MISSING_QUANTIFICATION" for w in warnings)


class TestContentDensity:
    """Tests for content density validation."""

    def test_short_bullet_warning(self):
        """Should warn about too-short bullets."""
        work_unit = {
            "actions": ["Did stuff"],  # Very short
        }
        warnings = validate_content_density(work_unit, "test.yaml")
        assert any(w.code == "BULLET_TOO_SHORT" for w in warnings)

    def test_long_bullet_warning(self):
        """Should warn about too-long bullets."""
        work_unit = {
            "actions": ["x" * 200],  # Very long
        }
        warnings = validate_content_density(work_unit, "test.yaml")
        assert any(w.code == "BULLET_TOO_LONG" for w in warnings)

    def test_optimal_length_no_warning(self):
        """Should not warn for optimal length bullets."""
        work_unit = {
            "actions": ["x" * 130],  # Within 100-160 range
        }
        warnings = validate_content_density(work_unit, "test.yaml")
        assert not any(w.code in ("BULLET_TOO_SHORT", "BULLET_TOO_LONG") for w in warnings)
```

### Verification Commands

```bash
# Test with missing required fields
cat > work-units/wu-missing.yaml << 'EOF'
schema_version: "1.0.0"
id: "wu-2026-01-10-missing"
# Missing title, problem, actions, outcome
EOF

resume validate work-units/wu-missing.yaml
# Should show helpful suggestions for each missing field

# Test with invalid enum
cat > work-units/wu-bad-enum.yaml << 'EOF'
schema_version: "1.0.0"
id: "wu-2026-01-10-enum"
title: "Test"
confidence: super-high
problem:
  statement: "Test"
actions:
  - "Test"
outcome:
  result: "Test"
EOF

resume validate work-units/wu-bad-enum.yaml
# Should show valid enum values

# Test content quality
cat > work-units/wu-weak.yaml << 'EOF'
schema_version: "1.0.0"
id: "wu-2026-01-10-weak"
title: "Test"
problem:
  statement: "Test problem"
actions:
  - "Managed the team"
  - "Handled the issues"
  - "Managed the project"
outcome:
  result: "Things got better"
EOF

resume validate --content-quality work-units/wu-weak.yaml
# Should flag weak verbs and missing quantification

# Test content density
resume validate --content-density work-units/wu-weak.yaml
# Should flag short bullets

# Code quality
ruff check src tests --fix
mypy src --strict
pytest tests/unit/test_validation_messages.py tests/unit/test_content_validator.py -v

# Cleanup
rm work-units/wu-missing.yaml work-units/wu-bad-enum.yaml work-units/wu-weak.yaml
```

### References

- [Source: epics.md#Story 3.2](_bmad-output/planning-artifacts/epics.md)
- [Source: architecture.md#Section 1.4 - Content Strategy](_bmad-output/planning-artifacts/architecture.md)
- [Source: project-context.md](_bmad-output/project-context.md)

## Dev Agent Record

### Agent Model Used

Claude Opus 4.5 (claude-opus-4-5-20251101)

### Debug Log References

- Code review remediation: Fixed time pattern regex, added exclusion words, added edge case tests

### Completion Notes List

- All acceptance criteria implemented and tested
- Code review identified 9 issues, all remediated

### File List

**Created:**
- `src/resume_as_code/services/content_validator.py` - Content quality and density validation
- `src/resume_as_code/utils/validation_messages.py` - Field-specific error message mappings
- `tests/unit/test_content_validator.py` - Unit tests for content validation (34 tests)
- `tests/unit/test_validation_messages.py` - Unit tests for message mappings (19 tests)

**Modified:**
- `src/resume_as_code/commands/validate.py` - Added --content-quality and --content-density flags, Rich Tree/Panel output
- `src/resume_as_code/services/validator.py` - Enhanced error suggestions using validation_messages
- `src/resume_as_code/utils/console.py` - Added json_output() function
- `tests/unit/test_validator.py` - Added tests for contextual suggestions
- `tests/integration/test_validate_command.py` - Added 9 tests for content validation flags

