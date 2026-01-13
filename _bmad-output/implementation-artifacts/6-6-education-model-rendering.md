# Story 6.6: Education Model & Rendering

Status: done

## Story

As a **user**,
I want **to include my education on the resume**,
So that **degree requirements are visibly met**.

## Acceptance Criteria

1. **Given** I add education to `.resume.yaml`
   **When** the config is:
   ```yaml
   education:
     - degree: "Bachelor of Science in Computer Science"
       institution: "University of Texas at Austin"
       year: "2012"
       honors: "Magna Cum Laude"
     - degree: "Master of Science in Cybersecurity"
       institution: "Georgia Tech"
       year: "2018"
   ```
   **Then** the config loads and validates successfully

2. **Given** education exists in config
   **When** the resume is generated
   **Then** an "Education" section appears
   **And** degrees are listed with institution and year

3. **Given** education has honors/GPA
   **When** it renders
   **Then** honors appear: "BS Computer Science, UT Austin, 2012 - Magna Cum Laude"

4. **Given** no education exists in config
   **When** the resume is generated
   **Then** no Education section appears (graceful absence)

5. **Given** I'm a senior professional (10+ years experience)
   **When** the resume is generated
   **Then** Education appears after Experience (industry standard for senior roles)

## Tasks / Subtasks

