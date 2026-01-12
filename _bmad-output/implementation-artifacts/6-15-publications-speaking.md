# Story 6.15: Publications & Speaking Engagements

Status: ready-for-dev

## Story

As a **thought leader with public visibility**,
I want **a Publications & Speaking section on my resume**,
So that **my industry influence and expertise are visible to hiring committees**.

> **Research Note (2026-01-12):** Publications and conference speaking demonstrate thought leadership and industry visibility, particularly valuable for executive candidates where public presence matters.

## Acceptance Criteria

1. **Given** I configure publications in `.resume.yaml`
   **When** the config is:
   ```yaml
   publications:
     - title: "Securing Industrial Control Systems at Scale"
       type: "conference"
       venue: "DEF CON 30"
       date: "2022-08"
       url: "https://example.com/talk"
     - title: "Zero Trust Architecture Implementation Guide"
       type: "whitepaper"
       venue: "Company Technical Blog"
       date: "2023-03"
       url: "https://example.com/whitepaper"
     - title: "Cloud Security Best Practices"
       type: "article"
       venue: "IEEE Security & Privacy"
       date: "2021-06"
   ```
   **Then** the config loads and validates successfully
   **And** publications are available for template rendering

2. **Given** publications exist in config
   **When** the executive or CTO template renders
   **Then** a "Publications & Speaking" section appears
   **And** entries are grouped by type or displayed chronologically
   **And** URLs are clickable in PDF output

3. **Given** a publication has `type: "conference"`
   **When** it renders
   **Then** it displays as speaking engagement: "DEF CON 30 (2022) - Securing Industrial Control Systems"

4. **Given** a publication has `type: "article"` or `"whitepaper"`
   **When** it renders
   **Then** it displays as written work: "Zero Trust Architecture Implementation Guide, Company Technical Blog (2023)"

5. **Given** no publications exist in config
   **When** the resume is generated
   **Then** no Publications section appears (graceful absence)

6. **Given** I run `resume new publication`
   **When** prompted
   **Then** I'm asked for:
     1. Title (required)
     2. Type: conference, article, whitepaper, book, podcast, webinar (select)
     3. Venue/publisher (required)
     4. Date (YYYY-MM)
     5. URL (optional)

7. **Given** I run non-interactively (LLM mode):
   ```bash
   resume new publication \
     --title "Securing Industrial Control Systems" \
     --type conference \
     --venue "DEF CON 30" \
     --date 2022-08 \
     --url "https://example.com/talk"
   ```
   **When** the command executes
   **Then** the publication is added without prompts

8. **Given** I run `resume list publications`
   **When** publications exist
   **Then** a formatted table shows all entries sorted by date

## Tasks / Subtasks

