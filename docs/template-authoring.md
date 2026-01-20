# Template Authoring Guide

This guide explains how to create custom resume templates for Resume as Code. Templates use Jinja2 HTML with CSS styling, supporting both standalone templates and extensions of built-in templates.

## Quick Start

Create a custom template in three steps:

### 1. Create Template Files

```bash
mkdir -p my-templates
touch my-templates/branded.html my-templates/branded.css
```

### 2. Write Minimal Template

**`my-templates/branded.html`:**

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
        {% if resume.contact.title %}
        <p class="title">{{ resume.contact.title }}</p>
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
        <article class="position">
            <h3>{{ item.title }}{% if item.organization %} - {{ item.organization }}{% endif %}</h3>
            <p class="dates">{{ item.start_date or '' }} - {{ item.end_date or 'Present' }}</p>
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

**`my-templates/branded.css`:**

```css
body {
    font-family: 'Segoe UI', Arial, sans-serif;
    max-width: 8.5in;
    margin: 0 auto;
    padding: 0.5in;
    color: #333;
}

h1 { font-size: 24pt; margin-bottom: 0.25em; }
h2 { font-size: 14pt; border-bottom: 1px solid #ccc; padding-bottom: 0.25em; }
h3 { font-size: 12pt; margin-bottom: 0.25em; }

.title { font-style: italic; color: #666; }
.dates { color: #666; font-size: 10pt; }
ul { margin: 0.5em 0; padding-left: 1.5em; }
li { margin-bottom: 0.25em; }
```

### 3. Build Your Resume

```bash
# Using templates_dir in .resume.yaml
resume build --jd job.txt --template branded

# Or via command line flag
resume build --jd job.txt --templates-dir ./my-templates --template branded
```

---

## Template File Structure

Templates consist of an HTML file and optional CSS file:

```
my-templates/
├── branded.html      # Required: Jinja2 HTML template
├── branded.css       # Optional: CSS styles
├── minimal.html      # Another template
└── minimal.css
```

### Configuration

Set your custom templates directory in `.resume.yaml`:

```yaml
templates_dir: ./my-templates  # Path relative to project root
```

Or use the CLI flag:

```bash
resume build --templates-dir ./my-templates --template branded
```

### Template Resolution

When you request a template, Resume as Code searches in order:

1. **Custom templates directory** (if configured)
2. **Built-in templates** (fallback)

This allows you to:
- Create entirely new templates
- Override built-in templates by name
- Extend built-in templates using Jinja2 inheritance

---

## Template Variables Reference

### Root Context Variables

| Variable | Type | Description |
|----------|------|-------------|
| `resume` | `ResumeData` | Main resume data object |
| `css` | `string` | Compiled CSS content |
| `employer_groups` | `list[EmployerGroup]` | Positions grouped by employer (Experience section) |

### ContactInfo (resume.contact)

| Field | Type | Description |
|-------|------|-------------|
| `name` | `string` | Full name (required) |
| `title` | `string?` | Professional title/headline |
| `email` | `string?` | Email address |
| `phone` | `string?` | Phone number |
| `location` | `string?` | City, State |
| `linkedin` | `string?` | LinkedIn URL |
| `github` | `string?` | GitHub URL |
| `website` | `string?` | Portfolio URL |

### ResumeData (resume)

| Field | Type | Description |
|-------|------|-------------|
| `contact` | `ContactInfo` | Contact information |
| `summary` | `string?` | Executive summary |
| `sections` | `list[ResumeSection]` | Experience sections |
| `skills` | `list[string]` | Skills list |
| `education` | `list[Education]` | Education entries |
| `certifications` | `list[Certification]` | Certifications |
| `career_highlights` | `list[string]` | Executive highlights |
| `board_roles` | `list[BoardRole]` | Board/advisory roles |
| `publications` | `list[Publication]` | Publications |
| `publications_curated` | `bool` | True if sorted by JD relevance |
| `tailored_notice_text` | `string?` | Footer notice text |

### ResumeSection

| Field | Type | Description |
|-------|------|-------------|
| `title` | `string` | Section title (e.g., "Experience") |
| `items` | `list[ResumeItem]` | Position entries |

