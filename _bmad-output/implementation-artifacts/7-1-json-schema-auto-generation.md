# Story 7.1: JSON Schema Auto-Generation

Status: ready-for-dev

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a **developer**,
I want **JSON schemas to be auto-generated from Pydantic models**,
so that **schemas never drift from implementation and documentation stays accurate**.

## Acceptance Criteria

1. **Given** the Pydantic models in `src/resume_as_code/models/`
   **When** I run `uv run python scripts/generate_schemas.py`
   **Then** JSON schemas are regenerated in `schemas/` directory

2. **Given** a Pydantic model changes (new field, type change, validation)
   **When** I commit the change
   **Then** the corresponding JSON schema is updated automatically via pre-commit hook
   **And** the commit includes both the model change and schema update

3. **Given** the generated schemas
   **When** I inspect them
   **Then** they include:
   - `$schema: "https://json-schema.org/draft/2020-12/schema"`
   - `$id` URLs following pattern `https://resume-as-code.dev/schemas/{name}.schema.json`
   - Proper `$defs` for nested models
   - `description` from docstrings
   - All validation constraints (minLength, pattern, enum, etc.)

4. **Given** I run the schema generation script
   **When** it completes
   **Then** it reports which schemas were updated/created
   **And** exits with code 0 on success, non-zero on failure

## Tasks / Subtasks

