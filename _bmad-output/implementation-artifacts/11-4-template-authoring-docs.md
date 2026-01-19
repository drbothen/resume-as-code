# Story 11.4: Template Authoring Documentation

Status: done

## Story

As a **user or designer creating custom resume templates**,
I want **comprehensive documentation on template variables, CSS patterns, and best practices**,
So that **I can create professional templates without reverse-engineering the codebase**.

## Acceptance Criteria

1. **AC1: Template variable reference** - Given a user wants to create a custom template, when they read the template authoring documentation, then they find complete variable reference with types and code examples for common patterns.

2. **AC2: Quick start guide** - Given the documentation, when a user follows the quick start guide, then they can create a basic working template and render it with `resume build --template my-template`.

3. **AC3: CSS styling guide** - Given the documentation CSS section, when a user styles their template, then they understand print vs screen considerations and can create ATS-compatible layouts.

4. **AC4: Template inheritance** - Given the documentation, when a user wants to extend a built-in template, then they understand how to use Jinja2 extends and block overrides.

5. **AC5: README linkage** - Given the documentation is complete, when a user reads the README, then they find a link to the template authoring guide.

## Tasks / Subtasks

- [x] Task 1: Create `docs/template-authoring.md` documentation file
  - [x] 1.1 Write Quick Start section with minimal working example
  - [x] 1.2 Document template file structure (HTML + CSS)
  - [x] 1.3 Create complete Template Variables Reference section

- [x] Task 2: Document all data models for templates
  - [x] 2.1 Document root context variables (resume, css, employer_groups)
  - [x] 2.2 Document ContactInfo fields
  - [x] 2.3 Document ResumeData fields
  - [x] 2.4 Document ResumeSection and ResumeItem
  - [x] 2.5 Document ResumeBullet
  - [x] 2.6 Document Certification model
  - [x] 2.7 Document Education model
  - [x] 2.8 Document BoardRole model
  - [x] 2.9 Document Publication model
  - [x] 2.10 Document EmployerGroup (for grouped positions)

- [x] Task 3: Document helper methods
  - [x] 3.1 Document `resume.get_active_certifications()`
  - [x] 3.2 Document `resume.get_sorted_board_roles()`
  - [x] 3.3 Document `resume.get_sorted_publications()`
  - [x] 3.4 Document `role.format_date_range()`
  - [x] 3.5 Document Publication properties (`year`, `is_speaking`)

- [x] Task 4: Write CSS Styling Guide section
  - [x] 4.1 Document file structure (template.html + template.css)
  - [x] 4.2 Document @page rules for print/PDF
  - [x] 4.3 Document recommended base styles
  - [x] 4.4 Document color palette recommendations
  - [x] 4.5 Document typography scale
  - [x] 4.6 Create complete CSS class reference table
  - [x] 4.7 Document print styles (@media print)
  - [x] 4.8 Document screen preview styles (@media screen)

- [x] Task 5: Document template inheritance
  - [x] 5.1 Explain Jinja2 extends pattern with executive.html example
  - [x] 5.2 Document available blocks in executive.html
  - [x] 5.3 Document CSS inheritance via `_css_inheritance` map

- [x] Task 6: Write Best Practices section
  - [x] 6.1 ATS compatibility guidelines
  - [x] 6.2 Handling null/empty values with `{% if field %}`
  - [x] 6.3 Page length control strategies
  - [x] 6.4 Testing templates with resume build command

- [x] Task 7: Add complete examples
  - [x] 7.1 Minimal template example (from scratch)
  - [x] 7.2 Template extending executive.html example
  - [x] 7.3 Custom CSS-only modification example

- [x] Task 8: Link documentation
  - [x] 8.1 Add link from README.md to template authoring guide
  - [x] 8.2 Reference in CLAUDE.md if needed (not needed - CLAUDE.md references docs/)

## Dev Notes

### Problem Statement

No documentation exists for users who want to create custom resume templates. Template authors need to understand:
- Available template variables and their types
- Data structures (ResumeData, ResumeSection, ResumeItem, etc.)
- CSS class reference and styling patterns
- Template inheritance and block overrides
- Print/PDF considerations
- Best practices for ATS compatibility

### Content Source