### ResumeItem (position/job)

| Field | Type | Description |
|-------|------|-------------|
| `title` | `string` | Job title |
| `organization` | `string?` | Employer name |
| `location` | `string?` | Job location |
| `start_date` | `string?` | Start date (YYYY or YYYY-MM) |
| `end_date` | `string?` | End date (null = Present) |
| `bullets` | `list[ResumeBullet]` | Achievement bullets |
| `scope_line` | `string?` | Pre-formatted scope (e.g., "Led team of 50 \| $10M budget") |

### ResumeBullet

| Field | Type | Description |
|-------|------|-------------|
| `text` | `string` | Bullet text |
| `metrics` | `string?` | Quantified impact |

### Certification

| Field | Type | Description |
|-------|------|-------------|
| `name` | `string` | Certification name |
| `issuer` | `string?` | Issuing organization |
| `date` | `string?` | Date obtained (YYYY-MM) |
| `expires` | `string?` | Expiration date (YYYY-MM) |
| `display` | `bool` | Show on resume |

### Education

| Field | Type | Description |
|-------|------|-------------|
| `degree` | `string` | Degree name |
| `institution` | `string` | School name |
| `graduation_year` | `string?` | Year |
| `honors` | `string?` | Honors/distinction |
| `gpa` | `string?` | GPA |
| `display` | `bool` | Show on resume |

### BoardRole

| Field | Type | Description |
|-------|------|-------------|
| `organization` | `string` | Organization name |
| `role` | `string` | Role title |
| `type` | `string` | "director", "advisory", or "committee" |
| `start_date` | `string?` | Start date (YYYY-MM) |
| `end_date` | `string?` | End date (null = current) |
| `focus` | `string?` | Focus area |
| `display` | `bool` | Show on resume |
| `is_current` | `property` | True if end_date is None |

### Publication

| Field | Type | Description |
|-------|------|-------------|
| `title` | `string` | Publication title |
| `type` | `string` | "conference", "article", "whitepaper", "book", "podcast", "webinar" |
| `venue` | `string` | Venue/publisher |
| `date` | `string?` | Publication date (YYYY-MM) |
| `url` | `string?` | URL |
| `topics` | `list[string]` | Topic tags for JD matching |
| `abstract` | `string?` | Brief description (max 500 chars) |
| `display` | `bool` | Show on resume |
| `year` | `property` | Extracted year (e.g., "2024") |
| `is_speaking` | `property` | True if conference/podcast/webinar |

### EmployerGroup (for grouped positions)

| Field | Type | Description |
|-------|------|-------------|
| `employer` | `string` | Employer name |
| `location` | `string?` | Location |
| `tenure_display` | `property` | Formatted tenure (e.g., "2020 - Present") |
| `is_multi_position` | `property` | True if multiple roles at employer |
| `positions` | `list[ResumeItem]` | Position entries (most recent first) |

---

## Helper Methods

### resume.get_active_certifications()

Returns certifications where `display=True` and not expired.

```jinja2
{% if resume.get_active_certifications() %}
<section class="certifications">
    <h2>Certifications</h2>
    <ul>
        {% for cert in resume.get_active_certifications() %}
        <li>
            <strong>{{ cert.name }}</strong>
            {% if cert.issuer %}, {{ cert.issuer }}{% endif %}
            {% if cert.date %}, {{ cert.date[:4] }}{% endif %}
        </li>
        {% endfor %}
    </ul>
</section>
{% endif %}
```

### resume.get_sorted_board_roles()

Returns board roles sorted by type (directors first) then date (most recent first). Only includes roles where `display=True`.

```jinja2
{% if resume.get_sorted_board_roles() %}
<section class="board-roles">
    <h2>Board & Advisory Roles</h2>
    {% for role in resume.get_sorted_board_roles() %}
    <div class="board-entry">
        <strong>{{ role.organization }}</strong> - {{ role.role }}
        <span class="dates">{{ role.format_date_range() }}</span>
        {% if role.focus %}
        <p class="focus">{{ role.focus }}</p>
        {% endif %}
    </div>
    {% endfor %}
</section>
{% endif %}
```

### resume.get_sorted_publications()

