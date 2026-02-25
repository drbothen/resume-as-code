---
title: 'Configurable Team Size Label for Position Scope'
slug: 'configurable-team-size-label'
created: '2026-02-25'
status: 'ready-for-dev'
stepsCompleted: [1, 2, 3, 4]
tech_stack: ['Python 3.10+', 'Pydantic v2', 'Click 8.1', 'Jinja2', 'ruamel.yaml', 'WeasyPrint']
files_to_modify:
  - 'src/resume_as_code/models/scope.py'
  - 'src/resume_as_code/services/position_service.py'
  - 'src/resume_as_code/schemas/positions.schema.json'
  - 'src/resume_as_code/commands/new.py'
  - 'src/resume_as_code/templates/cto.css'
  - 'tests/unit/test_position_scope.py'
  - 'tests/integration/test_template_rendering.py'
  - 'docs/data-model.md'
  - 'website/docs/data-model/position.md'
  - 'CLAUDE.md'
  - '_bmad-output/implementation-artifacts/6-16-enhanced-scope-indicators.md'
  - '_bmad-output/implementation-artifacts/7-2-unified-scope-model.md'
  - '_bmad-output/implementation-artifacts/6-17-cto-resume-template.md'
  - '_bmad-output/implementation-artifacts/6-4-executive-resume-template.md'
  - '_bmad-output/planning-artifacts/epics/fr-coverage-map-update.md'
code_patterns:
  - 'Pydantic v2: ConfigDict(extra="forbid"), Field(default=None, description="...")'
  - 'CLI: Click @click.option with --scope-{field} naming'
  - '_build_position_scope() takes individual kwargs, returns Scope | None'
  - 'JSON schema is static file, must be manually updated to match Pydantic model'
  - 'format_scope_line() is a module-level function, not a method'
test_patterns:
  - 'Unit tests: tests/unit/test_position_scope.py — class-based, pytest'
  - 'Integration tests: tests/integration/test_template_rendering.py — template rendering'
  - 'Naming: test_{function}_{scenario}_{expected}'
  - 'Scope tests use Position + Scope fixtures, call format_scope_line() directly'
github_issue: 6
triggers_release: true
adversarial_review: completed
findings_remediated: [F1, F2, F3, F4, F5, F6, F7, F8, F9, F10, F11, F12]
---

# Tech-Spec: Configurable Team Size Label for Position Scope

**Created:** 2026-02-25
**GitHub Issue:** #6
**Closes:** #6
**Adversarial Review:** Completed — 12 findings remediated

## Overview

### Problem Statement

The `format_scope_line()` function in `position_service.py` hardcodes `"engineers"` as the label for the `team_size` scope field. When a non-engineering position (e.g., bank teller supervisor, retail manager, sales director) has `scope.team_size` defined, the rendered resume incorrectly displays "X+ engineers" regardless of the actual role or industry.

### Solution

Add an optional `team_label: str | None` field to the `Scope` Pydantic model. When `format_scope_line()` renders the team size, it uses `scope.team_label or "team members"` — giving users per-position control with a safe, industry-neutral default. This also triggers a new release (PATCH bump to 2.0.3).

### Scope

**In Scope:**

- Scope model: add `team_label` field
- `format_scope_line()`: use configurable label instead of hardcoded "engineers"
- CLI: `--scope-team-label` flag and interactive prompt
- JSON schema: add `team_label` to Scope definition
- Tests: update assertions across unit and integration test files
- Spec/architecture docs: update implementation artifact files
- User-facing docs: update data-model.md, website docs, CLAUDE.md
- Template CSS comments: update format examples
- Release: version bump and changelog

**Out of Scope:**

- Schema version migration (field is optional, fully backward compatible)
- Title-based inference / magic role detection
- Template structural changes (templates already consume pre-formatted `scope_line` string)
- Changes to `content_curator.py` or `archetype_inference_service.py` (use "engineers" in content analysis, not scope rendering)

## Context for Development

### Codebase Patterns

- Pydantic v2 models with `model_config = ConfigDict(extra="forbid")`
- Optional fields use `field: str | None = Field(default=None, description="...")`
- Business logic lives in `services/`, never in `commands/`
- CLI flags use Click `@click.option` with explicit help text
- All YAML fields use snake_case
- Tests follow `test_{function}_{scenario}_{expected}` naming
- JSON schema is a static file manually kept in sync with Pydantic models
- Never use `print()` — use Rich console from `utils/console.py`
- Type hints required on all public functions

