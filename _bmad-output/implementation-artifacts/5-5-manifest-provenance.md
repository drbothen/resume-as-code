# Story 5.5: Manifest & Provenance

Status: done

## Story

As a **user**,
I want **a manifest file with every build**,
So that **I know exactly what went into each resume version**.

## Acceptance Criteria

1. **Given** a build completes successfully
   **When** I check the output directory
   **Then** I find `manifest.yaml` alongside the resume files

2. **Given** I inspect the manifest
   **When** I read its contents
   **Then** I see: timestamp, Work Unit IDs included, JD file hash, template used, scoring weights

3. **Given** I build two resumes from different JDs
   **When** I compare their manifests
   **Then** I can see exactly what differed between them

4. **Given** the manifest includes Work Unit IDs
   **When** I review it later
   **Then** I can trace back to the exact Work Units used

5. **Given** the same inputs (JD, Work Units, config)
   **When** I run build twice
   **Then** the output is identical (NFR5 - deterministic)
   **And** manifests have different timestamps but same content hash

## Tasks / Subtasks

- [x] Task 1: Create Manifest model (AC: #1, #2, #4)
  - [x] 1.1: Create `src/resume_as_code/models/manifest.py`
  - [x] 1.2: Define `BuildManifest` Pydantic model
  - [x] 1.3: Include timestamp, version, Work Unit IDs
  - [x] 1.4: Include JD hash and template info
  - [x] 1.5: Include content hash for determinism check

- [x] Task 2: Create ManifestProvider (AC: #1, #5)
  - [x] 2.1: Create `src/resume_as_code/providers/manifest.py`
  - [x] 2.2: Implement `generate()` method
  - [x] 2.3: Compute content hash of inputs
  - [x] 2.4: Save as human-readable YAML

- [x] Task 3: Integrate with build command (AC: #1)
  - [x] 3.1: Generate manifest after successful build
  - [x] 3.2: Save alongside resume files
  - [x] 3.3: Include manifest in atomic write

- [x] Task 4: Add comparison support (AC: #3)
  - [x] 4.1: Store comparable fields
  - [x] 4.2: Add `resume manifest diff` command (optional) - Added `diff()` and `is_equivalent()` methods instead
  - [x] 4.3: Human-readable diff format

- [x] Task 5: Code quality verification
  - [x] 5.1: Run `ruff check src tests --fix`
  - [x] 5.2: Run `mypy src --strict` with zero errors
  - [x] 5.3: Add tests for manifest generation
  - [x] 5.4: Test determinism with same inputs

## Dev Notes

### Architecture Compliance

The manifest provides full provenance for every generated resume, enabling reproducibility and auditing.

**Source:** [epics.md#Story 5.5](_bmad-output/planning-artifacts/epics.md)

### Dependencies

This story REQUIRES:
- Story 5.4 (Build Command) - Build pipeline to integrate with

This story ENABLES:
- Complete provenance tracking for resumes

### Manifest Model

**`src/resume_as_code/models/manifest.py`:**

```python
"""Build manifest for provenance tracking."""

from __future__ import annotations

import hashlib
from datetime import datetime
from pathlib import Path

from pydantic import BaseModel, Field
from ruamel.yaml import YAML


class WorkUnitReference(BaseModel):
    """Reference to a Work Unit included in the build."""

    id: str
    title: str
    score: float


class BuildManifest(BaseModel):
    """Manifest documenting what went into a resume build."""

    # Version info
    version: str = "1.0.0"
    resume_as_code_version: str = Field(
        default="0.1.0",
        description="Version of resume-as-code used"
    )

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.now)

    # JD information
    jd_hash: str = Field(..., description="SHA256 hash of JD content")
    jd_title: str | None = None
    jd_path: str | None = None

    # Work Units included
    work_units: list[WorkUnitReference] = Field(default_factory=list)
    work_unit_count: int = 0

    # Build settings
    template: str = "modern"
    output_formats: list[str] = Field(default_factory=lambda: ["pdf", "docx"])

    # Scoring configuration
    ranker_version: str = "hybrid-rrf-v1"
    top_k: int = 8

    # Content hash for determinism
    content_hash: str = Field(
        default="",
        description="Hash of inputs for reproducibility check"
    )

    @classmethod
    def from_build(
        cls,
        plan,
        work_units: list[dict],
        template: str,
        output_formats: list[str],
    ) -> "BuildManifest":
        """Create manifest from build parameters."""
        wu_refs = [
            WorkUnitReference(
                id=wu.get("id", ""),
                title=wu.get("title", ""),
                score=next(
                    (s.score for s in plan.selected_work_units if s.id == wu.get("id")),
                    0.0
                ),
            )
            for wu in work_units
        ]

        manifest = cls(
            jd_hash=plan.jd_hash,
            jd_title=plan.jd_title,
            jd_path=plan.jd_path,
            work_units=wu_refs,
            work_unit_count=len(wu_refs),
            template=template,
            output_formats=output_formats,
            ranker_version=plan.ranker_version,
            top_k=plan.top_k,
        )

        # Compute content hash
        manifest.content_hash = manifest._compute_content_hash()

        return manifest

    def _compute_content_hash(self) -> str:
        """Compute hash of content-affecting inputs."""
        # Hash inputs that affect output content
        content_parts = [
            self.jd_hash,
            self.template,
            ",".join(sorted(wu.id for wu in self.work_units)),
            str(self.top_k),
        ]

        combined = "|".join(content_parts)
        return hashlib.sha256(combined.encode()).hexdigest()[:16]

    def save(self, path: Path) -> None:
        """Save manifest to YAML file."""
        yaml = YAML()
        yaml.default_flow_style = False

        data = self.model_dump(mode="json")

        with open(path, "w") as f:
            f.write("# Resume Build Manifest\n")
            f.write(f"# Generated: {self.created_at.isoformat()}\n")
            f.write("# This file documents what went into the resume build\n\n")
            yaml.dump(data, f)

    @classmethod
    def load(cls, path: Path) -> "BuildManifest":
        """Load manifest from YAML file."""
        yaml = YAML()
        with open(path) as f:
            data = yaml.load(f)
        return cls.model_validate(data)
```

### ManifestProvider

**`src/resume_as_code/providers/manifest.py`:**

```python
"""Manifest provider for build provenance."""

from __future__ import annotations

from pathlib import Path

from resume_as_code.models.manifest import BuildManifest


class ManifestProvider:
    """Provider for generating build manifests."""

    def generate(
        self,
        plan,
        work_units: list[dict],
        template: str,
        output_formats: list[str],
        output_path: Path,
    ) -> Path:
        """Generate and save manifest.

        Args:
            plan: The SavedPlan used for the build.
            work_units: Work Units included in the build.
            template: Template name used.
            output_formats: Formats generated.
            output_path: Path to save manifest.

        Returns:
            Path to generated manifest file.
        """
        manifest = BuildManifest.from_build(
            plan=plan,
            work_units=work_units,
            template=template,
            output_formats=output_formats,
        )

        manifest.save(output_path)
        return output_path
```

### Updated Build Command Integration

**Update `src/resume_as_code/commands/build.py`:**

```python
from resume_as_code.providers.manifest import ManifestProvider

def _generate_outputs(
    resume: ResumeData,
    plan: SavedPlan,
    work_units: list[dict],
    output_format: str,
    output_dir: Path,
    template_name: str,
) -> None:
    """Generate output files atomically."""
    formats_generated = []

    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        generated_files: list[tuple[Path, Path]] = []

        try:
            # Generate PDF
            if output_format in ("pdf", "all"):
                pdf_provider = PDFProvider(template_name=template_name)
                tmp_pdf = tmp_path / "resume.pdf"
                pdf_provider.render(resume, tmp_pdf)
                generated_files.append((tmp_pdf, output_dir / "resume.pdf"))
                formats_generated.append("pdf")

            # Generate DOCX
            if output_format in ("docx", "all"):
                docx_provider = DOCXProvider()
                tmp_docx = tmp_path / "resume.docx"
                docx_provider.render(resume, tmp_docx)
                generated_files.append((tmp_docx, output_dir / "resume.docx"))
                formats_generated.append("docx")

            # Generate manifest
            manifest_provider = ManifestProvider()
            tmp_manifest = tmp_path / "manifest.yaml"
            manifest_provider.generate(
                plan=plan,
                work_units=work_units,
                template=template_name,
                output_formats=formats_generated,
                output_path=tmp_manifest,
            )
            generated_files.append((tmp_manifest, output_dir / "manifest.yaml"))

            # All succeeded - move to final location
            output_dir.mkdir(parents=True, exist_ok=True)
            for src, dst in generated_files:
                shutil.move(str(src), str(dst))

        except Exception:
            raise
```

### Example Manifest File

```yaml
# Resume Build Manifest
# Generated: 2026-01-10T15:30:00
# This file documents what went into the resume build

version: "1.0.0"
resume_as_code_version: "0.1.0"

created_at: "2026-01-10T15:30:00"

jd_hash: "a1b2c3d4e5f67890"
jd_title: "Senior Software Engineer"
jd_path: "jobs/senior-engineer.txt"

work_units:
  - id: "wu-2026-01-05-python-api"
    title: "Built Python REST API"
    score: 0.87
  - id: "wu-2025-08-20-kubernetes"
    title: "Kubernetes Migration"
    score: 0.72
  - id: "wu-2025-06-15-team-lead"
    title: "Technical Team Leadership"
    score: 0.68

work_unit_count: 3

template: "modern"
output_formats:
  - pdf
  - docx

ranker_version: "hybrid-rrf-v1"
top_k: 8

content_hash: "f8a9b2c3d4e5f678"
```

### Testing Requirements

**`tests/unit/test_manifest.py`:**

```python
"""Tests for manifest and provenance."""

from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from resume_as_code.models.manifest import BuildManifest, WorkUnitReference
from resume_as_code.providers.manifest import ManifestProvider


@pytest.fixture
def sample_plan():
    """Create sample plan for testing."""
    plan = MagicMock()
    plan.jd_hash = "abc123"
    plan.jd_title = "Senior Engineer"
    plan.jd_path = "job.txt"
    plan.ranker_version = "hybrid-rrf-v1"
    plan.top_k = 8
    plan.selected_work_units = [
        MagicMock(id="wu-1", score=0.9),
        MagicMock(id="wu-2", score=0.8),
    ]
    return plan


class TestBuildManifest:
    """Tests for BuildManifest model."""

    def test_creates_from_build(self, sample_plan):
        """Should create manifest from build parameters."""
        work_units = [
            {"id": "wu-1", "title": "Work Unit 1"},
            {"id": "wu-2", "title": "Work Unit 2"},
        ]

        manifest = BuildManifest.from_build(
            plan=sample_plan,
            work_units=work_units,
            template="modern",
            output_formats=["pdf", "docx"],
        )

        assert manifest.jd_hash == "abc123"
        assert manifest.work_unit_count == 2
        assert len(manifest.work_units) == 2

    def test_content_hash_deterministic(self, sample_plan):
        """Same inputs should produce same content hash."""
        work_units = [{"id": "wu-1", "title": "Work Unit 1"}]

        manifest1 = BuildManifest.from_build(
            plan=sample_plan,
            work_units=work_units,
            template="modern",
            output_formats=["pdf"],
        )

        manifest2 = BuildManifest.from_build(
            plan=sample_plan,
            work_units=work_units,
            template="modern",
            output_formats=["pdf"],
        )

        assert manifest1.content_hash == manifest2.content_hash

    def test_save_and_load(self, sample_plan, tmp_path):
        """Should save and load manifest."""
        work_units = [{"id": "wu-1", "title": "Work Unit 1"}]
        manifest = BuildManifest.from_build(
            plan=sample_plan,
            work_units=work_units,
            template="modern",
            output_formats=["pdf"],
        )

        path = tmp_path / "manifest.yaml"
        manifest.save(path)

        loaded = BuildManifest.load(path)
        assert loaded.jd_hash == manifest.jd_hash
        assert loaded.content_hash == manifest.content_hash


class TestManifestProvider:
    """Tests for ManifestProvider."""

    def test_generates_manifest(self, sample_plan, tmp_path):
        """Should generate manifest file."""
        provider = ManifestProvider()
        work_units = [{"id": "wu-1", "title": "Test"}]

        path = provider.generate(
            plan=sample_plan,
            work_units=work_units,
            template="modern",
            output_formats=["pdf"],
            output_path=tmp_path / "manifest.yaml",
        )

        assert path.exists()
        content = path.read_text()
        assert "jd_hash" in content
        assert "wu-1" in content
```

### Verification Commands

```bash
# Build resume and check manifest
resume build --jd job.txt
cat dist/manifest.yaml

# Compare two manifests
diff dist/manifest.yaml applications/google/manifest.yaml

# Verify determinism (same content hash)
resume build --jd job.txt --output-dir test1
resume build --jd job.txt --output-dir test2
diff test1/manifest.yaml test2/manifest.yaml
```

### References

- [Source: epics.md#Story 5.5](_bmad-output/planning-artifacts/epics.md)

## Dev Agent Record

### Agent Model Used

Claude Opus 4.5 (claude-opus-4-5-20251101)

### Debug Log References

None

### Completion Notes List

- Implemented `BuildManifest` Pydantic model in `src/resume_as_code/models/manifest.py`
- Implemented `WorkUnitReference` model for tracking Work Units included in builds
- Added content hash computation for deterministic builds (AC #5)
- Created `ManifestProvider` in `src/resume_as_code/providers/manifest.py`
- Integrated manifest generation into `build` command's atomic write flow
- Added `diff()` method for manifest comparison (AC #3)
- Added `is_equivalent()` method for checking content equivalence
- All 909 tests pass (6 new tests added during code review)
- ruff check passes with no errors
- mypy strict mode passes with no errors

### File List

- src/resume_as_code/models/manifest.py (new)
- src/resume_as_code/models/__init__.py (modified)
- src/resume_as_code/providers/manifest.py (new)
- src/resume_as_code/providers/__init__.py (modified)
- src/resume_as_code/commands/build.py (modified)
- tests/unit/test_manifest.py (new - 21 tests)
- tests/unit/test_build_command.py (modified)

### Change Log

- 2026-01-11: Implemented Story 5.5 - Manifest & Provenance tracking for resume builds
- 2026-01-11: Code review completed - all issues fixed

## Code Review Record

### Review Date

2026-01-11

### Reviewer

Claude Opus 4.5 (adversarial code review)

### Issues Found and Fixed

| Issue | Severity | Description | Fix Applied |
|-------|----------|-------------|-------------|
| M1 | MEDIUM | Missing `ranker_version` in content hash | Added to `_compute_content_hash()` |
| M2 | MEDIUM | `datetime.now()` without timezone | Changed to `datetime.now(timezone.utc)` |
| M3 | MEDIUM | No error handling in save/load | Added try/except with RenderError/ValidationError |
| M5 | MEDIUM | Test DOCX mock inconsistent | Added `side_effect` to create dummy file |
| L1 | LOW | Magic string "hybrid-rrf-v1" | Created `DEFAULT_RANKER_VERSION` constant |
| L2 | LOW | Hardcoded version "0.1.0" | Now reads from `__version__` |
| L3 | LOW | Type annotation too narrow | Changed to `dict[str, Any]` |

### New Tests Added

- `test_content_hash_includes_ranker_version` - Verifies ranker version affects hash
- `test_created_at_has_timezone` - Verifies UTC timezone on timestamps
- `test_load_nonexistent_file_raises_validation_error` - Error handling
- `test_load_empty_file_raises_validation_error` - Error handling
- `test_load_invalid_yaml_raises_validation_error` - Error handling
- `test_save_to_readonly_raises_render_error` - Error handling

### Verification

- All 909 tests pass
- ruff check: no errors
- mypy --strict: no errors

