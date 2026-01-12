# Story 6.4: Executive Resume Template

Status: ready-for-dev

## Story

As a **user applying for senior positions**,
I want **an executive-format resume template**,
So that **my resume meets industry standards for leadership roles**.

## Acceptance Criteria

1. **Given** I run `resume build --jd file.txt --template executive`
   **When** the resume is generated
   **Then** the layout follows executive resume best practices:
     - Name prominently displayed (18-24pt)
     - Professional title below name
     - Contact info on single line with separators
     - Executive summary section (3-5 sentences)
     - Core competencies in categorized groups
     - Experience with scope indicators (budget, team size)
     - Certifications section
     - Education section
     - Skills as curated list (not dump)

2. **Given** the executive template renders
   **When** I inspect the PDF
   **Then** it uses professional typography (Calibri or similar)
   **And** single-column layout for ATS compatibility
   **And** strategic use of bold for section headers
   **And** accent color limited to section dividers (navy or dark gray)
   **And** 1-inch margins on all sides

3. **Given** work units have scope data (budget_managed, team_size)
   **When** the executive template renders
   **Then** scope indicators appear prominently:
     "Led team of 15 engineers | $2M budget | Global scope"

4. **Given** the resume content exceeds 1 page
   **When** the PDF is generated
   **Then** page breaks occur between sections (not mid-bullet)
   **And** header with name appears on page 2

5. **Given** I have an executive summary in profile config
   **When** the template renders
   **Then** the summary appears below contact info
   **And** it is 3-5 sentences focused on value proposition

6. **Given** no executive summary exists in config
   **When** the template renders
   **Then** a placeholder or auto-generated summary from top work units is shown

## Tasks / Subtasks

