# Epic 13: Output Format Enhancements

**Goal:** Enhance resume output formats to support branded, template-based generation for all output types

**User Outcome:** Users can generate professionally branded DOCX resumes that match their PDF templates, with consistent visual identity across all output formats

**Priority:** P2
**Total Points:** 11 (2 stories)

---

## Story 13.1: DOCX Template System

As a **user who generates branded PDF resumes**,
I want **template-based DOCX generation that matches my PDF templates**,
So that **I have consistent branding across all output formats**.

**Story Points:** 8
**Priority:** P2

**Problem Statement:**
Currently, PDF and DOCX outputs have fundamentally different styling:
- **PDF**: Uses Jinja2 HTML templates + CSS (fully customizable via `templates/branded.html` + `branded.css`)
- **DOCX**: Programmatic generation with python-docx, hardcoded styling, no template system

This means branded resumes generated as PDF look professional with logo, custom colors, and typography, while DOCX output uses generic Word defaults.

**Current Architecture:**

| Aspect | Current State |
|--------|---------------|
| Template System | None - programmatic only |
| Styling | Hardcoded Python values |
| Colors/Branding | Default black text only |
| Logo/Images | Not supported |
| Fonts | Default (Calibri) |
| Layout | Fixed structure |

**Proposed Solution:**

Use the `docxtpl` library (already a dependency in `pyproject.toml` but unused) to enable template-based DOCX generation:

```python
from docxtpl import DocxTemplate

doc = DocxTemplate("templates/docx/branded.docx")
context = {
    'name': resume.contact.name,
    'summary': resume.summary,
    'experience': [...],
}
doc.render(context)
doc.save(output_path)
```

**Acceptance Criteria:**

**Given** a `.resume.yaml` with `docx.template: branded`
**When** running `resume build --format docx`
**Then** the system uses `templates/docx/branded.docx` as the template
**And** the output matches the PDF branded template visually

**Given** a `--template` flag with `resume build`
**When** building DOCX format
**Then** the flag applies to both PDF and DOCX generation
**And** the system looks for matching templates in both `templates/` and `templates/docx/`

**Given** no DOCX template exists for the requested template name
**When** building DOCX
**Then** the system falls back to programmatic generation (current behavior)
**And** logs a warning about missing DOCX template

**Given** a custom templates directory via `--templates-dir` or config
**When** building DOCX
**Then** the system checks `{templates_dir}/docx/{template_name}.docx`
**And** falls back to built-in templates if not found

**Given** a branded DOCX template with logo
**When** the resume is generated
**Then** the logo appears in the document header
**And** brand colors are applied to headings and accents

**Technical Notes:**

**Template Directory Structure:**
```
templates/
├── executive.html
├── executive.css
├── branded.html
├── branded.css
└── docx/
    ├── branded.docx      # Master template matching branded.html
    ├── executive.docx    # Matches executive.html
    └── ats-safe.docx     # Simple ATS-friendly format
```

**docxtpl Template Placeholders:**
```
{{ contact.name }}
{{ contact.title }}
{% for section in sections %}
  {{ section.title }}
  {% for item in section.items %}
    {{ item.title }} | {{ item.subtitle }}
    {% for bullet in item.bullets %}
      {{ bullet.text }}
    {% endfor %}
  {% endfor %}
{% endfor %}
```

**Config Options:**
```yaml
# .resume.yaml
docx:
  template: branded  # Uses templates/docx/branded.docx
```

**Files to Modify:**
- `src/resume_as_code/providers/docx.py` - Add template support, docxtpl integration
- `src/resume_as_code/commands/build.py` - Pass template params to DOCXProvider
- `src/resume_as_code/models/config.py` - Add DocxConfig options (optional)
- `templates/docx/branded.docx` - New file - branded template

**Dependencies:**
Already installed:
- `docxtpl>=0.16` - Template-based DOCX generation
- `python-docx>=1.1` - Low-level DOCX manipulation

**Definition of Done:**
- [ ] DOCXProvider accepts template_name and templates_dir parameters
- [ ] Template loading checks custom dir first, then built-in `templates/docx/`
- [ ] Fallback to programmatic generation if no template found
- [ ] `docx.template` config option in `.resume.yaml`
- [ ] `--template` flag applies to DOCX generation
- [ ] At least one branded DOCX template created
- [ ] Logo appears in DOCX header
- [ ] Brand colors applied to headings
- [ ] Unit tests for template loading and rendering
- [ ] Integration test comparing PDF and DOCX output structure
- [ ] CLAUDE.md updated with DOCX template options

