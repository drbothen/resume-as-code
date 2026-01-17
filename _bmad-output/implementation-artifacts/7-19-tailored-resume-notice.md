# Story 7.19: Tailored Resume Notice

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a **job seeker**,
I want **an optional footer notice indicating this resume is tailored for the role**,
So that **recruiters understand relevant details were prioritized and can request my full history**.

## Acceptance Criteria

1. **Given** configuration `tailored_notice: true` in .resume.yaml
   **When** building a resume
   **Then** a footer notice appears on the last page
   **And** the notice reads: "This resume highlights experience most relevant to this role. Full details available upon request."

2. **Given** CLI flag `--tailored-notice`
   **When** building a resume
   **Then** the footer notice is included regardless of config setting

3. **Given** CLI flag `--no-tailored-notice`
   **When** building a resume
   **Then** the footer notice is excluded regardless of config setting

4. **Given** neither config nor CLI flag is set
   **When** building a resume
   **Then** no footer notice is included (opt-in by default)

5. **Given** configuration `tailored_notice_text: "Custom message here"`
   **When** building a resume
   **Then** the custom text is used instead of the default

6. **Given** the footer notice is enabled
   **When** viewing the rendered PDF
   **Then** the notice appears as subtle text at the bottom of the last page
   **And** it uses smaller font (8-9pt) and muted color
   **And** it does not interfere with main resume content

## Tasks / Subtasks

