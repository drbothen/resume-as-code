# Technical Debt Tracking

This file tracks identified technical debt and performance improvements to be addressed in future sprints.

---

## Performance Optimizations

### TD-001: Batch Embedding for Certifications
**Identified:** 2026-01-16
**Story:** 7-14 (JD-Relevant Content Curation)
**Severity:** LOW
**Location:** `src/resume_as_code/services/content_curator.py:214-232`

**Problem:**
For each certification, a new embedding is computed via `embed_query()`. With many certifications (e.g., 20+), this could become slow since each call is a separate model inference.

**Current Behavior:**
```python
for cert in candidates:
    cert_text = f"{cert.name} {cert.issuer or ''}"
    cert_emb = self.embedder.embed_query(cert_text)  # Individual call per cert
    semantic_score = self._cosine_similarity(cert_emb, jd_embedding)
```

**Proposed Fix:**
1. Add `embed_queries_batch()` method to EmbeddingService that accepts a list of strings
2. Compute all certification embeddings in a single batch call
3. Apply same optimization to board_roles and highlights if they exceed a threshold (e.g., 10+ items)

**Impact:**
- Would reduce N embedding calls to 1 batch call
- Estimated 5-10x speedup for users with 20+ certifications
- Not blocking any features, purely performance improvement

---

## Code Quality

### TD-008: Comprehensive Resource Validation ✅ RESOLVED
**Identified:** 2026-01-18
**Resolved:** 2026-01-19
**Story:** 11-5-comprehensive-resource-validation
**Severity:** MEDIUM
**Location:** `src/resume_as_code/commands/validate.py`, `src/resume_as_code/services/validators/`

**Problem:**
The `resume validate` command only validates Work Units against their JSON schema. Other resources (positions, certifications, education, publications, board-roles, highlights) are only validated by Pydantic at load time, meaning users must run other commands to discover validation errors.

**Current Behavior:**
```bash
resume validate                    # Only validates work-units/
resume validate --check-positions  # Validates work unit position_id references, not positions.yaml itself
```

Other resources fail silently until a command tries to load them:
```bash
resume list certifications         # Fails here if certifications.yaml is malformed
```

**Proposed Enhancement:**

1. **Default behavior** - `resume validate` checks ALL resources:
   - Work Units (existing JSON schema validation)
   - Positions (schema + date logic)
   - Certifications (schema + expiration dates)
   - Education (schema)
   - Publications (schema + date format)
   - Board Roles (schema + date logic)
   - Highlights (schema)
   - `.resume.yaml` config (schema version, paths exist)

2. **Subcommands for individual validation:**
   ```bash
   resume validate                      # Validate everything
   resume validate work-units           # Just work units (current behavior)
   resume validate positions            # Just positions.yaml
   resume validate certifications       # Just certifications
   resume validate education            # Just education
   resume validate publications         # Just publications
   resume validate board-roles          # Just board roles
   resume validate highlights           # Just highlights
   resume validate config               # Just .resume.yaml
   ```

3. **Cross-resource validation:**
   - Work unit `position_id` references valid position (existing `--check-positions`)
   - Certification dates are logical (date <= expires)
   - Position dates are logical (start_date <= end_date)
   - Board role dates are logical
   - Publication dates are valid format

4. **Output format:**
   ```
   Validating all resources...

   Work Units:     ✓ 44/44 valid
   Positions:      ✓ 12/12 valid
   Certifications: ✓ 11/11 valid
   Education:      ✓ 1/1 valid
   Publications:   ⚠ 43/45 valid (2 warnings)
   Board Roles:    ✓ 1/1 valid
   Highlights:     ✓ 5/5 valid
   Config:         ✓ Valid

   ────────────────────────────────
   Overall: ✓ All resources valid (2 warnings)
   ```

**Implementation Approach:**
1. Create `ResourceValidator` base class with common validation logic
2. Create specific validators: `PositionValidator`, `CertificationValidator`, etc.
3. Add JSON schemas for other resource types (optional, Pydantic may suffice)
4. Update CLI to support subcommands via Click group
5. Aggregate results for summary output