### Files to Reference

| File | Purpose |
| ---- | ------- |
| `src/resume_as_code/models/scope.py` | Scope Pydantic model — add `team_label` field after `team_size` (line 35) |
| `src/resume_as_code/services/position_service.py` | `format_scope_line()` — fix hardcoded `"engineers"` (line 47), update docstring (line 32) |
| `src/resume_as_code/schemas/positions.schema.json` | Static JSON schema — add `team_label` to Scope `$defs` (after line 33) |
| `src/resume_as_code/commands/new.py` | CLI — add `--scope-team-label` option (after line 695), interactive prompt (after line 870), update `_build_position_scope()` (line 1065) |
| `src/resume_as_code/templates/cto.css` | CSS comment — update format example (line 34) |
| `tests/unit/test_position_scope.py` | Unit tests — update 12 `"engineers"` assertions (lines 131, 167, 207, 247, 249, 287, 321, 434, 445, 547, 587), add new tests |
| `tests/integration/test_template_rendering.py` | Integration tests — update 8 scope_line references (lines 126, 145, 305, 319, 881, 891, 1022, 1242) |
| `docs/data-model.md` | User docs — add `team_label` to scope YAML example (lines 146-154 is a YAML block, NOT a table) |
| `website/docs/data-model/position.md` | Website docs — add `team_label` to schema (lines 22-29), example (line 59), and scope table (lines 97-105). Note: file uses `pl` but model uses `pl_responsibility` (pre-existing inconsistency F9, not in scope) |
| `CLAUDE.md` | CLI reference — add `--scope-team-label` to scope flags table (line 534) and example (line 549) |
| `_bmad-output/implementation-artifacts/6-16-enhanced-scope-indicators.md` | Story spec — update scope fields list and format examples |
| `_bmad-output/implementation-artifacts/7-2-unified-scope-model.md` | Story spec — update unified model definition |
| `_bmad-output/implementation-artifacts/6-17-cto-resume-template.md` | Story spec — update CTO scope rendering example |
| `_bmad-output/implementation-artifacts/6-4-executive-resume-template.md` | Story spec — update executive scope rendering example |
| `_bmad-output/planning-artifacts/epics/fr-coverage-map-update.md` | Epic doc — update scope format examples (lines 399, 446, 468, 524) |

### Technical Decisions

- **Default label**: `"team members"` — industry-neutral, professional, works for any role
- **Field type**: `str | None` — consistent with other optional Scope fields
- **No migration needed**: New field is optional with `None` default; existing YAML files remain valid
- **Formatting logic change**: Single line change in `format_scope_line()` from hardcoded string to dynamic lookup
- **Release type**: `fix` (bug fix) → PATCH bump → `2.0.3`. Rationale: the tool is industry-agnostic; hardcoding "engineers" was a defect, not a feature. Users who want "engineers" can now set it explicitly, which is better than the accidental default. (See Adversarial Finding F12 disposition below.)
- **`content_curator.py:802`** regex for `engineers` is content analysis, NOT scope rendering — left as-is
- **`archetype_inference_service.py:158`** uses "engineers" in leadership archetype text — general content, left as-is

## Implementation Plan

### Tasks

Tasks are ordered by dependency — models first, then services, CLI, tests, docs.

- [ ] **Task 1: Add `team_label` field to Scope model**
  - File: `src/resume_as_code/models/scope.py`
  - Action: Add new field after `team_size` (after line 35):
    ```python
    team_label: str | None = Field(
        default=None,
        description="Label for team_size display, e.g., 'engineers', 'tellers'. Defaults to 'team members'.",
    )
    ```
  - Notes: Follows existing pattern. `extra="forbid"` means unknown YAML fields will still error — but `team_label` is now a known field.