- [x] Task 1: Add configuration fields (AC: #1, #4, #5)
  - [x] 1.1 Add `tailored_notice: bool = False` to `ResumeConfig`
  - [x] 1.2 Add `tailored_notice_text: str | None = None` to `ResumeConfig`
  - [x] 1.3 Define `DEFAULT_TAILORED_NOTICE` constant
  - [x] 1.4 Add unit tests for config validation

- [x] Task 2: Add CLI flags (AC: #2, #3)
  - [x] 2.1 Add `--tailored-notice/--no-tailored-notice` flag to build.py
  - [x] 2.2 CLI flag overrides config when set
  - [x] 2.3 Add unit tests for CLI flag behavior

- [x] Task 3: Pass notice to template context
  - [x] 3.1 Add `tailored_notice_text` field to `ResumeData` model
  - [x] 3.2 Resolve final text (custom or default) in build command
  - [x] 3.3 Add unit tests for template context

- [x] Task 4: Update templates (AC: #6)
  - [x] 4.1 Add conditional footer block to `modern.html`
  - [x] 4.2 Add conditional footer block to `ats-safe.html`
  - [x] 4.3 Add conditional footer block to `executive.html` (inherited by cto.html)
  - [x] 4.4 Add conditional footer block to `executive-classic.html`

- [x] Task 5: Add CSS styling (AC: #6)
  - [x] 5.1 Add `.tailored-notice` class with subtle styling to all CSS files
  - [x] 5.2 Ensure 8.5pt font, muted color (#666/#777), italic
  - [x] 5.3 Consistent styling across modern, ats-safe, executive, executive-classic CSS

- [x] Task 6: Quality checks
  - [x] 6.1 Run `ruff check` - passed
  - [x] 6.2 Run `mypy --strict` - passed (zero errors)
  - [x] 6.3 Run unit tests - all 10 tailored notice tests pass

## Dev Notes

### Current State Analysis

**What exists:**
- `ResumeConfig` in `models/config.py` with various output settings
- `build.py` command with template selection
- Template files in `templates/` directory
- WeasyPrint for PDF generation

**Gap:**
- No tailored notice configuration
- No CLI flag for tailored notice
- No footer section in templates

### Implementation Pattern

**Configuration:**
```python
# models/config.py

DEFAULT_TAILORED_NOTICE = (
    "This resume highlights experience most relevant to this role. "
    "Full details available upon request."
)

class ResumeConfig(BaseModel):
    # ... existing fields ...

    tailored_notice: bool = Field(
        default=False,
        description="Show footer notice that resume is tailored",
    )
    tailored_notice_text: str | None = Field(
        default=None,
        description="Custom tailored notice text (overrides default)",
    )
```

**CLI Integration:**
```python
# commands/build.py

@click.option(
    "--tailored-notice/--no-tailored-notice",
    default=None,
    help="Include/exclude tailored resume footer notice",
)
def build(
    tailored_notice: bool | None,
    # ... other params ...
):
    # CLI flag overrides config
    show_notice = tailored_notice if tailored_notice is not None else config.tailored_notice

    # Resolve notice text
    notice_text = None
    if show_notice:
        notice_text = config.tailored_notice_text or DEFAULT_TAILORED_NOTICE
```

**Template Footer:**
```html
{# Add to base of all templates before </body> #}
{% if tailored_notice_text %}
<footer class="tailored-notice">
    {{ tailored_notice_text }}
</footer>
{% endif %}
```

**CSS Styling:**
```css
.tailored-notice {
    font-size: 8pt;
    color: #666;
    text-align: center;
    font-style: italic;
    margin-top: 2em;
    padding-top: 0.5em;
    border-top: 1px solid #ddd;
}

/* WeasyPrint: Place on last page only */
@page :last {
    @bottom-center {
        content: element(tailored-footer);
    }
}
```

### Dependencies

- **Depends on:** None
- **Blocked by:** None

### Testing Strategy

```python
# tests/unit/test_config.py

def test_tailored_notice_defaults_false():
    """Tailored notice is opt-in."""
    config = ResumeConfig()
    assert config.tailored_notice is False
    assert config.tailored_notice_text is None


def test_tailored_notice_custom_text():
    """Custom notice text can be set."""
    config = ResumeConfig(
        tailored_notice=True,
        tailored_notice_text="Custom message"
    )
    assert config.tailored_notice_text == "Custom message"


# tests/integration/test_build_command.py

def test_build_with_tailored_notice_flag(cli_runner, tmp_path):
    """--tailored-notice adds footer to PDF."""
    result = runner.invoke(cli, ["build", "--tailored-notice", "--jd", "job.txt"])
    assert result.exit_code == 0
    # Verify PDF contains notice text


def test_build_no_tailored_notice_flag(cli_runner, tmp_path):
    """--no-tailored-notice excludes footer even if config enables it."""
    # Config has tailored_notice: true
    result = runner.invoke(cli, ["build", "--no-tailored-notice", "--jd", "job.txt"])
    assert result.exit_code == 0
    # Verify PDF does not contain notice text
```

### Project Context Rules

From `project-context.md`:
- Run `ruff check` and `mypy --strict` before completing
- Use Rich console for CLI output, never `print()`
- Type hints required on all public functions
- Use `|` union syntax (Python 3.10+)

### References

- [Source: src/resume_as_code/models/config.py - ResumeConfig]
- [Source: src/resume_as_code/commands/build.py]
- [Source: src/resume_as_code/templates/modern.html]
- [Epic: epic-7-schema-data-model-refactoring.md - Story 7.19]

## Dev Agent Record

### Agent Model Used

Claude Opus 4.5 (claude-opus-4-5-20251101)

### Debug Log References

N/A - No significant debugging required

### Completion Notes List

1. **Configuration Fields (Task 1)**: Added `tailored_notice: bool` and `tailored_notice_text: str | None` to `ResumeConfig` with proper Field definitions. Added `DEFAULT_TAILORED_NOTICE` constant. 6 unit tests added to `test_config_models.py`.

2. **CLI Flags (Task 2)**: Added `--tailored-notice/--no-tailored-notice` boolean flag to build command. CLI flag overrides config when provided. 4 unit tests added to `test_build_command.py`.

3. **Template Context (Task 3)**: Added `tailored_notice_text: str | None` field to `ResumeData` model rather than template_service.py - this allows templates to access via `resume.tailored_notice_text` which is cleaner.

4. **Templates (Task 4)**: Updated 5 templates with conditional footer block:
   - `modern.html` - standalone
   - `ats-safe.html` - standalone
   - `executive.html` - base template (cto.html and cto-results.html inherit)
   - `executive-classic.html` - standalone

5. **CSS Styling (Task 5)**: Added `.tailored-notice` class to 4 CSS files with consistent styling:
   - 8.5pt font (9pt for ats-safe)
   - Muted color (#666/#777)
   - Italic text
   - Top border separator
   - Centered alignment

6. **Quality Checks (Task 6)**: All linting and type checks pass. All 10 tailored notice tests pass.

### File List

**Modified:**
- `src/resume_as_code/models/config.py` - Added DEFAULT_TAILORED_NOTICE constant and config fields
- `src/resume_as_code/models/resume.py` - Added tailored_notice_text field to ResumeData
- `src/resume_as_code/commands/build.py` - Added CLI flag and resolution logic
- `src/resume_as_code/templates/modern.html` - Added conditional footer
- `src/resume_as_code/templates/ats-safe.html` - Added conditional footer
- `src/resume_as_code/templates/executive.html` - Added conditional footer
- `src/resume_as_code/templates/executive-classic.html` - Added conditional footer
- `src/resume_as_code/templates/modern.css` - Added .tailored-notice styles
- `src/resume_as_code/templates/ats-safe.css` - Added .tailored-notice styles
- `src/resume_as_code/templates/executive.css` - Added .tailored-notice styles
- `src/resume_as_code/templates/executive-classic.css` - Added .tailored-notice styles
- `tests/unit/test_config_models.py` - Added TestResumeConfigTailoredNotice class (6 tests)
- `tests/unit/test_build_command.py` - Added TestTailoredNoticeFlag class (4 tests)