- [x] Task 1: Create Education model (AC: #1)
  - [x] 1.1: Create `Education` Pydantic model in `models/education.py`
  - [x] 1.2: Add fields: degree, institution, year, honors, gpa, display
  - [x] 1.3: Add year validation (YYYY format)
  - [x] 1.4: Add `education: list[Education]` field to `ResumeConfig`

- [x] Task 2: Update ResumeData model (AC: #2, #4)
  - [x] 2.1: Add `education: list[Education]` to `ResumeData`
  - [x] 2.2: Load education from config in build command
  - [x] 2.3: Handle empty education list gracefully

- [x] Task 3: Update templates (AC: #2, #3, #5)
  - [x] 3.1: Add education section to `modern.html`
  - [x] 3.2: Add education section to `executive.html`
  - [x] 3.3: Add education section to `ats-safe.html`
  - [x] 3.4: Position after Experience for all templates
  - [x] 3.5: Format with degree, institution, year, honors
  - [x] 3.6: Add CSS styling for education sections
  - [x] 3.7: Add education section to `executive-classic.html` (bonus)

- [x] Task 4: Update DOCX provider (AC: #2, #3)
  - [x] 4.1: Add `_add_education_item()` method
  - [x] 4.2: Use Word heading style for section
  - [x] 4.3: Format education entries consistently
  - [x] 4.4: Filter by display field

- [x] Task 5: Testing
  - [x] 5.1: Add unit tests for Education model validation
  - [x] 5.2: Add tests for education loading from config
  - [x] 5.3: Add tests for template rendering with education
  - [x] 5.4: Add tests for honors/GPA display
  - [x] 5.5: Add tests for empty education handling
  - [x] 5.6: Update existing test fixtures to use Education model

- [x] Task 6: Code quality verification
  - [x] 6.1: Run `ruff check src tests --fix`
  - [x] 6.2: Run `mypy src --strict` with zero errors
  - [x] 6.3: Run `pytest` - all 1114 tests pass

## Dev Notes

### Architecture Compliance

This story adds education storage and rendering following the same patterns as Story 6.2 (Certifications). Education is positioned after Experience per industry standards for senior professionals (Architecture Section 1.4).

**Critical Rules from project-context.md:**
- Use `|` union syntax for optional fields (Python 3.10+)
- Templates render gracefully when optional sections missing
- Use Jinja2 conditionals for all optional content

**Industry Standards (Architecture 1.4):**
- For senior roles (10+ years), education appears after experience
- Focus on degree and institution; GPA optional for experienced professionals
- Honors/distinctions add credibility

### Education Model Design

```python
# src/resume_as_code/models/education.py

from __future__ import annotations

from pydantic import BaseModel, Field, field_validator


class Education(BaseModel):
    """Educational credential record."""

    degree: str
    institution: str
    year: str | None = None  # YYYY format
    honors: str | None = None  # e.g., "Magna Cum Laude", "With Distinction"
    gpa: str | None = None  # e.g., "3.8/4.0"
    display: bool = Field(default=True)  # Allow hiding without deleting

    @field_validator("year", mode="before")
    @classmethod
    def validate_year_format(cls, v: str | None) -> str | None:
        """Validate YYYY year format."""
        if v is None:
            return None
        # Accept YYYY or strip to YYYY if longer
        import re
        if not re.match(r"^\d{4}", str(v)):
            raise ValueError("Year must be in YYYY format")
        return str(v)[:4]

    def format_display(self) -> str:
        """Format education for resume display.

        Examples:
        - "BS Computer Science, UT Austin, 2012 - Magna Cum Laude"
        - "MS Cybersecurity, Georgia Tech, 2018"
        - "MBA, Harvard Business School"
        """
        parts = [self.degree, self.institution]

        if self.year:
            parts.append(self.year)

        base = ", ".join(parts)

        if self.honors:
            base += f" - {self.honors}"

        if self.gpa and not self.honors:
            base += f" (GPA: {self.gpa})"

        return base
```

### Updated ResumeConfig

```python
# In models/config.py

from resume_as_code.models.education import Education

class ResumeConfig(BaseModel):
    """Complete configuration for Resume as Code."""

    # ... existing fields ...

    # Education (NEW)
    education: list[Education] = Field(default_factory=list)
```

### Template Updates

#### Modern Template

```html
<!-- In templates/modern.html - add after Experience section -->

{% if resume.education %}
<section class="education">
  <h2>Education</h2>
  {% for edu in resume.education %}
  {% if edu.display is not defined or edu.display %}
  <div class="edu-entry">
    <p>
      <strong>{{ edu.degree }}</strong>, {{ edu.institution }}
      {%- if edu.year %}, {{ edu.year }}{% endif %}
      {%- if edu.honors %} - {{ edu.honors }}{% endif %}
      {%- if edu.gpa and not edu.honors %} (GPA: {{ edu.gpa }}){% endif %}
    </p>
  </div>
  {% endif %}
  {% endfor %}
</section>
{% endif %}
```

#### Executive Template

```html
<!-- In templates/executive.html - add after Experience section -->

{% if resume.education %}
<section class="education">
  <h2>Education</h2>
  {% for edu in resume.education %}
  {% if edu.display is not defined or edu.display %}
  <p class="edu-entry">
    <strong>{{ edu.degree }}</strong><br>
    {{ edu.institution }}{% if edu.year %}, {{ edu.year }}{% endif %}
    {% if edu.honors %}<span class="honors">{{ edu.honors }}</span>{% endif %}
  </p>
  {% endif %}
  {% endfor %}
</section>
{% endif %}
```

#### ATS-Safe Template

```html
<!-- In templates/ats-safe.html - add after Experience section -->

{% if resume.education %}
<section>
  <h2>EDUCATION</h2>
  {% for edu in resume.education %}
  {% if edu.display is not defined or edu.display %}
  <p>{{ edu.degree }}, {{ edu.institution }}{% if edu.year %}, {{ edu.year }}{% endif %}{% if edu.honors %} - {{ edu.honors }}{% endif %}</p>
  {% endif %}
  {% endfor %}
</section>
{% endif %}
```

### CSS Styling

```css
/* Modern template - templates/modern.css */

.education {
  margin-top: 1.5em;
}

.education h2 {
  font-size: 14pt;
  border-bottom: 1px solid #333;
  padding-bottom: 0.25em;
  margin-bottom: 0.5em;
}

.edu-entry {
  margin-bottom: 0.5em;
}

.edu-entry p {
  margin: 0;
}

/* Executive template - templates/executive.css */

.education {
  margin-top: 1.25em;
}

.edu-entry {
  margin-bottom: 0.75em;
}

.edu-entry .honors {
  display: block;
  font-style: italic;
  color: #555;
  font-size: 10pt;
}
```

### DOCX Provider Update

```python
# In providers/docx.py

def _add_education_section(
    self,
    document: Document,
    education: list[Education],
) -> None:
    """Add education section to DOCX."""
    if not education:
        return

    # Add section heading
    document.add_heading("Education", level=2)

    for edu in education:
        if edu.display is False:
            continue

        # Format: "Degree, Institution, Year - Honors"
        parts = [edu.degree, edu.institution]
        if edu.year:
            parts.append(edu.year)

        text = ", ".join(parts)
        if edu.honors:
            text += f" - {edu.honors}"
        elif edu.gpa:
            text += f" (GPA: {edu.gpa})"

        p = document.add_paragraph(text)
        p.style = "Normal"
```

### Example .resume.yaml

```yaml
# Education
education:
  - degree: "Bachelor of Science in Computer Science"
    institution: "University of Texas at Austin"
    year: "2012"
    honors: "Magna Cum Laude"

  - degree: "Master of Science in Cybersecurity"
    institution: "Georgia Tech"
    year: "2018"

  - degree: "Associate Degree in IT"
    institution: "Austin Community College"
    year: "2008"
    display: false  # Hide older/less relevant degree
```

### Dependencies

This story REQUIRES:
- Story 6.1 (Profile Configuration) - Config pattern established
- Story 6.4 (Executive Template) - Base executive template
- Story 6.5 (Template Certifications) - Template update patterns
- Story 5.1-5.3 (Resume Data, PDF, DOCX) ✓ DONE

This story ENABLES:
- Story 6.12 (Education Management Commands)
- Complete resume with all standard sections

### Files to Create/Modify

**New Files:**
- `src/resume_as_code/models/education.py` - Education model
- `tests/unit/test_education.py` - Unit tests

**Modified Files:**
- `src/resume_as_code/models/config.py` - Add education list
- `src/resume_as_code/models/resume.py` - Add education to ResumeData
- `src/resume_as_code/commands/build.py` - Load and pass education
- `src/resume_as_code/templates/modern.html` - Add education section
- `src/resume_as_code/templates/modern.css` - Add education styling
- `src/resume_as_code/templates/executive.html` - Add education section
- `src/resume_as_code/templates/executive.css` - Add education styling
- `src/resume_as_code/templates/ats-safe.html` - Add education section
- `src/resume_as_code/providers/docx.py` - Add `_add_education_section()`

### Testing Strategy

```python
# tests/unit/test_education.py

import pytest
from pydantic import ValidationError

from resume_as_code.models.education import Education


class TestEducationModel:
    """Tests for Education model."""

    def test_minimal_education(self):
        """Should create education with required fields only."""
        edu = Education(
            degree="BS Computer Science",
            institution="MIT",
        )
        assert edu.degree == "BS Computer Science"
        assert edu.institution == "MIT"
        assert edu.year is None
        assert edu.honors is None

    def test_full_education(self):
        """Should create education with all fields."""
        edu = Education(
            degree="BS Computer Science",
            institution="UT Austin",
            year="2012",
            honors="Magna Cum Laude",
            gpa="3.8/4.0",
        )
        assert edu.year == "2012"
        assert edu.honors == "Magna Cum Laude"

    def test_year_validation(self):
        """Should validate YYYY format."""
        edu = Education(
            degree="BS",
            institution="School",
            year="2012",
        )
        assert edu.year == "2012"

    def test_year_normalization(self):
        """Should normalize longer date to YYYY."""
        edu = Education(
            degree="BS",
            institution="School",
            year="2012-05",
        )
        assert edu.year == "2012"

    def test_invalid_year(self):
        """Should reject invalid year format."""
        with pytest.raises(ValidationError):
            Education(
                degree="BS",
                institution="School",
                year="invalid",
            )

    def test_format_display_full(self):
        """Should format with all components."""
        edu = Education(
            degree="BS Computer Science",
            institution="UT Austin",
            year="2012",
            honors="Magna Cum Laude",
        )
        display = edu.format_display()
        assert "BS Computer Science" in display
        assert "UT Austin" in display
        assert "2012" in display
        assert "Magna Cum Laude" in display

    def test_format_display_minimal(self):
        """Should format with minimal data."""
        edu = Education(
            degree="MBA",
            institution="Harvard",
        )
        display = edu.format_display()
        assert display == "MBA, Harvard"

    def test_display_flag(self):
        """Should support display flag for hiding."""
        edu = Education(
            degree="Old Degree",
            institution="Old School",
            display=False,
        )
        assert edu.display is False


class TestEducationInConfig:
    """Tests for education in configuration."""

    def test_loads_education_from_yaml(self, tmp_path):
        """Should load education list from .resume.yaml."""
        from resume_as_code.config import get_config

        config_file = tmp_path / ".resume.yaml"
        config_file.write_text("""
education:
  - degree: "BS Computer Science"
    institution: "MIT"
    year: "2015"
""")
        config = get_config(tmp_path)
        assert len(config.education) == 1
        assert config.education[0].degree == "BS Computer Science"

    def test_empty_education_default(self, tmp_path):
        """Should default to empty list."""
        from resume_as_code.config import get_config

        config_file = tmp_path / ".resume.yaml"
        config_file.write_text("output_dir: ./dist")

        config = get_config(tmp_path)
        assert config.education == []
```

### Verification Commands

```bash
# After implementation, verify:
uv run ruff check src tests --fix
uv run mypy src --strict
uv run pytest tests/unit/test_education.py -v

# Manual verification:
# Add education to .resume.yaml
uv run resume build --jd examples/job-description.txt --template modern
uv run resume build --jd examples/job-description.txt --template executive

# Check each output:
# - Education section present after Experience
# - Degree, institution, year displayed
# - Honors/GPA displayed when present
# - Hidden education not displayed
```

### Section Ordering (Industry Standard)

For senior professionals (10+ years), sections should appear in this order:
1. Header (Name, Title, Contact)
2. Executive Summary
3. Core Competencies / Skills
4. Professional Experience
5. **Education** (after Experience for senior roles)
6. Certifications
7. Additional sections (optional)

### References

- [Source: epics.md#Story 6.6](_bmad-output/planning-artifacts/epics.md)
- [Architecture: Content Strategy Standards](_bmad-output/planning-artifacts/architecture.md#1.4)
- [Related: Story 6.2 Certifications Model](_bmad-output/implementation-artifacts/6-2-certifications-model-storage.md)

## Dev Agent Record

### Agent Model Used

Claude Opus 4.5 (claude-opus-4-5-20251101)

### Debug Log References

N/A

### Completion Notes List

- Created `Education` Pydantic model in `src/resume_as_code/models/education.py` with degree, institution, year, honors, gpa, and display fields
- Added year validation that normalizes longer date formats (e.g., "2012-05-15") to YYYY format
- Implemented `format_display()` method for consistent education formatting
- Updated `ResumeConfig` in `models/config.py` to include `education: list[Education]`
- Changed `ResumeData` education field type from `list[ResumeItem]` to `list[Education]`
- Updated `build.py` to load education from config
- Updated all 4 HTML templates (modern, executive, ats-safe, executive-classic) with education sections
- Updated corresponding CSS files with education styling
- Positioned education after Experience and before Certifications in all templates (industry standard for senior roles)
- Updated DOCX provider with `_add_education_item()` method that filters by display field
- Created comprehensive test suite in `tests/unit/test_education.py` with 22 tests
- Updated test fixtures in test_docx_provider.py, test_executive_template.py, test_pdf_provider.py, and test_template_rendering.py to use Education model instead of ResumeItem
- All 1114 tests pass, ruff check clean, mypy strict passes

**Code Review Fixes (2026-01-12):**
- Added `.edu-entry` CSS class to ats-safe.css for consistent education styling
- Added `class="edu-entry"` to ats-safe.html education entries
- Added integration tests for education rendering in ats-safe, executive, and executive-classic templates
- Added DOCX education ordering test to verify AC#5 (education appears after experience)

**Section Ordering Verification (AC#5):**
- modern.html: Experience → Education → Certifications → Skills ✓
- executive.html: Skills → Experience → Education → Certifications ✓
- executive-classic.html: Experience → Education → Certifications → Skills ✓
- ats-safe.html: Skills → Experience → Education → Certifications ✓
- DOCX: Experience → Education → Certifications → Skills ✓
- All templates position Education after Experience per industry standard

**Design Decision - format_display() Method:**
- The `Education.format_display()` method exists but is intentionally NOT used in templates
- Templates use inline Jinja2 formatting for template-specific control (e.g., executive uses `<br>` between degree and institution, modern uses inline commas)
- The method remains available for programmatic use cases (e.g., text-only exports, CLI display)

### File List

**Created:**
- `src/resume_as_code/models/education.py`
- `tests/unit/test_education.py`

**Modified:**
- `src/resume_as_code/models/config.py`
- `src/resume_as_code/models/resume.py`
- `src/resume_as_code/commands/build.py`
- `src/resume_as_code/templates/modern.html`
- `src/resume_as_code/templates/modern.css`
- `src/resume_as_code/templates/executive.html`
- `src/resume_as_code/templates/executive.css`
- `src/resume_as_code/templates/ats-safe.html`
- `src/resume_as_code/templates/ats-safe.css`
- `src/resume_as_code/templates/executive-classic.html`
- `src/resume_as_code/templates/executive-classic.css`
- `src/resume_as_code/providers/docx.py`
- `tests/unit/test_resume_model.py`
- `tests/unit/test_docx_provider.py`
- `tests/unit/test_executive_template.py`
- `tests/unit/test_pdf_provider.py`
- `tests/integration/test_template_rendering.py`