- [ ] **Task 2: Fix `format_scope_line()` to use configurable label**
  - File: `src/resume_as_code/services/position_service.py`
  - Action 1: Replace line 47:
    ```python
    # Before:
    parts.append(f"{scope.team_size}+ engineers")
    # After:
    label = scope.team_label or "team members"
    parts.append(f"{scope.team_size}+ {label}")
    ```
  - Action 2: Update docstring at line 32:
    ```python
    # Before:
    Formatted scope line (e.g., "$100M P&L | $500M revenue | 200+ engineers")
    # After:
    Formatted scope line (e.g., "$100M P&L | $500M revenue | 200+ team members")
    ```
  - **F2 remediation**: If `team_label` is set but `team_size` is not, the label is silently ignored (team_size block not entered). This is correct behavior — `team_label` only affects formatting when `team_size` is present. Add a test to confirm this (see Task 6).

- [ ] **Task 3: Update JSON schema**
  - File: `src/resume_as_code/schemas/positions.schema.json`
  - Action: Add `team_label` property to the `Scope` `$defs` object, after the `team_size` property (after line 33):
    ```json
    "team_label": {
      "anyOf": [
        {
          "type": "string",
          "minLength": 1
        },
        {
          "type": "null"
        }
      ],
      "default": null,
      "description": "Label for team_size display, e.g., 'engineers', 'tellers'. Defaults to 'team members'.",
      "title": "Team Label"
    },
    ```
  - **F3 remediation**: Add `minLength: 1` to the JSON schema string type to prevent empty string `""` at the schema validation level. The Pydantic model does not need a validator because empty string from CLI is converted to `None` via `or None` pattern, and direct YAML with `team_label: ""` is caught by schema validation.

- [ ] **Task 4: Add `--scope-team-label` CLI flag**
  - File: `src/resume_as_code/commands/new.py`
  - Action 1: Add Click option after `--scope-team-size` (after line 695):
    ```python
    @click.option("--scope-team-label", help="Label for team size (e.g., 'engineers', 'tellers', default: 'team members')")
    ```
  - Action 2: Add `scope_team_label: str | None` parameter to `new_position()` function signature (after line 714):
    ```python
    scope_team_label: str | None,
    ```
  - Action 3: Pass `team_label` to `_build_position_scope()` in non-interactive mode (line 775-783):
    ```python
    scope = _build_position_scope(
        revenue=scope_revenue,
        team_size=scope_team_size,
        team_label=scope_team_label,
        direct_reports=scope_direct_reports,
        budget=scope_budget,
        pl=scope_pl,
        geography=scope_geography,
        customers=scope_customers,
    )
    ```
  - Action 4: Add interactive prompt after team size prompt (after line 870):
    ```python
    scope_team_label_input: str = click.prompt(
        "Team label (e.g., engineers, tellers, default: team members)", default=""
    )
    ```
  - Action 5: Pass `team_label` in interactive `_build_position_scope()` call (line 878-886):
    ```python
    scope = _build_position_scope(
        revenue=scope_revenue_input or None,
        team_size=int(scope_team_input) if scope_team_input else None,
        team_label=scope_team_label_input or None,
        direct_reports=int(scope_direct_input) if scope_direct_input else None,
        budget=scope_budget_input or None,
        pl=scope_pl_input or None,
        geography=scope_geo_input or None,
        customers=scope_customers_input or None,
    )
    ```
  - Action 6: Update `_build_position_scope()` helper (line 1065-1089).
    **F5/F8 remediation**: Add `team_label` with a default value of `None` so existing callers (including tests) don't break:
    ```python
    def _build_position_scope(
        revenue: str | None,
        team_size: int | None,
        direct_reports: int | None,
        budget: str | None,
        pl: str | None,
        geography: str | None,
        customers: str | None = None,
        team_label: str | None = None,
    ) -> PositionScope | None:
        """Build PositionScope from individual scope flags.

        Returns None if no scope fields are populated.
        """
        if not any([revenue, team_size, team_label, direct_reports, budget, pl, geography, customers]):
            return None

        return PositionScope(
            revenue=revenue,
            team_size=team_size,
            team_label=team_label,
            direct_reports=direct_reports,
            budget=budget,
            pl_responsibility=pl,
            geography=geography,
            customers=customers,
        )
    ```
    **IMPORTANT**: `team_label` is placed at the END with `= None` default to maintain backward compatibility with existing callers that pass positional args. The two call sites in `new_position()` (non-interactive and interactive) pass it as a keyword argument: `team_label=scope_team_label`.