**Benefits:**
- Single command to validate entire resume project
- Catch all errors before `build` or `plan` commands
- Useful for CI/CD pipelines
- Consistent validation experience across resource types

**Impact:**
- Improves user experience significantly
- Catches errors earlier in workflow
- Medium effort - requires new validators and CLI changes

---

## Architecture

### TD-005: Directory-Based Sharding for Data Files ✅ RESOLVED
**Identified:** 2026-01-18
**Resolved:** 2026-01-19
**Story:** 11-2-directory-based-sharding
**Severity:** LOW
**Location:** `src/resume_as_code/data_loader.py`, `src/resume_as_code/commands/new.py`

**Problem:**
Currently, data files (certifications, education, publications, board-roles, highlights) are stored as single YAML files containing all items. For users with large collections (20+ items) or those who prefer per-item version control, this can be limiting compared to the work unit sharding pattern.

**Current Behavior:**
```
certifications.yaml      # Contains all certifications as a list
education.yaml           # Contains all education entries as a list
publications.yaml        # Contains all publications as a list
board-roles.yaml         # Contains all board roles as a list
highlights.yaml          # Contains all highlights as a list
```

**Proposed Enhancement:**
Support optional directory-based storage (similar to `work-units/`):

```
certifications/
├── cert-2023-06-aws-solutions-architect.yaml
├── cert-2022-11-cissp.yaml
└── cert-2021-03-cka.yaml

publications/
├── pub-2023-10-scaling-engineering-teams.yaml
├── pub-2022-06-zero-trust-architecture.yaml
└── pub-2021-03-devops-practices.yaml

education/
├── edu-2016-stanford-mba.yaml
└── edu-2012-utaustin-bs-cs.yaml

board-roles/
├── board-2022-03-cybershield-ventures.yaml
└── board-2020-01-techstars-austin.yaml

highlights/
├── hl-001-digital-transformation.yaml
└── hl-002-engineering-org-scaling.yaml
```

**Implementation Requirements:**
1. Add `*_dir` config options: `certifications_dir`, `publications_dir`, `education_dir`, `board_roles_dir`, `highlights_dir`
2. Create generic `DataTypeLoader` class following `WorkUnitLoader` pattern
3. Update `data_loader.py` with three-tier fallback: directory → single file → embedded
4. Update CLI commands (`new`, `list`, `show`, `remove`) to support both modes
5. Add migration support (single file → sharded directory)
6. Define ID patterns per type:
   - Certifications: `cert-YYYY-MM-{slug}.yaml`
   - Publications: `pub-YYYY-MM-{slug}.yaml`
   - Education: `edu-YYYY-{institution-slug}.yaml`
   - Board Roles: `board-YYYY-MM-{org-slug}.yaml`
   - Highlights: `hl-NNN-{slug}.yaml`

**Benefits:**
- Fine-grained version control per item
- Parallel editing friendly (no merge conflicts)
- Natural caching at item level
- Consistent with work unit pattern
- Per-item metadata possible (created_date, modified_date)

**Considerations:**
- Most users have 3-15 items per category (sharding may be overkill)
- Adds complexity to data loading
- Should remain optional, not replace single-file mode

**Impact:**
- Not blocking any features
- Enhancement for power users with large collections
- Aligns data management patterns across all entity types

---

### TD-006: Custom Templates Directory Support ✅ RESOLVED
**Identified:** 2026-01-18
**Resolved:** 2026-01-19
**Story:** 11-3-custom-templates-directory
**Severity:** LOW
**Location:** `src/resume_as_code/services/template_service.py`, `src/resume_as_code/models/config.py`

**Problem:**
Users cannot create or use custom resume templates without modifying the installed package. The `TemplateService` class already accepts a `templates_dir` parameter internally, but this is not exposed via CLI or configuration.

**Current Behavior:**
```python
# TemplateService supports custom directory (line 19)
def __init__(self, templates_dir: Path | None = None) -> None:
    if templates_dir is None:
        templates_dir = Path(__file__).parent.parent / "templates"  # Package default only
```

