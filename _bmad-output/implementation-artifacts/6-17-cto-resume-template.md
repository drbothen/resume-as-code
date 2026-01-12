# Story 6.17: CTO Resume Template Variant

Status: ready-for-dev

## Story

As a **CTO targeting board-level enterprise positions**,
I want **a CTO-specific resume template optimized for executive hiring**,
So that **my resume follows research-validated best practices for CTO candidates**.

> **Research Note (2026-01-12):** CTO resume layout research confirms Classic Executive (reverse chronological) or Hybrid format is optimal for board-level positions. The CTO template combines both with Career Highlights section.

## Acceptance Criteria

1. **Given** I run `resume build --jd file.txt --template cto`
   **When** the resume is generated
   **Then** the layout follows CTO resume best practices:
     - Name prominently displayed (22pt)
     - Professional title "Chief Technology Officer" below name
     - Contact info on single line with separators
     - Executive summary (3-5 sentences, business impact focus)
     - Career Highlights section (3-4 bullets, P&L/team/revenue metrics)
     - Professional Experience with prominent scope indicators
     - Board & Advisory Roles section (if populated)
     - Certifications section
     - Education section (brief, after experience)
     - Publications/Speaking (if populated)

2. **Given** the CTO template renders
   **When** I inspect the PDF
   **Then** it uses professional typography (Calibri or Arial)
   **And** single-column layout for ATS compatibility
   **And** strategic use of bold for metrics and numbers
   **And** accent color limited to section dividers (#2c3e50 navy)
   **And** 1-inch margins on all sides
   **And** 2 pages maximum (research-validated)

3. **Given** positions have scope data
   **When** the CTO template renders
   **Then** scope indicators appear prominently under each position:
   ```
   $500M revenue | 200+ engineers | $50M technology budget | Global
   ```

4. **Given** career highlights exist
   **When** the CTO template renders
   **Then** Career Highlights appears after Executive Summary
   **And** before Professional Experience
   **And** uses prominent styling with business-impact focus

5. **Given** board roles exist
   **When** the CTO template renders
   **Then** Board & Advisory Roles appears after Certifications
   **And** demonstrates governance and strategic advisory experience

6. **Given** the resume exceeds 2 pages
   **When** the PDF is generated
   **Then** a warning is displayed: "CTO resumes should be 2 pages maximum"
   **And** content is still rendered (user decides what to trim)

7. **Given** I run `resume build --jd file.txt --template executive`
   **When** compared to `--template cto`
   **Then** executive uses same structure but Career Highlights is optional
   **And** both share the same CSS styling
   **And** CTO template has Career Highlights as expected/prominent

## Tasks / Subtasks

- [ ] Task 1: Create CTO HTML template (AC: #1, #4, #5)
  - [ ] 1.1: Create `templates/cto.html` extending executive template
  - [ ] 1.2: Add `{% block after_summary %}` for Career Highlights
  - [ ] 1.3: Add `{% block after_certifications %}` for Board & Advisory Roles
  - [ ] 1.4: Add `{% block end_sections %}` for Publications/Speaking
  - [ ] 1.5: Add CTO-specific emphasis classes

- [ ] Task 2: Create CTO CSS styling (AC: #2)
  - [ ] 2.1: Create `templates/cto.css` importing executive base styles
  - [ ] 2.2: Add Career Highlights emphasis styling
  - [ ] 2.3: Add larger scope indicator styling
  - [ ] 2.4: Add Board & Advisory Roles styling
  - [ ] 2.5: Add Publications/Speaking styling
  - [ ] 2.6: Ensure 2-page optimized spacing

- [ ] Task 3: Register CTO template (AC: #1)
  - [ ] 3.1: Add "cto" template to template provider/registry
  - [ ] 3.2: Map template name to cto.html and cto.css

- [ ] Task 4: Add page count warning (AC: #6)
  - [ ] 4.1: Add page count detection to build command
  - [ ] 4.2: Display warning if CTO template exceeds 2 pages
  - [ ] 4.3: Continue rendering (don't block)

- [ ] Task 5: Update executive template with blocks (AC: #7)
  - [ ] 5.1: Add block definitions to `executive.html` for inheritance
  - [ ] 5.2: Ensure Career Highlights renders in executive when present
  - [ ] 5.3: Ensure Board Roles renders in executive when present

- [ ] Task 6: Testing
  - [ ] 6.1: Add unit tests for CTO template selection
  - [ ] 6.2: Add tests for template rendering with all sections
  - [ ] 6.3: Add tests for page count warning
  - [ ] 6.4: Visual inspection of generated PDF (both templates)

- [ ] Task 7: Code quality verification
  - [ ] 7.1: Run `ruff check src tests --fix`
  - [ ] 7.2: Run `mypy src --strict` with zero errors
  - [ ] 7.3: Run `pytest` - all tests pass

## Dev Notes

### Architecture Compliance

This story implements FR53 (CTO Resume Template) based on CTO resume research (2026-01-12). The CTO template is a specialized variant of the executive template optimized for board-level positions.

**Critical Rules from project-context.md:**
- Use Jinja2 template inheritance for template variants
- Templates render gracefully when optional sections missing
- Single-column layout for ATS compatibility (94-97% parsing accuracy)

### CTO Template Structure

```html
{# src/resume_as_code/templates/cto.html #}
{% extends "executive.html" %}

{% block after_summary %}
{# Career Highlights is required/prominent for CTO #}
{% if resume.career_highlights %}
<section class="career-highlights cto-emphasis">
  <h2>Career Highlights</h2>
  <ul class="highlights-list">
    {% for highlight in resume.career_highlights %}
    <li>{{ highlight }}</li>
    {% endfor %}
  </ul>
</section>
{% endif %}
{% endblock %}

{% block after_certifications %}
{# Board roles prominent for CTO #}
{% if resume.board_roles %}
<section class="board-roles">
  <h2>Board & Advisory Roles</h2>
  {% for role in resume.board_roles %}
  <div class="board-entry">
    <div class="board-header">
      <strong>{{ role.organization }}</strong>
      <span class="dates">{{ role.format_date_range() }}</span>
    </div>
    <p class="role-title">{{ role.role }}</p>
    {% if role.focus %}
    <p class="focus">{{ role.focus }}</p>
    {% endif %}
  </div>
  {% endfor %}
</section>
{% endif %}
{% endblock %}

{% block end_sections %}
{# Publications/Speaking at end #}
{% if resume.publications %}
<section class="publications">
  <h2>Publications & Speaking</h2>
  {% for pub in resume.publications %}
  <div class="pub-entry">
    {% if pub.url %}
    <a href="{{ pub.url }}">
    {% endif %}
    <strong>{{ pub.title }}</strong>
    {% if pub.url %}
    </a>
    {% endif %}
    , {{ pub.venue }} ({{ pub.year }})
  </div>
  {% endfor %}
</section>
{% endif %}
{% endblock %}
```

### CTO CSS Styling

```css
/* src/resume_as_code/templates/cto.css */
@import "executive.css";

/* CTO-specific emphasis for Career Highlights */
.career-highlights.cto-emphasis {
  background-color: #f8f9fa;
  padding: 0.75em 1em;
  border-left: 3px solid #2c3e50;
  margin-bottom: 1.5em;
}

.career-highlights.cto-emphasis h2 {
  margin-top: 0;
}

/* Larger scope indicators for CTO */
.cto-template .scope-indicators {
  font-size: 10.5pt;
  font-weight: 500;
}

/* Board roles styling */
.board-roles {
  margin-top: 1em;
  page-break-inside: avoid;
}

.board-entry {
  margin-bottom: 0.75em;
}

.board-header {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
}

.role-title {
  font-style: italic;
  margin: 0.25em 0;
}

.focus {
  color: #5a6a7a;
  font-size: 10pt;
  margin: 0;
}

/* Publications styling */
.publications {
  margin-top: 1em;
  page-break-inside: avoid;
}

.pub-entry {
  margin-bottom: 0.5em;
  font-size: 10.5pt;
}

.pub-entry a {
  color: #2c3e50;
  text-decoration: none;
}
```

### Section Order (CTO Template)

1. Header (Name 22pt, Title, Contact)
2. Executive Summary
3. Career Highlights (CTO-specific emphasis)
4. Professional Experience (with prominent scope)
5. Certifications
6. Board & Advisory Roles
7. Education (brief)
8. Publications/Speaking (optional)

### Dependencies

This story REQUIRES:
- Story 6.4 (Executive Template) - Base template to extend
- Story 6.13 (Career Highlights) - Career Highlights section
- Story 6.14 (Board Roles) - Board & Advisory Roles section
- Story 6.15 (Publications) - Publications/Speaking section
- Story 6.16 (Enhanced Scope) - Scope indicators

### Files to Create/Modify

**New Files:**
- `src/resume_as_code/templates/cto.html` - CTO template
- `src/resume_as_code/templates/cto.css` - CTO styling
- `tests/unit/test_cto_template.py` - Unit tests

**Modified Files:**
- `src/resume_as_code/templates/executive.html` - Add block definitions
- `src/resume_as_code/services/template_provider.py` - Register CTO template
- `src/resume_as_code/commands/build.py` - Add page count warning

### Verification Commands

```bash
# After implementation, verify:
uv run ruff check src tests --fix
uv run mypy src --strict
uv run pytest tests/unit/test_cto_template.py -v

# Manual verification:
uv run resume build --jd examples/job-description.txt --template cto
# Open dist/resume.pdf and verify:
# - Career Highlights appears prominently after summary
# - Scope indicators below each position
# - Board roles appear (if configured)
# - Publications appear (if configured)
# - Professional 2-page layout
```

### References

- [Source: epics.md#Story 6.17](_bmad-output/planning-artifacts/epics.md)
- [CTO Resume Research](_bmad-output/planning-artifacts/research/cto-resume-layout-research-2026-01-12.md)
- [CTO Wireframe](_bmad-output/excalidraw-diagrams/cto-resume-wireframe.excalidraw)

## Dev Agent Record

### Agent Model Used

{{agent_model_name_version}}

### Debug Log References

### Completion Notes List

### File List