- [ ] **Task 5: Update CSS comment**
  - File: `src/resume_as_code/templates/cto.css`
  - Action: Update line 34:
    ```css
    /* Before: */
    * Format: "$500M revenue | 200+ engineers | $50M technology budget | Global"
    /* After: */
    * Format: "$500M revenue | 200+ team members | $50M technology budget | Global"
    ```

- [ ] **Task 6: Update unit tests**
  - File: `tests/unit/test_position_scope.py`
  - Action 1: Update existing assertions that reference `"engineers"` to `"team members"`:
    - Line 131: `assert "200+ engineers"` → `assert "200+ team members"`
    - Line 167: `assert "50+ engineers"` → `assert "50+ team members"`
    - Line 207: `assert result == "30+ engineers"` → `assert result == "30+ team members"`
    - Line 247: `scope_line="...200+ engineers"` → `scope_line="...200+ team members"` (constructor data)
    - **F7 remediation** — Line 249: `assert item.scope_line == "...200+ engineers"` → `assert item.scope_line == "...200+ team members"` (the actual assertion)
    - Line 287: `assert "200+ engineers"` → `assert "200+ team members"`
    - Line 321: `assert "200+ engineers"` → `assert "200+ team members"`
    - Line 434: `scope_line="...200+ engineers"` → `scope_line="...200+ team members"` (constructor data)
    - Line 445: `assert "200+ engineers"` → `assert "200+ team members"` (assertion on rendered HTML)
    - Line 547: `assert "200+ engineers"` → `assert "200+ team members"`
    - Line 587: `assert "50+ engineers"` → `assert "50+ team members"`
  - Action 2: Update `test_all_fields_optional` (line 40) to also assert `team_label`:
    ```python
    assert scope.team_label is None
    ```
  - Action 3: Add new tests to `TestUnifiedScopeModel` class:
    ```python
    def test_team_label_field(self) -> None:
        """Test scope accepts team_label field."""
        scope = Scope(team_size=200, team_label="engineers")
        assert scope.team_label == "engineers"
        assert scope.team_size == 200

    def test_team_label_defaults_to_none(self) -> None:
        """Test team_label defaults to None."""
        scope = Scope(team_size=50)
        assert scope.team_label is None
    ```
  - Action 4: Add new tests to `TestFormatScopeLine` class:
    ```python
    def test_format_scope_line_default_team_label(self) -> None:
        """Test team_size renders with 'team members' when no team_label set."""
        position = Position(
            id="pos-test",
            employer="Example Bank",
            title="Lead Teller Supervisor",
            start_date="2020-01",
            scope=Scope(team_size=4),
        )
        result = format_scope_line(position)
        assert result == "4+ team members"

    def test_format_scope_line_custom_team_label(self) -> None:
        """Test team_size renders with custom team_label."""
        position = Position(
            id="pos-test",
            employer="TechCorp",
            title="CTO",
            start_date="2020-01",
            scope=Scope(team_size=200, team_label="engineers"),
        )
        result = format_scope_line(position)
        assert result == "200+ engineers"

    def test_format_scope_line_custom_team_label_with_other_fields(self) -> None:
        """Test custom team_label integrates with other scope fields."""
        position = Position(
            id="pos-test",
            employer="Retail Co",
            title="Store Manager",
            start_date="2020-01",
            scope=Scope(
                team_size=25,
                team_label="associates",
                revenue="$5M",
            ),
        )
        result = format_scope_line(position)
        assert result is not None
        assert "25+ associates" in result
        assert "$5M revenue" in result

    def test_format_scope_line_team_label_without_team_size_ignored(self) -> None:
        """F2 remediation: team_label without team_size is silently ignored."""
        position = Position(
            id="pos-test",
            employer="Test Corp",
            title="Manager",
            start_date="2020-01",
            scope=Scope(team_label="analysts", revenue="$10M"),
        )
        result = format_scope_line(position)
        assert result == "$10M revenue"
        assert "analysts" not in result
    ```
  - Action 5: Add new test to `TestPositionCommandScope` class:
    ```python
    def test_build_position_scope_with_team_label(self) -> None:
        """Test _build_position_scope passes team_label through."""
        from resume_as_code.commands.new import _build_position_scope

        scope = _build_position_scope(
            revenue=None,
            team_size=50,
            direct_reports=None,
            budget=None,
            pl=None,
            geography=None,
            team_label="analysts",
        )

        assert scope is not None
        assert scope.team_size == 50
        assert scope.team_label == "analysts"

    def test_build_position_scope_existing_callers_unbroken(self) -> None:
        """F5/F8 remediation: existing callers without team_label still work."""
        from resume_as_code.commands.new import _build_position_scope

        scope = _build_position_scope(
            revenue="$500M",
            team_size=200,
            direct_reports=15,
            budget="$50M",
            pl="$100M",
            geography="Global",
        )

        assert scope is not None
        assert scope.team_label is None
        assert scope.team_size == 200
    ```

