# Schema & Data Model Refactoring Analysis

**Date:** 2026-01-14
**Analyst:** Mary (Business Analyst Agent)
**Status:** Ready for Story Creation
**Breaking Changes:** Allowed (per stakeholder)

---

## Executive Summary

Deep analysis of the resume-as-code data models reveals 7 key improvement areas. This document provides complete technical specifications for creating implementation stories.

**Key Decisions:**
- JSON schemas are documentation-only → auto-generate from Pydantic
- O*NET integration is desired → wire up API + lookup service
- Backward compatibility NOT required → clean refactoring possible

---

## Table of Contents

1. [JSON Schema Auto-Generation](#1-json-schema-auto-generation)
2. [Unified Scope Model](#2-unified-scope-model)
3. [Standardized Date Types](#3-standardized-date-types)
4. [Skills Registry & O*NET Integration](#4-skills-registry--onet-integration)
5. [Position Reference Integrity](#5-position-reference-integrity)
6. [Evidence Model Enhancement](#6-evidence-model-enhancement)
7. [Config/Data Separation](#7-configdata-separation-optional)

---

## 1. JSON Schema Auto-Generation

### Problem Statement

JSON schemas in `schemas/*.json` are **manually maintained** and have drifted from Pydantic models:

| Missing in JSON Schema | Present in Pydantic |
|------------------------|---------------------|
| `profile` | `ProfileConfig` with 9 fields |
| `certifications` | `list[Certification]` |
| `education` | `list[Education]` |
| `board_roles` | `list[BoardRole]` |
| `publications` | `list[Publication]` |
| `positions_path` | `Path` field |
| `career_highlights` | `list[str]` |
| `skills` config | `SkillsConfig` |

### Solution

Auto-generate JSON schemas from Pydantic models at build time.

### Technical Specification

#### New File: `src/resume_as_code/schemas/generator.py`

```python
"""JSON Schema generator from Pydantic models."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from pydantic import TypeAdapter

from resume_as_code.models.config import ResumeConfig
from resume_as_code.models.position import Position
from resume_as_code.models.work_unit import WorkUnit


SCHEMA_OUTPUT_DIR = Path(__file__).parent.parent.parent.parent / "schemas"

MODELS_TO_EXPORT = {
    "config.schema.json": ResumeConfig,
    "work-unit.schema.json": WorkUnit,
    "position.schema.json": Position,
}


def generate_json_schema(model: type, title: str | None = None) -> dict[str, Any]:
    """Generate JSON Schema from a Pydantic model.

    Args:
        model: Pydantic model class.
        title: Optional title override.

    Returns:
        JSON Schema dictionary.
    """
    adapter = TypeAdapter(model)
    schema = adapter.json_schema(mode="serialization")

    # Add JSON Schema metadata
    schema["$schema"] = "https://json-schema.org/draft/2020-12/schema"
    schema["$id"] = f"https://resume-as-code.dev/schemas/{title or model.__name__.lower()}.json"

    if title:
        schema["title"] = title

    return schema


def generate_all_schemas() -> dict[str, Path]:
    """Generate all JSON schemas and write to files.

    Returns:
        Dict mapping schema name to output path.
    """
    SCHEMA_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    outputs: dict[str, Path] = {}

    for filename, model in MODELS_TO_EXPORT.items():
        title = filename.replace(".schema.json", "").replace("-", " ").title()
        schema = generate_json_schema(model, title)

        output_path = SCHEMA_OUTPUT_DIR / filename
        output_path.write_text(json.dumps(schema, indent=2) + "\n")
        outputs[filename] = output_path

    return outputs


if __name__ == "__main__":
    outputs = generate_all_schemas()
    for name, path in outputs.items():
        print(f"Generated: {path}")
```

#### New CLI Command: `resume schema generate`

Add to `commands/` directory:

```python
"""Schema generation command."""

import click
from rich.console import Console

from resume_as_code.schemas.generator import generate_all_schemas

console = Console()


@click.command("generate")
def schema_generate() -> None:
    """Generate JSON schemas from Pydantic models."""
    console.print("[bold]Generating JSON schemas...[/bold]")

    outputs = generate_all_schemas()

    for name, path in outputs.items():
        console.print(f"  [green]✓[/green] {name} → {path}")

    console.print(f"\n[bold green]Generated {len(outputs)} schemas[/bold green]")
```

#### Pre-commit Hook Addition

Add to `.pre-commit-config.yaml`:

```yaml
  - repo: local
    hooks:
      - id: generate-schemas
        name: Generate JSON Schemas
        entry: uv run python -m resume_as_code.schemas.generator
        language: system
        pass_filenames: false
        files: ^src/resume_as_code/models/.*\.py$
```

### Acceptance Criteria

- [ ] `resume schema generate` command creates all schemas
- [ ] Pre-commit hook regenerates schemas when models change
- [ ] Generated schemas match Pydantic model definitions exactly
- [ ] Existing `schemas/` directory files are overwritten
- [ ] CI validates schemas are up-to-date (diff check)

### Files to Create/Modify

| File | Action |
|------|--------|
| `src/resume_as_code/schemas/__init__.py` | Create |
| `src/resume_as_code/schemas/generator.py` | Create |
| `src/resume_as_code/commands/schema.py` | Create |
| `src/resume_as_code/cli.py` | Add `schema` command group |
| `.pre-commit-config.yaml` | Add hook |
| `schemas/*.json` | Auto-generated (overwrite) |

---

## 2. Unified Scope Model

### Problem Statement

"Scope" appears in THREE places with inconsistent fields:

**WorkUnit.scope (`Scope`):**
```python
budget_managed: str | None
team_size: int | None = Field(ge=0)  # min 0
revenue_influenced: str | None
geographic_reach: str | None
```

**Position.scope (`PositionScope`):**
```python
revenue: str | None              # Different name!
team_size: int | None            # No minimum
direct_reports: int | None       # Unique to Position
budget: str | None               # Different name!
pl_responsibility: str | None    # Unique to Position
geography: str | None            # Different name!
customers: str | None            # Unique to Position
```

**ResumeItem (output):**
```python
scope_budget: str | None
scope_team_size: int | None
scope_revenue: str | None
scope_line: str | None  # Formatted display
```

### Solution

Create a single `UnifiedScope` model used everywhere.

### Technical Specification

#### Replace in `src/resume_as_code/models/scope.py` (new file)

```python
"""Unified scope model for leadership/executive indicators."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class Scope(BaseModel):
    """Scope indicators for positions and work units.

    Captures leadership scale: budget, team, revenue, P&L, geography.
    All fields optional - only populated fields render in scope line.

    Used by:
    - Position.scope: Role-level scope
    - WorkUnit.scope: Achievement-level scope
    """

    model_config = ConfigDict(extra="forbid")

    # Financial
    budget: str | None = Field(
        default=None,
        description="Budget managed, e.g., '$50M'",
        examples=["$50M", "$2.5M annual"],
    )
    revenue: str | None = Field(
        default=None,
        description="Revenue impact/influenced, e.g., '$500M'",
        examples=["$500M", "$12M ARR"],
    )
    pl_responsibility: str | None = Field(
        default=None,
        description="P&L responsibility amount, e.g., '$100M'",
        examples=["$100M", "Full P&L"],
    )

    # Team
    team_size: int | None = Field(
        default=None,
        ge=0,
        description="Total team members (direct + indirect)",
    )
    direct_reports: int | None = Field(
        default=None,
        ge=0,
        description="Number of direct reports",
    )

    # Reach
    geography: str | None = Field(
        default=None,
        description="Geographic reach, e.g., 'Global', 'APAC', '15 countries'",
        examples=["Global", "EMEA", "North America"],
    )
    customers: str | None = Field(
        default=None,
        description="Customer scope, e.g., '500K users', 'Fortune 500'",
        examples=["500K MAU", "Fortune 100", "B2B Enterprise"],
    )

    def format_scope_line(self) -> str | None:
        """Format scope for resume display.

        Returns:
            Formatted string like "$50M budget | 200 engineers | Global"
            or None if no scope fields are set.
        """
        parts: list[str] = []

        if self.pl_responsibility:
            parts.append(f"{self.pl_responsibility} P&L")
        elif self.revenue:
            parts.append(f"{self.revenue} revenue")

        if self.budget:
            parts.append(f"{self.budget} budget")

        if self.team_size:
            label = "engineers" if self.team_size > 10 else "team"
            parts.append(f"{self.team_size} {label}")

        if self.geography:
            parts.append(self.geography)

        return " | ".join(parts) if parts else None

    def is_empty(self) -> bool:
        """Check if all scope fields are None/empty."""
        return all(
            getattr(self, f) is None
            for f in self.model_fields
        )
```

#### Migration: Update WorkUnit

```python
# In work_unit.py - replace Scope class import
from resume_as_code.models.scope import Scope

# Remove old Scope class definition (lines 179-187)

# WorkUnit.scope field stays the same type
scope: Scope | None = None
```

#### Migration: Update Position

```python
# In position.py - replace PositionScope
from resume_as_code.models.scope import Scope

# Remove PositionScope class (lines 17-36)

# Update field type
scope: Scope | None = Field(
    default=None,
    description="Scope indicators for executive positions"
)
```

#### Migration: Update ResumeItem

```python
# In resume.py - simplify scope fields
class ResumeItem(BaseModel):
    # ... existing fields ...

    # Replace individual scope_* fields with single scope object
    scope: Scope | None = None

    @property
    def scope_line(self) -> str | None:
        """Formatted scope line for display."""
        return self.scope.format_scope_line() if self.scope else None
```

### Data Migration

Existing YAML files using old field names need migration:

```yaml
# OLD (positions.yaml)
scope:
  revenue: "$500M"
  budget: "$50M"

# NEW (unchanged - already correct in Position)
scope:
  revenue: "$500M"
  budget: "$50M"

# OLD (work-unit.yaml)
scope:
  budget_managed: "$50M"      # RENAME
  revenue_influenced: "$500M" # RENAME
  geographic_reach: "Global"  # RENAME

# NEW (work-unit.yaml)
scope:
  budget: "$50M"
  revenue: "$500M"
  geography: "Global"
```

#### Migration Script: `scripts/migrate_scope_fields.py`

```python
"""Migrate old scope field names to unified names."""

import re
from pathlib import Path

import yaml

FIELD_RENAMES = {
    "budget_managed": "budget",
    "revenue_influenced": "revenue",
    "geographic_reach": "geography",
}


def migrate_work_unit(path: Path) -> bool:
    """Migrate a single work unit file.

    Returns:
        True if file was modified.
    """
    content = path.read_text()
    modified = False

    for old_name, new_name in FIELD_RENAMES.items():
        if old_name in content:
            content = re.sub(
                rf"(\s+){old_name}:",
                rf"\1{new_name}:",
                content,
            )
            modified = True

    if modified:
        path.write_text(content)

    return modified


def migrate_all(work_units_dir: Path) -> int:
    """Migrate all work unit files.

    Returns:
        Count of files modified.
    """
    count = 0
    for path in work_units_dir.glob("*.yaml"):
        if migrate_work_unit(path):
            print(f"  Migrated: {path.name}")
            count += 1
    return count


if __name__ == "__main__":
    import sys

    work_units_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("work-units")
    count = migrate_all(work_units_dir)
    print(f"\nMigrated {count} files")
```

### Acceptance Criteria

- [ ] Single `Scope` model in `models/scope.py`
- [ ] `Position` uses unified `Scope`
- [ ] `WorkUnit` uses unified `Scope`
- [ ] `ResumeItem` uses unified `Scope`
- [ ] `format_scope_line()` method produces consistent output
- [ ] Migration script updates existing work unit files
- [ ] All tests pass with new model
- [ ] JSON schemas regenerated with unified Scope

### Files to Create/Modify

| File | Action |
|------|--------|
| `src/resume_as_code/models/scope.py` | Create |
| `src/resume_as_code/models/work_unit.py` | Remove old Scope, import new |
| `src/resume_as_code/models/position.py` | Remove PositionScope, import Scope |
| `src/resume_as_code/models/resume.py` | Simplify ResumeItem |
| `scripts/migrate_scope_fields.py` | Create |
| `tests/unit/test_scope.py` | Create |

---

## 3. Standardized Date Types

### Problem Statement

Mixed date representations cause type confusion:

| Model | Field | Type | Format |
|-------|-------|------|--------|
| WorkUnit | time_started | `date` | Python date object |
| Position | start_date | `str` | "YYYY-MM" string |
| Certification | date | `str` | "YYYY-MM" string |
| BoardRole | start_date | `str` | "YYYY-MM" string |
| Education | year | `str` | "YYYY" string |

### Solution

Create reusable annotated types for consistent date handling.

### Technical Specification

#### New File: `src/resume_as_code/models/types.py`

```python
"""Reusable type definitions for Resume as Code models."""

from __future__ import annotations

import re
from datetime import date
from typing import Annotated, Any

from pydantic import BeforeValidator, PlainSerializer


def _parse_year_month(v: Any) -> str | None:
    """Parse various inputs to YYYY-MM format.

    Accepts:
    - None → None
    - date object → "YYYY-MM"
    - "YYYY-MM" → "YYYY-MM"
    - "YYYY-MM-DD" → "YYYY-MM"
    - "YYYY" → "YYYY-01" (assume January)
    """
    if v is None:
        return None

    if isinstance(v, date):
        return v.strftime("%Y-%m")

    v_str = str(v).strip()

    # Already YYYY-MM format
    if re.match(r"^\d{4}-\d{2}$", v_str):
        return v_str

    # YYYY-MM-DD format - truncate
    if re.match(r"^\d{4}-\d{2}-\d{2}$", v_str):
        return v_str[:7]

    # YYYY only - assume January
    if re.match(r"^\d{4}$", v_str):
        return f"{v_str}-01"

    raise ValueError(
        f"Invalid date format: {v_str!r}. "
        "Expected YYYY-MM, YYYY-MM-DD, or YYYY."
    )


def _parse_year(v: Any) -> str | None:
    """Parse various inputs to YYYY format.

    Accepts:
    - None → None
    - date object → "YYYY"
    - "YYYY" → "YYYY"
    - "YYYY-MM" → "YYYY"
    - "YYYY-MM-DD" → "YYYY"
    """
    if v is None:
        return None

    if isinstance(v, date):
        return str(v.year)

    v_str = str(v).strip()

    if re.match(r"^\d{4}", v_str):
        return v_str[:4]

    raise ValueError(
        f"Invalid year format: {v_str!r}. "
        "Expected YYYY or longer date string."
    )


def _serialize_year_month(v: str | None) -> str | None:
    """Serialize YearMonth to string (no-op, already string)."""
    return v


# Annotated types for use in models
YearMonth = Annotated[
    str | None,
    BeforeValidator(_parse_year_month),
    PlainSerializer(_serialize_year_month),
]
"""Date type normalized to YYYY-MM string format.

Accepts: date objects, "YYYY-MM", "YYYY-MM-DD", "YYYY"
Stores as: "YYYY-MM" string
"""

Year = Annotated[
    str | None,
    BeforeValidator(_parse_year),
]
"""Year type normalized to YYYY string format.

Accepts: date objects, "YYYY", "YYYY-MM", "YYYY-MM-DD"
Stores as: "YYYY" string
"""


# Helper functions for display formatting
def format_year_range(start: str | None, end: str | None) -> str:
    """Format a date range for display.

    Args:
        start: Start date in YYYY-MM or YYYY format.
        end: End date in YYYY-MM or YYYY format, or None for current.

    Returns:
        Formatted string like "2022 - Present" or "2020 - 2022".
    """
    if not start:
        return ""

    start_year = start[:4]

    if end is None:
        return f"{start_year} - Present"

    end_year = end[:4]
    return f"{start_year} - {end_year}"
```

#### Migration: Update Models

```python
# In position.py
from resume_as_code.models.types import YearMonth, format_year_range

class Position(BaseModel):
    start_date: YearMonth  # Was: str with custom validator
    end_date: YearMonth = None

    # Remove @field_validator for dates - handled by YearMonth type

    def format_date_range(self) -> str:
        return format_year_range(self.start_date, self.end_date)
```

```python
# In certification.py
from resume_as_code.models.types import YearMonth

class Certification(BaseModel):
    date: YearMonth = None
    expires: YearMonth = None

    # Remove @field_validator for dates
```

```python
# In board_role.py
from resume_as_code.models.types import YearMonth, format_year_range

class BoardRole(BaseModel):
    start_date: YearMonth  # Required
    end_date: YearMonth = None

    def format_date_range(self) -> str:
        return format_year_range(self.start_date, self.end_date)
```

```python
# In education.py
from resume_as_code.models.types import Year

class Education(BaseModel):
    year: Year = None  # Was: str with custom validator

    # Remove @field_validator for year
```

```python
# In work_unit.py - DECISION NEEDED
# Option A: Keep as date objects (current)
time_started: date | None = None
time_ended: date | None = None

# Option B: Convert to YearMonth for consistency
time_started: YearMonth = None
time_ended: YearMonth = None
```

### Recommendation

**Keep WorkUnit dates as `date` objects** because:
1. They represent specific days (project start/end)
2. Time delta calculations are easier with date objects
3. More precision is valuable for sorting

Other models use `YearMonth` because month-level precision is sufficient for employment/certification dates.

### Acceptance Criteria

- [ ] `YearMonth` type handles all valid input formats
- [ ] `Year` type handles all valid input formats
- [ ] All models using date strings use annotated types
- [ ] Individual `@field_validator` decorators removed (DRY)
- [ ] `format_year_range()` used consistently
- [ ] Tests cover edge cases (None, date objects, various strings)
- [ ] WorkUnit keeps `date` objects (documented decision)

### Files to Create/Modify

| File | Action |
|------|--------|
| `src/resume_as_code/models/types.py` | Create |
| `src/resume_as_code/models/position.py` | Use YearMonth |
| `src/resume_as_code/models/certification.py` | Use YearMonth |
| `src/resume_as_code/models/board_role.py` | Use YearMonth |
| `src/resume_as_code/models/education.py` | Use Year |
| `tests/unit/test_types.py` | Create |

---

## 4. Skills Registry & O*NET Integration

### Problem Statement

Skills appear in 4 places with no shared vocabulary:
1. `WorkUnit.skills_demonstrated` → `list[Skill]`
2. `WorkUnit.tags` → `list[str]`
3. `ResumeConfig.skills` → `SkillsConfig`
4. `JobDescription.skills` → `list[str]`

O*NET integration exists in schema but is not wired up.

### Solution

1. Create a skills registry with normalization and aliases
2. Wire up O*NET API for skill lookup and validation
3. Add CLI command to lookup/validate skills

### Technical Specification

#### O*NET API Integration

**API Details:**
- Base URL: `https://services.onetcenter.org/ws/`
- Authentication: Username (API key) via Basic Auth
- Rate Limit: ~100 requests/minute
- Documentation: https://services.onetcenter.org/reference/

**Key Endpoints:**
- `GET /online/search?keyword={skill}` - Search skills/occupations
- `GET /mnm/search?keyword={skill}` - My Next Move search
- `GET /online/occupations/{soc_code}/skills` - Skills for occupation

#### New File: `src/resume_as_code/services/onet_service.py`

```python
"""O*NET Web Services API integration."""

from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from typing import Any

import httpx

ONET_BASE_URL = "https://services.onetcenter.org/ws"
ONET_USERNAME_ENV = "ONET_API_USERNAME"


@dataclass
class ONetSkill:
    """Skill from O*NET taxonomy."""

    element_id: str  # e.g., "2.A.1.a"
    name: str  # e.g., "Programming"
    description: str
    category: str  # e.g., "Skills", "Knowledge", "Abilities"

    @property
    def category_code(self) -> str:
        """First part of element_id indicates category."""
        return self.element_id.split(".")[0]


@dataclass
class ONetSearchResult:
    """Search result from O*NET."""

    code: str  # SOC code or element ID
    name: str
    relevance_score: float


class ONetService:
    """Service for O*NET API interactions."""

    def __init__(self, api_username: str | None = None):
        """Initialize O*NET service.

        Args:
            api_username: O*NET API username. Falls back to ONET_API_USERNAME env var.
        """
        self.api_username = api_username or os.environ.get(ONET_USERNAME_ENV)
        if not self.api_username:
            raise ValueError(
                f"O*NET API username required. Set {ONET_USERNAME_ENV} env var "
                "or pass api_username parameter."
            )

        self._client = httpx.Client(
            base_url=ONET_BASE_URL,
            auth=(self.api_username, ""),  # Password is empty
            headers={"Accept": "application/json"},
            timeout=10.0,
        )

    def search_skills(self, keyword: str, limit: int = 10) -> list[ONetSearchResult]:
        """Search O*NET for skills matching keyword.

        Args:
            keyword: Skill name to search for.
            limit: Maximum results to return.

        Returns:
            List of matching skills with relevance scores.
        """
        response = self._client.get(
            "/online/search",
            params={"keyword": keyword, "end": limit},
        )
        response.raise_for_status()

        data = response.json()
        results: list[ONetSearchResult] = []

        for item in data.get("occupation", []):
            results.append(ONetSearchResult(
                code=item["code"],
                name=item["title"],
                relevance_score=float(item.get("relevance_score", 0)),
            ))

        return results

    @lru_cache(maxsize=100)
    def get_element_details(self, element_id: str) -> ONetSkill | None:
        """Get details for a specific O*NET element.

        Args:
            element_id: O*NET element ID (e.g., "2.A.1.a").

        Returns:
            Skill details or None if not found.
        """
        # O*NET elements are nested in occupation data
        # This is a simplified lookup - full implementation would
        # need to traverse the element hierarchy
        try:
            response = self._client.get(f"/online/occupations/")
            # Parse response for element...
            return None  # Placeholder
        except httpx.HTTPError:
            return None

    def validate_element_id(self, element_id: str) -> bool:
        """Validate that an O*NET element ID exists.

        Args:
            element_id: O*NET element ID to validate.

        Returns:
            True if element exists in O*NET taxonomy.
        """
        details = self.get_element_details(element_id)
        return details is not None

    def close(self) -> None:
        """Close the HTTP client."""
        self._client.close()

    def __enter__(self) -> ONetService:
        return self

    def __exit__(self, *args: Any) -> None:
        self.close()


# Singleton for CLI usage
_service: ONetService | None = None


def get_onet_service() -> ONetService:
    """Get or create O*NET service singleton."""
    global _service
    if _service is None:
        _service = ONetService()
    return _service
```

#### New File: `src/resume_as_code/services/skill_registry.py`

```python
"""Skill normalization and alias registry."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


@dataclass
class SkillEntry:
    """Registered skill with metadata."""

    canonical_name: str
    aliases: list[str] = field(default_factory=list)
    category: str | None = None  # "language", "framework", "cloud", "soft-skill"
    onet_element_id: str | None = None

    def matches(self, query: str) -> bool:
        """Check if query matches this skill."""
        query_lower = query.lower().strip()
        if self.canonical_name.lower() == query_lower:
            return True
        return any(alias.lower() == query_lower for alias in self.aliases)


class SkillRegistry:
    """Registry of known skills with normalization."""

    def __init__(self, entries: list[SkillEntry] | None = None):
        self._entries: dict[str, SkillEntry] = {}
        self._alias_index: dict[str, str] = {}  # alias → canonical

        if entries:
            for entry in entries:
                self.register(entry)

    def register(self, entry: SkillEntry) -> None:
        """Register a skill entry."""
        key = entry.canonical_name.lower()
        self._entries[key] = entry

        # Index aliases
        for alias in entry.aliases:
            self._alias_index[alias.lower()] = entry.canonical_name

    def normalize(self, skill_name: str) -> str:
        """Normalize a skill name to canonical form.

        Args:
            skill_name: Raw skill name.

        Returns:
            Canonical skill name, or original if not found.
        """
        key = skill_name.lower().strip()

        # Direct match
        if key in self._entries:
            return self._entries[key].canonical_name

        # Alias match
        if key in self._alias_index:
            return self._alias_index[key]

        # Not found - return as-is with title case
        return skill_name.strip()

    def get(self, skill_name: str) -> SkillEntry | None:
        """Get skill entry by name or alias."""
        key = skill_name.lower().strip()

        if key in self._entries:
            return self._entries[key]

        if key in self._alias_index:
            canonical = self._alias_index[key]
            return self._entries[canonical.lower()]

        return None

    def get_onet_id(self, skill_name: str) -> str | None:
        """Get O*NET element ID for a skill."""
        entry = self.get(skill_name)
        return entry.onet_element_id if entry else None

    @classmethod
    def from_yaml(cls, path: Path) -> SkillRegistry:
        """Load registry from YAML file."""
        data = yaml.safe_load(path.read_text())
        entries = []

        for item in data.get("skills", []):
            entries.append(SkillEntry(
                canonical_name=item["name"],
                aliases=item.get("aliases", []),
                category=item.get("category"),
                onet_element_id=item.get("onet_element_id"),
            ))

        return cls(entries)


# Default skill registry with common tech skills
DEFAULT_SKILLS = [
    SkillEntry(
        canonical_name="Python",
        aliases=["python3", "py"],
        category="language",
        onet_element_id="2.A.1.a",
    ),
    SkillEntry(
        canonical_name="JavaScript",
        aliases=["js", "JS", "ecmascript"],
        category="language",
    ),
    SkillEntry(
        canonical_name="TypeScript",
        aliases=["ts", "TS"],
        category="language",
    ),
    SkillEntry(
        canonical_name="Kubernetes",
        aliases=["k8s", "K8s", "kube"],
        category="cloud",
    ),
    SkillEntry(
        canonical_name="Amazon Web Services",
        aliases=["AWS", "aws"],
        category="cloud",
    ),
    SkillEntry(
        canonical_name="Terraform",
        aliases=["tf", "HCL"],
        category="infrastructure",
    ),
    SkillEntry(
        canonical_name="Docker",
        aliases=["containers", "containerization"],
        category="infrastructure",
    ),
    SkillEntry(
        canonical_name="PostgreSQL",
        aliases=["postgres", "psql", "pg"],
        category="database",
    ),
    SkillEntry(
        canonical_name="CI/CD",
        aliases=["continuous integration", "continuous deployment", "CICD"],
        category="devops",
    ),
]


def get_default_registry() -> SkillRegistry:
    """Get the default skill registry."""
    return SkillRegistry(DEFAULT_SKILLS)
```

#### CLI Commands: `resume skill`

```python
"""Skill management commands."""

import click
from rich.console import Console
from rich.table import Table

from resume_as_code.services.onet_service import get_onet_service, ONetService
from resume_as_code.services.skill_registry import get_default_registry

console = Console()


@click.group("skill")
def skill_group() -> None:
    """Skill lookup and validation commands."""
    pass


@skill_group.command("lookup")
@click.argument("keyword")
@click.option("--onet", is_flag=True, help="Search O*NET database")
def skill_lookup(keyword: str, onet: bool) -> None:
    """Look up a skill by name.

    Examples:
        resume skill lookup python
        resume skill lookup "machine learning" --onet
    """
    registry = get_default_registry()
    entry = registry.get(keyword)

    if entry:
        console.print(f"[bold]{entry.canonical_name}[/bold]")
        if entry.aliases:
            console.print(f"  Aliases: {', '.join(entry.aliases)}")
        if entry.category:
            console.print(f"  Category: {entry.category}")
        if entry.onet_element_id:
            console.print(f"  O*NET ID: {entry.onet_element_id}")
    else:
        console.print(f"[yellow]'{keyword}' not in registry[/yellow]")

    if onet:
        console.print("\n[bold]O*NET Search Results:[/bold]")
        try:
            service = get_onet_service()
            results = service.search_skills(keyword)

            if results:
                table = Table()
                table.add_column("Code")
                table.add_column("Name")
                table.add_column("Relevance")

                for r in results[:5]:
                    table.add_row(r.code, r.name, f"{r.relevance_score:.2f}")

                console.print(table)
            else:
                console.print("[dim]No O*NET results found[/dim]")
        except Exception as e:
            console.print(f"[red]O*NET lookup failed: {e}[/red]")


@skill_group.command("normalize")
@click.argument("skills", nargs=-1)
def skill_normalize(skills: tuple[str, ...]) -> None:
    """Normalize skill names to canonical form.

    Examples:
        resume skill normalize k8s aws py
    """
    registry = get_default_registry()

    for skill in skills:
        normalized = registry.normalize(skill)
        if normalized.lower() != skill.lower():
            console.print(f"{skill} → [green]{normalized}[/green]")
        else:
            console.print(f"{skill} → [dim]{normalized}[/dim] (unchanged)")


@skill_group.command("validate")
@click.argument("onet_id")
def skill_validate(onet_id: str) -> None:
    """Validate an O*NET element ID.

    Examples:
        resume skill validate 2.A.1.a
    """
    try:
        service = get_onet_service()
        is_valid = service.validate_element_id(onet_id)

        if is_valid:
            console.print(f"[green]✓[/green] {onet_id} is valid")
        else:
            console.print(f"[red]✗[/red] {onet_id} not found in O*NET")
    except Exception as e:
        console.print(f"[red]Validation failed: {e}[/red]")
```

#### Environment Variable

Add to documentation and `.env.example`:

```bash
# O*NET Web Services API username
# Get your free account at: https://services.onetcenter.org/developer/
ONET_API_USERNAME=your_username_here
```

### Acceptance Criteria

- [ ] `SkillRegistry` normalizes common aliases (k8s → Kubernetes)
- [ ] `ONetService` connects to O*NET API with auth
- [ ] `resume skill lookup <name>` shows skill info
- [ ] `resume skill lookup <name> --onet` queries O*NET
- [ ] `resume skill normalize <names...>` batch normalizes
- [ ] `resume skill validate <onet_id>` validates IDs
- [ ] Default registry includes 20+ common tech skills
- [ ] Custom registry loadable from YAML file
- [ ] O*NET API errors handled gracefully
- [ ] Environment variable documented

### Files to Create/Modify

| File | Action |
|------|--------|
| `src/resume_as_code/services/onet_service.py` | Create |
| `src/resume_as_code/services/skill_registry.py` | Create |
| `src/resume_as_code/commands/skill.py` | Create |
| `src/resume_as_code/cli.py` | Add skill command group |
| `data/skills.yaml` | Create (optional custom registry) |
| `.env.example` | Add ONET_API_USERNAME |
| `docs/onet-integration.md` | Create |
| `tests/unit/test_onet_service.py` | Create |
| `tests/unit/test_skill_registry.py` | Create |

---

## 5. Position Reference Integrity

### Problem Statement

`position_id` in WorkUnit has no enforced relationship:
- `--check-positions` flag is opt-in
- No validation during `resume new work-unit`
- Invalid references silently ignored

### Solution

Make position validation default and add inline warnings.

### Technical Specification

#### Update Validation Command

```python
# In commands/validate.py

@click.command("validate")
@click.argument("path", required=False, type=click.Path(exists=True))
@click.option("--content-quality", is_flag=True)
@click.option("--content-density", is_flag=True)
@click.option(
    "--skip-positions",  # INVERTED: opt-out instead of opt-in
    is_flag=True,
    help="Skip position reference validation",
)
def validate_command(
    path: str | None,
    content_quality: bool,
    content_density: bool,
    skip_positions: bool,  # Changed from check_positions
) -> None:
    """Validate Work Units against schema.

    Position references are validated by default. Use --skip-positions to disable.
    """
    # ... existing logic ...

    if not skip_positions:  # Now default ON
        validate_position_references(work_units, positions)
```

#### Add Warning During Work Unit Creation

```python
# In commands/new.py - work unit creation

def create_work_unit(..., position_id: str | None = None) -> None:
    # Validate position_id if provided
    if position_id:
        positions = load_positions()
        if position_id not in positions:
            console.print(
                f"[yellow]Warning: position_id '{position_id}' not found in positions.yaml[/yellow]"
            )
            console.print("  Available positions:")
            for pid in list(positions.keys())[:5]:
                console.print(f"    - {pid}")

            if not click.confirm("Create work unit anyway?"):
                raise click.Abort()
```

#### Add Model-Level Validation (Optional Enhancement)

```python
# In work_unit.py - add class method for validation

class WorkUnit(BaseModel):
    # ... existing fields ...

    @classmethod
    def validate_position_reference(
        cls,
        position_id: str | None,
        positions: dict[str, Any],
    ) -> list[str]:
        """Validate position_id reference.

        Args:
            position_id: Position ID to validate.
            positions: Dict of position_id → Position data.

        Returns:
            List of warning messages (empty if valid).
        """
        if position_id is None:
            return []

        if position_id not in positions:
            return [
                f"position_id '{position_id}' not found in positions.yaml"
            ]

        return []
```

### Acceptance Criteria

- [ ] Position validation ON by default in `resume validate`
- [ ] `--skip-positions` flag disables validation
- [ ] Warning shown during `resume new work-unit` if position_id invalid
- [ ] User prompted to confirm or abort on invalid position_id
- [ ] Available positions listed in warning message
- [ ] Update documentation for new default behavior

### Files to Modify

| File | Action |
|------|--------|
| `src/resume_as_code/commands/validate.py` | Invert flag logic |
| `src/resume_as_code/commands/new.py` | Add position warning |
| `src/resume_as_code/models/work_unit.py` | Add validation helper |
| `docs/cli-reference.md` | Update flag documentation |

---

## 6. Evidence Model Enhancement

### Problem Statement

All evidence types require `url: HttpUrl`, but some evidence is:
- Local files (design docs in repo)
- Private/internal (no public URL)
- Reference-only (attestation without link)

### Solution

Make `url` optional and add `path` field for local files.

### Technical Specification

#### Update Evidence Base Pattern

```python
# In work_unit.py

from pathlib import Path as FilePath  # Avoid conflict with pydantic Path


class EvidenceBase(BaseModel):
    """Base class for all evidence types."""

    model_config = ConfigDict(extra="forbid")

    # At least one of url or path should be provided
    url: HttpUrl | None = None
    path: FilePath | None = Field(
        default=None,
        description="Local file path relative to work-units directory",
    )
    description: str | None = None

    @model_validator(mode="after")
    def validate_has_reference(self) -> EvidenceBase:
        """Ensure at least url or path is provided."""
        if self.url is None and self.path is None:
            raise ValueError("Evidence must have either url or path")
        return self


class GitRepoEvidence(EvidenceBase):
    """Evidence from a code repository."""

    type: Literal["git_repo"] = "git_repo"
    branch: str | None = None
    commit_sha: str | None = None


class MetricsEvidence(EvidenceBase):
    """Evidence from a metrics dashboard."""

    type: Literal["metrics"] = "metrics"
    dashboard_name: str | None = None
    metric_names: list[str] = Field(default_factory=list)


class DocumentEvidence(EvidenceBase):
    """Evidence from a document or publication."""

    type: Literal["document"] = "document"
    title: str | None = None
    publication_date: date | None = None


class ArtifactEvidence(EvidenceBase):
    """Evidence from an artifact or release."""

    type: Literal["artifact"] = "artifact"
    artifact_type: str | None = None


class OtherEvidence(EvidenceBase):
    """Evidence that doesn't fit other categories."""

    type: Literal["other"] = "other"


# New: Attestation without external reference
class AttestationEvidence(BaseModel):
    """Internal attestation or verbal confirmation."""

    model_config = ConfigDict(extra="forbid")

    type: Literal["attestation"] = "attestation"
    attester: str | None = Field(
        default=None,
        description="Person who can attest (e.g., 'Manager: John Smith')",
    )
    date: str | None = None  # When attestation was given
    description: str | None = None


# Updated discriminated union
Evidence = Annotated[
    GitRepoEvidence
    | MetricsEvidence
    | DocumentEvidence
    | ArtifactEvidence
    | OtherEvidence
    | AttestationEvidence,  # NEW
    Field(discriminator="type"),
]
```

#### YAML Example

```yaml
evidence:
  # URL-based evidence (existing pattern)
  - type: git_repo
    url: https://github.com/org/repo
    branch: main
    description: "Main implementation PR"

  # Local file evidence (NEW)
  - type: document
    path: ./docs/architecture-decision.md
    title: "Architecture Decision Record"
    description: "ADR for this implementation"

  # Attestation evidence (NEW)
  - type: attestation
    attester: "VP Engineering: Jane Doe"
    date: "2024-01"
    description: "Confirmed impact metrics in quarterly review"
```

### Acceptance Criteria

- [ ] `url` is optional (None allowed) on all evidence types
- [ ] `path` field accepts local file paths
- [ ] Validation ensures url OR path is provided
- [ ] New `attestation` evidence type for verbal confirmations
- [ ] JSON schema updated with new patterns
- [ ] Example archetypes show new evidence patterns

### Files to Modify

| File | Action |
|------|--------|
| `src/resume_as_code/models/work_unit.py` | Update evidence classes |
| `schemas/work-unit.schema.json` | Regenerate |
| `archetypes/*.yaml` | Add path/attestation examples |
| `tests/unit/test_work_unit_models.py` | Add evidence tests |

---

## 7. Config/Data Separation (Optional)

### Problem Statement

`.resume.yaml` mixes configuration and personal data:

**Configuration:**
- output_dir
- default_format
- default_template
- work_units_dir
- scoring_weights
- default_top_k
- editor

**Personal Data:**
- profile (name, email, phone, etc.)
- certifications
- education
- board_roles
- publications
- career_highlights

### Recommendation

**Consider separating in future epic**, not this one. Reasons:
1. Significant breaking change for existing users
2. Requires migration tooling
3. Current structure works, just not ideal
4. Lower priority than other improvements

### If Implemented Later

```
.resume.yaml          → Config only (paths, weights, templates)
profile.yaml          → Personal info (name, contact, summary)
credentials.yaml      → Certifications, education
career.yaml           → Board roles, publications, highlights
positions.yaml        → Employment history (already separate)
work-units/           → Achievements (already separate)
```

---

## Story Breakdown

### Epic: Schema & Data Model Refactoring

| Story | Points | Priority | Dependencies |
|-------|--------|----------|--------------|
| **Story 1:** JSON Schema Auto-Generation | 3 | P1 | None |
| **Story 2:** Unified Scope Model | 5 | P1 | None |
| **Story 3:** Standardized Date Types | 3 | P2 | None |
| **Story 4:** Skills Registry (no O*NET) | 5 | P2 | None |
| **Story 5:** O*NET API Integration | 8 | P3 | Story 4 |
| **Story 6:** Position Reference Integrity | 2 | P2 | None |
| **Story 7:** Evidence Model Enhancement | 3 | P3 | None |

**Total Points:** 29

### Recommended Sprint Allocation

**Sprint 1 (P1):** Stories 1, 2 = 8 points
**Sprint 2 (P2):** Stories 3, 4, 6 = 10 points
**Sprint 3 (P3):** Stories 5, 7 = 11 points

---

## Appendix: File Inventory

### Files to Create

| Path | Story |
|------|-------|
| `src/resume_as_code/models/scope.py` | 2 |
| `src/resume_as_code/models/types.py` | 3 |
| `src/resume_as_code/schemas/__init__.py` | 1 |
| `src/resume_as_code/schemas/generator.py` | 1 |
| `src/resume_as_code/services/onet_service.py` | 5 |
| `src/resume_as_code/services/skill_registry.py` | 4 |
| `src/resume_as_code/commands/schema.py` | 1 |
| `src/resume_as_code/commands/skill.py` | 4, 5 |
| `scripts/migrate_scope_fields.py` | 2 |
| `tests/unit/test_scope.py` | 2 |
| `tests/unit/test_types.py` | 3 |
| `tests/unit/test_onet_service.py` | 5 |
| `tests/unit/test_skill_registry.py` | 4 |

### Files to Modify

| Path | Stories |
|------|---------|
| `src/resume_as_code/models/work_unit.py` | 2, 7 |
| `src/resume_as_code/models/position.py` | 2, 3 |
| `src/resume_as_code/models/certification.py` | 3 |
| `src/resume_as_code/models/board_role.py` | 3 |
| `src/resume_as_code/models/education.py` | 3 |
| `src/resume_as_code/models/resume.py` | 2 |
| `src/resume_as_code/cli.py` | 1, 4 |
| `src/resume_as_code/commands/validate.py` | 6 |
| `src/resume_as_code/commands/new.py` | 6 |
| `.pre-commit-config.yaml` | 1 |
| `schemas/*.json` | 1 (auto-generated) |

---

*Document generated by Mary (Business Analyst) - BMAD Framework*
*Ready for PM review and story creation*