- [ ] Task 1: Create executive HTML template (AC: #1, #2)
  - [ ] 1.1: Create `templates/executive.html` with semantic structure
  - [ ] 1.2: Add header section (name, title, contact line)
  - [ ] 1.3: Add executive summary section
  - [ ] 1.4: Add experience section with scope indicators
  - [ ] 1.5: Add certifications section
  - [ ] 1.6: Add education section
  - [ ] 1.7: Add skills section (curated list)
  - [ ] 1.8: Use Jinja2 conditionals for optional sections

- [ ] Task 2: Create executive CSS styling (AC: #2)
  - [ ] 2.1: Create `templates/executive.css`
  - [ ] 2.2: Set professional font stack (Calibri, Segoe UI, Arial)
  - [ ] 2.3: Configure single-column layout
  - [ ] 2.4: Set color scheme (#1a1a1a text, #2c3e50 accent)
  - [ ] 2.5: Set 1-inch margins for print
  - [ ] 2.6: Style scope indicators
  - [ ] 2.7: Style section headers with subtle dividers

- [ ] Task 3: Handle page breaks (AC: #4)
  - [ ] 3.1: Add CSS page-break rules (avoid mid-section breaks)
  - [ ] 3.2: Add page 2+ header with name
  - [ ] 3.3: Test multi-page rendering with WeasyPrint

- [ ] Task 4: Scope indicators support (AC: #3)
  - [ ] 4.1: Extract scope data from work units (budget_managed, team_size, etc.)
  - [ ] 4.2: Format scope line for display
  - [ ] 4.3: Add scope rendering to template

- [ ] Task 5: Executive summary handling (AC: #5, #6)
  - [ ] 5.1: Load summary from profile.summary config
  - [ ] 5.2: Pass summary to template context
  - [ ] 5.3: Add placeholder text if no summary configured
  - [ ] 5.4: Consider auto-generation from top work units (optional)

- [ ] Task 6: Template registration (AC: #1)
  - [ ] 6.1: Register "executive" template in provider
  - [ ] 6.2: Update build command to accept --template executive
  - [ ] 6.3: Add executive to available templates list

- [ ] Task 7: Testing
  - [ ] 7.1: Add template rendering tests
  - [ ] 7.2: Test with sample work units containing scope data
  - [ ] 7.3: Test page break behavior
  - [ ] 7.4: Test with/without executive summary
  - [ ] 7.5: Visual inspection of generated PDF

- [ ] Task 8: Code quality verification
  - [ ] 8.1: Run `ruff check src tests --fix`
  - [ ] 8.2: Run `mypy src --strict` with zero errors
  - [ ] 8.3: Run `pytest` - all tests pass

## Dev Notes

### Architecture Compliance

This story implements FR42 (executive-format resume) per the PRD and Architecture Section 1.4 (Content Strategy Standards). The template follows research-validated executive resume best practices.

**Critical Rules from project-context.md:**
- Templates render gracefully when optional sections missing
- Use Jinja2 conditionals for all optional content
- Single-column layout for ATS compatibility (94-97% parsing accuracy)

**Research-Validated Standards (Architecture 1.4):**
- 2-3 pages for senior roles (two-page achieves 35% higher callback rate)
- Single-column preferred for ATS
- Sans-serif 10-12pt body (Calibri, Arial, Helvetica)
- Summary: 3-5 sentences, quantified
- Bullets per recent role: 4-6 (up to 8)
- Characters per bullet: 100-160

### Executive Template Structure

```html
<!-- templates/executive.html -->
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <link rel="stylesheet" href="executive.css">
</head>
<body>
  <header class="resume-header">
    <h1 class="name">{{ resume.contact.name }}</h1>
    {% if resume.contact.title %}
    <p class="professional-title">{{ resume.contact.title }}</p>
    {% endif %}
    <div class="contact-line">
      {% if resume.contact.location %}{{ resume.contact.location }}{% endif %}
      {% if resume.contact.email %} | {{ resume.contact.email }}{% endif %}
      {% if resume.contact.phone %} | {{ resume.contact.phone }}{% endif %}
      {% if resume.contact.linkedin %} | <a href="{{ resume.contact.linkedin }}">LinkedIn</a>{% endif %}
    </div>
  </header>

  {% if resume.summary %}
  <section class="executive-summary">
    <h2>Executive Summary</h2>
    <p>{{ resume.summary }}</p>
  </section>
  {% endif %}

  {% if resume.skills %}
  <section class="core-competencies">
    <h2>Core Competencies</h2>
    <div class="skills-grid">
      {% for skill in resume.skills %}
      <span class="skill">{{ skill }}</span>
      {% endfor %}
    </div>
  </section>
  {% endif %}

  <section class="experience">
    <h2>Professional Experience</h2>
    {% for entry in resume.experience %}
    <article class="position">
      <div class="position-header">
        <h3 class="company">{{ entry.company }}</h3>
        <span class="dates">{{ entry.start_date }} - {{ entry.end_date or "Present" }}</span>
      </div>
      <p class="role">{{ entry.title }}{% if entry.location %}, {{ entry.location }}{% endif %}</p>

      {% if entry.scope %}
      <p class="scope-line">{{ entry.scope }}</p>
      {% endif %}

      <ul class="achievements">
        {% for achievement in entry.achievements %}
        <li>{{ achievement }}</li>
        {% endfor %}
      </ul>
    </article>
    {% endfor %}
  </section>

  {% if resume.certifications %}
  <section class="certifications">
    <h2>Certifications</h2>
    <ul class="cert-list">
      {% for cert in resume.certifications %}
      <li>
        <strong>{{ cert.name }}</strong>
        {% if cert.issuer %}, {{ cert.issuer }}{% endif %}
        {% if cert.date %}, {{ cert.date[:4] }}{% endif %}
      </li>
      {% endfor %}
    </ul>
  </section>
  {% endif %}

  {% if resume.education %}
  <section class="education">
    <h2>Education</h2>
    {% for edu in resume.education %}
    <p>
      <strong>{{ edu.degree }}</strong>, {{ edu.institution }}
      {% if edu.year %}, {{ edu.year }}{% endif %}
      {% if edu.honors %} - {{ edu.honors }}{% endif %}
    </p>
    {% endfor %}
  </section>
  {% endif %}
</body>
</html>
```

### Executive CSS Styling

```css
/* templates/executive.css */

@page {
  size: letter;
  margin: 1in;
}

@page :not(:first) {
  @top-center {
    content: element(running-header);
  }
}

body {
  font-family: 'Calibri', 'Segoe UI', Arial, sans-serif;
  font-size: 11pt;
  line-height: 1.4;
  color: #1a1a1a;
  margin: 0;
  padding: 0;
}

/* Header */
.resume-header {
  text-align: center;
  margin-bottom: 1.5em;
  border-bottom: 2px solid #2c3e50;
  padding-bottom: 1em;
}

.name {
  font-size: 22pt;
  font-weight: bold;
  margin: 0;
  color: #1a1a1a;
}

.professional-title {
  font-size: 14pt;
  color: #2c3e50;
  margin: 0.25em 0;
}

.contact-line {
  font-size: 10pt;
  color: #555;
}

.contact-line a {
  color: #2c3e50;
  text-decoration: none;
}

/* Section Headers */
h2 {
  font-size: 12pt;
  font-weight: bold;
  color: #2c3e50;
  border-bottom: 1px solid #ddd;
  padding-bottom: 0.25em;
  margin-top: 1.25em;
  margin-bottom: 0.75em;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

/* Executive Summary */
.executive-summary p {
  text-align: justify;
  margin: 0;
}

/* Core Competencies */
.skills-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5em;
}

.skill {
  background: #f5f5f5;
  padding: 0.25em 0.75em;
  border-radius: 3px;
  font-size: 10pt;
}

/* Experience */
.position {
  margin-bottom: 1.25em;
  page-break-inside: avoid;
}

.position-header {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
}

.company {
  font-size: 11pt;
  font-weight: bold;
  margin: 0;
}

.dates {
  font-size: 10pt;
  color: #555;
}

.role {
  font-style: italic;
  margin: 0.25em 0;
}

.scope-line {
  font-size: 10pt;
  color: #2c3e50;
  font-weight: 500;
  margin: 0.5em 0;
}

.achievements {
  margin: 0.5em 0;
  padding-left: 1.25em;
}

.achievements li {
  margin-bottom: 0.35em;
}

/* Certifications */
.cert-list {
  list-style: none;
  padding: 0;
  margin: 0;
}

.cert-list li {
  margin-bottom: 0.35em;
}

/* Education */
.education p {
  margin: 0.35em 0;
}

/* Page break controls */
section {
  page-break-inside: avoid;
}

.position {
  page-break-inside: avoid;
}

/* Running header for page 2+ */
.running-header {
  position: running(running-header);
  font-size: 10pt;
  color: #555;
}
```

### Scope Indicators Formatting

```python
def format_scope_line(work_unit: WorkUnit) -> str | None:
    """Format scope indicators for executive template.

    Returns: "Led team of 15 engineers | $2M budget | Global scope"
    """
    parts = []

    scope = work_unit.scope or {}

    if team_size := scope.get("team_size"):
        parts.append(f"Led team of {team_size}")

    if budget := scope.get("budget_managed"):
        parts.append(f"{budget} budget")

    if revenue := scope.get("revenue_influenced"):
        parts.append(f"{revenue} revenue impact")

    if geo := scope.get("geographic_reach"):
        parts.append(geo)

    return " | ".join(parts) if parts else None
```

### ResumeData Extensions

```python
# Ensure ResumeData includes fields for executive template

@dataclass
class ExperienceEntry:
    """Single experience entry for resume."""
    company: str
    title: str
    start_date: str
    end_date: str | None
    location: str | None
    achievements: list[str]
    scope: str | None  # Formatted scope line
```

### Dependencies

This story REQUIRES:
- Story 6.1 (Profile Configuration) - profile.title, profile.summary
- Story 6.2 (Certifications) - certifications rendering
- Story 6.3 (Skills Curation) - curated skills list
- Story 5.1 (Resume Data Model) - ResumeData structure [DONE]
- Story 5.2 (PDF Provider) - WeasyPrint rendering [DONE]

This story ENABLES:
- Story 6.5 (Template Certifications Section) - builds on this
- Production-ready executive resumes

### Files to Create/Modify

**New Files:**
- `src/resume_as_code/templates/executive.html` - Executive template
- `src/resume_as_code/templates/executive.css` - Executive styling
- `tests/unit/test_executive_template.py` - Template tests

**Modified Files:**
- `src/resume_as_code/providers/pdf.py` - Register executive template
- `src/resume_as_code/commands/build.py` - Support --template executive
- `src/resume_as_code/models/resume.py` - Add scope/summary fields if needed

### Testing Strategy

```python
# tests/unit/test_executive_template.py

import pytest
from pathlib import Path

from resume_as_code.models.resume import ResumeData, ContactInfo
from resume_as_code.providers.pdf import PDFProvider


class TestExecutiveTemplate:
    """Tests for executive template rendering."""

    def test_template_exists(self):
        """Executive template files should exist."""
        templates_dir = Path("src/resume_as_code/templates")
        assert (templates_dir / "executive.html").exists()
        assert (templates_dir / "executive.css").exists()

    def test_renders_with_minimal_data(self, tmp_path):
        """Should render with minimal required data."""
        resume = ResumeData(
            contact=ContactInfo(name="Test User"),
            experience=[],
            skills=[],
        )
        provider = PDFProvider(template="executive")
        output = tmp_path / "test.pdf"

        provider.render(resume, output)

        assert output.exists()
        assert output.stat().st_size > 0

    def test_renders_executive_summary(self, tmp_path):
        """Should render executive summary when present."""
        resume = ResumeData(
            contact=ContactInfo(name="Test User"),
            summary="Experienced leader with 15+ years...",
            experience=[],
            skills=[],
        )
        provider = PDFProvider(template="executive")
        # Visual inspection needed for content verification

    def test_renders_scope_indicators(self, tmp_path):
        """Should render scope indicators for experience entries."""
        # Test with experience entries that have scope data
        pass

    def test_page_breaks_between_sections(self, tmp_path):
        """Should not break pages mid-section."""
        # Test with enough content for 2+ pages
        pass

    def test_certifications_section(self, tmp_path):
        """Should render certifications when present."""
        pass

    def test_graceful_absence_of_optional_sections(self, tmp_path):
        """Should render cleanly when optional sections missing."""
        pass
```

### Verification Commands

```bash
# After implementation, verify:
uv run ruff check src tests --fix
uv run mypy src --strict
uv run pytest tests/unit/test_executive_template.py -v

# Manual verification:
uv run resume build --jd examples/job-description.txt --template executive
# Open dist/resume.pdf and verify:
# - Name is prominent (18-24pt)
# - Single-column layout
# - Professional typography
# - Section dividers with accent color
# - Scope indicators displayed
# - Page breaks occur between sections
```

### Visual Design Checklist

- [ ] Name: 22pt, bold, centered
- [ ] Professional title: 14pt, accent color
- [ ] Contact line: 10pt, single line with separators
- [ ] Section headers: 12pt, uppercase, accent border
- [ ] Body text: 11pt, Calibri/Arial
- [ ] Margins: 1 inch all sides
- [ ] Color scheme: #1a1a1a text, #2c3e50 accent
- [ ] Single-column layout
- [ ] Page 2+ header with name

### References

- [Source: epics.md#Story 6.4](_bmad-output/planning-artifacts/epics.md)
- [Architecture: Content Strategy Standards](_bmad-output/planning-artifacts/architecture.md#1.4)
- [Architecture: Executive Templates](_bmad-output/planning-artifacts/architecture.md#2.3)
- [Related: Story 5.1 Resume Data Model](_bmad-output/implementation-artifacts/5-1-resume-data-model-template-system.md)

## Dev Agent Record

### Agent Model Used

{{agent_model_name_version}}

### Debug Log References

### Completion Notes List

### File List