- [ ] **Task 7: Update integration tests**
  - File: `tests/integration/test_template_rendering.py`
  - **F1 remediation**: Include lines 145 and 319 in the update list — these ARE scope_line assertions rendered in HTML, not bullet content.
  - Action: Update ALL scope_line references containing `"engineers"` in scope context:
    - Line 126: `scope_line="$50M ARR revenue | 80+ engineers | $10M budget"` → `scope_line="$50M ARR revenue | 80+ team members | $10M budget"`
    - **Line 145**: `assert "80+ engineers" in html` → `assert "80+ team members" in html` **(F1 fix)**
    - Line 305: `scope_line="$100M ARR revenue | 25+ engineers | $5M budget"` → `scope_line="$100M ARR revenue | 25+ team members | $5M budget"`
    - **Line 319**: `assert "25+ engineers" in html` → `assert "25+ team members" in html` **(F1 fix)**
    - Line 881: `scope_line="$10M budget | 50+ engineers"` → `scope_line="$10M budget | 50+ team members"`
    - Line 891: `scope_line="$5M budget | 25 engineers"` → `scope_line="$5M budget | 25 team members"`
    - Line 1022: `scope_line="$50M budget | 100+ engineers"` → `scope_line="$50M budget | 100+ team members"`
    - Line 1242: `scope_line="$100M ARR | 200 engineers | $25M budget"` → `scope_line="$100M ARR | 200 team members | $25M budget"`
  - Lines that stay as-is (bullet/metric content, NOT scope labels): 35, 130, 351, 363, 480, 498, 1284

- [ ] **Task 8: Update user-facing documentation**
  - File 1: `docs/data-model.md`
    - **F10 remediation**: Lines 146-154 are a YAML code block, NOT a markdown table. Do NOT try to add a table row.
    - Action: Add `team_label: "engineers"` to the YAML example scope block (after line 149, the `team_size: 150` line):
      ```yaml
      team_label: "engineers"    # Optional, defaults to "team members"
      ```
  - File 2: `website/docs/data-model/position.md`
    - Action 1: Add `team_label: string` to schema reference (after line 24, `team_size` line):
      ```yaml
      team_label: string  # Custom label for team size (default: "team members")
      ```
    - Action 2: Add `team_label: "engineers"` to executive example (after line 59, `team_size` line)
    - Action 3: Add `team_label` row to scope indicators table (after line 100, `team_size` row):
      ```
      | `team_label` | Custom label for team size | "engineers" |
      ```
    - **F9 note**: This file uses `pl` in examples but the model uses `pl_responsibility`. This is a pre-existing inconsistency, NOT introduced by this spec. Out of scope — log as separate tech debt if desired.
  - File 3: `CLAUDE.md`
    - Action 1: Add to scope flags table (after line 534, `--scope-team-size` row):
      ```
      | `--scope-team-label` | Label for team size (e.g., 'engineers', 'tellers') |
      ```
    - Action 2: Add `--scope-team-label "engineers"` to the example block (after line 549, `--scope-team-size` line)

