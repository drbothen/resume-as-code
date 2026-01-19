# Epic 11: Technical Debt & Platform Enhancements

**Goal:** Address accumulated technical debt to improve platform quality, extensibility, and user experience

**User Outcome:** Users gain comprehensive validation, customization capabilities, and improved PyPI presence while the codebase becomes more maintainable

**Priority:** P2
**Total Points:** 23 (6 stories)

---

## Story 11.1: PyPI Logo Display Fix (TD-004)

As a **potential resume-as-code user browsing PyPI**,
I want **to see the project logo displayed correctly on the package page**,
So that **the project appears professional and trustworthy**.

**Story Points:** 1
**Priority:** P3
**Tech Debt ID:** TD-004

**Problem Statement:**
The project logo is not displaying correctly on the PyPI package page at https://pypi.org/project/resume-as-code-ng/. This reduces visual appeal and makes the project appear less polished compared to other packages.

**Root Cause Analysis:**
PyPI renders README.md but requires absolute URLs for images. Relative paths like `./docs/assets/logo.png` don't resolve correctly since PyPI doesn't host the repository files.

**Acceptance Criteria:**

**Given** the README.md file
**When** rendered on PyPI package page
**Then** the project logo displays correctly
**And** the logo is properly sized and centered

**Given** a local README.md render check
**When** running `python -m readme_renderer README.md`
**Then** no errors or warnings are reported
**And** the logo renders in the preview

**Technical Notes:**

1. Update logo reference in README.md to use absolute raw GitHub URL:
   ```markdown
   ![Resume as Code Logo](https://raw.githubusercontent.com/drbothen/resume-as-code/main/docs/assets/logo.png)
   ```

2. Ensure logo file exists at the referenced path

3. Verify logo format is supported (PNG recommended, SVG may have issues)

4. Test rendering locally before release:
   ```bash
   pip install readme_renderer
   python -m readme_renderer README.md -o /tmp/readme.html
   open /tmp/readme.html
   ```

**Files to Modify:**
- `README.md` (update logo image URL)

**Definition of Done:**
- [ ] Logo URL updated to absolute raw GitHub URL
- [ ] `python -m readme_renderer README.md` passes without errors
- [ ] Logo displays correctly on PyPI after next release
- [ ] Image is appropriately sized (recommended: 200-400px width)

---

## Story 11.2: Directory-Based Sharding for Data Files (TD-005)

As a **power user with many certifications, publications, or other data items**,
I want **optional per-item YAML files organized in directories (like work-units/)**,
So that **I get fine-grained version control and avoid merge conflicts**.

**Story Points:** 8
**Priority:** P3
**Tech Debt ID:** TD-005

**Problem Statement:**
Currently, data files (certifications, education, publications, board-roles, highlights) are stored as single YAML files containing all items as a list. For users with large collections (20+ items) or teams working on shared resume data, this creates:
- Merge conflicts when multiple people edit the same file
- No per-item version history
- Large files that are harder to navigate
- Inconsistency with the work-units/ pattern

**Current Structure:**
```
certifications.yaml      # Contains all certifications as a list
education.yaml           # Contains all education entries as a list
publications.yaml        # Contains all publications as a list
board-roles.yaml         # Contains all board roles as a list
highlights.yaml          # Contains all highlights as a list
```

