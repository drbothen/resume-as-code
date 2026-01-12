# Story 5.2: PDF Provider (WeasyPrint)

Status: done

## Story

As a **user**,
I want **to generate a professional PDF resume**,
So that **I have a polished document ready for submission**.

## Acceptance Criteria

1. **Given** a ResumeData instance
   **When** the PDFProvider renders it
   **Then** a PDF file is generated
   **And** the PDF is properly formatted with styles from CSS

2. **Given** the modern template
   **When** a PDF is generated
   **Then** it has professional typography and layout
   **And** sections are clearly delineated
   **And** it fits standard letter/A4 page sizes

3. **Given** I run `resume build --format pdf`
   **When** the build completes
   **Then** `dist/resume.pdf` is created
   **And** the file is a valid PDF document

4. **Given** a Work Unit with a long outcome description
   **When** the PDF is generated
   **Then** text wraps appropriately
   **And** page breaks occur at sensible locations

5. **Given** the PDF generation
   **When** it completes
   **Then** it finishes within 5 seconds (NFR2)

## Tasks / Subtasks

- [x] Task 1: Create PDFProvider class (AC: #1, #2)
  - [x] 1.1: Create `src/resume_as_code/providers/pdf.py`
  - [x] 1.2: Implement `PDFProvider` class with `render()` method
  - [x] 1.3: Use WeasyPrint for HTML→PDF conversion
  - [x] 1.4: Load and apply CSS from template

- [x] Task 2: Handle page formatting (AC: #2, #4)
  - [x] 2.1: Configure page size (letter/A4)
  - [x] 2.2: Set appropriate margins
  - [x] 2.3: Handle page breaks with CSS
  - [x] 2.4: Ensure text wrapping works correctly

- [x] Task 3: Font handling (AC: #2)
  - [x] 3.1: Use web-safe fonts by default
  - [x] 3.2: Support custom fonts via CSS @font-face
  - [x] 3.3: Test rendering with special characters

- [x] Task 4: Output file handling (AC: #3)
  - [x] 4.1: Write PDF to specified output path
  - [x] 4.2: Handle file overwrite gracefully
  - [x] 4.3: Create output directory if needed

- [x] Task 5: Performance optimization (AC: #5)
  - [x] 5.1: Profile WeasyPrint rendering time
  - [x] 5.2: Optimize CSS for fast rendering
  - [x] 5.3: Verify NFR2: <5 seconds

- [x] Task 6: Code quality verification
  - [x] 6.1: Run `ruff check src tests --fix`
  - [x] 6.2: Run `mypy src --strict` with zero errors
  - [x] 6.3: Add tests for PDF generation
  - [x] 6.4: Add visual inspection test artifacts

## Dev Notes

### Architecture Compliance

This story implements the PDF provider using WeasyPrint per Architecture Section 2.4.

**Source:** [epics.md#Story 5.2](_bmad-output/planning-artifacts/epics.md)

### Dependencies

This story REQUIRES:
- Story 5.1 (Resume Data Model & Template System)

This story ENABLES:
- Story 5.4 (Build Command)

### PDFProvider Implementation

**`src/resume_as_code/providers/pdf.py`:**

```python
"""PDF provider using WeasyPrint."""

from __future__ import annotations

from pathlib import Path

from weasyprint import HTML, CSS

from resume_as_code.models.resume import ResumeData
from resume_as_code.services.template_service import TemplateService


class PDFProvider:
    """Provider for generating PDF resumes."""

    def __init__(
        self,
        template_service: TemplateService | None = None,
        template_name: str = "modern",
    ) -> None:
        """Initialize PDF provider.

        Args:
            template_service: Template service for rendering.
            template_name: Name of template to use.
        """
        self.template_service = template_service or TemplateService()
        self.template_name = template_name

    def render(self, resume: ResumeData, output_path: Path) -> Path:
        """Render resume to PDF.

        Args:
            resume: ResumeData to render.
            output_path: Path for output PDF file.

        Returns:
            Path to generated PDF.
        """
        # Render HTML
        html_content = self.template_service.render(resume, self.template_name)

        # Get CSS
        css_content = self.template_service.get_css(self.template_name)

        # Ensure output directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Generate PDF
        html = HTML(string=html_content)
        css = CSS(string=css_content)

        html.write_pdf(
            output_path,
            stylesheets=[css],
        )

        return output_path

    def render_to_bytes(self, resume: ResumeData) -> bytes:
        """Render resume to PDF bytes.

        Useful for streaming or in-memory processing.

        Args:
            resume: ResumeData to render.

        Returns:
            PDF content as bytes.
        """
        html_content = self.template_service.render(resume, self.template_name)
        css_content = self.template_service.get_css(self.template_name)

        html = HTML(string=html_content)
        css = CSS(string=css_content)

        return html.write_pdf(stylesheets=[css])
```

### Enhanced CSS for PDF

**Update `templates/modern.css`:**

```css
/* Page setup for WeasyPrint */
@page {
    size: letter;
    margin: 0.75in;

    @bottom-center {
        content: counter(page);
        font-size: 9pt;
        color: #999;
    }
}

/* Prevent orphans and widows */
p, li {
    orphans: 2;
    widows: 2;
}

/* Page break control */
.job {
    page-break-inside: avoid;
}

h2 {
    page-break-after: avoid;
}

/* Print-specific styles */
@media print {
    body {
        font-size: 10pt;
    }

    a {
        text-decoration: none;
        color: inherit;
    }
}
```

### Testing Requirements

**`tests/unit/test_pdf_provider.py`:**

```python
"""Tests for PDF provider."""

from pathlib import Path

import pytest

from resume_as_code.models.resume import ResumeData, ContactInfo
from resume_as_code.providers.pdf import PDFProvider


@pytest.fixture
def sample_resume() -> ResumeData:
    """Create sample resume for testing."""
    return ResumeData(
        contact=ContactInfo(
            name="John Doe",
            email="john@example.com",
            phone="555-1234",
        ),
        summary="Experienced software engineer",
        skills=["Python", "AWS", "Kubernetes"],
    )


class TestPDFProvider:
    """Tests for PDFProvider."""

    def test_generates_pdf(self, sample_resume: ResumeData, tmp_path: Path):
        """Should generate a PDF file."""
        output_path = tmp_path / "resume.pdf"
        provider = PDFProvider()

        result = provider.render(sample_resume, output_path)

        assert result.exists()
        assert result.suffix == ".pdf"

        # Check it's a valid PDF (starts with %PDF)
        with open(result, "rb") as f:
            assert f.read(4) == b"%PDF"

    def test_creates_output_directory(self, sample_resume: ResumeData, tmp_path: Path):
        """Should create output directory if needed."""
        output_path = tmp_path / "nested" / "dir" / "resume.pdf"
        provider = PDFProvider()

        result = provider.render(sample_resume, output_path)

        assert result.exists()

    def test_render_to_bytes(self, sample_resume: ResumeData):
        """Should render PDF to bytes."""
        provider = PDFProvider()

        pdf_bytes = provider.render_to_bytes(sample_resume)

        assert pdf_bytes.startswith(b"%PDF")


class TestPDFPerformance:
    """Performance tests for PDF generation."""

    def test_renders_within_5_seconds(self, sample_resume: ResumeData, tmp_path: Path):
        """NFR2: PDF generation should complete within 5 seconds."""
        import time

        output_path = tmp_path / "resume.pdf"
        provider = PDFProvider()

        start = time.perf_counter()
        provider.render(sample_resume, output_path)
        elapsed = time.perf_counter() - start

        assert elapsed < 5.0, f"PDF generation took {elapsed:.2f}s (should be <5s)"
```

### Verification Commands

```bash
# Test PDF generation
python -c "
from pathlib import Path
from resume_as_code.models.resume import ResumeData, ContactInfo
from resume_as_code.providers.pdf import PDFProvider

resume = ResumeData(
    contact=ContactInfo(name='John Doe', email='john@example.com'),
    summary='Experienced engineer with 10+ years in Python',
    skills=['Python', 'AWS', 'Docker'],
)

provider = PDFProvider()
output = provider.render(resume, Path('test-resume.pdf'))
print(f'Generated: {output}')
"

# Open the PDF
open test-resume.pdf  # macOS

# Clean up
rm test-resume.pdf
```

### References

- [Source: epics.md#Story 5.2](_bmad-output/planning-artifacts/epics.md)

## Dev Agent Record

### Agent Model Used

Claude Opus 4.5 (claude-opus-4-5-20251101)

### Debug Log References

- WeasyPrint requires system dependencies (pango, cairo) on macOS
- Added automatic DYLD_LIBRARY_PATH configuration in tests/conftest.py

### Completion Notes List

- Created `PDFProvider` class using WeasyPrint for HTML→PDF conversion
- Provider uses `TemplateService` to render HTML and load CSS
- Added orphans/widows and page-break-after CSS rules for professional PDF layout
- Performance: 0.112s rendering time (NFR2 <5s requirement met)
- All 20 tests pass (18 original + 2 error handling), 842 total tests pass
- mypy --strict passes with type: ignore for untyped weasyprint import
- Configured DYLD_LIBRARY_PATH automatically for macOS in conftest.py

**Code Review Fixes (2026-01-11):**
- Added `RenderError` class to wrap WeasyPrint exceptions with actionable suggestions
- Added error handling tests for invalid template names
- Documented macOS platform requirements in README.md
- Updated File List with accurate file changes

### File List

- src/resume_as_code/providers/__init__.py (new)
- src/resume_as_code/providers/pdf.py (new - with RenderError handling)
- src/resume_as_code/templates/modern.css (modified - added orphans/widows and page-break-after CSS rules for PDF)
- src/resume_as_code/models/errors.py (modified - added RenderError class)
- src/resume_as_code/models/__init__.py (modified - exported RenderError)
- tests/conftest.py (modified - added WeasyPrint library path config for macOS)
- tests/unit/test_pdf_provider.py (new - 20 tests including error handling)
- README.md (modified - added macOS platform requirements for WeasyPrint)