The detailed template variable reference and CSS guide already exists in `_bmad-output/implementation-artifacts/tech-debt.md` under TD-007. This story extracts, formats, and enhances it as proper documentation.

### Documentation Structure

```
docs/
├── template-authoring.md    # Main documentation file (NEW)
├── philosophy.md            # Existing
├── data-model.md            # Existing
└── algorithm.md             # Existing
```

### Template Variables Reference

Extract this content from tech-debt.md TD-007 and format as proper documentation:

**Root Context Variables:**

| Variable | Type | Description |
|----------|------|-------------|
| `resume` | ResumeData | Main resume data object |
| `css` | string | Compiled CSS (from .css file) |
| `employer_groups` | list[EmployerGroup] | Grouped positions by employer (Experience section only) |

**resume.contact (ContactInfo):**

| Field | Type | Description |
|-------|------|-------------|
| `name` | string | Full name (required) |
| `title` | string? | Professional title/headline |
| `email` | string? | Email address |
| `phone` | string? | Phone number |
| `location` | string? | City, State |
| `linkedin` | string? | LinkedIn URL |
| `github` | string? | GitHub URL |
| `website` | string? | Portfolio URL |

**resume (ResumeData):**

| Field | Type | Description |
|-------|------|-------------|
| `contact` | ContactInfo | Contact information |
| `summary` | string? | Executive summary |
| `sections` | list[ResumeSection] | Experience sections |
| `skills` | list[string] | Skills list |
| `education` | list[Education] | Education entries |
| `certifications` | list[Certification] | Certifications |
| `career_highlights` | list[string] | Executive highlights |
| `board_roles` | list[BoardRole] | Board/advisory roles |
| `publications` | list[Publication] | Publications |
| `publications_curated` | bool | True if sorted by JD relevance |
| `tailored_notice_text` | string? | Footer notice text |

**ResumeSection:**

| Field | Type | Description |
|-------|------|-------------|
| `title` | string | Section title ("Experience") |
| `items` | list[ResumeItem] | Position entries |

**ResumeItem (position/job):**

| Field | Type | Description |
|-------|------|-------------|
| `title` | string | Job title |
| `organization` | string? | Employer name |
| `location` | string? | Job location |
| `start_date` | string? | Start date |
| `end_date` | string? | End date (null = Present) |
| `bullets` | list[ResumeBullet] | Achievement bullets |
| `scope_line` | string? | Pre-formatted scope (e.g., "Led team of 50 | $10M budget") |

**ResumeBullet:**

| Field | Type | Description |
|-------|------|-------------|
| `text` | string | Bullet text |
| `metrics` | string? | Quantified impact |

**Certification:**

| Field | Type | Description |
|-------|------|-------------|
| `name` | string | Certification name |
| `issuer` | string? | Issuing organization |
| `date` | string? | Date obtained (YYYY-MM) |
| `expires` | string? | Expiration date |
| `display` | bool | Show on resume |

**Education:**

| Field | Type | Description |
|-------|------|-------------|
| `degree` | string | Degree name |
| `institution` | string | School name |
| `graduation_year` | string? | Year |
| `honors` | string? | Honors/distinction |
| `gpa` | string? | GPA |
| `display` | bool | Show on resume |

**BoardRole:**

| Field | Type | Description |
|-------|------|-------------|
| `organization` | string | Organization name |
| `role` | string | Role title |
| `type` | string | director/advisory/committee |
| `start_date` | string? | Start date |
| `end_date` | string? | End date |
| `focus` | string? | Focus area |
| `format_date_range()` | method | Returns formatted date range |

**Publication:**

| Field | Type | Description |
|-------|------|-------------|
| `title` | string | Publication title |
| `type` | string | conference/article/whitepaper/book/podcast/webinar |
| `venue` | string | Venue/publisher |
| `date` | string? | Publication date |
| `url` | string? | URL |
| `year` | property | Extracted year |
| `is_speaking` | property | True if conference/podcast/webinar |

**EmployerGroup (for Experience section):**

| Field | Type | Description |
|-------|------|-------------|
| `employer` | string | Employer name |
| `location` | string? | Location |
| `tenure_display` | string | Formatted tenure (e.g., "2020 - Present") |
| `is_multi_position` | bool | True if multiple roles at employer |
| `positions` | list[ResumeItem] | Position entries |