**Proposed Structure (optional, additive):**
```
certifications/
├── cert-2023-06-aws-solutions-architect.yaml
├── cert-2022-11-cissp.yaml
└── cert-2021-03-cka.yaml

publications/
├── pub-2023-10-scaling-engineering-teams.yaml
└── pub-2022-06-zero-trust-architecture.yaml

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

**Acceptance Criteria:**

**Given** a `.resume.yaml` with `certifications_dir: ./certifications/`
**When** loading certifications data
**Then** the system reads all YAML files from the directory
**And** combines them into a single list for processing

**Given** both `certifications.yaml` AND `certifications/` directory exist
**When** loading certifications
**Then** the system uses the directory (directory takes precedence)
**And** logs a warning about the dual configuration

**Given** a user runs `resume new certification` with directory mode enabled
**When** the certification is created
**Then** it's written to a new file in `certifications/`
**And** the filename follows pattern: `cert-YYYY-MM-{slug}.yaml`

**Given** a project with single-file storage
**When** running `resume migrate --shard certifications`
**Then** items are extracted to individual files
**And** original file is backed up
**And** config is updated to use directory mode

**Given** a `resume list certifications` command
**When** in directory mode
**Then** all certifications display identically to single-file mode
**And** source file path is shown with `--verbose` flag

**Technical Notes:**

**ID Patterns per Type:**
| Resource | ID Pattern | Example |
|----------|------------|---------|
| Certifications | `cert-YYYY-MM-{slug}` | `cert-2023-06-aws-solutions-architect.yaml` |
| Publications | `pub-YYYY-MM-{slug}` | `pub-2022-06-zero-trust-architecture.yaml` |
| Education | `edu-YYYY-{institution-slug}` | `edu-2016-stanford-mba.yaml` |
| Board Roles | `board-YYYY-MM-{org-slug}` | `board-2022-03-cybershield-ventures.yaml` |
| Highlights | `hl-NNN-{slug}` | `hl-001-digital-transformation.yaml` |

**Config Options:**
```yaml
# .resume.yaml
data_paths:
  certifications: ./certifications.yaml     # Single file (default)
  # OR
  certifications_dir: ./certifications/     # Directory mode

  publications: ./publications.yaml         # Single file (default)
  # OR
  publications_dir: ./publications/         # Directory mode

  # Same pattern for education, board_roles, highlights
```

**Three-tier Loading Fallback:**
1. Check for `*_dir` config → load from directory
2. Check for single file → load from file
3. Return empty list

**Files to Create/Modify:**
- Create: `src/resume_as_code/services/sharded_loader.py` (generic directory loader)
- Modify: `src/resume_as_code/services/data_loader.py` (add fallback logic)
- Modify: `src/resume_as_code/commands/new.py` (support directory writes)
- Modify: `src/resume_as_code/commands/remove.py` (support directory deletes)
- Modify: `src/resume_as_code/models/config.py` (add *_dir options)
- Create: migration for single-file to sharded conversion

**Definition of Done:**
- [ ] Generic `ShardedLoader` class following `WorkUnitLoader` pattern
- [ ] Config supports both `*_path` and `*_dir` options per resource type
- [ ] Three-tier loading fallback implemented
- [ ] `resume new <resource>` writes to directory when configured
- [ ] `resume list <resource>` works identically in both modes
- [ ] `resume remove <resource>` works in directory mode
- [ ] Migration command to convert single-file to directory
- [ ] Unit tests for both storage modes
- [ ] Documentation updated with new config options

---

## Story 11.3: Custom Templates Directory Support (TD-006)

As a **user who wants branded or customized resume templates**,
I want **to specify a custom templates directory via config or CLI**,
So that **I can create and use my own templates without modifying the package**.

**Story Points:** 3
**Priority:** P2
**Tech Debt ID:** TD-006

**Problem Statement:**
Users cannot create or use custom resume templates without modifying the installed package. The `TemplateService` class already accepts a `templates_dir` parameter internally, but this is not exposed via CLI or configuration. This limits customization and prevents organizations from maintaining corporate templates.

**Current Behavior:**
```python
# TemplateService supports custom directory internally but not exposed
def __init__(self, templates_dir: Path | None = None) -> None:
    if templates_dir is None:
        templates_dir = Path(__file__).parent.parent / "templates"  # Package default only
