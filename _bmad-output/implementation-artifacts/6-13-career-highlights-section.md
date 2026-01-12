# Story 6.13: Career Highlights Section (CTO/Hybrid Format)

Status: ready-for-dev

## Story

As a **senior executive applying for CTO or board-level positions**,
I want **a Career Highlights section prominently displaying my top achievements**,
So that **recruiters immediately see my business impact before reading detailed experience**.

> **Research Note (2026-01-12):** CTO resume research confirms hybrid format with career highlights achieves higher callback rates for board-level positions. This section appears between Executive Summary and Professional Experience, containing 3-4 bullet points focused on P&L impact, team scale, and strategic outcomes.

## Acceptance Criteria

1. **Given** I configure career highlights in `.resume.yaml`
   **When** the config is:
   ```yaml
   career_highlights:
     - "$50M revenue growth through digital transformation"
     - "Built engineering org from 12 to 150+ engineers (94% retention)"
     - "Led M&A tech due diligence for 5 acquisitions ($200M total value)"
     - "Achieved SOC 2 Type II and ISO 27001 certification"
   ```
   **Then** the config loads and validates successfully
   **And** career highlights are available for template rendering

2. **Given** career highlights exist in config
   **When** the executive or CTO template renders
   **Then** a "Career Highlights" section appears after Executive Summary
   **And** before Professional Experience section
   **And** bullets are rendered prominently with strategic styling

3. **Given** career highlights are rendered
   **When** I inspect the PDF
   **Then** each highlight is a single impactful line
   **And** metrics/numbers are visually emphasized
   **And** max 4 highlights are shown (research-validated optimal)

4. **Given** no career highlights exist in config
   **When** the resume is generated
   **Then** no Career Highlights section appears (graceful absence)
   **And** Executive Summary flows directly into Professional Experience

5. **Given** I run `resume new highlight`
   **When** prompted
   **Then** I'm asked for a single-line achievement with metrics
   **And** the highlight is added to `career_highlights` array in config

6. **Given** I run non-interactively (LLM mode):
   ```bash
   resume new highlight --text "$50M revenue growth through digital transformation"
   ```
   **When** the command executes
   **Then** the highlight is added without prompts

## Tasks / Subtasks

- [ ] Task 1: Add career_highlights to config model (AC: #1)
  - [ ] 1.1: Add `career_highlights: list[str] = Field(default_factory=list)` to `ResumeConfig`
  - [ ] 1.2: Add validation for max 4 highlights (warn if more)
  - [ ] 1.3: Add validation for max 150 characters per highlight

- [ ] Task 2: Update ResumeData model (AC: #1, #2)
  - [ ] 2.1: Add `career_highlights: list[str]` to `ResumeData`
  - [ ] 2.2: Update `ResumeData.from_config()` to load career highlights
  - [ ] 2.3: Pass career_highlights to template context

- [ ] Task 3: Update executive template (AC: #2, #3)
  - [ ] 3.1: Add career highlights section to `templates/executive.html`
  - [ ] 3.2: Position section after Executive Summary, before Experience
  - [ ] 3.3: Add CSS styling for prominent display in `templates/executive.css`
  - [ ] 3.4: Ensure graceful absence when no highlights configured

- [ ] Task 4: Create highlight management command (AC: #5, #6)
  - [ ] 4.1: Add `resume new highlight` command
  - [ ] 4.2: Support interactive prompt for highlight text
  - [ ] 4.3: Support `--text` flag for non-interactive mode
  - [ ] 4.4: Add `resume list highlights` command
  - [ ] 4.5: Add `resume remove highlight` command

- [ ] Task 5: Testing
  - [ ] 5.1: Add unit tests for config loading with career highlights
  - [ ] 5.2: Add tests for template rendering with/without highlights
  - [ ] 5.3: Add tests for highlight management commands
  - [ ] 5.4: Visual inspection of generated PDF

- [ ] Task 6: Code quality verification
  - [ ] 6.1: Run `ruff check src tests --fix`
  - [ ] 6.2: Run `mypy src --strict` with zero errors
  - [ ] 6.3: Run `pytest` - all tests pass

## Dev Notes

### Architecture Compliance

This story implements FR49 (Career Highlights) based on CTO resume research (2026-01-12). Career Highlights is a key differentiator for the hybrid resume format used by CTOs targeting board-level positions.

**Critical Rules from project-context.md:**
- Use `|` union syntax for optional fields (Python 3.10+)
- Templates render gracefully when optional sections missing
- Use Jinja2 conditionals for all optional content

### Project Structure Notes

- **Alignment:** Follows existing config extension pattern from Story 6.1 (ProfileConfig)
- **Paths:** New field in `models/config.py`, template updates in `templates/executive.html`
- **Modules:** Config model extension, no new modules required
- **Naming:** `career_highlights` follows snake_case convention per Architecture
- **Conflicts:** None detected - extends existing patterns without breaking changes

### Career Highlights Template Structure

```html
{% if resume.career_highlights %}
<section class="career-highlights">
  <h2>Career Highlights</h2>
  <ul class="highlights-list">
    {% for highlight in resume.career_highlights %}
    <li>{{ highlight }}</li>
    {% endfor %}
  </ul>
</section>
{% endif %}
```

### Career Highlights CSS Styling

```css
.career-highlights {
  margin-bottom: 1.5em;
  page-break-inside: avoid;
}

.career-highlights h2 {
  font-size: 12pt;
  color: #2c3e50;
  border-bottom: 1px solid #ddd;
  padding-bottom: 0.25em;
  margin-bottom: 0.75em;
  text-transform: uppercase;
}

.highlights-list {
  list-style: disc;
  padding-left: 1.25em;
  margin: 0;
}

.highlights-list li {
  font-size: 11pt;
  margin-bottom: 0.5em;
  line-height: 1.4;
}
```

### Dependencies

This story REQUIRES:
- Story 6.1 (Profile Configuration) - Config system [DONE]

This story ENABLES:
- Story 6.17 (CTO Template) - Uses career highlights as prominent section

### Files to Create/Modify

**Modified Files:**
- `src/resume_as_code/models/config.py` - Add career_highlights field
- `src/resume_as_code/models/resume.py` - Add career_highlights to ResumeData
- `src/resume_as_code/commands/build.py` - Load career highlights from config
- `src/resume_as_code/templates/executive.html` - Add career highlights section
- `src/resume_as_code/templates/executive.css` - Add career highlights styling

**New Files:**
- `src/resume_as_code/commands/highlights.py` - Highlight management commands
- `tests/unit/test_career_highlights.py` - Unit tests

### Verification Commands

```bash
# After implementation, verify:
uv run ruff check src tests --fix
uv run mypy src --strict
uv run pytest tests/unit/test_career_highlights.py -v

# Manual verification:
uv run resume new highlight --text "$50M revenue growth"
uv run resume list highlights
uv run resume build --jd examples/job-description.txt --template executive
# Open dist/resume.pdf and verify Career Highlights section appears
```

### References

- [Source: epics.md#Story 6.13](_bmad-output/planning-artifacts/epics.md)
- [CTO Resume Research](_bmad-output/planning-artifacts/research/cto-resume-layout-research-2026-01-12.md)
- [CTO Wireframe](_bmad-output/excalidraw-diagrams/cto-resume-wireframe.excalidraw)

## Dev Agent Record

### Agent Model Used

{{agent_model_name_version}}

### Debug Log References

### Completion Notes List

### File List