Returns publications sorted by relevance (when JD provided) or date (fallback). Only includes publications where `display=True`.

```jinja2
{% if resume.get_sorted_publications() %}
<section class="publications">
    <h2>Publications & Speaking</h2>
    {% for pub in resume.get_sorted_publications() %}
    <div class="pub-entry">
        {% if pub.is_speaking %}
        {# Speaking: "Venue (Year) - Title" #}
        {{ pub.venue }} ({{ pub.year }}) - {{ pub.title }}
        {% else %}
        {# Written: "Title, Venue (Year)" #}
        {{ pub.title }}, {{ pub.venue }} ({{ pub.year }})
        {% endif %}
    </div>
    {% endfor %}
</section>
{% endif %}
```

### role.format_date_range()

Formats BoardRole date range for display.

```jinja2
{{ role.format_date_range() }}  {# "2020 - Present" or "2018 - 2022" #}
```

### Publication Properties

```jinja2
{{ pub.year }}        {# "2024" - extracted from date #}
{{ pub.is_speaking }} {# True for conference/podcast/webinar #}
```

---

## CSS Styling Guide

### File Structure

Each template can have a matching CSS file:

```
templates/
├── branded.html
├── branded.css    # Loaded automatically for branded template
├── modern.html
└── modern.css
```

### @page Rules for Print/PDF

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
```

### Recommended Base Styles

```css
body {
    font-family: 'Segoe UI', Calibri, Arial, sans-serif;
    font-size: 11pt;
    line-height: 1.4;
    color: #333;
    max-width: 8.5in;
    margin: 0 auto;
}

/* Typography scale */
h1 { font-size: 24pt; margin-bottom: 0.25em; }
h2 { font-size: 14pt; margin-top: 1em; margin-bottom: 0.5em; }
h3 { font-size: 12pt; margin-bottom: 0.25em; }