```

**Acceptance Criteria:**

**Given** a `.resume.yaml` with `templates_dir: ./templates`
**When** running `resume build --template my-custom`
**Then** the system looks for `./templates/my-custom.html`
**And** falls back to built-in templates if not found

**Given** a `--templates-dir ./my-templates` CLI flag
**When** running `resume build --templates-dir ./my-templates --template branded`
**Then** the CLI flag overrides the config setting
**And** `./my-templates/branded.html` is used

**Given** a custom templates directory with `custom.html`
**When** running `resume build --template custom`
**Then** the custom template is used successfully
**And** all built-in templates remain available

**Given** a custom template that uses `{% extends "executive.html" %}`
**When** building the resume
**Then** the template inheritance works correctly
**And** the custom template can override specific blocks

**Given** `resume build --template nonexistent`
**When** template doesn't exist in custom or built-in directories
**Then** clear error message indicates available templates
**And** lists templates from both custom and built-in directories

**Technical Notes:**

**Config Addition:**
```yaml
# .resume.yaml
templates_dir: ./templates  # Optional, supplements built-in templates
```

**CLI Flag:**
```bash
resume build --jd job.txt --templates-dir ./my-templates --template branded
```

**Template Loading Order (additive, not replacement):**
```
1. Check custom templates_dir first (if configured)
2. Fall back to package built-in templates
Result: All built-in templates remain available; custom templates add to options
```

**Jinja2 Implementation:**
```python
# Use multiple directories with FileSystemLoader
from jinja2 import FileSystemLoader, Environment

loaders = []
if custom_templates_dir:
    loaders.append(custom_templates_dir)
loaders.append(builtin_templates_dir)

env = Environment(loader=FileSystemLoader(loaders))
```

**Files to Modify:**
- Modify: `src/resume_as_code/models/config.py` (add `templates_dir` field)
- Modify: `src/resume_as_code/services/template_service.py` (support multiple directories)
- Modify: `src/resume_as_code/commands/build.py` (add `--templates-dir` flag, pass to service)
- Update: `schemas/config.schema.json` (add templates_dir)

**Definition of Done:**
- [ ] `templates_dir` config option in `.resume.yaml`
- [ ] `--templates-dir` CLI flag for `resume build`
- [ ] Multi-directory FileSystemLoader in TemplateService
- [ ] Built-in templates always available as fallback
- [ ] Template inheritance works across directories
- [ ] Error messages list available templates from all sources
- [ ] Unit tests for custom template loading
- [ ] CLAUDE.md updated with new options

---

## Story 11.4: Template Authoring Documentation (TD-007)

As a **user or designer creating custom resume templates**,
I want **comprehensive documentation on template variables, CSS patterns, and best practices**,
So that **I can create professional templates without reverse-engineering the codebase**.

**Story Points:** 3
**Priority:** P3
**Tech Debt ID:** TD-007

**Problem Statement:**
No documentation exists for users who want to create custom resume templates. Template authors need to understand:
- Available template variables and their types
- Data structures (ResumeData, ResumeSection, ResumeItem, etc.)
- CSS class reference and styling patterns
- Template inheritance and block overrides
- Print/PDF considerations
- Best practices for ATS compatibility

**Acceptance Criteria:**

**Given** a user wants to create a custom template
**When** they read the template authoring documentation
**Then** they find complete variable reference with types
**And** code examples for common patterns
**And** CSS class reference

**Given** the documentation
**When** a user follows the quick start guide
**Then** they can create a basic working template
**And** render it with `resume build --template my-template`

**Given** the documentation CSS section
**When** a user styles their template
**Then** they understand print vs screen considerations
**And** can create ATS-compatible layouts

**Technical Notes:**

**Documentation Structure:**
```
docs/
└── template-authoring.md
    ├── Quick Start
    ├── Template Structure
    ├── Template Variables Reference
    │   ├── Root Context
    │   ├── resume.contact (ContactInfo)
    │   ├── resume (ResumeData)
    │   ├── ResumeSection
    │   ├── ResumeItem
    │   ├── ResumeBullet
    │   ├── Certification
    │   ├── Education
    │   ├── BoardRole
    │   ├── Publication
    │   └── employer_groups
    ├── Helper Methods
    ├── Template Inheritance
    ├── CSS Styling Guide
    │   ├── File Structure
    │   ├── Page Setup (@page rules)
    │   ├── Base Styles
    │   ├── Color Palette
    │   ├── Typography Scale
    │   ├── CSS Class Reference
    │   ├── Print Styles
    │   └── Screen Preview Styles
    ├── CSS Inheritance
    ├── Best Practices
    │   ├── ATS Compatibility
    │   ├── Handling Null Values
    │   ├── Page Length Control
    │   └── Testing Templates
    └── Examples