Templates must be one of the built-in options: `modern`, `executive`, `executive-classic`, `ats-safe`, `cto`.

**Proposed Enhancement:**
1. Add `templates_dir` to `ResumeConfig` in `models/config.py`:
   ```yaml
   # .resume.yaml
   templates_dir: ./templates  # Optional custom templates directory
   ```

2. Update `build.py` to pass config value to TemplateService:
   ```python
   template_service = TemplateService(
       templates_dir=Path(config.templates_dir) if config.templates_dir else None
   )
   ```

3. Add `--templates-dir` CLI flag as override:
   ```bash
   resume build --jd job.txt --templates-dir ./my-templates --template custom
   ```

4. Support template inheritance - custom templates can extend built-in templates:
   ```html
   {# my-templates/custom.html #}
   {% extends "executive.html" %}
   {% block header %}...{% endblock %}
   ```

5. **Additive template loading** - custom dir supplements (not replaces) built-in templates:
   ```
   Template lookup order:
   1. Check custom templates_dir first (if configured)
   2. Fall back to package built-in templates

   Result: All built-in templates (modern, executive, etc.) remain available
           Custom templates are added to the available options
   ```

6. `resume build --template` accepts either built-in or custom template names

**Benefits:**
- Users can create branded templates without forking
- Organizations can maintain corporate templates
- Designers can iterate locally before contributing upstream
- Enables template marketplace/sharing
- **Built-in templates always available as baseline**

**Implementation Notes:**
- Template files: `{name}.html` and optional `{name}.css`
- CSS inheritance already supported via `_css_inheritance` map
- Jinja2 FileSystemLoader supports multiple directories via list: `FileSystemLoader([custom_dir, builtin_dir])`
- First match wins - custom templates can override built-ins if same name used

**Impact:**
- Not blocking any features
- Enables customization without package modification
- Low effort - architecture already supports it

---

### TD-007: Template Authoring Documentation ✅ RESOLVED
**Identified:** 2026-01-18
**Resolved:** 2026-01-19
**Story:** 11-4-template-authoring-docs
**Severity:** LOW
**Location:** `docs/template-authoring.md`

**Problem:**
No documentation exists for users who want to create custom resume templates. Template authors need to understand available variables, data structures, CSS patterns, and best practices.

**Proposed Documentation:**

#### 1. Template Structure
```
my-template/
├── my-template.html    # Required: Jinja2 HTML template
└── my-template.css     # Optional: CSS styles (injected via {{ css }})
```

#### 2. Available Template Variables

**Root Context:**
| Variable | Type | Description |
|----------|------|-------------|
| `resume` | ResumeData | Main resume data object |
| `css` | string | Compiled CSS (from .css file) |
| `employer_groups` | list | Grouped positions by employer (Experience section only) |

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
| `scope_team_size` | int? | Team size (raw) |
| `scope_budget` | string? | Budget (raw) |
| `scope_revenue` | string? | Revenue impact (raw) |

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

**employer_groups (for Experience section):**
| Field | Type | Description |
|-------|------|-------------|
| `employer` | string | Employer name |
| `location` | string? | Location |
| `tenure_display` | string | Formatted tenure (e.g., "2020 - Present") |
| `is_multi_position` | bool | True if multiple roles at employer |
| `positions` | list[ResumeItem] | Position entries |

#### 3. Helper Methods
```jinja2
{# Active certifications (not expired, display=true) #}
{% for cert in resume.get_active_certifications() %}

{# Board roles sorted by date #}
{% for role in resume.get_sorted_board_roles() %}

{# Publications sorted by date #}
{% for pub in resume.get_sorted_publications() %}
```

#### 4. Template Inheritance
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

Available blocks (executive.html): `career_highlights`, `achievements`, `board_roles`, `publications`

#### 5. CSS Inheritance
Add to `TemplateService._css_inheritance` for CSS chaining:
```python
_css_inheritance = {
    "cto": "executive",           # cto.css loads after executive.css
    "cto-results": "cto",         # cto-results.css loads after cto.css
    "my-template": "modern",      # my-template.css loads after modern.css
}
```

#### 6. CSS Styling Guide

