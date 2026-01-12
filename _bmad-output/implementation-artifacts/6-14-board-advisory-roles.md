# Story 6.14: Board & Advisory Roles Section

Status: ready-for-dev

## Story

As a **CTO or executive with board experience**,
I want **a Board & Advisory Roles section on my resume**,
So that **my governance experience and strategic advisory work is visible to recruiters**.

> **Research Note (2026-01-12):** Board presentation experience and advisory roles signal executive maturity to hiring committees. This section is critical for CTO candidates targeting public companies or board-level enterprise positions.

## Acceptance Criteria

1. **Given** I configure board roles in `.resume.yaml`
   **When** the config is:
   ```yaml
   board_roles:
     - organization: "Tech Nonprofit Foundation"
       role: "Board Advisor"
       type: "advisory"
       start_date: "2023-01"
       end_date: null
       focus: "Technology strategy and digital transformation"
     - organization: "Startup Accelerator"
       role: "Technical Advisory Board Member"
       type: "advisory"
       start_date: "2021-06"
       end_date: "2023-12"
       focus: "Technical due diligence for investments"
   ```
   **Then** the config loads and validates successfully
   **And** board roles are available for template rendering

2. **Given** board roles exist in config
   **When** the executive or CTO template renders
   **Then** a "Board & Advisory Roles" section appears
   **And** roles show: organization, role title, dates, and focus area
   **And** current roles display "Present" for end date

3. **Given** a board role has `type: "director"`
   **When** it renders
   **Then** it is distinguished from advisory roles (e.g., "Director" vs "Advisor")
   **And** director roles appear first (higher governance level)

4. **Given** no board roles exist in config
   **When** the resume is generated
   **Then** no Board & Advisory section appears (graceful absence)

5. **Given** I run `resume new board-role`
   **When** prompted
   **Then** I'm asked for:
     1. Organization name (required)
     2. Role title (required)
     3. Type: director, advisory, committee (select)
     4. Start date (YYYY-MM)
     5. End date (YYYY-MM or blank for current)
     6. Focus area (optional description)

6. **Given** I run non-interactively (LLM mode):
   ```bash
   resume new board-role \
     --organization "Tech Nonprofit" \
     --role "Board Advisor" \
     --type advisory \
     --start-date 2023-01 \
     --focus "Technology strategy"
   ```
   **When** the command executes
   **Then** the board role is added without prompts

7. **Given** I run `resume list board-roles`
   **When** board roles exist
   **Then** a formatted table shows all roles with status (Active/Past)

## Tasks / Subtasks