- [ ] **Task 9: Update implementation artifact specs**
  - File 1: `_bmad-output/implementation-artifacts/6-16-enhanced-scope-indicators.md`
    - Action 1: Update scope field list (line 84 area) to include `team_label`
    - Action 2: Update format example at line 38 from `"200+ engineers"` to `"200+ team members"`
    - Action 3: Update code snippet at line 157 to include `team_label`:
      ```python
      team_label: str | None = None  # Custom label for team_size (default: "team members")
      ```
    - Action 4: Update format_scope_line snippet at line 188 from `"engineers"` to use `team_label or "team members"`
  - File 2: `_bmad-output/implementation-artifacts/7-2-unified-scope-model.md`
    - Action 1: Add `team_label` to unified model definition (after line 105, `team_size` field):
      ```python
      team_label: str | None = Field(default=None, description="Custom label for team_size display")
      ```
    - Action 2: Update field mapping table at line 172 to add `team_label` row
  - File 3: `_bmad-output/implementation-artifacts/6-17-cto-resume-template.md`
    - Action: Update scope rendering example at line 42 from `"200+ engineers"` to `"200+ team members"`
  - File 4: `_bmad-output/implementation-artifacts/6-4-executive-resume-template.md`
    - Action: Update scope rendering example at line 37 from `"Led team of 15 engineers"` to `"Led team of 15 team members"`
  - **F4 remediation** — File 5: `_bmad-output/planning-artifacts/epics/fr-coverage-map-update.md`
    - Action 1: Update line 399 from `"200+ engineers"` to `"200+ team members"`
    - Action 2: Update line 446 to include `team_label` in model snippet
    - Action 3: Update line 468 from `"engineers"` to `team_label or "team members"`
    - Action 4: Update line 524 from `"200+ engineers"` to `"200+ team members"`
    - Lines 38 and 80 stay as-is (bullet content about "building engineering org", not scope labels)

- [ ] **Task 10: Run validation suite**
  - Action 1: Run `uv run ruff check src tests --fix` — lint and auto-fix
  - Action 2: Run `uv run ruff format src tests` — format
  - Action 3: Run `uv run mypy src --strict` — type check with zero errors
  - Action 4: Run `uv run pytest` — all tests pass
  - Action 5: Run `uv run resume validate` — validate all resources

- [ ] **Task 11: Release preparation**
  - Action 1: Commit all changes with message: `fix(scope): make team_size label configurable instead of hardcoded "engineers"`
  - Action 2: Include `Closes: #6` in commit footer
  - Action 3: Trigger Prepare-Release workflow to bump version to 2.0.3

### Acceptance Criteria

- [ ] **AC 1:** Given a position with `scope.team_size: 4` and no `team_label`, when `format_scope_line()` is called, then the output contains `"4+ team members"` (not `"4+ engineers"`).

- [ ] **AC 2:** Given a position with `scope.team_size: 200` and `scope.team_label: "engineers"`, when `format_scope_line()` is called, then the output contains `"200+ engineers"`.

- [ ] **AC 3:** Given a position with `scope.team_size: 25` and `scope.team_label: "tellers"`, when `format_scope_line()` is called, then the output contains `"25+ tellers"`.

- [ ] **AC 4:** Given a position created with `--scope-team-size 50 --scope-team-label "analysts"`, when the position is saved and its scope line formatted, then the output contains `"50+ analysts"`.

- [ ] **AC 5:** Given an existing `positions.yaml` with `team_size` but no `team_label` field, when the file is loaded, then no validation error occurs (backward compatible).

- [ ] **AC 6:** Given the CLI `resume new position` command in interactive mode, when the user enters scope indicators, then they are prompted for "Team label" after "Team size".

- [ ] **AC 7:** Given the JSON schema `positions.schema.json`, when validated, then it includes the `team_label` field in the Scope definition with type `string | null` and default `null`.

- [ ] **AC 8:** Given all existing tests are updated, when `uv run pytest` is executed, then all tests pass with zero failures.

- [ ] **AC 9:** Given the codebase after all changes, when `uv run mypy src --strict` is executed, then it reports zero type errors.

- [ ] **AC 10 (F2):** Given a Scope with `team_label: "analysts"` but NO `team_size`, when `format_scope_line()` is called, then the label is silently ignored and does not appear in the output.

- [ ] **AC 11 (F3):** Given the JSON schema, when a position is validated with `team_label: ""` (empty string), then schema validation rejects it (`minLength: 1`).

- [ ] **AC 12 (F5/F8):** Given existing code that calls `_build_position_scope()` without a `team_label` argument, when the code runs, then it works without error (backward compatible default).

## Additional Context

### Dependencies

- No new dependencies required
- Release process per RELEASING.md (Prepare-Release workflow recommended)
- Current version: 2.0.2 → target: 2.0.3

### Testing Strategy