/* Section spacing */
section { margin-bottom: 1em; }
```

### Color Palette Recommendations

Use accessible colors with sufficient contrast:

```css
:root {
    --text-primary: #333333;
    --text-secondary: #666666;
    --accent: #2c5282;         /* Professional blue */
    --border: #e2e8f0;
    --background: #ffffff;
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
| `.total-tenure` | Total tenure display |
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

### Print Styles

```css
@media print {
    body {
        font-size: 10.5pt;
        color: #000;
    }

    /* Page break control */
    section { page-break-inside: avoid; }
    .position { page-break-inside: avoid; }
    h2 { page-break-after: avoid; }

    /* Orphan/widow control */
    p, li { orphans: 2; widows: 2; }

    /* Hide screen-only elements */
    .screen-only { display: none; }
}
```

### Screen Preview Styles

```css
@media screen {
    body {
        background: #f5f5f5;
        padding: 2em;
    }

    /* Visual page boundary */
    .resume-container {
        background: white;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
        padding: 1in;
    }
}
```

---

## Template Inheritance

Templates can extend built-in templates using Jinja2 inheritance.

### Extending executive.html

```html
{# my-templates/branded-executive.html #}
{% extends "executive.html" %}

{% block career_highlights %}
{# Custom career highlights rendering #}
<section class="career-highlights custom-style">
    <h2>Key Accomplishments</h2>
    {% for highlight in resume.career_highlights %}
    <p>{{ highlight }}</p>
    {% endfor %}
</section>
{% endblock %}
```

### Available Blocks in executive.html

| Block | Purpose |
|-------|---------|
| `career_highlights` | Career highlights section |
| `achievements` | Bullet list within position (use `scoped`) |
| `board_roles` | Board roles section |
| `publications` | Publications section |

### Using Scoped Blocks

The `achievements` block requires `scoped` to access loop variables:

```html
{% block achievements scoped %}
<ul class="achievements custom">
    {% for bullet in item.bullets %}
    <li class="fancy-bullet">{{ bullet.text }}</li>
    {% endfor %}
</ul>
{% endblock %}
```

### CSS Inheritance

Templates that extend another template inherit CSS via the `_css_inheritance` map in `TemplateService`:

```python
_css_inheritance = {
    "cto": "executive",           # cto.css loads after executive.css
    "cto-results": "cto",         # cto-results.css loads after cto.css
}
```

For custom templates extending built-in templates, you have two options:

1. **Copy parent CSS** - Include the parent CSS in your custom CSS file
2. **Use only custom CSS** - Write complete standalone styles

Note: HTML inheritance via `{% extends %}` works automatically, but CSS inheritance requires the map or manual copying.

---

## Best Practices

### ATS Compatibility

Applicant Tracking Systems parse your resume automatically. Follow these guidelines:

1. **Use semantic HTML** - `<h1>`, `<h2>`, `<section>`, `<article>` tags
2. **Avoid tables for layout** - Use CSS flexbox/grid instead
3. **Standard fonts** - Calibri, Arial, Segoe UI, Georgia
4. **No images in content** - ATS can't read text in images
5. **Simple layouts** - Single or two-column maximum
6. **Text-based contact info** - Don't use icons without text labels

### Handling Null/Empty Values

Always check before rendering optional fields:

```jinja2
{# Safe field access #}
{% if resume.contact.email %}{{ resume.contact.email }}{% endif %}

{# Join non-empty values #}
{% set contact_parts = [] %}
{% if resume.contact.location %}{% set _ = contact_parts.append(resume.contact.location) %}{% endif %}
{% if resume.contact.email %}{% set _ = contact_parts.append(resume.contact.email) %}{% endif %}
{{ contact_parts | join(' | ') }}

{# Default values #}
{{ item.end_date or 'Present' }}
```

### Page Length Control

Keep resumes to appropriate length:

```css
/* Prevent awkward page breaks */
section { page-break-inside: avoid; }
.position { page-break-inside: avoid; }
h2 { page-break-after: avoid; }

/* Control list spacing for density */
.achievements li { margin-bottom: 0.15em; }
```

Executive templates should be 2 pages maximum. Entry-level templates should be 1 page.

### Testing Templates

```bash
# Test with actual resume data
resume build --jd job-description.txt --template my-template --format pdf

# Preview in browser
open dist/resume.pdf

# Test edge cases
# - Empty sections (no certifications, no publications)
# - Long content (many bullets, long titles)
# - Special characters (accents, ampersands)
```

---

## Built-in Templates Reference

| Template | Purpose | Features |
|----------|---------|----------|
| `modern` | Clean, minimal design | Single-column, ATS-friendly |
| `executive` | Executive-level format | Scope indicators, career highlights, board roles, publications |
| `executive-classic` | Traditional executive | Conservative styling |
| `ats-safe` | ATS-optimized | Minimal styling, maximum parseability |
| `cto` | CTO-specific | Results metrics, extends executive |
| `cto-results` | CTO with enhanced metrics | Performance highlights, extends cto |

---

## Complete Examples

### Example 1: Minimal Template from Scratch

**`my-templates/clean.html`:**

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>{{ resume.contact.name }}</title>
    <style>{{ css }}</style>
</head>
<body>
    <header>
        <h1>{{ resume.contact.name }}</h1>
        {% if resume.contact.title %}<p class="title">{{ resume.contact.title }}</p>{% endif %}
        <p class="contact">
            {% set parts = [] %}
            {% if resume.contact.email %}{% set _ = parts.append(resume.contact.email) %}{% endif %}
            {% if resume.contact.phone %}{% set _ = parts.append(resume.contact.phone) %}{% endif %}
            {% if resume.contact.location %}{% set _ = parts.append(resume.contact.location) %}{% endif %}
            {{ parts | join(' | ') }}
        </p>
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
            <div class="job-header">
                <strong>{{ item.title }}</strong>
                {% if item.organization %} | {{ item.organization }}{% endif %}
                <span class="dates">{{ item.start_date }} - {{ item.end_date or 'Present' }}</span>
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
    <section>
        <h2>Skills</h2>
        <p>{{ resume.skills | join(' | ') }}</p>
    </section>
    {% endif %}

    {% if resume.education %}
    <section>
        <h2>Education</h2>
        {% for edu in resume.education %}
        {% if edu.display is not defined or edu.display %}
        <p><strong>{{ edu.degree }}</strong>, {{ edu.institution }}{% if edu.graduation_year %} ({{ edu.graduation_year }}){% endif %}</p>
        {% endif %}
        {% endfor %}
    </section>
    {% endif %}
</body>
</html>
```

**`my-templates/clean.css`:**

```css
@page { size: letter; margin: 0.5in; }

body {
    font-family: Calibri, Arial, sans-serif;
    font-size: 11pt;
    line-height: 1.4;
    color: #333;
}

header { text-align: center; margin-bottom: 1em; }
h1 { font-size: 22pt; margin: 0; }
.title { font-style: italic; color: #666; margin: 0.25em 0; }
.contact { font-size: 10pt; color: #666; }

h2 {
    font-size: 12pt;
    border-bottom: 1px solid #999;
    padding-bottom: 0.25em;
    margin-top: 1em;
}

.job-header { display: flex; justify-content: space-between; }
.dates { color: #666; font-size: 10pt; }
ul { margin: 0.5em 0; padding-left: 1.5em; }
li { margin-bottom: 0.2em; }
```

### Example 2: Template Extending executive.html

**`my-templates/branded-exec.html`:**

```html
{% extends "executive.html" %}

{% block career_highlights %}
<section class="career-highlights branded">
    <h2>Executive Highlights</h2>
    <div class="highlights-grid">
        {% for highlight in resume.career_highlights %}
        <div class="highlight-card">{{ highlight }}</div>
        {% endfor %}
    </div>
</section>
{% endblock %}

{% block publications %}
{# Custom publications with visual styling #}
{% if resume.get_sorted_publications() %}
<section class="publications branded">
    <h2>Thought Leadership</h2>
    {% for pub in resume.get_sorted_publications() %}
    <div class="pub-card">
        <span class="pub-type {{ pub.type }}">{{ pub.type | upper }}</span>
        {% if pub.is_speaking %}
        <strong>{{ pub.venue }}</strong> ({{ pub.year }}) - {{ pub.title }}
        {% else %}
        <strong>{{ pub.title }}</strong>, {{ pub.venue }} ({{ pub.year }})
        {% endif %}
    </div>
    {% endfor %}
</section>
{% endif %}
{% endblock %}
```

**`my-templates/branded-exec.css`:**

```css
/* Inherits executive.css styles via parent template */

/* Override career highlights */
.career-highlights.branded h2 { color: #1a365d; }

.highlights-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 0.5em;
}

.highlight-card {
    background: #f7fafc;
    padding: 0.5em;
    border-left: 3px solid #2b6cb0;
}

/* Custom publications */
.publications.branded { margin-top: 1em; }

.pub-card {
    margin-bottom: 0.5em;
    padding: 0.25em 0;
}

.pub-type {
    display: inline-block;
    padding: 0.1em 0.4em;
    font-size: 8pt;
    border-radius: 3px;
    margin-right: 0.5em;
}

.pub-type.conference { background: #c6f6d5; color: #22543d; }
.pub-type.article { background: #bee3f8; color: #2a4365; }
.pub-type.whitepaper { background: #feebc8; color: #744210; }
```

### Example 3: CSS-Only Customization

To customize styling without changing HTML structure, create a CSS file matching a built-in template name:

**`my-templates/executive.css`:**

```css
/* Override built-in executive.css styles */
/* This file loads INSTEAD of the builtin executive.css */

@page { size: letter; margin: 0.4in 0.5in; }

body {
    font-family: Georgia, serif;
    font-size: 10.5pt;
    color: #2d3748;
}

h1.name {
    font-size: 26pt;
    color: #1a365d;
    letter-spacing: 0.05em;
}

h2 {
    font-size: 11pt;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    color: #4a5568;
    border-bottom: 2px solid #e2e8f0;
}

.skills-grid {
    display: flex;
    flex-wrap: wrap;
    gap: 0.5em;
}

.skill {
    background: #edf2f7;
    padding: 0.2em 0.6em;
    border-radius: 4px;
    font-size: 9pt;
}
```

Use it:

```bash
resume build --jd job.txt --templates-dir ./my-templates --template executive
```

---

## Troubleshooting

### Template Not Found

```
RenderError: Template 'mytemplate' not found
Did you mean 'modern'? Available templates: executive, modern, ats-safe
```

Check:
- Template file exists with `.html` extension
- `templates_dir` path is correct in `.resume.yaml`
- File name matches (case-sensitive on Linux/macOS)

### CSS Not Loading

If your template renders but styles are missing:

1. Verify CSS file name matches template name: `branded.html` → `branded.css`
2. Check CSS file is in same directory as HTML template
3. Verify `{{ css }}` is in your template's `<style>` tag

### Blocks Not Overriding

If `{% block %}` overrides don't work:

1. Check block name matches exactly (case-sensitive)
2. Add `scoped` for blocks that need loop variables: `{% block achievements scoped %}`
3. Verify `{% extends "parent.html" %}` is first line

### Print Layout Issues

If PDF output looks different from screen:

1. Use `@page` rules for PDF margins
2. Add `@media print` styles for print-specific formatting
3. Test with `resume build --format pdf` directly

---

## DOCX Templates (Story 13.1)

Resume as Code supports template-based DOCX generation using [docxtpl](https://docxtpl.readthedocs.io/), which embeds Jinja2 templating directly in Word documents.

### Creating a DOCX Template

1. **Create a Word document** with your desired formatting and layout
2. **Insert Jinja2 placeholders** where dynamic content should appear
3. **Save as `.docx`** in your templates directory

### Directory Structure

```
my-templates/
├── branded.html      # PDF template
├── branded.css
└── docx/
    └── branded.docx  # DOCX template (in docx/ subdirectory)
```

**Important:** DOCX templates must be in a `docx/` subdirectory.

### Template Resolution

DOCX templates are resolved in order:

1. `{templates_dir}/docx/{template_name}.docx` (custom)
2. Built-in `templates/docx/{template_name}.docx`
3. Fallback to programmatic generation (if no template found)

### Configuration

Set DOCX-specific template in `.resume.yaml`:

```yaml
# DOCX-specific template (independent of PDF template)
docx:
  template: branded  # Uses templates/docx/branded.docx

# Or use same template name for both PDF and DOCX
default_template: executive
```

Priority: CLI `--template` > `docx.template` > `default_template` > programmatic.

### Available Template Variables

DOCX templates have access to the same variables as HTML templates, structured for docxtpl:

#### Contact Information

```
{{ contact.name }}
{{ contact.title }}
{{ contact.email }}
{{ contact.phone }}
{{ contact.location }}
{{ contact.linkedin }}
{{ contact.github }}
{{ contact.website }}
```

#### Summary

```
{{ summary }}
```

#### Experience Sections

```jinja2
{% for section in sections %}
{{ section.title }}
{% for item in section.items %}
{{ item.title }}
{{ item.organization }}
{{ item.location }}
{{ item.start_date }} - {{ item.end_date }}
{{ item.scope_line }}
{% for bullet in item.bullets %}
• {{ bullet }}
{% endfor %}
{% endfor %}
{% endfor %}
```

#### Employer Groups (for grouped position rendering)

```jinja2
{% for group in employer_groups %}
{{ group.employer }}
{{ group.location }}
{{ group.date_range }}
{% if group.is_multi_position %}
{# Multiple positions at same employer #}
{% for pos in group.positions %}
{{ pos.title }}
{{ pos.start_date }} - {{ pos.end_date }}
{{ pos.scope_line }}
{% for bullet in pos.bullets %}
• {{ bullet }}
{% endfor %}
{% endfor %}
{% endif %}
{% endfor %}
```

#### Skills

```jinja2
{% for skill in skills %}{{ skill }}{% if not loop.last %}, {% endif %}{% endfor %}
```

#### Certifications

```jinja2
{% for cert in certifications %}
{{ cert.name }} - {{ cert.issuer }} ({{ cert.year }}){% if cert.expires %}, expires {{ cert.expires[:4] }}{% endif %}
{% endfor %}
```

#### Education

```jinja2
{% for edu in education %}
{{ edu.degree }}, {{ edu.institution }}{% if edu.graduation_year %} ({{ edu.graduation_year }}){% endif %}{% if edu.honors %} - {{ edu.honors }}{% endif %}
{% endfor %}
```

#### Career Highlights

```jinja2
{% for highlight in highlights %}
• {{ highlight }}
{% endfor %}
```

#### Board Roles

```jinja2
{% for role in board_roles %}
{{ role.organization }} - {{ role.role }} ({{ role.type }})
{{ role.start_date }} - {{ role.end_date }}
{% if role.focus %}Focus: {{ role.focus }}{% endif %}
{% endfor %}
```

#### Publications

```jinja2
{% for pub in publications %}
{{ pub.title }}, {{ pub.venue }} ({{ pub.date }})
{% endfor %}
```

#### Tailored Notice (Story 7.19)

```jinja2
{% if tailored_notice_text %}
{{ tailored_notice_text }}
{% endif %}
```

### Example DOCX Template

Create a Word document with this structure:

```
┌─────────────────────────────────────────────────┐
│                 {{ contact.name }}               │
│              {{ contact.title }}                 │
│ {{ contact.email }} | {{ contact.phone }}        │
│             {{ contact.location }}               │
├─────────────────────────────────────────────────┤
│ PROFESSIONAL SUMMARY                             │
│ {{ summary }}                                    │
├─────────────────────────────────────────────────┤
│ PROFESSIONAL EXPERIENCE                          │
│ {% for group in employer_groups %}               │
│ {{ group.employer }} | {{ group.location }}      │
│ {{ group.date_range }}                           │
│ {% for pos in group.positions %}                 │
│   {{ pos.title }}                                │
│   {{ pos.start_date }} - {{ pos.end_date }}      │
│   {% for bullet in pos.bullets %}                │
│   • {{ bullet }}                                 │
│   {% endfor %}                                   │
│ {% endfor %}                                     │
│ {% endfor %}                                     │
├─────────────────────────────────────────────────┤
│ SKILLS                                           │
│ {{ skills|join(", ") }}                          │
├─────────────────────────────────────────────────┤
│ CERTIFICATIONS                                   │
│ {% for cert in certifications %}                 │
│ • {{ cert.name }} - {{ cert.issuer }}            │
│ {% endfor %}                                     │
└─────────────────────────────────────────────────┘
```

### Styling in DOCX Templates

Unlike HTML/CSS, DOCX styling is embedded in the Word document:

1. **Format text directly** - Use Word's formatting tools (bold, italic, fonts, sizes)
2. **Use Word styles** - Apply Heading 1, Heading 2, etc. for section titles
3. **Set colors** - Apply colors using Word's font color picker
4. **Insert logo** - Add images directly in the template (they're preserved during rendering)

### Built-in DOCX Templates

| Template | Description |
|----------|-------------|
| `modern` | Clean, minimal design |
| `executive` | Executive-level with scope indicators |
| `executive-classic` | Traditional executive styling |
| `ats-safe` | ATS-optimized, minimal formatting |
| `cto` | CTO-specific format |
| `cto-results` | CTO with results metrics emphasis |
| `branded` | Brand-colored template with logo |

### Testing DOCX Templates

```bash
# Build with your template
resume build --jd job.txt --format docx --template branded

# Open in Word to verify
open dist/resume.docx
```

### Troubleshooting DOCX Templates

#### Template Not Found

```
DOCX template 'mytemplate' not found, using programmatic generation
```

Check:
- File is in `docx/` subdirectory: `my-templates/docx/mytemplate.docx`
- File has `.docx` extension
- `templates_dir` is configured correctly

#### Placeholder Not Rendering

If `{{ variable }}` appears literally in output:

1. Verify placeholder syntax is exact (no extra spaces)
2. Check variable name matches available variables
3. Ensure docxtpl can read the placeholder (some Word formatting can break it)

**Tip:** Type placeholders in a plain text editor first, then paste into Word.

#### Conditional Sections Not Working

For `{% if %}` and `{% for %}` tags in Word:

1. Each tag must be in its own paragraph or table cell
2. Don't split tags across formatting boundaries
3. Use Word's "Show/Hide ¶" to verify paragraph structure

#### Logo Not Appearing

If your logo disappears:

1. Insert the logo directly in the template (not as a linked image)
2. Use PNG or JPEG format (not SVG)
3. Embed the image (Insert → Pictures → This Device)