- [ ] Task 1: Create Publication model (AC: #1)
  - [ ] 1.1: Create `models/publication.py` with Publication Pydantic model
  - [ ] 1.2: Add fields: title, type, venue, date, url, display
  - [ ] 1.3: Add type enum: conference, article, whitepaper, book, podcast, webinar
  - [ ] 1.4: Add date validation (YYYY-MM format)
  - [ ] 1.5: Add URL validation with HttpUrl type

- [ ] Task 2: Update config model (AC: #1)
  - [ ] 2.1: Add `publications: list[Publication] = Field(default_factory=list)` to `ResumeConfig`
  - [ ] 2.2: Add Publication import to config module

- [ ] Task 3: Update ResumeData model (AC: #2, #3, #4)
  - [ ] 3.1: Add `publications: list[Publication]` to `ResumeData`
  - [ ] 3.2: Update `ResumeData.from_config()` to load publications
  - [ ] 3.3: Sort publications by date descending
  - [ ] 3.4: Pass publications to template context

- [ ] Task 4: Update templates (AC: #2, #3, #4, #5)
  - [ ] 4.1: Add publications section to `templates/executive.html`
  - [ ] 4.2: Position section at end (optional section)
  - [ ] 4.3: Format conference vs written work differently
  - [ ] 4.4: Make URLs clickable in PDF
  - [ ] 4.5: Add CSS styling for publications in `templates/executive.css`
  - [ ] 4.6: Ensure graceful absence when no publications configured

- [ ] Task 5: Create publication management commands (AC: #6, #7, #8)
  - [ ] 5.1: Add `resume new publication` command
  - [ ] 5.2: Support interactive prompts for all fields
  - [ ] 5.3: Support flags for non-interactive mode
  - [ ] 5.4: Add `resume list publications` command with table output
  - [ ] 5.5: Add `resume remove publication` command

- [ ] Task 6: Testing
  - [ ] 6.1: Add unit tests for Publication model
  - [ ] 6.2: Add tests for config loading with publications
  - [ ] 6.3: Add tests for template rendering with/without publications
  - [ ] 6.4: Add tests for publication management commands
  - [ ] 6.5: Visual inspection of generated PDF

- [ ] Task 7: Code quality verification
  - [ ] 7.1: Run `ruff check src tests --fix`
  - [ ] 7.2: Run `mypy src --strict` with zero errors
  - [ ] 7.3: Run `pytest` - all tests pass

## Dev Notes

### Architecture Compliance

This story implements FR51 (Publications & Speaking) based on CTO resume research (2026-01-12). Publications and speaking engagements demonstrate thought leadership and industry visibility.

**Critical Rules from project-context.md:**
- Use `|` union syntax for optional fields (Python 3.10+)
- Use `HttpUrl` type for URL fields with proper validation
- Templates render gracefully when optional sections missing

### Publication Model Design

```python
# src/resume_as_code/models/publication.py

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, HttpUrl, field_validator


PublicationType = Literal["conference", "article", "whitepaper", "book", "podcast", "webinar"]


class Publication(BaseModel):
    """Publication or speaking engagement record."""

    title: str
    type: PublicationType
    venue: str  # Conference name, publisher, blog name
    date: str  # YYYY-MM format
    url: HttpUrl | None = None
    display: bool = True

    @field_validator("date", mode="before")
    @classmethod
    def validate_date_format(cls, v: str) -> str:
        """Validate YYYY-MM date format."""
        import re
        if not re.match(r"^\d{4}-\d{2}$", str(v)):
            raise ValueError("Date must be in YYYY-MM format")
        return v

    @property
    def year(self) -> str:
        """Extract year from date."""
        return self.date[:4]

    @property
    def is_speaking(self) -> bool:
        """Check if this is a speaking engagement."""
        return self.type in ("conference", "podcast", "webinar")

    def format_display(self) -> str:
        """Format for resume display."""
        if self.is_speaking:
            return f"{self.venue} ({self.year}) - {self.title}"
        return f"{self.title}, {self.venue} ({self.year})"
```

### Publications Template Structure

```html
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
```

### Publications CSS Styling

```css
.publications {
  margin-top: 1em;
  page-break-inside: avoid;
}

.publications h2 {
  font-size: 12pt;
  color: #2c3e50;
  border-bottom: 1px solid #ddd;
  padding-bottom: 0.25em;
  margin-bottom: 0.75em;
  text-transform: uppercase;
}

.pub-entry {
  margin-bottom: 0.5em;
  font-size: 10.5pt;
}

.pub-entry a {
  color: #2c3e50;
  text-decoration: none;
}

.pub-entry a:hover {
  text-decoration: underline;
}
```

### Dependencies

This story REQUIRES:
- Story 6.1 (Profile Configuration) - Config system [DONE]
- Story 6.2 (Certifications) - Similar config pattern [DONE]

This story ENABLES:
- Story 6.17 (CTO Template) - Uses publications section

### Files to Create/Modify

**New Files:**
- `src/resume_as_code/models/publication.py` - Publication model
- `src/resume_as_code/commands/publications.py` - Publication commands
- `tests/unit/test_publications.py` - Unit tests

**Modified Files:**
- `src/resume_as_code/models/config.py` - Add publications field
- `src/resume_as_code/models/resume.py` - Add publications to ResumeData
- `src/resume_as_code/commands/build.py` - Load publications from config
- `src/resume_as_code/templates/executive.html` - Add publications section
- `src/resume_as_code/templates/executive.css` - Add publications styling

### Verification Commands

```bash
# After implementation, verify:
uv run ruff check src tests --fix
uv run mypy src --strict
uv run pytest tests/unit/test_publications.py -v

# Manual verification:
uv run resume new publication --title "My Talk" --type conference --venue "DEF CON" --date 2022-08
uv run resume list publications
uv run resume build --jd examples/job-description.txt --template executive
# Open dist/resume.pdf and verify Publications section appears
```

### References

- [Source: epics.md#Story 6.15](_bmad-output/planning-artifacts/epics.md)
- [CTO Resume Research](_bmad-output/planning-artifacts/research/cto-resume-layout-research-2026-01-12.md)

## Dev Agent Record

### Agent Model Used

{{agent_model_name_version}}

### Debug Log References

### Completion Notes List

### File List