```

**Content Source:**
The detailed template variable reference and CSS guide already exists in TD-007 description in tech-debt.md. This story extracts and formats it as proper documentation.

**Files to Create:**
- Create: `docs/template-authoring.md`

**Definition of Done:**
- [ ] `docs/template-authoring.md` created
- [ ] Complete variable reference with types documented
- [ ] All CSS classes documented with purpose
- [ ] Template inheritance explained with examples
- [ ] Print/PDF considerations documented
- [ ] Quick start example that works out of the box
- [ ] Best practices section for ATS compatibility
- [ ] README.md links to template authoring guide

---

## Story 11.5: Comprehensive Resource Validation (TD-008)

As a **resume-as-code user**,
I want **`resume validate` to check ALL resources, not just work units**,
So that **I can catch all errors before running build or plan commands**.

**Story Points:** 6
**Priority:** P2
**Tech Debt ID:** TD-008

**Problem Statement:**
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

**Acceptance Criteria:**

**Given** a user runs `resume validate` with no arguments
**When** validation completes
**Then** ALL resources are validated:
  - Work Units (existing schema validation)
  - Positions (schema + date logic)
  - Certifications (schema + expiration dates)
  - Education (schema)
  - Publications (schema + date format)
  - Board Roles (schema + date logic)
  - Highlights (schema)
  - `.resume.yaml` config (schema version, paths exist)

**Given** validation of all resources
**When** complete
**Then** summary output shows status per resource type:
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

**Given** `resume validate positions` (subcommand)
**When** validation runs
**Then** only positions.yaml is validated
**And** output shows position-specific results

**Given** cross-resource validation
**When** a certification has `date > expires`
**Then** a validation error is reported
**And** the specific field and issue is identified

**Given** the `--json` flag
**When** running `resume validate`
**Then** output is structured JSON with all validation results
**And** includes resource type, item count, errors, and warnings

**Technical Notes:**

**CLI Structure:**
```bash
resume validate                      # Validate everything (new default)
resume validate work-units           # Just work units (current behavior)
resume validate positions            # Just positions.yaml
resume validate certifications       # Just certifications
resume validate education            # Just education
resume validate publications         # Just publications
resume validate board-roles          # Just board roles
resume validate highlights           # Just highlights
resume validate config               # Just .resume.yaml
```

**Validation Rules per Resource:**

| Resource | Schema | Cross-field | Cross-resource |
|----------|--------|-------------|----------------|
| Work Units | JSON schema | date logic | position_id exists |
| Positions | Pydantic | start_date <= end_date | - |
| Certifications | Pydantic | date <= expires | - |
| Education | Pydantic | - | - |
| Publications | Pydantic | valid date format | - |
| Board Roles | Pydantic | start_date <= end_date | - |
| Highlights | Pydantic | - | - |
| Config | JSON schema | paths exist | schema_version valid |

**Architecture:**
```python
# src/resume_as_code/services/validators/base.py
class ResourceValidator(ABC):
    @abstractmethod
    def validate(self, path: Path) -> ValidationResult:
        pass

# src/resume_as_code/services/validators/position_validator.py
class PositionValidator(ResourceValidator):
    def validate(self, path: Path) -> ValidationResult:
        # Load, validate schema, check date logic
        pass
