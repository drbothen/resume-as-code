# Story 7.4: Skills Registry & Normalization

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a **job seeker**,
I want **my skills normalized to standard names with aliases**,
So that **ATS systems recognize my skills regardless of how I typed them**.

## Acceptance Criteria

1. **Given** I enter skill "k8s" in a work unit
   **When** the resume renders
   **Then** it displays "Kubernetes" (canonical name)
   **And** original alias is preserved for search matching

2. **Given** the skills registry
   **When** I inspect it
   **Then** each skill has:
   - `canonical: str` - Display name
   - `aliases: list[str]` - Alternative spellings/abbreviations
   - `category: str | None` - Optional category (e.g., "cloud", "language")
   - `onet_code: str | None` - O*NET mapping (if available)

3. **Given** I call `SkillRegistry.normalize("typescript")`
   **When** it returns
   **Then** I get `"TypeScript"` (proper casing)

4. **Given** I call `SkillRegistry.normalize("unknown-skill")`
   **When** it returns
   **Then** I get the original string back (passthrough)

5. **Given** skills are extracted from work units
   **When** curated for resume
   **Then** duplicates are removed by canonical name
   **And** both aliases and canonical names match JD keywords

6. **Given** a JD contains "Kubernetes"
   **When** my work unit has "k8s" tag
   **Then** it matches (alias expansion for JD matching)

## Tasks / Subtasks