- **Unit tests** (`tests/unit/test_position_scope.py`):
  - Update 12 existing assertions from `"engineers"` to `"team members"` (including line 249 assertion, F7)
  - Update `test_all_fields_optional` to assert `team_label is None`
  - Add `test_team_label_field` — verifies Scope model accepts the field
  - Add `test_team_label_defaults_to_none` — verifies None default
  - Add `test_format_scope_line_default_team_label` — verifies `"team members"` default rendering
  - Add `test_format_scope_line_custom_team_label` — verifies custom label rendering
  - Add `test_format_scope_line_custom_team_label_with_other_fields` — verifies label integrates with other scope fields
  - Add `test_format_scope_line_team_label_without_team_size_ignored` — F2 edge case
  - Add `test_build_position_scope_with_team_label` — verifies CLI helper passes label through
  - Add `test_build_position_scope_existing_callers_unbroken` — F5/F8 backward compat
- **Integration tests** (`tests/integration/test_template_rendering.py`):
  - Update 8 scope_line references from `"engineers"` to `"team members"` (including F1 lines 145, 319)
- **Manual testing**:
  - Create a position with custom `team_label` via CLI and verify rendered scope line
  - Build a resume with the test data to verify end-to-end rendering

### Adversarial Review Findings Disposition

| ID | Severity | Finding | Disposition |
|----|----------|---------|-------------|
| F1 | High | Integration test lines 145, 319 are scope assertions, not bullet content | **Fixed**: Added to Task 7 update list |
| F2 | Medium | `team_label` without `team_size` creates orphaned field | **Fixed**: Documented as intentional (silently ignored), added test in Task 6 and AC 10 |
| F3 | Medium | No validation on empty/whitespace `team_label` | **Fixed**: Added `minLength: 1` to JSON schema (Task 3), CLI uses `or None` to convert empty to None |
| F4 | Medium | `fr-coverage-map-update.md` has 4 scope "engineers" examples | **Fixed**: Added as File 5 in Task 9 |
| F5 | Low | Existing `_build_position_scope` callers break without default | **Fixed**: `team_label` placed at end with `= None` default in Task 4 |
| F6 | Low | "+" suffix + custom label awkward phrasing risk | **Accepted**: User-input quality issue, not a code concern. The "+" suffix works for all common labels. |
| F7 | Low | Line 247 is constructor data, line 249 is the assertion | **Fixed**: Both lines explicitly listed in Task 6 |
| F8 | Medium | `team_label` needs default in `_build_position_scope` | **Fixed**: Combined with F5 — `team_label` at end with `= None` |
| F9 | Low | Website docs use `pl` but model uses `pl_responsibility` | **Noted**: Pre-existing inconsistency, not introduced by this spec. Out of scope. |
| F10 | Low | `docs/data-model.md` has YAML block, not a table | **Fixed**: Task 8 instructions corrected to add to YAML block |
| F11 | Low | Proposed test doesn't exercise `customers` param | **Fixed**: Test uses keyword arg; added `test_build_position_scope_existing_callers_unbroken` for full backward compat |
| F12 | Medium | Default change is behavioral break classified as PATCH | **Accepted (Option 3)**: Tool is industry-agnostic; hardcoding "engineers" was a defect. PATCH is justified. Users who want "engineers" can now set it explicitly. |

### Notes

- **Intentional behavior change**: Existing positions with `team_size` but no `team_label` will render with `"team members"` instead of `"engineers"`. This is the bug fix — the old behavior was incorrect for an industry-agnostic tool.
- **The `+` suffix** on team_size (e.g., "200+ team members") is retained as-is.
- **`content_curator.py`** and **`archetype_inference_service.py`** use "engineers" in content analysis and archetype text contexts unrelated to scope rendering — these are NOT bugs and should not be changed.
- **No schema_version bump** needed: the new `team_label` field is optional with a `None` default. Existing YAML files without the field will load without error. Pydantic's `extra="forbid"` only rejects *unknown* fields, and `team_label` is now a known field.
- **Risk**: Low. Change is isolated to a single formatting function with comprehensive test coverage. The model change is backward compatible. The `_build_position_scope()` signature change is backward compatible via default parameter.
- **Pre-existing issue (F9)**: `website/docs/data-model/position.md` uses `pl` in examples but the model field is `pl_responsibility`. Consider logging as separate tech debt.