```

**Files to Create/Modify:**
- Create: `src/resume_as_code/services/validators/__init__.py`
- Create: `src/resume_as_code/services/validators/base.py`
- Create: `src/resume_as_code/services/validators/position_validator.py`
- Create: `src/resume_as_code/services/validators/certification_validator.py`
- Create: `src/resume_as_code/services/validators/education_validator.py`
- Create: `src/resume_as_code/services/validators/publication_validator.py`
- Create: `src/resume_as_code/services/validators/board_role_validator.py`
- Create: `src/resume_as_code/services/validators/highlight_validator.py`
- Create: `src/resume_as_code/services/validators/config_validator.py`
- Modify: `src/resume_as_code/commands/validate.py` (add subcommands, aggregate results)
- Modify: `src/resume_as_code/services/validator.py` (orchestrate all validators)

**Definition of Done:**
- [ ] `resume validate` validates ALL resources by default
- [ ] Subcommands for individual resource validation
- [ ] Summary output with counts per resource type
- [ ] Cross-field validation (date logic) for applicable resources
- [ ] Cross-resource validation (position_id references)
- [ ] `--json` flag produces structured output
- [ ] Exit code reflects validation status (0=pass, 1=errors, warnings don't affect exit)
- [ ] Unit tests for each validator
- [ ] CLAUDE.md updated with new validate subcommands

---

## Story 11.6: Expose Publication Abstracts in Templates

As a **CTO or executive with curated publications**,
I want **to optionally display publication abstracts on my resume**,
So that **recruiters and hiring managers can understand the depth and relevance of my thought leadership**.

**Story Points:** 2
**Priority:** P3

**Problem Statement:**
The `Publication` model already stores an `abstract` field (max 500 chars) used for JD-relevant curation during the `plan` and `build` commands. However, this valuable content is never rendered in the resume output. For executive roles where publications demonstrate thought leadership, showing abstracts provides context that titles alone cannot convey.

**Current Behavior:**
```html
<!-- Publications render as title + venue + year only -->
RSA Conference (2024) - Zero Trust Architecture: A Practical Guide
Scaling Engineering Teams, O'Reilly Media (2023)
```

**Proposed Behavior:**
```html
<!-- With abstracts enabled -->
RSA Conference (2024) - Zero Trust Architecture: A Practical Guide
  Deep dive into implementing zero trust principles across hybrid cloud environments.

Scaling Engineering Teams, O'Reilly Media (2023)
  Practical strategies for growing engineering organizations from 20 to 200+ engineers.
```

**Acceptance Criteria:**

**Given** a `.resume.yaml` with `template_options.show_publication_abstracts: true`
**When** building a resume with publications that have abstracts
**Then** abstracts are rendered below each publication entry
**And** publications without abstracts render normally (no empty space)

**Given** `template_options.show_publication_abstracts: false` (default)
**When** building a resume
**Then** publications render exactly as they do today (no abstracts)
**And** existing resumes are not affected

**Given** `template_options.abstract_style: block`
**When** building with abstracts enabled
**Then** abstracts render with left-border blockquote styling

**Given** `template_options.abstract_style: compact`
**When** building with abstracts enabled
**Then** abstracts are truncated to `abstract_max_length` characters with ellipsis
**And** render inline after the publication title

**Given** a custom template that overrides the publications block
**When** the user wants to show abstracts
**Then** the `pub.abstract` variable is available in the template context

**Technical Notes:**

**Config Options:**
```yaml
# .resume.yaml
template_options:
  show_publication_abstracts: false  # default: false (opt-in feature)
  abstract_style: inline             # inline | block | compact (default: inline)
  abstract_max_length: 120           # for compact style truncation (default: 120)
