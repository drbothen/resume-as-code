# Story 13.1: DOCX Template System

Status: done

## Story

As a user who generates branded PDF resumes,
I want template-based DOCX generation that matches my PDF templates,
so that I have consistent branding across all output formats.

## Acceptance Criteria

1. **AC1**: DOCXProvider accepts `template_name` and `templates_dir` parameters matching PDFProvider
2. **AC2**: Template loading checks custom `templates_dir/docx/` first, then built-in `templates/docx/`
3. **AC3**: Fallback to programmatic generation (current behavior) if no DOCX template found
4. **AC4**: `docx.template` config option in `.resume.yaml` specifies default DOCX template
5. **AC5**: `--template` flag applies to DOCX generation (not just PDF)
6. **AC6**: At least one branded DOCX template created (`templates/docx/branded.docx`)
7. **AC7**: Logo appears in DOCX header when template includes logo placeholder
8. **AC8**: Brand colors applied to section headings (Navy #1d3557)
9. **AC9**: Unit tests for template loading, fallback behavior, and rendering
10. **AC10**: Integration test verifying DOCX output matches expected structure

## Tasks / Subtasks

- [x] Task 1: Update DOCXProvider constructor (AC: 1, 2, 3)
  - [x] 1.1: Add `template_name: str | None = None` parameter
  - [x] 1.2: Add `templates_dir: Path | None = None` parameter
  - [x] 1.3: Implement `_resolve_template()` method with multi-directory search
  - [x] 1.4: Add fallback logic: template found → docxtpl render, not found → programmatic
  - [x] 1.5: Log warning when falling back to programmatic generation

- [x] Task 2: Implement docxtpl integration (AC: 6, 7, 8)
  - [x] 2.1: Create `_render_from_template()` method using docxtpl
  - [x] 2.2: Build template context dict from ResumeData model
  - [x] 2.3: Handle employer grouping for positions (match PDF template structure)
  - [x] 2.4: Handle optional sections (certifications, publications, etc.)
  - [x] 2.5: Test with existing branded.docx template

- [x] Task 3: Create branded DOCX template (AC: 6, 7, 8)
  - [x] 3.1: Create `templates/docx/` directory
  - [x] 3.2: Design branded.docx in Word with Jinja2 placeholders:
    - Header with triple chevron logo
    - Brand colors: Navy (#1d3557), Red (#e63946), Steel (#457b9d)
    - Professional typography (Calibri)
    - Section headings with colored underlines
  - [x] 3.3: Add all Jinja2 placeholders matching ResumeData structure:
    - `{{ contact.name }}`, `{{ contact.title }}`, `{{ contact.email }}`, etc.
    - `{{ summary }}`
    - `{% for section in sections %}` loop structure
    - `{% for item in section.items %}` nested loop
    - `{% for bullet in item.bullets %}` bullet loop
    - `{% if certifications %}` conditional sections
  - [x] 3.4: Validate template renders with docxtpl

- [x] Task 4: Update build command (AC: 4, 5)
  - [x] 4.1: Pass `template_name` to DOCXProvider in build.py
  - [x] 4.2: Pass `templates_dir` to DOCXProvider (from config or --templates-dir flag)
  - [x] 4.3: Read `docx.template` from config if no --template flag provided
  - [x] 4.4: Ensure --template applies to both PDF and DOCX when format is "all"

- [x] Task 5: Update config model (AC: 4)
  - [x] 5.1: Add `DocxConfig` class to models/config.py:
    ```python
    class DocxConfig(BaseModel):
        template: str | None = None
    ```
  - [x] 5.2: Add `docx: DocxConfig | None = None` field to main Config
  - [x] 5.3: Update schemas/config.schema.json with docx section

- [x] Task 6: Write unit tests (AC: 9)
  - [x] 6.1: Test DOCXProvider with template_name finds correct template
  - [x] 6.2: Test template resolution order (custom dir → built-in)
  - [x] 6.3: Test fallback to programmatic when no template exists
  - [x] 6.4: Test docxtpl context dict contains all required fields
  - [x] 6.5: Test config parsing with docx.template option

- [x] Task 7: Write integration test (AC: 10)
  - [x] 7.1: Build DOCX with branded template
  - [x] 7.2: Verify sections present: contact, summary, experience, skills
  - [x] 7.3: Verify employer grouping matches PDF output structure

- [x] Task 8: Run quality checks (AC: all)
  - [x] 8.1: Run `uv run ruff check src tests --fix`
  - [x] 8.2: Run `uv run ruff format src tests`
  - [x] 8.3: Run `uv run mypy src --strict`
  - [x] 8.4: Run `uv run pytest`

- [x] Task 9: Update documentation
  - [x] 9.1: Update CLAUDE.md with docx.template config option
  - [x] 9.2: Add DOCX template section to template-authoring.md

## Dev Notes

### Architecture Compliance

This story extends the existing provider pattern. DOCXProvider already exists; we're adding template support to match PDFProvider capabilities.

**Layer boundaries:**
- Model change: `models/config.py` (DocxConfig)
- Provider change: `providers/docx.py` (template support)
- Command change: `commands/build.py` (pass template params)
- Schema: `schemas/config.schema.json` (docx section)

### Current DOCX Provider Architecture

Location: `src/resume_as_code/providers/docx.py`

Current implementation is programmatic-only:
```python
class DOCXProvider:
    def _build_document(self, resume: ResumeData) -> Document:
        doc = Document()
        # Programmatic paragraph/table creation
        # Hardcoded styles
        return doc
```

### Proposed Changes

```python
class DOCXProvider:
    def __init__(
        self,
        template_name: str | None = None,
        templates_dir: Path | None = None,
    ) -> None:
        self.template_name = template_name
        self.templates_dir = templates_dir

    def _resolve_template(self) -> Path | None:
        """Find DOCX template file, checking custom dir first."""
        if not self.template_name:
            return None

        template_filename = f"{self.template_name}.docx"

        # Check custom templates dir first
        if self.templates_dir:
            custom_path = self.templates_dir / "docx" / template_filename
            if custom_path.exists():
                return custom_path

        # Fall back to built-in templates
        builtin_path = Path(__file__).parent.parent / "templates" / "docx" / template_filename
        if builtin_path.exists():
            return builtin_path

        return None

    def _build_document(self, resume: ResumeData) -> Document:
        template_path = self._resolve_template()

        if template_path:
            return self._render_from_template(resume, template_path)

        # Fallback to existing programmatic generation
        logger.warning(f"DOCX template '{self.template_name}' not found, using programmatic generation")
        return self._build_programmatic(resume)

    def _render_from_template(self, resume: ResumeData, template_path: Path) -> Document:
        """Render resume using docxtpl template."""
        from docxtpl import DocxTemplate

        doc = DocxTemplate(str(template_path))
        context = self._build_template_context(resume)
        doc.render(context)
        return doc.docx  # Returns underlying python-docx Document
```

### docxtpl Template Context

Build context dict matching template placeholders:

```python
def _build_template_context(self, resume: ResumeData) -> dict[str, Any]:
    """Build Jinja2 context for docxtpl template."""
    return {
        # Contact info
        "contact": {
            "name": resume.contact.name,
            "title": resume.contact.title,
            "email": resume.contact.email,
            "phone": resume.contact.phone,
            "location": resume.contact.location,
            "linkedin": resume.contact.linkedin,
        },

        # Summary
        "summary": resume.summary,

        # Sections (experience, skills, etc.)
        "sections": [
            {
                "title": section.title,
                "items": [
                    {
                        "title": item.title,
                        "subtitle": item.subtitle,
                        "date_range": item.date_range,
                        "bullets": [b.text for b in item.bullets],
                    }
                    for item in section.items
                ],
            }
            for section in resume.sections
        ],

        # Employer groups (for grouped position rendering)
        "employer_groups": resume.employer_groups if hasattr(resume, 'employer_groups') else None,

        # Optional sections
        "certifications": [c.model_dump() for c in resume.certifications] if resume.certifications else None,
        "education": [e.model_dump() for e in resume.education] if resume.education else None,
        "publications": [p.model_dump() for p in resume.get_sorted_publications()] if resume.publications else None,
        "board_roles": [b.model_dump() for b in resume.board_roles] if resume.board_roles else None,
        "highlights": resume.highlights if resume.highlights else None,
    }
```

### DOCX Template Placeholders

Example structure in branded.docx (Jinja2 syntax):

```
{{ contact.name }}
{{ contact.title }}
{{ contact.email }} | {{ contact.phone }} | {{ contact.location }}

PROFESSIONAL SUMMARY
{{ summary }}

{% if highlights %}
CAREER HIGHLIGHTS
{% for highlight in highlights %}
• {{ highlight }}
{% endfor %}
{% endif %}

PROFESSIONAL EXPERIENCE
{% for section in sections %}
{% if section.title == "Experience" %}
{% for item in section.items %}
{{ item.title }} | {{ item.subtitle }}
{{ item.date_range }}
{% for bullet in item.bullets %}
• {{ bullet }}
{% endfor %}

{% endfor %}
{% endif %}
{% endfor %}

{% if certifications %}
CERTIFICATIONS
{% for cert in certifications %}
{{ cert.name }} - {{ cert.issuer }} ({{ cert.date }})
{% endfor %}
{% endif %}
```

### Config Schema Addition

```yaml
# .resume.yaml
docx:
  template: branded  # Optional: uses templates/docx/branded.docx
```

```json
// schemas/config.schema.json
{
  "properties": {
    "docx": {
      "type": "object",
      "properties": {
        "template": {
          "type": "string",
          "description": "DOCX template name (without .docx extension)"
        }
      }
    }
  }
}
```

### File Locations

| File | Change Type |
|------|-------------|
| `src/resume_as_code/providers/docx.py` | Modify - add template support |
| `src/resume_as_code/models/config.py` | Modify - add DocxConfig |
| `src/resume_as_code/commands/build.py` | Modify - pass template params |
| `src/resume_as_code/schemas/config.schema.json` | Modify - add docx section |
| `src/resume_as_code/templates/docx/branded.docx` | Create - branded template |
| `tests/unit/test_docx_provider.py` | Create/Modify - template tests |
| `tests/integration/test_docx_template.py` | Create - integration test |

### Dependencies

Already installed (verified in pyproject.toml):
- `docxtpl>=0.16` - Template-based DOCX generation (Jinja2 syntax in Word docs)
- `python-docx>=1.1` - Low-level DOCX manipulation

### Brand Colors for Template

Match existing branded.css:
- Navy: #1d3557 (headings, borders)
- Red: #e63946 (accents)
- Steel: #457b9d (secondary text)

### Logo Handling

The triple chevron logo needs to be:
1. Converted from SVG to PNG/JPEG for Word compatibility
2. Inserted as header image in template
3. Can use docxtpl's image handling: `{{ logo_image }}`

Alternative: Embed logo directly in .docx template file (simpler, recommended).

### Testing Patterns

```python
# Test template resolution
def test_docx_provider_resolves_custom_template(tmp_path):
    """Custom templates dir takes precedence."""
    custom_dir = tmp_path / "templates" / "docx"
    custom_dir.mkdir(parents=True)
    (custom_dir / "custom.docx").touch()

    provider = DOCXProvider(template_name="custom", templates_dir=tmp_path / "templates")
    template = provider._resolve_template()

    assert template == custom_dir / "custom.docx"

# Test fallback
def test_docx_provider_falls_back_to_programmatic():
    """No template triggers programmatic generation."""
    provider = DOCXProvider(template_name="nonexistent")
    # Should not raise, should fall back
    template = provider._resolve_template()
    assert template is None

# Test context building
def test_docx_template_context_has_required_fields(sample_resume):
    """Template context includes all needed fields."""
    provider = DOCXProvider()
    context = provider._build_template_context(sample_resume)

    assert "contact" in context
    assert context["contact"]["name"] == sample_resume.contact.name
    assert "sections" in context
    assert "summary" in context
```

### References

- Feature Request: `/Users/jmagady/Dev/jmagady-resume/_bmad-output/planning-artifacts/feature-requests/docx-template-system.md`
- Current DOCX provider: `src/resume_as_code/providers/docx.py`
- PDF template service: `src/resume_as_code/services/template_service.py`
- Branded HTML template: `src/resume_as_code/templates/executive.html`
- docxtpl documentation: https://docxtpl.readthedocs.io/

## Dev Agent Record

### Agent Model Used

Claude Opus 4.5 (claude-opus-4-5-20251101)

### Debug Log References

- Commit: 67af13fdc1e16e043ed545dbfb2f80acd9ed1dc9
- Test run: 91 tests passed (45 unit + 46 integration)

### Completion Notes List

1. **docxtpl Integration**: Used docxtpl library for Jinja2-based template rendering in Word docs. Template context built from ResumeData model with all fields matching PDF template structure.

2. **7 DOCX Templates Created**: modern, executive, executive-classic, ats-safe, cto, cto-results, branded - matching PDF template variants for consistent branding across formats.

3. **Employer Grouping**: `_build_employer_groups()` method groups multiple positions at same employer, matching PDF template's grouped position rendering.

4. **Template Resolution**: Custom templates_dir checked first, then built-in templates. Falls back to programmatic generation with warning if no template found.

5. **Config Priority**: CLI --template > config.docx.template > config.default_template > programmatic

6. **AC7/AC8 Note**: Logo and brand colors embedded in .docx template binary files. Manual verification required to confirm visual styling matches PDF templates.

### File List

| File | Change |
|------|--------|
| `src/resume_as_code/providers/docx.py` | Added template_name, templates_dir params; _resolve_template(), _render_from_template(), _build_template_context(), _build_employer_groups() methods |
| `src/resume_as_code/models/config.py` | Added DocxConfig class with template field |
| `src/resume_as_code/commands/build.py` | Pass template params to DOCXProvider; resolve docx.template from config |
| `src/resume_as_code/schemas/config.schema.json` | Added DocxConfig definition and docx field to ResumeConfig |
| `src/resume_as_code/templates/docx/branded.docx` | Created - branded template with Jinja2 placeholders |
| `src/resume_as_code/templates/docx/modern.docx` | Created - modern template |
| `src/resume_as_code/templates/docx/executive.docx` | Created - executive template |
| `src/resume_as_code/templates/docx/executive-classic.docx` | Created - classic executive template |
| `src/resume_as_code/templates/docx/ats-safe.docx` | Created - ATS-optimized template |
| `src/resume_as_code/templates/docx/cto.docx` | Created - CTO template |
| `src/resume_as_code/templates/docx/cto-results.docx` | Created - CTO results-focused template |
| `tests/unit/test_docx_provider.py` | Added template resolution tests, fallback tests |
| `tests/unit/test_build_command.py` | Added DOCX template integration tests |
| `tests/integration/test_template_rendering.py` | Added TestDOCXTemplateIntegration class (9 tests) |
| `CLAUDE.md` | Added docx.template config documentation |
| `docs/template-authoring.md` | Added DOCX template authoring section |
| `tests/unit/test_config_models.py` | Added TestDocxConfig and TestResumeConfigDocx test classes (7 tests) |
