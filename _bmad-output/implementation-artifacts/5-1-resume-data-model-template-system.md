# Story 5.1: Resume Data Model & Template System

Status: done

## Story

As a **developer**,
I want **a structured resume data model and template infrastructure**,
So that **providers can render consistent output across formats**.

## Acceptance Criteria

1. **Given** the models directory exists
   **When** I inspect `models/resume.py`
   **Then** I find a `ResumeData` model with: contact info, summary, work units, skills
   **And** I find a `ResumeSection` model for grouping content

2. **Given** selected Work Units from a plan
   **When** I build a ResumeData instance
   **Then** Work Units are transformed into resume-ready format
   **And** problem/action/outcome becomes achievement bullets

3. **Given** the templates directory exists
   **When** I inspect `templates/modern.html`
   **Then** I find a Jinja2 template for PDF rendering
   **And** it uses `{{ resume.name }}`, `{{ resume.sections }}`, etc.

4. **Given** a ResumeData instance and a template
   **When** Jinja2 renders the template
   **Then** all placeholders are replaced with actual data
   **And** the output is valid HTML

5. **Given** the template system
   **When** I create a new template
   **Then** I only need to create HTML/CSS files
   **And** the provider automatically discovers and uses them

6. **Given** executive templates exist
   **When** I inspect `templates/executive.html`
   **Then** I find a 2-3 page layout optimized for senior professionals
   **And** it displays scope indicators (budget, team size, revenue) when present

## Tasks / Subtasks

