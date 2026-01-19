# Story 11.3: Custom Templates Directory Support

Status: done

## Story

As a **user who wants branded or customized resume templates**,
I want **to specify a custom templates directory via config or CLI**,
So that **I can create and use my own templates without modifying the package**.

## Acceptance Criteria

1. **AC1: Config-based custom templates** - Given a `.resume.yaml` with `templates_dir: ./templates`, when running `resume build --template my-custom`, then the system looks for `./templates/my-custom.html` and falls back to built-in templates if not found.

2. **AC2: CLI flag override** - Given a `--templates-dir ./my-templates` CLI flag, when running `resume build --templates-dir ./my-templates --template branded`, then the CLI flag overrides the config setting and `./my-templates/branded.html` is used.

3. **AC3: Custom template rendering** - Given a custom templates directory with `custom.html`, when running `resume build --template custom`, then the custom template is used successfully and all built-in templates remain available.

4. **AC4: Template inheritance works** - Given a custom template that uses `{% extends "executive.html" %}`, when building the resume, then the template inheritance works correctly and the custom template can override specific blocks.

5. **AC5: Missing template error message** - Given `resume build --template nonexistent`, when template doesn't exist in custom or built-in directories, then clear error message indicates available templates and lists templates from both custom and built-in directories.

## Tasks / Subtasks

- [x] Task 1: Add `templates_dir` config option to ResumeConfig (AC: 1)
  - [x] 1.1 Add `templates_dir: Path | None` field to `ResumeConfig` in `models/config.py`
  - [x] 1.2 Add path expansion validator (same as `output_dir`, `work_units_dir`)
  - [x] 1.3 Update JSON schema generation to include the new field

- [x] Task 2: Add `--templates-dir` CLI flag to build command (AC: 2)
  - [x] 2.1 Add `--templates-dir` option to `build_command` in `commands/build.py`
  - [x] 2.2 Implement resolution: CLI flag > config > None (package default)
  - [x] 2.3 Pass resolved templates_dir to TemplateService

- [x] Task 3: Update TemplateService for multi-directory support (AC: 1, 3, 4)
  - [x] 3.1 Modify `__init__` to accept optional `custom_templates_dir` parameter
  - [x] 3.2 Use Jinja2 FileSystemLoader with list of directories (custom first, then builtin)
  - [x] 3.3 Update CSS loading to check custom directory first, then builtin
  - [x] 3.4 Ensure template inheritance works across directories

- [x] Task 4: Update `list_templates()` to show all available templates (AC: 5)
  - [x] 4.1 Collect templates from both custom and builtin directories
  - [x] 4.2 Deduplicate (custom takes precedence)
  - [ ] 4.3 Add source indicator in verbose mode (e.g., "[custom]" or "[builtin]") - Deferred to future enhancement

- [x] Task 5: Improve error messages for missing templates (AC: 5)
  - [x] 5.1 Catch `jinja2.TemplateNotFound` in TemplateService.render()
  - [x] 5.2 List available templates from all directories
  - [x] 5.3 Suggest closest match if typo detected

- [x] Task 6: Write tests
  - [x] 6.1 Unit tests for TemplateService with custom directory
  - [x] 6.2 Test template inheritance across directories
  - [x] 6.3 Integration test for CLI `--templates-dir` flag
  - [x] 6.4 Test error message with available templates list

- [x] Task 7: Update documentation
  - [x] 7.1 Update CLAUDE.md with `templates_dir` config option
  - [x] 7.2 Update CLAUDE.md with `--templates-dir` CLI flag
  - [x] 7.3 Add example of custom template usage

## Dev Notes

### Problem Statement

Users cannot create or use custom resume templates without modifying the installed package. The `TemplateService` class already accepts a `templates_dir` parameter internally, but this is not exposed via CLI or configuration. This limits customization and prevents organizations from maintaining corporate templates.

### Current Implementation Analysis

**TemplateService (`src/resume_as_code/services/template_service.py`):**

```python
def __init__(self, templates_dir: Path | None = None) -> None:
    if templates_dir is None:
        templates_dir = Path(__file__).parent.parent / "templates"  # Package default only

    self.templates_dir = templates_dir
    self.env = Environment(
        loader=FileSystemLoader(templates_dir),
        autoescape=select_autoescape(["html", "xml"]),
    )
```

Key observations:
- Already accepts `templates_dir` parameter but only uses ONE directory
- Need to change to support MULTIPLE directories (custom + builtin)
- `list_templates()` only scans `self.templates_dir`
- CSS loading in `get_css()` only checks `self.templates_dir`