- [ ] Task 1: Create schema generation script (AC: #1, #3)
  - [ ] 1.1 Create `scripts/generate_schemas.py` with TypeAdapter pattern
  - [ ] 1.2 Map models to schema names: WorkUnit→work-unit, Position→positions, ResumeConfig→config, Certification→certifications, Education→education, BoardRole→board-roles, Publication→publications
  - [ ] 1.3 Add `$id` URL injection post-generation
  - [ ] 1.4 Add CLI output for generated/updated schemas
  - [ ] 1.5 Add `--check` mode for CI that fails if schemas would change

- [ ] Task 2: Create pre-commit configuration (AC: #2)
  - [ ] 2.1 Create `.pre-commit-config.yaml` with ruff, mypy, and schema generation hooks
  - [ ] 2.2 Configure schema generation hook to run on `src/resume_as_code/models/**/*.py` changes
  - [ ] 2.3 Add `stages: [pre-commit]` to schema hook
  - [ ] 2.4 Test hook catches schema drift

- [ ] Task 3: Update existing schemas or regenerate (AC: #3, #4)
  - [ ] 3.1 Run generation script to create new baseline
  - [ ] 3.2 Verify generated schemas match expected format
  - [ ] 3.3 Add unit test for schema generation script
  - [ ] 3.4 Add integration test verifying model-schema consistency

## Dev Notes

### Relevant Architecture Patterns and Constraints

**From Architecture Document (architecture.md):**
- Schema Validation: JSON Schema 2020-12 (modern draft)
- Model Validation: Pydantic v2 with `model_validator(mode='after')`, `field_validator`
- Use `TypeAdapter` for schema generation (not deprecated `schema()` method)

**From Project Context (project-context.md):**
- Run `ruff check` and `mypy --strict` before completing
- Use Rich console for CLI output, never `print()`
- Type hints required on all public functions
- Use `|` union syntax (Python 3.10+)

### Models to Include in Schema Generation

Based on `src/resume_as_code/models/__init__.py`:

| Schema Name | Primary Model | Location |
|-------------|---------------|----------|
| `work-unit.schema.json` | `WorkUnit` | `models/work_unit.py` |
| `positions.schema.json` | `Position` | `models/position.py` |
| `config.schema.json` | `ResumeConfig` | `models/config.py` |
| `certifications.schema.json` | `Certification` | `models/certification.py` |
| `education.schema.json` | `Education` | `models/education.py` |
| `board-roles.schema.json` | `BoardRole` | `models/board_role.py` |
| `publications.schema.json` | `Publication` | `models/publication.py` |

### Implementation Pattern

**CRITICAL: Use `mode="serialization"`** - YAML files store serialized output, not validation input. Key differences:
- `mode="validation"` (default): Schema for input data (e.g., Decimal expects number)
- `mode="serialization"`: Schema for output data (e.g., Decimal serializes to string)

Since work units are stored as YAML (serialized form), use serialization mode.

**Custom Schema Generator Required** - To add `$schema` field, subclass `GenerateJsonSchema`:

```python
# scripts/generate_schemas.py
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

from pydantic import TypeAdapter
from pydantic.json_schema import GenerateJsonSchema
from rich.console import Console

from resume_as_code.models import (
    BoardRole,
    Certification,
    Education,
    Publication,
    ResumeConfig,
    WorkUnit,
)
from resume_as_code.models.position import Position

console = Console()

SCHEMA_DIR = Path(__file__).parent.parent / "schemas"
BASE_URL = "https://resume-as-code.dev/schemas"

MODELS: dict[str, type] = {
    "work-unit": WorkUnit,
    "positions": Position,
    "config": ResumeConfig,
    "certifications": Certification,
    "education": Education,
    "board-roles": BoardRole,
    "publications": Publication,
}


class ResumeSchemaGenerator(GenerateJsonSchema):
    """Custom generator that adds $schema field."""

    def generate(
        self, schema: Any, mode: str = "validation"
    ) -> dict[str, Any]:
        json_schema = super().generate(schema, mode=mode)
        # self.schema_dialect is 'https://json-schema.org/draft/2020-12/schema'
        json_schema["$schema"] = self.schema_dialect
        return json_schema


def generate_schema(name: str, model: type) -> dict[str, Any]:
    """Generate JSON schema from Pydantic model with proper $schema and $id."""
    adapter = TypeAdapter(model)
    schema = adapter.json_schema(
        mode="serialization",  # CRITICAL: Match YAML storage format
        schema_generator=ResumeSchemaGenerator,
    )
    schema["$id"] = f"{BASE_URL}/{name}.schema.json"
    return schema


def main(check: bool = False) -> int:
    """Generate all schemas. Returns 0 on success, 1 if changes detected in check mode."""
    ...
```

### Existing Schema Format Reference

Current `schemas/work-unit.schema.json` uses:
- `"$schema": "https://json-schema.org/draft/2020-12/schema"`
- `"$id": "https://resume-as-code.dev/schemas/work-unit.schema.json"`
- Required fields, type constraints, patterns, enums

### Pre-commit Configuration Pattern

**Best Practice (2025 Research):**
- Use `repo: local` with `language: system` for project-specific hooks that depend on the project's virtualenv
- This ensures hooks use the same dependencies as the project
- Avoid remote repos for schema generation since it's tightly coupled to local models

```yaml
# .pre-commit-config.yaml
repos:
  - repo: local
    hooks:
      - id: ruff-check
        name: ruff check
        entry: uv run ruff check --fix
        language: system
        types: [python]

      - id: ruff-format
        name: ruff format
        entry: uv run ruff format
        language: system
        types: [python]

      - id: mypy
        name: mypy
        entry: uv run mypy src --strict
        language: system
        types: [python]
        pass_filenames: false

      - id: generate-schemas
        name: generate json schemas
        entry: uv run python scripts/generate_schemas.py
        language: system
        files: ^src/resume_as_code/models/.*\.py$
        pass_filenames: false
        stages: [pre-commit]  # Only run on commit, not push
```

**After creating config, run:**
```bash
pre-commit install  # Set up git hooks
pre-commit run --all-files  # Test all hooks manually
```

### Project Structure Notes

- Scripts location: `scripts/` (create directory if needed)
- Schemas location: `schemas/` (exists with 3 schemas)
- Pre-commit config: `.pre-commit-config.yaml` (needs to be created)

### Testing Standards

```python
# tests/unit/test_generate_schemas.py
def test_generate_schema_includes_id():
    """Schema includes proper $id URL."""
    ...

def test_generate_schema_includes_draft_ref():
    """Schema references JSON Schema 2020-12 draft."""
    ...

def test_all_models_have_schemas():
    """All registered models produce valid schemas."""
    ...
```

### Research Findings (2026-01-15)

**Pydantic v2 JSON Schema Generation:**
1. **mode parameter is critical**:
   - `mode="validation"` (default) - schema for data coming IN
   - `mode="serialization"` - schema for data going OUT (what we store in YAML)
   - Example: `Decimal` validates as `number` but serializes as `string`

2. **Custom GenerateJsonSchema subclass needed** to add `$schema` field:
   - Override `generate()` method
   - Use `self.schema_dialect` which equals `'https://json-schema.org/draft/2020-12/schema'`

3. **TypeAdapter is the preferred API** (not deprecated `schema()` method)

4. **Available customization parameters:**
   - `by_alias: bool = True` - use field aliases in schema
   - `ref_template: str` - format for $ref strings (default: `#/$defs/{model}`)
   - `schema_generator: type[GenerateJsonSchema]` - custom generator class

**Pre-commit Best Practices:**
1. Use `repo: local` with `language: system` for project-specific hooks
2. This ensures hooks use the project's virtualenv dependencies
3. Remote repos better for reusable, standardized checks
4. Always run `pre-commit install` after cloning
5. Pin specific `rev` versions for reproducibility (when using remote repos)

**Sources:**
- Pydantic v2 docs: https://docs.pydantic.dev/latest/concepts/json_schema/
- Pre-commit docs: https://pre-commit.com

### References

- [Source: _bmad-output/planning-artifacts/architecture.md#1.3 Technical Constraints]
- [Source: _bmad-output/planning-artifacts/epics/epic-7-schema-data-model-refactoring.md#Story 7.1]
- [Source: _bmad-output/project-context.md#Critical Implementation Rules]
- [Source: schemas/work-unit.schema.json - existing schema format reference]

## Dev Agent Record

### Agent Model Used

{{agent_model_name_version}}

### Debug Log References

### Completion Notes List

### File List