- [ ] Task 1: Create BoardRole model (AC: #1)
  - [ ] 1.1: Create `models/board_role.py` with BoardRole Pydantic model
  - [ ] 1.2: Add fields: organization, role, type, start_date, end_date, focus, display
  - [ ] 1.3: Add type enum: director, advisory, committee
  - [ ] 1.4: Add date validation (YYYY-MM format)

- [ ] Task 2: Update config model (AC: #1)
  - [ ] 2.1: Add `board_roles: list[BoardRole] = Field(default_factory=list)` to `ResumeConfig`
  - [ ] 2.2: Add BoardRole import to config module

- [ ] Task 3: Update ResumeData model (AC: #2, #3)
  - [ ] 3.1: Add `board_roles: list[BoardRole]` to `ResumeData`
  - [ ] 3.2: Update `ResumeData.from_config()` to load board roles
  - [ ] 3.3: Sort board roles: directors first, then by start_date descending
  - [ ] 3.4: Pass board_roles to template context

- [ ] Task 4: Update templates (AC: #2, #3, #4)
  - [ ] 4.1: Add board roles section to `templates/executive.html`
  - [ ] 4.2: Position section after Certifications, before Education
  - [ ] 4.3: Add CSS styling for board roles in `templates/executive.css`
  - [ ] 4.4: Ensure graceful absence when no roles configured

- [ ] Task 5: Create board role management commands (AC: #5, #6, #7)
  - [ ] 5.1: Add `resume new board-role` command
  - [ ] 5.2: Support interactive prompts for all fields
  - [ ] 5.3: Support flags for non-interactive mode
  - [ ] 5.4: Add `resume list board-roles` command with table output
  - [ ] 5.5: Add `resume remove board-role` command

- [ ] Task 6: Testing
  - [ ] 6.1: Add unit tests for BoardRole model
  - [ ] 6.2: Add tests for config loading with board roles
  - [ ] 6.3: Add tests for template rendering with/without board roles
  - [ ] 6.4: Add tests for board role management commands
  - [ ] 6.5: Visual inspection of generated PDF

- [ ] Task 7: Code quality verification
  - [ ] 7.1: Run `ruff check src tests --fix`
  - [ ] 7.2: Run `mypy src --strict` with zero errors
  - [ ] 7.3: Run `pytest` - all tests pass

## Dev Notes

### Architecture Compliance

This story implements FR50 (Board & Advisory Roles) based on CTO resume research (2026-01-12). Board experience signals executive maturity and governance capability.

**Critical Rules from project-context.md:**
- Use `|` union syntax for optional fields (Python 3.10+)
- Templates render gracefully when optional sections missing
- Services do the heavy lifting, commands orchestrate

### BoardRole Model Design

```python
# src/resume_as_code/models/board_role.py

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, field_validator


BoardRoleType = Literal["director", "advisory", "committee"]


class BoardRole(BaseModel):
    """Board or advisory role record."""

    organization: str
    role: str
    type: BoardRoleType = "advisory"
    start_date: str  # YYYY-MM format
    end_date: str | None = None  # None = current
    focus: str | None = None
    display: bool = True

    @field_validator("start_date", "end_date", mode="before")
    @classmethod
    def validate_date_format(cls, v: str | None) -> str | None:
        """Validate YYYY-MM date format."""
        if v is None:
            return None
        import re
        if not re.match(r"^\d{4}-\d{2}$", str(v)):
            raise ValueError("Date must be in YYYY-MM format")
        return v

    @property
    def is_current(self) -> bool:
        """Check if this is a current role."""
        return self.end_date is None

    def format_date_range(self) -> str:
        """Format date range for display."""
        start_year = self.start_date[:4]
        if self.end_date:
            end_year = self.end_date[:4]
            return f"{start_year} - {end_year}"
        return f"{start_year} - Present"
```

### Board Roles Template Structure

```html
{% if resume.board_roles %}
<section class="board-roles">
  <h2>Board & Advisory Roles</h2>
  {% for role in resume.board_roles %}
  <div class="board-entry">
    <div class="board-header">
      <strong>{{ role.organization }}</strong>
      <span class="dates">{{ role.format_date_range() }}</span>
    </div>
    <p class="role-title">{{ role.role }}</p>
    {% if role.focus %}
    <p class="focus">{{ role.focus }}</p>
    {% endif %}
  </div>
  {% endfor %}
</section>
{% endif %}
```

### Dependencies

This story REQUIRES:
- Story 6.1 (Profile Configuration) - Config system [DONE]
- Story 6.2 (Certifications) - Similar config pattern [DONE]

This story ENABLES:
- Story 6.17 (CTO Template) - Uses board roles section

### Files to Create/Modify

**New Files:**
- `src/resume_as_code/models/board_role.py` - BoardRole model
- `src/resume_as_code/commands/board_roles.py` - Board role commands
- `tests/unit/test_board_roles.py` - Unit tests

**Modified Files:**
- `src/resume_as_code/models/config.py` - Add board_roles field
- `src/resume_as_code/models/resume.py` - Add board_roles to ResumeData
- `src/resume_as_code/commands/build.py` - Load board roles from config
- `src/resume_as_code/templates/executive.html` - Add board roles section
- `src/resume_as_code/templates/executive.css` - Add board roles styling

### Verification Commands

```bash
# After implementation, verify:
uv run ruff check src tests --fix
uv run mypy src --strict
uv run pytest tests/unit/test_board_roles.py -v

# Manual verification:
uv run resume new board-role --organization "Tech Nonprofit" --role "Advisor" --type advisory --start-date 2023-01
uv run resume list board-roles
uv run resume build --jd examples/job-description.txt --template executive
# Open dist/resume.pdf and verify Board & Advisory Roles section appears
```

### References

- [Source: epics.md#Story 6.14](_bmad-output/planning-artifacts/epics.md)
- [CTO Resume Research](_bmad-output/planning-artifacts/research/cto-resume-layout-research-2026-01-12.md)
- [CTO Wireframe](_bmad-output/excalidraw-diagrams/cto-resume-wireframe.excalidraw)

## Dev Agent Record

### Agent Model Used

{{agent_model_name_version}}

### Debug Log References

### Completion Notes List

### File List