---

## Story 13.2: Work History Duration Filter

As a **user generating a resume for a specific role**,
I want **to limit my work history to the last N years**,
So that **I can focus on recent, relevant experience and avoid resume bloat from ancient positions**.

**Story Points:** 3
**Priority:** P2

**Problem Statement:**
Users with long careers (15+ years) may have positions from early in their career that are no longer relevant. ATS systems and recruiters typically focus on the last 10-15 years. Currently, the plan/build commands include all positions regardless of age, leading to:
- Resumes that exceed 2 pages with old, less-relevant experience
- Dated technologies and skills appearing on the resume
- Employment continuity calculations including very old gaps

**Current Behavior:**
All positions and work units are considered during planning, regardless of date.

**Proposed Solution:**
Add `--years N` flag to `plan` and `build` commands to filter positions and work units by recency:

```bash
# Include only positions/work units from last 10 years
resume plan --jd job.txt --years 10

# Build with 15 years of history
resume build --jd job.txt --years 15
```

**Acceptance Criteria:**

**Given** a `--years 10` flag on the plan command
**When** filtering positions and work units
**Then** only positions with `end_date >= (today - 10 years)` OR `end_date = null` (current) are included
**And** only work units associated with included positions are considered
**And** work units without position_id but with dates in range are included

**Given** the `--years` flag filters out a position
**When** the position is excluded
**Then** it does not appear in the Position Grouping Preview
**And** its work units are excluded from ranking

**Given** no `--years` flag is provided
**When** running plan or build
**Then** all positions and work units are considered (current behavior preserved)

**Given** config option `history_years: 10` in `.resume.yaml`
**When** running plan or build without `--years` flag
**Then** the config value is used as default
**And** CLI flag overrides config value

**Given** employment continuity mode is `minimum_bullet`
**When** `--years 15` excludes a position from 20 years ago
**Then** no gap warning is generated for that ancient position
**And** continuity only considers positions within the year filter

**Given** a position spans the cutoff (started 12 years ago, ended 8 years ago)
**When** `--years 10` is applied
**Then** the position IS included (end_date is within range)

**Technical Notes:**

**Files to Modify:**
- `src/resume_as_code/commands/plan.py` - Add `--years` option, filter positions before ranking
- `src/resume_as_code/commands/build.py` - Add `--years` option, pass to implicit plan generation
- `src/resume_as_code/models/config.py` - Add `history_years: int | None` config option
- `src/resume_as_code/services/position_service.py` - Add `filter_by_years(positions, years)` method

**Filter Logic:**
```python
from datetime import date
from dateutil.relativedelta import relativedelta

def filter_by_years(positions: list[Position], years: int) -> list[Position]:
    """Filter positions to those active within the last N years."""
    cutoff = date.today() - relativedelta(years=years)
    return [
        pos for pos in positions
        if pos.end_date is None  # Current position
        or _parse_date(pos.end_date) >= cutoff
    ]
```

**Config Options:**
```yaml
# .resume.yaml
history_years: 10  # Default years of history (null = unlimited)
```

**CLI Help:**
```
--years INTEGER  Limit work history to last N years (default: from config or unlimited)
```

**Definition of Done:**
- [ ] `--years` flag added to plan command
- [ ] `--years` flag added to build command
- [ ] Config option `history_years` added
- [ ] Position filtering by end_date implemented
- [ ] Work unit filtering respects position filter
- [ ] Employment continuity respects year filter
- [ ] Position Grouping Preview shows only filtered positions
- [ ] Unit tests for date filtering logic
- [ ] CLAUDE.md updated with `--years` flag documentation

---

## Epic Dependencies

| Story | Depends On | Blocks |
|-------|------------|--------|
| 13.1 (DOCX Template) | Epic 11 Story 11.3 (Custom Templates Dir) | None |
| 13.2 (History Filter) | None | None |

## Recommended Implementation Order

1. **13.1** - DOCX template system (in progress)
2. **13.2** - Work history duration filter (independent, can parallelize)

---

## References

- Feature Request: `/Users/jmagady/Dev/jmagady-resume/_bmad-output/planning-artifacts/feature-requests/docx-template-system.md`
- Current DOCX provider: `/src/resume_as_code/providers/docx.py`
- PDF template system: `/src/resume_as_code/services/template_service.py`
- docxtpl documentation: https://docxtpl.readthedocs.io/