- [x] Task 1: Create ResumeData model (AC: #1, #2)
  - [x] 1.1: Create `src/resume_as_code/models/resume.py`
  - [x] 1.2: Define `ContactInfo` model (name, email, phone, location, links)
  - [x] 1.3: Define `ResumeSection` model (title, items)
  - [x] 1.4: Define `ResumeItem` model (title, organization, dates, bullets)
  - [x] 1.5: Define `ResumeData` model (contact, summary, sections, skills)
  - [x] 1.6: Implement `from_work_units()` factory method

- [x] Task 2: Create template service (AC: #3, #4, #5)
  - [x] 2.1: Create `src/resume_as_code/services/template_service.py`
  - [x] 2.2: Implement template discovery (list available templates)
  - [x] 2.3: Implement template loading with Jinja2
  - [x] 2.4: Implement `render(resume: ResumeData, template: str) -> str`

- [x] Task 3: Create modern template (AC: #3, #4)
  - [x] 3.1: Create `templates/modern.html` with Jinja2 placeholders
  - [x] 3.2: Create `templates/modern.css` with professional styling
  - [x] 3.3: Support letter/A4 page sizes
  - [x] 3.4: Add print-friendly styles

- [x] Task 4: Create executive template (AC: #6)
  - [x] 4.1: Create `templates/executive.html` for 2-3 page layout
  - [x] 4.2: Create `templates/executive.css` with scope indicator styling
  - [x] 4.3: Support RAS (Results-Action-Situation) bullet format
  - [x] 4.4: Add professional summary section

- [x] Task 5: Create ATS-safe template (AC: #5)
  - [x] 5.1: Create `templates/ats-safe.html` single-column layout
  - [x] 5.2: Use standard section headers
  - [x] 5.3: Minimize formatting for parseability

- [x] Task 6: Code quality verification
  - [x] 6.1: Run `ruff check src tests --fix`
  - [x] 6.2: Run `mypy src --strict` with zero errors
  - [x] 6.3: Add tests for ResumeData model
  - [x] 6.4: Add tests for template rendering

## Dev Notes

### Architecture Compliance

This story provides the foundation for all resume output. The ResumeData model is provider-agnostic.

**Source:** [epics.md#Story 5.1](_bmad-output/planning-artifacts/epics.md)

### Dependencies

This story REQUIRES:
- Story 2.1 (Work Unit Schema) - Work Unit models

This story ENABLES:
- Story 5.2 (PDF Provider)
- Story 5.3 (DOCX Provider)
- Story 5.4 (Build Command)

### ResumeData Model

**`src/resume_as_code/models/resume.py`:**

```python
"""Resume data models for output generation."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import TYPE_CHECKING

from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from resume_as_code.services.ranker import RankingResult


class ContactInfo(BaseModel):
    """Contact information for resume header."""

    name: str
    email: str | None = None
    phone: str | None = None
    location: str | None = None
    linkedin: str | None = None
    github: str | None = None
    website: str | None = None


class ResumeBullet(BaseModel):
    """A single achievement bullet point."""

    text: str
    metrics: str | None = None  # Quantified impact


class ResumeItem(BaseModel):
    """A single experience entry (job, project, etc.)."""

    title: str
    organization: str | None = None
    location: str | None = None
    start_date: str | None = None
    end_date: str | None = None
    bullets: list[ResumeBullet] = Field(default_factory=list)

    # Executive fields
    scope_budget: str | None = None
    scope_team_size: int | None = None
    scope_revenue: str | None = None


class ResumeSection(BaseModel):
    """A section of the resume (Experience, Projects, etc.)."""

    title: str
    items: list[ResumeItem] = Field(default_factory=list)


class ResumeData(BaseModel):
    """Complete resume data for rendering."""

    contact: ContactInfo
    summary: str | None = None
    sections: list[ResumeSection] = Field(default_factory=list)
    skills: list[str] = Field(default_factory=list)
    education: list[ResumeItem] = Field(default_factory=list)

    @classmethod
    def from_work_units(
        cls,
        work_units: list[dict],
        contact: ContactInfo,
        summary: str | None = None,
    ) -> "ResumeData":
        """Build ResumeData from selected Work Units.

        Transforms Work Units into resume-ready format, converting
        problem/action/outcome into achievement bullets.
        """
        # Group Work Units into Experience section
        experience_items: list[ResumeItem] = []

        for wu in work_units:
            bullets = cls._extract_bullets(wu)
            item = ResumeItem(
                title=wu.get("title", ""),
                organization=wu.get("organization"),
                start_date=cls._format_date(wu.get("time_started")),
                end_date=cls._format_date(wu.get("time_ended")),
                bullets=bullets,
                scope_budget=wu.get("scope", {}).get("budget_managed"),
                scope_team_size=wu.get("scope", {}).get("team_size"),
                scope_revenue=wu.get("scope", {}).get("revenue_influenced"),
            )
            experience_items.append(item)

        sections = [
            ResumeSection(title="Experience", items=experience_items),
        ]

        # Extract skills from all Work Units
        all_skills: set[str] = set()
        for wu in work_units:
            all_skills.update(wu.get("tags", []))
            all_skills.update(wu.get("skills_demonstrated", []))

        return cls(
            contact=contact,
            summary=summary,
            sections=sections,
            skills=sorted(all_skills),
        )

    @staticmethod
    def _extract_bullets(work_unit: dict) -> list[ResumeBullet]:
        """Extract achievement bullets from Work Unit."""
        bullets: list[ResumeBullet] = []

        # Main outcome as primary bullet
        outcome = work_unit.get("outcome", {})
        if result := outcome.get("result"):
            bullets.append(ResumeBullet(
                text=result,
                metrics=outcome.get("quantified_impact"),
            ))

        # Actions as supporting bullets
        for action in work_unit.get("actions", [])[:3]:  # Limit to 3 actions
            bullets.append(ResumeBullet(text=action))

        return bullets

    @staticmethod
    def _format_date(d) -> str | None:
        """Format date for display."""
        if d is None:
            return None
        if isinstance(d, date):
            return d.strftime("%b %Y")
        if isinstance(d, str) and len(d) >= 7:
            return d[:7]  # YYYY-MM
        return str(d)
```

### Template Service

**`src/resume_as_code/services/template_service.py`:**

```python
"""Template service for resume rendering."""

from __future__ import annotations

from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

from resume_as_code.models.resume import ResumeData


class TemplateService:
    """Service for rendering resumes with Jinja2 templates."""

    def __init__(self, templates_dir: Path | None = None) -> None:
        """Initialize template service.

        Args:
            templates_dir: Path to templates directory.
        """
        if templates_dir is None:
            templates_dir = Path(__file__).parent.parent / "templates"

        self.templates_dir = templates_dir
        self.env = Environment(
            loader=FileSystemLoader(templates_dir),
            autoescape=select_autoescape(["html", "xml"]),
        )

    def list_templates(self) -> list[str]:
        """List available template names."""
        templates = []
        for path in self.templates_dir.glob("*.html"):
            if not path.name.startswith("_"):  # Skip partials
                templates.append(path.stem)
        return sorted(templates)

    def render(self, resume: ResumeData, template_name: str = "modern") -> str:
        """Render resume to HTML.

        Args:
            resume: ResumeData to render.
            template_name: Name of template (without .html extension).

        Returns:
            Rendered HTML string.
        """
        template = self.env.get_template(f"{template_name}.html")
        return template.render(resume=resume)

    def get_css(self, template_name: str = "modern") -> str:
        """Get CSS for a template.

        Args:
            template_name: Name of template.

        Returns:
            CSS content.
        """
        css_path = self.templates_dir / f"{template_name}.css"
        if css_path.exists():
            return css_path.read_text()
        return ""
```

### Modern Template

**`templates/modern.html`:**

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>{{ resume.contact.name }} - Resume</title>
    <style>{{ css }}</style>
</head>
<body>
    <header>
        <h1>{{ resume.contact.name }}</h1>
        <div class="contact-info">
            {% if resume.contact.email %}
            <span>{{ resume.contact.email }}</span>
            {% endif %}
            {% if resume.contact.phone %}
            <span>{{ resume.contact.phone }}</span>
            {% endif %}
            {% if resume.contact.location %}
            <span>{{ resume.contact.location }}</span>
            {% endif %}
        </div>
        {% if resume.contact.linkedin or resume.contact.github %}
        <div class="links">
            {% if resume.contact.linkedin %}
            <a href="{{ resume.contact.linkedin }}">LinkedIn</a>
            {% endif %}
            {% if resume.contact.github %}
            <a href="{{ resume.contact.github }}">GitHub</a>
            {% endif %}
        </div>
        {% endif %}
    </header>

    {% if resume.summary %}
    <section class="summary">
        <h2>Summary</h2>
        <p>{{ resume.summary }}</p>
    </section>
    {% endif %}

    {% for section in resume.sections %}
    <section class="experience">
        <h2>{{ section.title }}</h2>
        {% for item in section.items %}
        <article class="job">
            <div class="job-header">
                <h3>{{ item.title }}</h3>
                {% if item.organization %}
                <span class="company">{{ item.organization }}</span>
                {% endif %}
                {% if item.start_date %}
                <span class="dates">{{ item.start_date }} - {{ item.end_date or 'Present' }}</span>
                {% endif %}
            </div>
            {% if item.bullets %}
            <ul>
                {% for bullet in item.bullets %}
                <li>{{ bullet.text }}</li>
                {% endfor %}
            </ul>
            {% endif %}
        </article>
        {% endfor %}
    </section>
    {% endfor %}

    {% if resume.skills %}
    <section class="skills">
        <h2>Skills</h2>
        <p>{{ resume.skills | join(', ') }}</p>
    </section>
    {% endif %}
</body>
</html>
```

**`templates/modern.css`:**

```css
@page {
    size: letter;
    margin: 0.75in;
}

body {
    font-family: 'Helvetica Neue', Arial, sans-serif;
    font-size: 11pt;
    line-height: 1.4;
    color: #333;
    max-width: 8.5in;
    margin: 0 auto;
}

header {
    text-align: center;
    margin-bottom: 1em;
    border-bottom: 2px solid #2c3e50;
    padding-bottom: 0.5em;
}

header h1 {
    margin: 0;
    font-size: 24pt;
    color: #2c3e50;
}

.contact-info {
    margin-top: 0.5em;
}

.contact-info span {
    margin: 0 0.5em;
}

h2 {
    font-size: 14pt;
    color: #2c3e50;
    border-bottom: 1px solid #bdc3c7;
    padding-bottom: 0.25em;
    margin-top: 1em;
    margin-bottom: 0.5em;
}

.job {
    margin-bottom: 1em;
}

.job-header {
    display: flex;
    justify-content: space-between;
    align-items: baseline;
    flex-wrap: wrap;
}

.job-header h3 {
    margin: 0;
    font-size: 12pt;
}

.company {
    font-style: italic;
}

.dates {
    color: #7f8c8d;
    font-size: 10pt;
}

ul {
    margin: 0.5em 0;
    padding-left: 1.5em;
}

li {
    margin-bottom: 0.25em;
}

.skills p {
    margin: 0;
}
```

### Verification Commands

```bash
# Test template rendering
python -c "
from resume_as_code.models.resume import ResumeData, ContactInfo
from resume_as_code.services.template_service import TemplateService

contact = ContactInfo(name='John Doe', email='john@example.com')
resume = ResumeData(contact=contact, summary='Experienced engineer')

service = TemplateService()
html = service.render(resume, 'modern')
print(html[:500])
"

# List available templates
python -c "
from resume_as_code.services.template_service import TemplateService
print(TemplateService().list_templates())
"
```

### References

- [Source: epics.md#Story 5.1](_bmad-output/planning-artifacts/epics.md)

## Dev Agent Record

### Agent Model Used

Claude Opus 4.5 (claude-opus-4-5-20251101)

### Debug Log References

### Completion Notes List

- Task 1: Created ResumeData model with ContactInfo, ResumeBullet, ResumeItem, ResumeSection models. Implemented from_work_units() factory method that transforms Work Units into resume-ready format, extracts skills from tags and skills_demonstrated, and formats dates. Added 17 unit tests covering all models and edge cases. All tests pass, mypy --strict passes.
- Task 2: Created TemplateService with list_templates(), render(), and get_css() methods. Uses Jinja2 Environment with FileSystemLoader and HTML autoescaping. Template discovery excludes partials (files starting with underscore). Added 16 unit tests. All tests pass, mypy --strict passes.
- Task 3: Created modern.html template with Jinja2 placeholders for contact, summary, sections, education, and skills. Created modern.css with @page rules for letter size (with A4 variant commented), professional styling, and @media print styles. Added 10 integration tests. All tests pass.
- Task 4: Created executive.html template optimized for senior professionals with 2-3 page layout. Features scope indicators (budget, team size, revenue), Executive Summary section, RAS-format achievement bullets with inline metrics, Core Competencies grid. Created executive.css with gradient backgrounds for scope indicators and serif typography. Added 7 integration tests. All tests pass.
- Task 5: Created ats-safe.html template optimized for ATS parseability. Features single-column layout, standard uppercase section headers (PROFESSIONAL SUMMARY, SKILLS, EXPERIENCE, EDUCATION), pipe-separated contact info and skills, minimal CSS without flex/grid. Added 7 integration tests. All tests pass.
- Task 6: Final code quality verification completed. ruff check/format passes, mypy --strict passes with zero errors. Full test suite passes: 817 tests (40 new tests added for this story).

### File List

- src/resume_as_code/models/resume.py (created)
- src/resume_as_code/models/__init__.py (modified - added exports)
- src/resume_as_code/services/template_service.py (created, modified during review)
- src/resume_as_code/services/__init__.py (modified - added TemplateService export)
- src/resume_as_code/templates/modern.html (created)
- src/resume_as_code/templates/modern.css (created)
- src/resume_as_code/templates/executive.html (created)
- src/resume_as_code/templates/executive.css (created)
- src/resume_as_code/templates/ats-safe.html (created)
- src/resume_as_code/templates/ats-safe.css (created)
- tests/unit/test_resume_model.py (created)
- tests/unit/test_template_service.py (created, modified during review)
- tests/integration/test_template_rendering.py (created, modified during review)

## Senior Developer Review (AI)

**Review Date:** 2026-01-11
**Reviewer:** Claude Opus 4.5 (Adversarial Code Review)

### Issues Found and Remediated

| Severity | Issue | Resolution |
|----------|-------|------------|
| HIGH | CSS not injected into templates - `render()` only passed `resume` but templates expected `css` variable | Fixed: Added `css = self.get_css(template_name)` and passed to `template.render(resume=resume, css=css)` |
| HIGH | TemplateService not exported from services `__init__.py` | Fixed: Added import and export to services package |
| MEDIUM | No tests for CSS injection into rendered HTML | Fixed: Added `TestCSSInjection` test class with 2 tests |
| MEDIUM | Fragile ATS template test with confusing boolean logic | Fixed: Simplified test to directly check CSS content |
| MEDIUM | No end-to-end integration test for Work Units → HTML | Fixed: Added `TestEndToEndWorkUnitToHTML` with 3 tests |
| LOW | Unit test fixtures missing `{{ css }}` placeholder | Fixed: Updated test template fixtures |

### Verification

- All 45 template-related tests pass
- mypy --strict passes with zero errors
- ruff check passes with no errors
- CSS now correctly injected into all three templates (modern, executive, ats-safe)