**File Structure:**
- CSS file must match template name: `my-template.css` for `my-template.html`
- CSS is injected into template via `{{ css }}` variable in `<style>` tag

**Page Setup:**
```css
/* Page size and margins */
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

**Base Styles:**
```css
/* Reset */
* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

body {
    font-family: 'Calibri', 'Segoe UI', Arial, sans-serif;
    font-size: 11pt;        /* 10-11pt for readability */
    line-height: 1.4;
    color: #1a1a1a;
    max-width: 8.5in;
    margin: 0 auto;
}
```

**Color Palette (recommended):**
| Variable | Hex | Usage |
|----------|-----|-------|
| Primary text | `#1a1a1a` | Body text |
| Secondary text | `#555` | Dates, locations |
| Accent | `#2c3e50` | Headers, links |
| Muted | `#7f8c8d` | Meta info |
| Metrics | `#27ae60` | Achievement metrics |
| Border | `#bdc3c7` | Dividers |
| Background | `#f5f5f5` | Skill tags |

**Typography Scale:**
| Element | Size | Weight |
|---------|------|--------|
| Name (h1) | 22pt | 700 |
| Professional title | 14pt | 400 |
| Section headers (h2) | 12pt | 700 |
| Company/position (h3) | 11pt | 600 |
| Body text | 10.5-11pt | 400 |
| Meta (dates, location) | 9.5-10pt | 400 |
| Footer notice | 8.5pt | 400 italic |

**CSS Class Reference:**

*Header:*
| Class | Purpose |
|-------|---------|
| `.resume-header` | Main header container |
| `.name` | Name styling |
| `.professional-title` | Title/headline |
| `.contact-line` | Contact info row |
| `.contact-item` | Individual contact items |
| `.links` | Social links container |

*Sections:*
| Class | Purpose |
|-------|---------|
| `.executive-summary` | Summary section |
| `.career-highlights` | Highlights section |
| `.highlights-list` | Highlights bullet list |
| `.core-competencies` | Skills section |
| `.skills-grid` | Flexbox skills container |
| `.skill` | Individual skill tag |
| `.experience` | Experience section |

*Positions:*
| Class | Purpose |
|-------|---------|
| `.position` | Single position entry |
| `.position-header` | Title + dates row |
| `.company` | Employer name |
| `.role` | Job title |
| `.dates` | Date range |
| `.location` | Location |
| `.scope-line` | Executive scope indicators |

*Employer Groups (multi-position):*
| Class | Purpose |
|-------|---------|
| `.employer-group` | Grouped positions container |
| `.employer-header` | Employer name + tenure |
| `.employer-name` | Company name |
| `.tenure` | Total tenure display |
| `.position.nested` | Nested position entry |
| `.nested-position-header` | Nested title + dates |
| `.role-title` | Role within company |

*Achievements:*
| Class | Purpose |
|-------|---------|
| `.achievements` | Bullet list |
| `.achievements li` | Individual bullet |
| `.metrics` | Quantified impact highlight |

*Other Sections:*
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

**Print Styles:**
```css
@media print {
    body {
        font-size: 10.5pt;
        color: #000;
    }

    /* Ensure black text for printing */
    .name, h2, .company { color: #000; }

    /* Remove link underlines */
    a { text-decoration: none; }

    /* Page break control */
    section { page-break-inside: avoid; }
    .position { page-break-inside: avoid; }
    h2 { page-break-after: avoid; }

    /* Orphan/widow control */
    p, li {
        orphans: 2;
        widows: 2;
    }
}
```

**Screen Preview Styles:**
```css
@media screen {
    body {
        padding: 1in;
        background: #e8e8e8;
    }

    /* Simulate printed page */
    body::before {
        content: '';
        display: block;
        position: fixed;
        top: 0; left: 0; right: 0; bottom: 0;
        background: white;
        box-shadow: 0 2px 15px rgba(0,0,0,0.15);
        z-index: -1;
        max-width: 8.5in;
        margin: 0 auto;
    }
}
```