### Helper Methods

```jinja2
{# Active certifications (not expired, display=true) #}
{% for cert in resume.get_active_certifications() %}

{# Board roles sorted by type and date #}
{% for role in resume.get_sorted_board_roles() %}

{# Publications sorted by date or relevance #}
{% for pub in resume.get_sorted_publications() %}

{# Format board role date range #}
{{ role.format_date_range() }}
```

### Template Inheritance

Templates can extend built-in templates:

```html
{# my-template.html #}
{% extends "executive.html" %}

{% block career_highlights %}
{# Override career highlights rendering #}
{% endblock %}

{% block achievements scoped %}
{# Override bullet rendering #}
{% endblock %}
```

**Available blocks in executive.html:**
- `career_highlights` - Career highlights section
- `achievements` (scoped) - Bullet list within position
- `board_roles` - Board roles section
- `publications` - Publications section

### CSS Inheritance

Add to `TemplateService._css_inheritance` for CSS chaining:

```python
_css_inheritance = {
    "cto": "executive",           # cto.css loads after executive.css
    "cto-results": "cto",         # cto-results.css loads after cto.css
    "my-template": "modern",      # my-template.css loads after modern.css
}
```

### CSS Class Reference

**Header Classes:**
| Class | Purpose |
|-------|---------|
| `.resume-header` | Main header container |
| `.name` | Name styling |
| `.professional-title` | Title/headline |
| `.contact-line` | Contact info row |
| `.contact-item` | Individual contact items |
| `.links` | Social links container |

**Section Classes:**
| Class | Purpose |
|-------|---------|
| `.executive-summary` | Summary section |
| `.career-highlights` | Highlights section |
| `.highlights-list` | Highlights bullet list |
| `.core-competencies` | Skills section |
| `.skills-grid` | Flexbox skills container |
| `.skill` | Individual skill tag |
| `.experience` | Experience section |

**Position Classes:**
| Class | Purpose |
|-------|---------|
| `.position` | Single position entry |
| `.position-header` | Title + dates row |
| `.company` | Employer name |
| `.role` | Job title |
| `.dates` | Date range |
| `.location` | Location |
| `.scope-line` | Executive scope indicators |

**Employer Group Classes (multi-position):**
| Class | Purpose |
|-------|---------|
| `.employer-group` | Grouped positions container |
| `.employer-header` | Employer name + tenure |
| `.employer-name` | Company name |
| `.tenure` | Total tenure display |
| `.position.nested` | Nested position entry |
| `.nested-position-header` | Nested title + dates |
| `.role-title` | Role within company |

**Achievement Classes:**
| Class | Purpose |
|-------|---------|
| `.achievements` | Bullet list |
| `.achievements li` | Individual bullet |
| `.metrics` | Quantified impact highlight |

**Other Section Classes:**
| Class | Purpose |
|-------|---------|
| `.certifications` | Certs section |
| `.cert-list` | Cert list (no bullets) |
| `.education` | Education section |
| `.edu-entry` | Education entry |
| `.honors` | Honors/distinction |
| `.board-roles` | Board roles section |
| `.board-entry` | Individual board role |
| `.board-header` | Org + dates |
| `.focus` | Focus area |
| `.publications` | Publications section |
| `.pub-entry` | Individual publication |
| `.tailored-notice` | Footer notice |

### Print/PDF Considerations

```css
@page {
    size: letter;           /* or 'A4' for international */
    margin: 0.5in 0.6in;    /* top/bottom left/right */
}

@page :first {
    margin-top: 0.5in;      /* Different margin for first page */
}

/* Running header for page 2+ (executive templates) */
@page :not(:first) {
    @top-center {
        content: element(running-header);
    }
}

@media print {
    body { font-size: 10.5pt; color: #000; }

    /* Page break control */
    section { page-break-inside: avoid; }
    .position { page-break-inside: avoid; }
    h2 { page-break-after: avoid; }

    /* Orphan/widow control */
    p, li { orphans: 2; widows: 2; }
}
```

### Best Practices