```

**Template Variable Access:**
The `Publication` model already exposes:
- `pub.abstract` - Full abstract text (or None)
- `pub.format_display(include_abstract=True)` - Pre-formatted display string

**Styling Options:**
| Style | Description | Use Case |
|-------|-------------|----------|
| `inline` | Indented italic text below title | Clean, professional look |
| `block` | Left-bordered blockquote | Academic/research emphasis |
| `compact` | Truncated inline after title | Space-constrained resumes |

**Template Changes (executive.html):**
```jinja2
{% block publications %}
{% if resume.get_sorted_publications() %}
<section class="publications">
    <h2>Publications & Speaking</h2>
    {% for pub in resume.get_sorted_publications() %}
    <div class="pub-entry">
        {# Existing title/venue/year rendering #}
        {% if pub.is_speaking %}
        {{ pub.venue }} ({{ pub.year }}) - {% if pub.url %}<a href="{{ pub.url }}">{{ pub.title }}</a>{% else %}{{ pub.title }}{% endif %}
        {% else %}
        {% if pub.url %}<a href="{{ pub.url }}">{{ pub.title }}</a>{% else %}{{ pub.title }}{% endif %}, {{ pub.venue }} ({{ pub.year }})
        {% endif %}

        {# NEW: Optional abstract rendering #}
        {% if show_abstracts and pub.abstract %}
        <span class="abstract abstract-{{ abstract_style }}">{{ pub.abstract | truncate(abstract_max_length) if abstract_style == 'compact' else pub.abstract }}</span>
        {% endif %}
    </div>
    {% endfor %}
</section>
{% endif %}
{% endblock %}
```

**CSS Additions (executive.css):**
```css
/* Publication abstracts */
.pub-entry .abstract {
    display: block;
    margin-top: 0.25em;
}

.pub-entry .abstract-inline {
    font-style: italic;
    color: #555;
    font-size: 10pt;
    margin-left: 1em;
}

.pub-entry .abstract-block {
    color: #444;
    font-size: 9.5pt;
    margin: 0.3em 0 0.5em 1.5em;
    padding-left: 0.5em;
    border-left: 2px solid #ddd;
}

.pub-entry .abstract-compact {
    display: inline;
    color: #666;
    font-size: 9.5pt;
}
```

**Files to Modify:**
- Modify: `src/resume_as_code/models/config.py` (add `TemplateOptions` fields)
- Modify: `src/resume_as_code/services/template_service.py` (pass config to template context)
- Modify: `src/resume_as_code/templates/executive.html` (conditional abstract rendering)
- Modify: `src/resume_as_code/templates/executive.css` (abstract styling)
- Modify: `src/resume_as_code/templates/cto.html` (inherits from executive, verify behavior)
- Update: `schemas/config.schema.json` (new template_options fields)

**Definition of Done:**
- [ ] `show_publication_abstracts` config option added to `TemplateOptions`
- [ ] `abstract_style` config option with enum validation (inline/block/compact)
- [ ] `abstract_max_length` config option for compact truncation
- [ ] executive.html publications block updated with conditional abstract rendering
- [ ] CSS classes for all three abstract styles
- [ ] Config values passed to template context via TemplateService
- [ ] Unit tests for config options
- [ ] Integration test verifying abstract appears in rendered HTML
- [ ] Default behavior unchanged (abstracts hidden by default)
- [ ] CLAUDE.md updated with new template_options
- [ ] Mockup file can be deleted after implementation

**Visual Mockup:**
See `_bmad-output/mockups/publications-with-abstracts-preview.html` for visual comparison of styling options.

---

## Epic Dependencies

| Story | Depends On | Blocks |
|-------|------------|--------|
| 11.1 (PyPI Logo) | None | None |
| 11.2 (Directory Sharding) | None | None |
| 11.3 (Custom Templates) | None | 11.4 |
| 11.4 (Template Docs) | 11.3 (partial) | None |
| 11.5 (Validation) | None | None |
| 11.6 (Publication Abstracts) | None | 11.4 (partial) |

## Recommended Implementation Order

1. **11.1** - Quick win, 1 point
2. **11.5** - High value, improves user experience
3. **11.3** - Enables customization
4. **11.6** - Small enhancement, 2 points
5. **11.4** - Documentation for 11.3 and 11.6
6. **11.2** - Lower priority, power user feature

---