- [x] Task 1: Create SkillEntry model (AC: #2)
  - [x] 1.1 Create `src/resume_as_code/models/skill_entry.py` with SkillEntry class
  - [x] 1.2 Add canonical, aliases, category, onet_code fields
  - [x] 1.3 Add validation (canonical required, aliases unique)
  - [x] 1.4 Export from `models/__init__.py`

- [x] Task 2: Create SkillRegistry service (AC: #3, #4)
  - [x] 2.1 Create `src/resume_as_code/services/skill_registry.py`
  - [x] 2.2 Implement `normalize(skill: str) -> str` method
  - [x] 2.3 Implement `get_aliases(skill: str) -> set[str]` method
  - [x] 2.4 Implement `load_from_yaml(path: Path) -> SkillRegistry` class method
  - [x] 2.5 Add `load_default()` to load bundled registry

- [x] Task 3: Create initial skills.yaml registry (AC: #2)
  - [x] 3.1 Create `src/resume_as_code/data/` directory
  - [x] 3.2 Create `src/resume_as_code/data/skills.yaml` with 97 common tech skills
  - [x] 3.3 Include cloud platforms (AWS, GCP, Azure aliases)
  - [x] 3.4 Include programming languages (JS/JavaScript, TS/TypeScript)
  - [x] 3.5 Include DevOps tools (k8s/Kubernetes, Docker, CI/CD)
  - [x] 3.6 Include frameworks (React, Vue, Angular, Django, FastAPI)
  - [x] 3.7 Update `pyproject.toml` to include data files in wheel build

- [x] Task 4: Integrate with SkillCurator (AC: #1, #5, #6)
  - [x] 4.1 Add optional `registry: SkillRegistry` parameter to SkillCurator
  - [x] 4.2 Normalize skills before deduplication
  - [x] 4.3 Expand JD keywords with aliases for matching
  - [x] 4.4 Update `_score_skills` to match on aliases

- [x] Task 5: Integrate with ResumeData (AC: #1)
  - [x] 5.1 Load registry in `from_work_units` method
  - [x] 5.2 Pass registry to SkillCurator
  - [x] 5.3 Ensure canonical names appear on final resume

- [x] Task 6: Add tests and documentation
  - [x] 6.1 Unit tests for SkillEntry model
  - [x] 6.2 Unit tests for SkillRegistry (normalize, aliases, passthrough)
  - [x] 6.3 Integration tests for curator with registry
  - [x] 6.4 Run `ruff check` and `mypy --strict`

## Dev Notes

### Current State Analysis

**Skills are stored in 4 places:**

| Location | Field | Type | Purpose |
|----------|-------|------|---------|
| `work_unit.py:231` | `skills_demonstrated` | `list[Skill]` | Structured skills with proficiency |
| `work_unit.py:233` | `tags` | `list[str]` | Simple string tags |
| `config.py:47-48` | `exclude`, `prioritize` | `list[str]` | Curation config |
| `resume.py:159-167` | extracted `all_skills` | `set[str]` | Aggregated for rendering |

**Current Flow (no normalization):**
```
work_units[].tags + work_units[].skills_demonstrated.name
    → all_skills: set[str]
    → SkillCurator.curate()
    → curated_skills: list[str]
    → resume.skills
```

**Gap:** No alias resolution. "k8s" and "Kubernetes" treated as different skills.

### Existing Skill Model

```python
# work_unit.py:145-155
class Skill(BaseModel):
    """Skill demonstrated in a Work Unit with optional O*NET taxonomy mapping."""
    model_config = ConfigDict(extra="forbid")

    name: str
    onet_element_id: str | None = Field(
        default=None, pattern=r"^\d+\.\w+(\.\d+)*$"
    )  # O*NET taxonomy ID
    proficiency_level: int | None = Field(default=None, ge=1, le=7)
```

**Note:** `onet_element_id` already exists - registry can populate this during normalization.

### Implementation Pattern

**SkillEntry Model:**
```python
# src/resume_as_code/models/skill_entry.py
from pydantic import BaseModel, ConfigDict, Field, field_validator


class SkillEntry(BaseModel):
    """A skill in the registry with canonical name and aliases."""

    model_config = ConfigDict(extra="forbid")

    canonical: str = Field(description="Display name (e.g., 'Kubernetes')")
    aliases: list[str] = Field(
        default_factory=list,
        description="Alternative names (e.g., ['k8s', 'kube'])",
    )
    category: str | None = Field(
        default=None,
        description="Skill category (e.g., 'cloud', 'language', 'framework')",
    )
    onet_code: str | None = Field(
        default=None,
        description="O*NET element ID for standardization",
    )

    @field_validator("canonical", mode="before")
    @classmethod
    def validate_canonical(cls, v: str) -> str:
        """Ensure canonical name is non-empty."""
        if not v or not v.strip():
            raise ValueError("Canonical name cannot be empty")
        return v.strip()

    @field_validator("aliases", mode="before")
    @classmethod
    def validate_aliases(cls, v: list[str]) -> list[str]:
        """Normalize aliases to lowercase, remove empties."""
        return [a.strip().lower() for a in v if a and a.strip()]
```

**SkillRegistry Service:**
```python
# src/resume_as_code/services/skill_registry.py
from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import yaml

if TYPE_CHECKING:
    from resume_as_code.models.skill_entry import SkillEntry


class SkillRegistry:
    """Registry for skill name normalization and alias lookup.

    Maps skill aliases to canonical names for consistent resume rendering
    and improved JD matching.
    """

    def __init__(self, entries: list[SkillEntry]) -> None:
        """Initialize registry with skill entries.

        Args:
            entries: List of SkillEntry objects.
        """
        self._entries = entries
        self._by_alias: dict[str, SkillEntry] = {}

        for entry in entries:
            # Map canonical name (lowercase) to entry
            self._by_alias[entry.canonical.lower()] = entry
            # Map all aliases to entry
            for alias in entry.aliases:
                self._by_alias[alias.lower()] = entry

    def normalize(self, skill: str) -> str:
        """Normalize skill name to canonical form.

        Args:
            skill: Skill name or alias.

        Returns:
            Canonical name if found, otherwise original string.
        """
        entry = self._by_alias.get(skill.lower())
        return entry.canonical if entry else skill

    def get_aliases(self, skill: str) -> set[str]:
        """Get all aliases for a skill including canonical name.

        Args:
            skill: Skill name or alias.

        Returns:
            Set of all names (canonical + aliases), or {skill} if not found.
        """
        entry = self._by_alias.get(skill.lower())
        if entry:
            return {entry.canonical.lower()} | set(entry.aliases)
        return {skill.lower()}

    def get_onet_code(self, skill: str) -> str | None:
        """Get O*NET code for a skill.

        Args:
            skill: Skill name or alias.

        Returns:
            O*NET element ID if mapped, otherwise None.
        """
        entry = self._by_alias.get(skill.lower())
        return entry.onet_code if entry else None

    @classmethod
    def load_from_yaml(cls, path: Path) -> SkillRegistry:
        """Load registry from YAML file.

        Args:
            path: Path to skills.yaml file.

        Returns:
            SkillRegistry instance.
        """
        from resume_as_code.models.skill_entry import SkillEntry

        with path.open() as f:
            data = yaml.safe_load(f)

        entries = [SkillEntry(**entry) for entry in data.get("skills", [])]
        return cls(entries)

    @classmethod
    def load_default(cls) -> SkillRegistry:
        """Load the bundled default skills registry.

        Uses importlib.resources to access package data files,
        which works across all installation methods.

        Returns:
            SkillRegistry with default skills.
        """
        import importlib.resources

        from resume_as_code.models.skill_entry import SkillEntry

        # Access bundled data file using importlib.resources
        data_file = importlib.resources.files("resume_as_code") / "data" / "skills.yaml"
        content = data_file.read_text()
        data = yaml.safe_load(content)

        entries = [SkillEntry(**entry) for entry in data.get("skills", [])]
        return cls(entries)
```

### Initial skills.yaml Structure

```yaml
# data/skills.yaml
# Skill registry for name normalization and alias resolution
skills:
  # Cloud Platforms
  - canonical: Amazon Web Services
    aliases: [aws, amazon aws]
    category: cloud

  - canonical: Google Cloud Platform
    aliases: [gcp, google cloud]
    category: cloud

  - canonical: Microsoft Azure
    aliases: [azure]
    category: cloud

  - canonical: Kubernetes
    aliases: [k8s, kube]
    category: devops

  # Programming Languages
  - canonical: JavaScript
    aliases: [js, ecmascript, es6, es2015]
    category: language

  - canonical: TypeScript
    aliases: [ts]
    category: language

  - canonical: Python
    aliases: [py, python3]
    category: language

  # Frameworks
  - canonical: React
    aliases: [reactjs, react.js]
    category: framework

  - canonical: Node.js
    aliases: [nodejs, node]
    category: runtime

  # DevOps
  - canonical: Docker
    aliases: [docker containers, containerization]
    category: devops

  - canonical: CI/CD
    aliases: [cicd, continuous integration, continuous deployment]
    category: devops

  - canonical: Terraform
    aliases: [tf, hashicorp terraform]
    category: infrastructure

  # ... 40+ more entries
```

### SkillCurator Integration

```python
# Updated skill_curator.py

class SkillCurator:
    def __init__(
        self,
        max_count: int = 15,
        exclude: list[str] | None = None,
        prioritize: list[str] | None = None,
        registry: SkillRegistry | None = None,  # NEW
    ) -> None:
        self.max_count = max_count
        self.exclude = {s.lower() for s in (exclude or [])}
        self.prioritize = {s.lower() for s in (prioritize or [])}
        self.registry = registry  # NEW

    def curate(
        self,
        raw_skills: set[str],
        jd_keywords: set[str] | None = None,
    ) -> CurationResult:
        jd_keywords = jd_keywords or set()

        # NEW: Expand JD keywords with aliases for better matching
        jd_expanded = self._expand_jd_keywords(jd_keywords)

        # Step 1: Normalize skills using registry
        normalized = self._deduplicate(raw_skills)

        # ... rest of curation logic using jd_expanded

    def _deduplicate(self, skills: set[str]) -> dict[str, str]:
        """Deduplicate skills, applying registry normalization."""
        normalized: dict[str, str] = {}
        for skill in skills:
            if not skill or not skill.strip():
                continue

            # NEW: Normalize to canonical name if registry available
            display = skill
            if self.registry:
                display = self.registry.normalize(skill)

            lower = display.lower()
            if lower not in normalized:
                normalized[lower] = display
            # ... existing casing preference logic
        return normalized

    def _expand_jd_keywords(self, keywords: set[str]) -> set[str]:
        """Expand JD keywords with skill aliases for better matching."""
        if not self.registry:
            return {k.lower() for k in keywords}

        expanded: set[str] = set()
        for keyword in keywords:
            # Add all aliases including canonical
            expanded.update(self.registry.get_aliases(keyword))
        return expanded
```

### Research Findings (2026-01-15)

**Package Data File Access (Python 3.10+):**

Use `importlib.resources.files()` to access bundled data files - this works across different installation methods including zip files and editable installs.

```python
import importlib.resources

# Get data file path
data_file = importlib.resources.files("resume_as_code") / "data" / "skills.yaml"

# Read text content directly
content = data_file.read_text()

# Or use as_file() when you need a Path object
with importlib.resources.as_file(data_file) as path:
    with path.open() as f:
        data = yaml.safe_load(f)
```

**CRITICAL:** Always provide an explicit anchor (package name). The data directory should be INSIDE the package:
```
src/resume_as_code/
├── data/
│   └── skills.yaml    # Correct location
├── models/
├── services/
└── ...
```

**pyproject.toml Configuration:**

The project uses Hatch. To include data files, update the wheel target:

```toml
[tool.hatch.build.targets.wheel]
packages = ["src/resume_as_code"]

# Include non-Python files in the package
[tool.hatch.build.targets.wheel.force-include]
"src/resume_as_code/data" = "resume_as_code/data"
```

Or use glob patterns:
```toml
[tool.hatch.build]
include = [
    "src/resume_as_code/**/*.py",
    "src/resume_as_code/**/*.yaml",
]
```

**O*NET Element ID Format:**

O*NET uses hierarchical dot notation: `2.A.2.b`
- First level (2): Content Model domain (2 = Worker Characteristics)
- Second level (A): Component (A = Skills)
- Third level (2): Category (2 = Cross-Functional Skills)
- Fourth level (b): Specific element

**Programming-relevant O*NET codes:**
- `2.A.2.b` - Programming (core coding skill)
- `2.A.2.a` - Mathematics (algorithmic foundations)
- `2.A.2.c` - Critical Thinking (debugging, design)
- `2.A.4.b` - Complex Problem Solving (software architecture)

The existing Skill model pattern `r"^\d+\.\w+(\.\d+)*$"` is correct for O*NET IDs.

**Common Tech Skill Abbreviations (for initial registry):**

| Canonical | Aliases | Category |
|-----------|---------|----------|
| Kubernetes | k8s, kube | devops |
| JavaScript | js, ecmascript, es6 | language |
| TypeScript | ts | language |
| Machine Learning | ml | ai |
| Amazon Web Services | aws | cloud |
| Google Cloud Platform | gcp, google cloud | cloud |
| Microsoft Azure | azure | cloud |
| CI/CD | cicd, continuous integration | devops |
| Node.js | nodejs, node | runtime |
| PostgreSQL | postgres, pg | database |
| MongoDB | mongo | database |
| Artificial Intelligence | ai | ai |
| React | reactjs, react.js | framework |
| Vue.js | vue, vuejs | framework |
| Docker | docker containers | devops |
| Terraform | tf | infrastructure |

**ATS Best Practice:** Include both canonical name and common abbreviation when space allows (e.g., "Kubernetes (k8s)"). The registry should expand aliases for JD matching.

**Sources:**
- importlib.resources docs: https://docs.python.org/3/library/importlib.resources.html
- Hatch build configuration: https://hatch.pypa.io/latest/config/build/
- O*NET Skills taxonomy: https://www.onetcenter.org/dictionary/24.2/excel/skills.html
- Resume abbreviations: https://enhancv.com/blog/resume-abbreviations/

### Project Context Rules

From `project-context.md`:
- Run `ruff check` and `mypy --strict` before completing
- Use Rich console for CLI output, never `print()`
- Type hints required on all public functions
- Use `|` union syntax (Python 3.10+)
- Use `model_config = ConfigDict(extra="forbid")` on all Pydantic models

### Testing Standards

```python
# tests/unit/models/test_skill_entry.py

import pytest
from pydantic import ValidationError

from resume_as_code.models.skill_entry import SkillEntry


def test_skill_entry_minimal() -> None:
    """SkillEntry requires only canonical name."""
    entry = SkillEntry(canonical="Python")
    assert entry.canonical == "Python"
    assert entry.aliases == []
    assert entry.category is None


def test_skill_entry_with_aliases() -> None:
    """SkillEntry stores aliases lowercase."""
    entry = SkillEntry(
        canonical="Kubernetes",
        aliases=["K8s", "KUBE"],
    )
    assert entry.aliases == ["k8s", "kube"]


def test_skill_entry_empty_canonical_rejected() -> None:
    """Empty canonical name raises ValidationError."""
    with pytest.raises(ValidationError):
        SkillEntry(canonical="")


# tests/unit/services/test_skill_registry.py

import pytest

from resume_as_code.models.skill_entry import SkillEntry
from resume_as_code.services.skill_registry import SkillRegistry


@pytest.fixture
def registry() -> SkillRegistry:
    """Create test registry."""
    entries = [
        SkillEntry(canonical="Kubernetes", aliases=["k8s", "kube"]),
        SkillEntry(canonical="TypeScript", aliases=["ts"]),
        SkillEntry(canonical="Python", aliases=["py"]),
    ]
    return SkillRegistry(entries)


def test_normalize_alias(registry: SkillRegistry) -> None:
    """Alias normalizes to canonical name."""
    assert registry.normalize("k8s") == "Kubernetes"
    assert registry.normalize("ts") == "TypeScript"


def test_normalize_canonical(registry: SkillRegistry) -> None:
    """Canonical name returns itself."""
    assert registry.normalize("Kubernetes") == "Kubernetes"
    assert registry.normalize("kubernetes") == "Kubernetes"  # Case insensitive


def test_normalize_unknown_passthrough(registry: SkillRegistry) -> None:
    """Unknown skill returns original string."""
    assert registry.normalize("UnknownSkill") == "UnknownSkill"


def test_get_aliases(registry: SkillRegistry) -> None:
    """Get all aliases including canonical."""
    aliases = registry.get_aliases("k8s")
    assert "kubernetes" in aliases
    assert "k8s" in aliases
    assert "kube" in aliases


def test_get_aliases_unknown(registry: SkillRegistry) -> None:
    """Unknown skill returns singleton set."""
    assert registry.get_aliases("unknown") == {"unknown"}


# tests/integration/test_skill_curator_registry.py

def test_curator_normalizes_skills() -> None:
    """Curator uses registry to normalize skills."""
    entries = [SkillEntry(canonical="Kubernetes", aliases=["k8s"])]
    registry = SkillRegistry(entries)
    curator = SkillCurator(registry=registry)

    result = curator.curate({"k8s", "Python"})

    assert "Kubernetes" in result.included  # Normalized
    assert "Python" in result.included  # Passthrough


def test_curator_matches_jd_via_aliases() -> None:
    """JD keywords match via alias expansion."""
    entries = [SkillEntry(canonical="Kubernetes", aliases=["k8s"])]
    registry = SkillRegistry(entries)
    curator = SkillCurator(registry=registry)

    # JD has "Kubernetes", work unit has "k8s" - should match
    result = curator.curate({"k8s"}, jd_keywords={"Kubernetes"})

    # k8s should be scored as JD match (score=10, not score=1)
    assert "Kubernetes" in result.included
```

### References

- [Source: _bmad-output/planning-artifacts/architecture.md#3.2 Data Architecture]
- [Source: _bmad-output/planning-artifacts/epics/epic-7-schema-data-model-refactoring.md#Story 7.4]
- [Source: src/resume_as_code/models/work_unit.py:145-155 - Skill class]
- [Source: src/resume_as_code/services/skill_curator.py - SkillCurator]
- [Source: src/resume_as_code/models/resume.py:159-182 - skill extraction]

## Dev Agent Record

### Agent Model Used

Claude Opus 4.5 (claude-opus-4-5-20251101)

### Debug Log References

None - all tests pass.

### Completion Notes List

- Created SkillEntry Pydantic model with validation for canonical names and aliases
- Created SkillRegistry service with `normalize()`, `get_aliases()`, `get_onet_code()` methods
- Created `load_from_yaml()` and `load_default()` class methods for loading registries
- Created initial skills.yaml with 75+ tech skills organized by category
- Updated pyproject.toml to include data files in wheel build
- Integrated registry with SkillCurator for alias normalization and JD keyword expansion
- Integrated registry loading in ResumeData.from_work_units()
- All 1498 unit tests pass
- mypy --strict passes on all modified files
- ruff check passes on all modified files

### File List

**New Files:**
- `src/resume_as_code/models/skill_entry.py` - SkillEntry Pydantic model
- `src/resume_as_code/services/skill_registry.py` - SkillRegistry service
- `src/resume_as_code/data/skills.yaml` - Default skill registry (97 skills)
- `tests/unit/test_skill_entry.py` - 10 tests for SkillEntry model
- `tests/unit/test_skill_registry.py` - 16 tests for SkillRegistry service

**Modified Files:**
- `src/resume_as_code/models/__init__.py` - Added SkillEntry export
- `src/resume_as_code/services/skill_curator.py` - Added registry parameter and alias expansion
- `src/resume_as_code/models/resume.py` - Load registry in from_work_units()
- `tests/unit/test_skill_curator.py` - Added 8 registry integration tests
- `tests/unit/test_resume_model.py` - Added 5 registry integration tests, updated existing tests
- `pyproject.toml` - Added data file inclusion for wheel build