1. **ATS Compatibility:**
   - Use semantic HTML (`<h1>`, `<h2>`, `<section>`, `<article>`)
   - Avoid tables for layout
   - Use standard fonts (Calibri, Arial, Segoe UI)
   - No images in content areas

2. **Handling Null Values:**
   ```jinja2
   {% if resume.contact.email %}{{ resume.contact.email }}{% endif %}
   {{ contact_parts | join(' | ') }}
   ```

3. **Page Length Control:**
   - Use CSS `page-break-inside: avoid` on sections
   - Test with `resume build --jd test.txt --template my-template`
   - CTO templates should be 2 pages maximum

4. **Testing Templates:**
   ```bash
   # Test with actual data
   resume build --jd test.txt --template my-template --format pdf

   # Preview in browser
   resume build --jd test.txt --template my-template --format pdf
   open dist/resume.pdf
   ```

### Built-in Templates Reference

| Template | Purpose | Base Style |
|----------|---------|------------|
| `modern` | Clean, minimal design | Standalone |
| `executive` | Executive-level with scope indicators | Standalone |
| `executive-classic` | Traditional executive format | Standalone |
| `ats-safe` | ATS-optimized minimal styling | Standalone |
| `cto` | CTO-specific with results metrics | Extends executive |
| `cto-results` | CTO with enhanced metrics display | Extends cto |

### Example: Minimal Custom Template

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
        {% if resume.contact.title %}<p>{{ resume.contact.title }}</p>{% endif %}
    </header>

    {% if resume.summary %}
    <section>
        <h2>Summary</h2>
        <p>{{ resume.summary }}</p>
    </section>
    {% endif %}

    {% for section in resume.sections %}
    <section>
        <h2>{{ section.title }}</h2>
        {% for item in section.items %}
        <article>
            <h3>{{ item.title }}{% if item.organization %} - {{ item.organization }}{% endif %}</h3>
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
</body>
</html>
```

### Files to Create

| File | Action | Description |
|------|--------|-------------|
| `docs/template-authoring.md` | Create | Main documentation file |
| `README.md` | Modify | Add link to template authoring guide |

### Project Context Rules to Follow

From `_bmad-output/project-context.md`:

- This is a documentation-only story - no code changes
- Follow existing docs/ folder structure and formatting
- Use markdown tables for reference documentation
- Include code examples in fenced code blocks with language hints
- Keep examples concise and focused

### References

- [Source: _bmad-output/planning-artifacts/epics/epic-11-technical-debt-platform-enhancements.md#Story-11.4]
- [Source: _bmad-output/implementation-artifacts/tech-debt.md#TD-007]
- Template: `src/resume_as_code/templates/executive.html`
- Models: `src/resume_as_code/models/resume.py`
- TemplateService: `src/resume_as_code/services/template_service.py`

## Dev Agent Record

### Agent Model Used

Claude Opus 4.5 (claude-opus-4-5-20251101)

### Debug Log References

None - documentation-only story, no debugging required.

### Completion Notes List

- Created comprehensive `docs/template-authoring.md` (800+ lines) covering:
  - Quick Start guide with 3-step minimal template creation
  - Template file structure and configuration
  - Complete Template Variables Reference for all data models
  - Helper methods documentation with code examples
  - CSS Styling Guide with @page rules, base styles, class reference
  - Template inheritance documentation with Jinja2 extends pattern
  - Best practices for ATS compatibility, null handling, page control
  - Three complete examples: minimal, extending executive, CSS-only
  - Troubleshooting section for common issues
- Verified all data models against actual source code (resume.py, publication.py, board_role.py)
- Verified template blocks against executive.html implementation
- Verified CSS inheritance map in template_service.py
- Added link to template authoring guide in README.md Documentation section

### Change Log
- 2026-01-18: Story created with comprehensive documentation content
- 2026-01-18: Implementation complete - created docs/template-authoring.md, linked from README.md
- 2026-01-18: Code review remediation - fixed CSS class name (.tenure → .total-tenure), updated File List

### File List
- `docs/template-authoring.md` - Created: Main template authoring documentation
- `README.md` - Modified: Added link to template authoring guide in Documentation table
- `_bmad-output/implementation-artifacts/sprint-status.yaml` - Modified: Story status tracking