**Build command (`src/resume_as_code/commands/build.py`):**

```python
@click.option(
    "--template",
    "-t",
    "template_name",
    default=None,
    help="Template to use for rendering (default: from config or 'modern')",
)
```

- Has `--template` but no `--templates-dir`
- Passes `template_name` to providers
- PDFProvider instantiated with `template_name` only

**PDFProvider (`src/resume_as_code/providers/pdf.py`):**

```python
def __init__(
    self,
    template_name: str = "modern",
    templates_dir: Path | None = None  # Likely not used
) -> None:
```

- Need to verify if templates_dir is passed through
- If not, add plumbing from build command

**Config model (`src/resume_as_code/models/config.py`):**

```python
class ResumeConfig(BaseModel):
    default_template: str = Field(default="modern")
    # NO templates_dir field currently
```

### Proposed Solution

**1. Jinja2 Multi-Directory Loader:**

```python
from jinja2 import FileSystemLoader, Environment

def __init__(
    self,
    custom_templates_dir: Path | None = None,
    builtin_templates_dir: Path | None = None,
) -> None:
    if builtin_templates_dir is None:
        builtin_templates_dir = Path(__file__).parent.parent / "templates"

    self.builtin_templates_dir = builtin_templates_dir
    self.custom_templates_dir = custom_templates_dir

    # Build loader list: custom first (higher priority), then builtin
    loader_paths: list[Path] = []
    if custom_templates_dir and custom_templates_dir.exists():
        loader_paths.append(custom_templates_dir)
    loader_paths.append(builtin_templates_dir)

    self.env = Environment(
        loader=FileSystemLoader([str(p) for p in loader_paths]),
        autoescape=select_autoescape(["html", "xml"]),
    )
```

**2. Config Addition:**

```python
class ResumeConfig(BaseModel):
    # ... existing fields ...
    templates_dir: Path | None = Field(
        default=None,
        description="Path to custom templates directory (supplements built-in templates)"
    )

    @field_validator("templates_dir", mode="before")
    @classmethod
    def expand_templates_path(cls, v: str | Path | None) -> Path | None:
        if v is None:
            return None
        if isinstance(v, str):
            v = Path(v)
        return v.expanduser()
```

**3. CLI Flag Addition:**

```python
@click.option(
    "--templates-dir",
    "templates_dir",
    type=click.Path(exists=True, file_okay=False, dir_okay=True, path_type=Path),
    default=None,
    help="Custom templates directory (supplements built-in templates)",
)
```

**4. Template Loading Order:**

```
1. Check custom templates_dir first (if configured via CLI or config)
2. Fall back to package built-in templates
Result: All built-in templates remain available; custom templates add/override options
```

### CSS Loading Update

Current `get_css()` method needs to check both directories:

```python
def get_css(self, template_name: str = "modern") -> str:
    css_parts: list[str] = []

    # Build inheritance chain (unchanged logic)
    chain: list[str] = []
    current = template_name
    while current in self._css_inheritance:
        parent = self._css_inheritance[current]
        chain.append(parent)
        current = parent

    # Load CSS from custom OR builtin for each ancestor
    for ancestor in reversed(chain):
        css_path = self._find_css(ancestor)  # New helper method
        if css_path:
            css_parts.append(css_path.read_text())

    # Load template-specific CSS
    css_path = self._find_css(template_name)
    if css_path:
        css_parts.append(css_path.read_text())

    return "\n".join(css_parts)

def _find_css(self, name: str) -> Path | None:
    """Find CSS file in custom or builtin directory."""
    # Custom first
    if self.custom_templates_dir:
        custom_css = self.custom_templates_dir / f"{name}.css"
        if custom_css.exists():
            return custom_css
    # Builtin fallback
    builtin_css = self.builtin_templates_dir / f"{name}.css"
    if builtin_css.exists():
        return builtin_css
    return None
```

### list_templates() Update

```python
def list_templates(self) -> list[str]:
    """List available template names from all directories."""
    templates: set[str] = set()

    # Add custom templates first
    if self.custom_templates_dir and self.custom_templates_dir.exists():
        for path in self.custom_templates_dir.glob("*.html"):
            if not path.name.startswith("_"):
                templates.add(path.stem)

    # Add builtin templates
    if self.builtin_templates_dir.exists():
        for path in self.builtin_templates_dir.glob("*.html"):
            if not path.name.startswith("_"):
                templates.add(path.stem)

    return sorted(templates)
```

### Error Message Improvement

When template not found, show available templates:

```python
def render(self, resume: ResumeData, template_name: str = "modern", ...) -> str:
    try:
        template = self.env.get_template(f"{template_name}.html")
    except jinja2.TemplateNotFound:
        available = self.list_templates()
        raise RenderError(
            message=f"Template '{template_name}' not found",
            suggestion=f"Available templates: {', '.join(available)}",
        )
```

### Files to Modify

| File | Action | Description |
|------|--------|-------------|
| `src/resume_as_code/models/config.py` | Modify | Add `templates_dir: Path \| None` field |
| `src/resume_as_code/services/template_service.py` | Modify | Multi-directory loader, CSS lookup |
| `src/resume_as_code/commands/build.py` | Modify | Add `--templates-dir` flag, pass to providers |
| `src/resume_as_code/providers/pdf.py` | Modify | Accept and pass templates_dir to TemplateService |
| `schemas/config.schema.json` | Update | Add templates_dir property (auto-generated) |
| `CLAUDE.md` | Update | Document new options |
| `tests/unit/services/test_template_service.py` | Create/Modify | Tests for multi-directory |
| `tests/integration/test_build_templates.py` | Create | Integration tests |

### Template Inheritance Considerations

Jinja2's FileSystemLoader with multiple directories handles inheritance correctly:

```html
{# my-templates/branded.html #}
{% extends "executive.html" %}  {# Finds builtin executive.html automatically #}

{% block header %}
  {# Custom branded header #}
  <img src="company-logo.png" />
  {{ super() }}
{% endblock %}
```

The loader searches directories in order, so `extends "executive.html"` will:
1. First check `my-templates/executive.html`
2. Then check `package/templates/executive.html` (builtin)

This means:
- Custom templates can extend builtin templates
- Custom templates can also override builtin templates entirely
- Partials (like `_base.html`) work across directories

### Project Context Rules to Follow

From `_bmad-output/project-context.md`:

- **Use `|` union syntax** not `Union[]` for types
- **Never use `print()`** — use Rich console from `utils/console.py`
- **Pydantic v2 syntax** — use `field_validator` and `model_validator`
- **Run ruff + mypy before completing any task**
- **Error hierarchy** — use `RenderError` from `models/errors.py`
- **Keep commands thin, services thick**

### Architecture Compliance

From `_bmad-output/planning-artifacts/architecture.md`:

- TemplateService is in `services/` layer — owns business logic
- Commands delegate to services — no template logic in build.py
- Providers use TemplateService — PDFProvider should pass templates_dir through

### Testing Strategy

1. **Unit tests for TemplateService:**
   - Custom directory only
   - Builtin directory only
   - Both directories (custom takes precedence)
   - Template inheritance across directories
   - CSS loading from custom/builtin

2. **Integration tests:**
   - `--templates-dir` CLI flag works
   - Config `templates_dir` works
   - CLI overrides config
   - Error message shows available templates

### Example Usage After Implementation

```yaml
# .resume.yaml
templates_dir: ./my-templates
```

```bash
# Use config templates_dir
resume build --jd job.txt --template branded

# Override with CLI flag
resume build --jd job.txt --templates-dir ./corporate-templates --template annual-review

# List available templates (shows both custom and builtin)
# (Future: could add `resume templates list` command)
```

### References

- [Source: _bmad-output/planning-artifacts/epics/epic-11-technical-debt-platform-enhancements.md#Story-11.3]
- [Source: _bmad-output/planning-artifacts/architecture.md#3.4-Provider-Architecture]
- [Source: _bmad-output/project-context.md]
- Template service: `src/resume_as_code/services/template_service.py`
- Build command: `src/resume_as_code/commands/build.py`
- Config model: `src/resume_as_code/models/config.py`
- Jinja2 FileSystemLoader: https://jinja.palletsprojects.com/en/3.1.x/api/#jinja2.FileSystemLoader

## Dev Agent Record

### Agent Model Used

{{agent_model_name_version}}

### Debug Log References

### Completion Notes List

### Change Log
- 2026-01-18: Story created with comprehensive implementation context

### File List
- `src/resume_as_code/models/config.py` - Add templates_dir field
- `src/resume_as_code/services/template_service.py` - Multi-directory loader support
- `src/resume_as_code/commands/build.py` - Add --templates-dir CLI flag
- `src/resume_as_code/providers/pdf.py` - Pass templates_dir to TemplateService
- `CLAUDE.md` - Document new options
- `tests/unit/services/test_template_service.py` - Unit tests
- `tests/integration/test_build_templates.py` - Integration tests