**Flexbox Patterns:**
```css
/* Header with right-aligned dates */
.position-header {
    display: flex;
    justify-content: space-between;
    align-items: baseline;
}

/* Skills grid with wrapping */
.skills-grid {
    display: flex;
    flex-wrap: wrap;
    gap: 0.5em;
}
```

**Nested Position Styling (career progression):**
```css
.position.nested {
    margin-left: 0.75em;
    padding-left: 0.75em;
    border-left: 2px solid #e0e0e0;  /* Visual hierarchy */
}
```

#### 7. Print/PDF Considerations
```css
@media print {
    .page-break { page-break-before: always; }
    .no-print { display: none; }
}

@page {
    margin: 0.5in;
    size: letter;
}
```

#### 8. Best Practices
- Test with `resume build --jd test.txt --template my-template`
- Use semantic HTML for ATS compatibility
- Provide print styles for PDF generation
- Handle null/empty values with `{% if field %}`
- Use `| join(', ')` for lists
- Keep templates under 2 pages for executive formats

**Impact:**
- Enables community template contributions
- Reduces support burden for custom template questions
- Complements TD-006 (custom templates directory)

---

## CI/CD

### TD-002: GitHub Actions Slow Test Timeout
**Identified:** 2026-01-18
**Story:** 10-1 (PyPI Package Distribution)
**Severity:** MEDIUM
**Location:** `.github/workflows/ci.yml`, `.github/workflows/release.yml`

**Problem:**
GitHub Actions runners are being shutdown during test execution, particularly during integration tests (`test_plan_command.py`, `test_build_command.py`). Current workaround skips these tests in CI entirely.

**Current Behavior:**
```yaml
run: uv run pytest -v -m "not slow" --ignore=tests/integration/test_plan_command.py --ignore=tests/integration/test_build_command.py
```

**Proposed Fix:**
1. Investigate why runners are being terminated (resource limits, timeouts)
2. Consider splitting integration tests into smaller, faster units
3. Add test parallelization with pytest-xdist
4. Configure appropriate timeouts per test category
5. Re-enable full test suite in CI once stable

**Impact:**
- Integration tests only run locally, not in CI
- Reduced confidence in PR validation
- Potential for regressions in plan/build commands

---

### TD-003: TestPyPI Trusted Publisher Configuration
**Identified:** 2026-01-18
**Story:** 10-1 (PyPI Package Distribution)
**Severity:** LOW
**Location:** `.github/workflows/release.yml`, TestPyPI account settings

**Problem:**
TestPyPI trusted publisher needs to be configured for `resume-as-code-ng` (same name as PyPI). Currently TestPyPI publish step fails in release workflow.

**Current Behavior:**
Release workflow publishes to PyPI successfully but TestPyPI step fails, causing smoke test to be skipped.

**Proposed Fix:**
1. Configure trusted publisher on TestPyPI for `resume-as-code-ng`:
   - Owner: `drbothen`
   - Repository: `resume-as-code`
   - Workflow: `release.yml`
   - Environment: `testpypi`
2. Verify with next release (0.1.1+)

**Impact:**
- No pre-release smoke testing on TestPyPI
- Reduced confidence before PyPI publish
- Not blocking releases since PyPI publish works

---

### TD-004: PyPI Logo Not Displaying ✅ RESOLVED
**Identified:** 2026-01-18
**Resolved:** 2026-01-19
**Story:** 11-1-pypi-logo-display-fix
**Severity:** LOW
**Location:** `README.md`, `pyproject.toml`

**Problem:**
Project logo is not displaying correctly on the PyPI package page.

**Current Behavior:**
Logo either missing or broken on https://pypi.org/project/resume-as-code-ng/

**Proposed Fix:**
1. Ensure logo image is accessible via absolute URL (not relative path)
2. Use raw GitHub URL for the image: `https://raw.githubusercontent.com/drbothen/resume-as-code/main/docs/assets/logo.png`
3. Verify image format is supported (PNG/SVG recommended)
4. Check README.md renders correctly with `python -m readme_renderer README.md`

**Impact:**
- Reduced visual appeal on PyPI
- Less professional appearance
- Purely cosmetic, not blocking functionality
