# Epic 6: Executive Resume Template & Profile System

**Goal:** Generate professional executive-level resumes with complete contact info, certifications, curated skills, and industry-standard formatting

**User Outcome:** Users can generate resumes that meet executive resume standards with proper header, summary, certifications, and curated skills sections

**New FRs Addressed:**
- FR39: User can configure profile information (name, contact, summary) in config
- FR40: User can store certifications with issuer, date, and credential ID
- FR41: System displays curated, deduplicated skills (max 15, prioritized by JD relevance)
- FR42: System generates executive-format resume with all standard sections
- FR43: Templates render certifications section when credentials exist

**Gap Analysis (2026-01-12):**
This epic addresses critical gaps identified during e2e testing where generated resumes:
- Showed "Your Name" placeholder instead of actual contact info
- Had no executive summary section
- Lacked certifications section entirely
- Dumped 50+ skills without deduplication or curation
- Missing education section
- No company/employer context for work units

---

## Story 6.1: Profile Configuration & Contact Info Loading

As a **user**,
I want **to store my profile information in configuration**,
So that **my resumes include accurate contact details without manual editing**.

**Acceptance Criteria:**

**Given** I add profile fields to `.resume.yaml`
**When** the config is:
```yaml
profile:
  name: "Joshua Magady"
  email: "joshua@example.com"
  phone: "555-123-4567"
  location: "Austin, TX"
  linkedin: "https://linkedin.com/in/jmagady"
  github: "https://github.com/jmagady"
  title: "Senior Platform Engineer"
```
**Then** the config loads and validates successfully

**Given** I run `resume build --jd file.txt`
**When** the resume is generated
**Then** the header shows my actual name (not "Your Name")
**And** contact info appears in the header section
**And** LinkedIn URL is displayed (optionally as shortened text)

**Given** profile is missing from config
**When** I run `resume build`
**Then** a warning is displayed: "No profile configured. Run `resume config profile.name 'Your Name'` to set."
**And** placeholders are used (backward compatible)

**Given** I run `resume config profile.name "Jane Doe"`
**When** the command completes
**Then** the value is saved to `.resume.yaml`
**And** subsequent builds use the new name

**Given** I run `resume config --json profile`
**When** the command executes
**Then** profile data is returned as JSON for scripting

**Technical Notes:**
- Extend `models/config.py` with `ProfileConfig` model:
  ```python
  class ProfileConfig(BaseModel):
      name: str
      email: str | None = None
      phone: str | None = None
      location: str | None = None
      linkedin: HttpUrl | None = None
      github: HttpUrl | None = None
      website: HttpUrl | None = None
      title: str | None = None  # Professional title/headline
      summary: str | None = None  # Executive summary template
  ```
- Update `commands/build.py` `_load_contact_info()` to read from config instead of returning hardcoded placeholder
- Add profile fields to `ResumeConfig` class
- Support nested config access: `resume config profile.email`

---

## Story 6.2: Certifications Model & Storage

As a **user**,
I want **to store my professional certifications in configuration**,
So that **they appear on my resume to meet job requirements**.

**Acceptance Criteria:**

**Given** I add certifications to `.resume.yaml`
**When** the config is:
```yaml
certifications:
  - name: "AWS Solutions Architect - Professional"
    issuer: "Amazon Web Services"
    date: "2024-06"
    credential_id: "ABC123XYZ"
    url: "https://aws.amazon.com/verification/ABC123XYZ"
  - name: "CISSP"
    issuer: "ISC²"
    date: "2023-01"
    expires: "2026-01"
```
**Then** the config loads and validates successfully
**And** certifications are available for template rendering

**Given** certifications exist in config
**When** I run `resume build --jd file.txt`
**Then** a "Certifications" section appears in the resume
**And** each certification shows name, issuer, and date

**Given** a certification has an expiration date
**When** it is rendered
**Then** the expiration is shown: "CISSP (ISC², 2023 - expires 2026)"

**Given** a certification has expired
**When** it is rendered
**Then** it is marked or optionally excluded based on config

**Given** no certifications exist in config
**When** the resume is generated
**Then** no certifications section appears (graceful absence)

**Given** I run `resume config certifications --list`
**When** the command executes
**Then** all certifications are displayed in a table

**Technical Notes:**
- Create `models/certification.py` with:
  ```python
  class Certification(BaseModel):
      name: str
      issuer: str | None = None
      date: str | None = None  # YYYY-MM format
      expires: str | None = None
      credential_id: str | None = None
      url: HttpUrl | None = None
      display: bool = True  # Allow hiding without deleting
  ```
- Add `certifications: list[Certification]` to `ResumeConfig`
- Update `ResumeData` model to include certifications
- Add `ResumeData.from_config()` method to load certifications

---

## Story 6.3: Skills Curation Service

As a **user**,
I want **my skills section to show relevant, deduplicated skills**,
So that **recruiters see a focused list instead of a skill dump**.

**Acceptance Criteria:**

**Given** work units contain skills: ["AWS", "aws", "Python", "python", "Terraform"]
**When** skills are extracted for the resume
**Then** duplicates are removed (case-insensitive): ["AWS", "Python", "Terraform"]

**Given** skills from work units and tags combined exceed 50 items
**When** skills are curated
**Then** maximum 15 skills appear on the resume
**And** skills matching JD keywords are prioritized

**Given** a JD mentions "Kubernetes" 3 times and "Python" 2 times
**When** skills are curated
**Then** Kubernetes and Python rank higher than skills not in JD
**And** skills are ordered by JD relevance, not alphabetically

**Given** I configure `skills.exclude: ["PHP", "jQuery"]` in config
**When** skills are curated
**Then** excluded skills never appear regardless of work unit content

**Given** I configure `skills.max_display: 12` in config
**When** skills are curated
**Then** only top 12 skills are shown

**Given** skills are curated
**When** I run `resume plan --jd file.txt`
**Then** the skill coverage section shows which skills will be included
**And** shows which were excluded due to dedup or low relevance

**Technical Notes:**
- Create `services/skill_curator.py` with:
  ```python
  class SkillCurator:
      def curate(
          self,
          raw_skills: set[str],
          jd_keywords: set[str] | None = None,
          max_count: int = 15,
          exclude: list[str] | None = None
      ) -> list[str]:
          """
          1. Normalize case (title case for display)
          2. Deduplicate (case-insensitive)
          3. Remove excluded skills
          4. Score by JD keyword match
          5. Sort by score descending
          6. Limit to max_count
          """
  ```
- Add skill curation config to `ResumeConfig`:
  ```python
  class SkillsConfig(BaseModel):
      max_display: int = 15
      exclude: list[str] = Field(default_factory=list)
      prioritize: list[str] = Field(default_factory=list)
  ```
- Update `ResumeData.from_work_units()` to use SkillCurator
- Integrate with JD parser for keyword extraction

---

## Story 6.4: Executive Resume Template

As a **user applying for senior positions**,
I want **an executive-format resume template**,
So that **my resume meets industry standards for leadership roles**.

**Acceptance Criteria:**

**Given** I run `resume build --jd file.txt --template executive`
**When** the resume is generated
**Then** the layout follows executive resume best practices:
  - Name prominently displayed (18-24pt)
  - Professional title below name
  - Contact info on single line with separators
  - Executive summary section (3-5 sentences)
  - Core competencies in categorized groups
  - Experience with scope indicators (budget, team size)
  - Certifications section
  - Education section
  - Skills as curated list (not dump)

**Given** the executive template renders
**When** I inspect the PDF
**Then** it uses professional typography (Calibri or similar)
**And** single-column layout for ATS compatibility
**And** strategic use of bold for section headers
**And** accent color limited to section dividers (navy or dark gray)
**And** 1-inch margins on all sides

**Given** work units have scope data (budget_managed, team_size)
**When** the executive template renders
**Then** scope indicators appear prominently:
  "Led team of 15 engineers | $2M budget | Global scope"

**Given** the resume content exceeds 1 page
**When** the PDF is generated
**Then** page breaks occur between sections (not mid-bullet)
**And** header with name appears on page 2

**Given** I have an executive summary in profile config
**When** the template renders
**Then** the summary appears below contact info
**And** it is 3-5 sentences focused on value proposition

**Given** no executive summary exists in config
**When** the template renders
**Then** a placeholder or auto-generated summary from top work units is shown

**Technical Notes:**
- Create `templates/executive.html` with:
  - Single-column, ATS-safe structure
  - CSS Grid/Flexbox for header layout
  - Print-optimized CSS for WeasyPrint
  - Page break controls via CSS
- Create `templates/executive.css` with:
  - Professional font stack: `'Calibri', 'Segoe UI', Arial, sans-serif`
  - Color scheme: `#1a1a1a` (text), `#2c3e50` (accent), `#ffffff` (bg)
  - Scope indicator styling
  - Certification badge styling
- Structure:
  ```html
  <header class="resume-header">
    <h1>{{ resume.contact.name }}</h1>
    <p class="title">{{ resume.contact.title }}</p>
    <div class="contact-line">
      {{ resume.contact.location }} | {{ resume.contact.email }} | {{ resume.contact.linkedin }}
    </div>
  </header>
  <section class="executive-summary">...</section>
  <section class="core-competencies">...</section>
  <section class="experience">...</section>
  <section class="certifications">...</section>
  <section class="education">...</section>
  <section class="skills">...</section>
  ```
- Template must render gracefully when optional sections are missing

---

## Story 6.5: Template Certifications Section

As a **user with professional certifications**,
I want **certifications to render properly in all templates**,
So that **recruiters see my credentials regardless of template choice**.

**Acceptance Criteria:**

**Given** certifications exist in config
**When** the modern template renders
**Then** a "Certifications" section appears after Education

**Given** certifications exist in config
**When** the executive template renders
**Then** certifications appear prominently (after Experience or Core Competencies)

**Given** certifications exist in config
**When** the ats-safe template renders
**Then** certifications use plain text formatting for maximum parseability

**Given** a certification has all fields populated
**When** it renders
**Then** format is: "AWS Solutions Architect - Professional, Amazon Web Services, June 2024"

**Given** a certification has only name and date
**When** it renders
**Then** format is: "CISSP, 2023"

**Given** certifications render in PDF
**When** I inspect the layout
**Then** certifications are in a clean list or grid format
**And** credential IDs are not shown (too detailed for resume)

**Given** certifications render in DOCX
**When** I open in Word
**Then** certifications use proper Word list formatting
**And** can be edited/removed by user

**Technical Notes:**
- Update `templates/modern.html` to add certifications section:
  ```html
  {% if resume.certifications %}
  <section class="certifications">
    <h2>Certifications</h2>
    <ul class="cert-list">
      {% for cert in resume.certifications %}
      <li>
        <strong>{{ cert.name }}</strong>
        {% if cert.issuer %}, {{ cert.issuer }}{% endif %}
        {% if cert.date %}, {{ cert.date }}{% endif %}
      </li>
      {% endfor %}
    </ul>
  </section>
  {% endif %}
  ```
- Update `templates/executive.html` with styled certifications
- Update `templates/ats-safe.html` with plain certifications
- Update `providers/docx.py` with `_add_certifications_section()` method
- Ensure `ResumeData` passes certifications to template context

---

## Story 6.6: Education Model & Rendering

As a **user**,
I want **to include my education on the resume**,
So that **degree requirements are visibly met**.

**Acceptance Criteria:**

**Given** I add education to `.resume.yaml`
**When** the config is:
```yaml
education:
  - degree: "Bachelor of Science in Computer Science"
    institution: "University of Texas at Austin"
    year: "2012"
    honors: "Magna Cum Laude"
  - degree: "Master of Science in Cybersecurity"
    institution: "Georgia Tech"
    year: "2018"
```
**Then** the config loads and validates successfully

**Given** education exists in config
**When** the resume is generated
**Then** an "Education" section appears
**And** degrees are listed with institution and year

**Given** education has honors/GPA
**When** it renders
**Then** honors appear: "BS Computer Science, UT Austin, 2012 - Magna Cum Laude"

**Given** no education exists in config
**When** the resume is generated
**Then** no Education section appears (graceful absence)

**Given** I'm a senior professional (10+ years experience)
**When** the resume is generated
**Then** Education appears after Experience (industry standard for senior roles)

**Technical Notes:**
- Create `models/education.py`:
  ```python
  class Education(BaseModel):
      degree: str
      institution: str
      year: str | None = None
      honors: str | None = None
      gpa: str | None = None
      display: bool = True
  ```
- Add `education: list[Education]` to `ResumeConfig`
- Update all templates to render education section
- Update `ResumeData` to include education from config

---

## Story 6.7: Positions Data Model & Employment History (Normalized Architecture)

As a **user**,
I want **a separate positions data store that work units reference**,
So that **my resume shows proper chronological employment history with achievements grouped by employer**.

> **Architecture Decision (2026-01-12):** Deep research on resume data modeling confirms that normalized relational models (separate positions entity) are superior to embedded organization fields for: ATS compatibility, career progression tracking, multiple roles at same employer, and skills-based filtering. This follows patterns from JSON Resume, HR-XML, and LinkedIn data models.

**Acceptance Criteria:**

**Given** the project has no positions file
**When** I run `resume new position`
**Then** a `positions.yaml` file is created in the project root
**And** the new position is added to the file

**Given** a `positions.yaml` file exists with:
```yaml
# positions.yaml - Employment History
schema_version: "1.0.0"

positions:
  pos-techcorp-senior:
    employer: "TechCorp Industries"
    title: "Senior Platform Engineer"
    location: "Austin, TX"
    start_date: "2022-01"
    end_date: null  # Current role
    employment_type: "full-time"
    promoted_from: "pos-techcorp-engineer"

  pos-techcorp-engineer:
    employer: "TechCorp Industries"
    title: "Platform Engineer"
    location: "Austin, TX"
    start_date: "2020-06"
    end_date: "2021-12"
    employment_type: "full-time"

  pos-acme-consultant:
    employer: "Acme Consulting"
    title: "Security Consultant"
    location: "Remote"
    start_date: "2018-03"
    end_date: "2020-05"
    employment_type: "contract"
```
**Then** the file loads and validates successfully
**And** positions are available for work unit association

**Given** a work unit YAML file
**When** I add a position reference:
```yaml
id: wu-2024-01-30-ics-assessment
position_id: pos-techcorp-senior  # References position
title: "Conducted ICS security assessment..."
problem: ...
actions: ...
outcome: ...
```
**Then** the work unit validates successfully
**And** the position_id is validated against existing positions

**Given** multiple work units reference the same position
**When** the resume is generated
**Then** work units are grouped under the position
**And** rendered as achievement bullets under the employer/role header

**Given** work units reference positions at the same employer
**When** the resume renders
**Then** format shows career progression:
```
TechCorp Industries                           Austin, TX
Senior Platform Engineer                      2022 - Present
• [achievement from wu referencing pos-techcorp-senior]
• [achievement from wu referencing pos-techcorp-senior]

Platform Engineer                             2020 - 2021
• [achievement from wu referencing pos-techcorp-engineer]
```

**Given** a position has `promoted_from` field
**When** positions are listed or rendered
**Then** promotion chains are visible
**And** can be used to show career progression narratives

**Given** a work unit has no position_id
**When** the resume renders
**Then** it appears as standalone entry (for personal projects, open source, etc.)
**And** a warning is displayed during `resume validate`

**Given** I have work units from multiple employers
**When** the resume renders
**Then** employers are ordered by most recent end date (chronological)
**And** within each employer, roles are ordered by date (showing progression)

**Technical Notes:**
- Create `models/position.py`:
  ```python
  class Position(BaseModel):
      id: str  # Unique identifier like "pos-techcorp-senior"
      employer: str
      title: str
      location: str | None = None
      start_date: str  # YYYY-MM format
      end_date: str | None = None  # null = current
      employment_type: Literal["full-time", "part-time", "contract", "consulting", "freelance"] | None = None
      promoted_from: str | None = None  # ID of previous position (career progression)
      description: str | None = None  # Optional role summary
  ```
- Create `services/position_service.py`:
  ```python
  class PositionService:
      def load_positions(self, path: Path = Path("positions.yaml")) -> dict[str, Position]
      def get_position(self, position_id: str) -> Position | None
      def group_by_employer(self, positions: list[Position]) -> dict[str, list[Position]]
      def get_promotion_chain(self, position_id: str) -> list[Position]
  ```
- Add `position_id: str | None` field to WorkUnit model
- Update `ResumeData.from_work_units()` to:
  1. Load positions from positions.yaml
  2. Group work units by position_id
  3. Group positions by employer
  4. Sort by date for chronological rendering
- Update work-unit.schema.json with optional position_id field
- Update templates to render employer → role → achievements hierarchy
- Create positions.schema.json for validation
- Schema version bump for backward compatibility

---

## Story 6.8: Position Management Commands (Human-Friendly UX)

As a **human user building my resume library**,
I want **interactive commands to manage positions**,
So that **I can easily set up my employment history without manually editing YAML**.

**Acceptance Criteria:**

**Given** I run `resume new position`
**When** prompted
**Then** I'm asked for:
  1. Employer name
  2. Job title
  3. Location (optional)
  4. Start date (YYYY-MM)
  5. End date (YYYY-MM or blank for current)
  6. Employment type (select from list)
  7. Was this a promotion? (y/n → select previous position if yes)

**Given** I complete the position prompts
**When** the position is created
**Then** a unique ID is generated: `pos-{employer-slug}-{title-slug}`
**And** the position is appended to `positions.yaml`
**And** the position ID is displayed for use in work units

**Given** I run `resume list positions`
**When** positions exist
**Then** a formatted table shows:
  | ID | Employer | Title | Dates | Type |
  |----|----------|-------|-------|------|
  | pos-techcorp-senior | TechCorp Industries | Senior Platform Engineer | 2022-Present | full-time |

**Given** I run `resume new work-unit`
**When** prompted for position
**Then** existing positions are listed for selection
**And** I can choose "Create new position..." to inline-create
**And** I can choose "No position (personal project)" to skip

**Given** a work unit's date range falls within a position's date range
**When** I run `resume new work-unit --from-memory`
**Then** the system suggests the matching position
**And** I can accept or override the suggestion

**Given** I run `resume validate`
**When** work units exist without position_id
**Then** a warning suggests: "Work unit '{id}' has no position. Consider adding position_id."
**And** validation still passes (position is optional)

**Given** I run `resume show position pos-techcorp-senior`
**When** the position exists
**Then** full details are displayed including:
  - Position info
  - List of work units referencing this position
  - Promotion chain (if part of one)

**Technical Notes:**
- Extend `commands/new.py` with `new position` subcommand
- Create `commands/positions.py` for `list positions` and `show position`
- Use Rich prompts for interactive input
- Position ID generation: `pos-{slugify(employer)}-{slugify(title)}`
- Integrate position selection into existing `new work-unit` flow
- Date matching logic: work unit overlaps with position if:
  `wu.time_started >= position.start_date AND wu.time_ended <= position.end_date`
- All prompts must support `--non-interactive` fallback for CI/scripting

---

## Story 6.9: Inline Position Creation (LLM-Optimized UX)

As an **AI agent (Claude Code) helping a user build their resume**,
I want **non-interactive flags to create positions and work units in one command**,
So that **I can efficiently build the resume library without interactive prompts**.

**Acceptance Criteria:**

**Given** I run:
```bash
resume new work-unit \
  --position "TechCorp Industries|Senior Engineer|2022-01|" \
  --title "Led ICS security assessment" \
  --archetype incident
```
**When** the position doesn't exist
**Then** a new position is auto-created in positions.yaml
**And** the work unit is created referencing the new position
**And** both IDs are returned in output

**Given** the position "TechCorp Industries + Senior Engineer" already exists
**When** I use the `--position` flag with the same employer/title
**Then** the existing position is reused (no duplicate created)
**And** the work unit references the existing position

**Given** I want to reference an existing position by ID
**When** I run:
```bash
resume new work-unit \
  --position-id pos-techcorp-senior \
  --title "Architected hybrid platform"
```
**Then** the work unit is created referencing that position
**And** an error is shown if the position ID doesn't exist

**Given** I run with JSON output:
```bash
resume --json new work-unit --position "Company|Title|2023-01|2024-01"
```
**When** the command succeeds
**Then** JSON output includes:
```json
{
  "status": "success",
  "data": {
    "work_unit_id": "wu-2024-01-30-ics-assessment",
    "position_id": "pos-company-title",
    "position_created": true,
    "file_path": "work-units/wu-2024-01-30-ics-assessment.yaml"
  }
}
```

**Given** I run `resume new position` non-interactively:
```bash
resume new position \
  --employer "Acme Corp" \
  --title "Security Consultant" \
  --location "Remote" \
  --start-date 2018-03 \
  --end-date 2020-05 \
  --employment-type contract
```
**When** the command executes
**Then** the position is created without prompts
**And** the position ID is returned

**Given** I'm creating a position that was a promotion
**When** I run:
```bash
resume new position \
  --employer "TechCorp" \
  --title "Senior Engineer" \
  --start-date 2022-01 \
  --promoted-from pos-techcorp-engineer
```
**Then** the `promoted_from` field is set
**And** career progression is tracked

**Given** I want to list positions programmatically
**When** I run `resume --json list positions`
**Then** positions are returned as a JSON array
**And** includes all fields for each position

**Technical Notes:**
- `--position` flag format: `"Employer|Title|StartDate|EndDate"` (pipe-separated)
  - EndDate can be empty for current position
  - Parse with: `employer, title, start, end = value.split("|")`
- Position matching logic for dedup:
  ```python
  def find_existing_position(employer: str, title: str) -> Position | None:
      # Normalize: lowercase, strip whitespace
      # Match on employer + title combination
  ```
- All position flags on `new work-unit`:
  - `--position "Employer|Title|Start|End"` - Create/reuse position inline
  - `--position-id <id>` - Reference existing position by ID
  - (no flag) - Interactive mode asks, or null if `--non-interactive`
- All position flags on `new position`:
  - `--employer`, `--title`, `--location`, `--start-date`, `--end-date`
  - `--employment-type`, `--promoted-from`
- JSON mode MUST work for all commands (LLM parsing)

---

## Story 6.10: CLAUDE.md System Documentation Update

As a **user working with Claude Code**,
I want **CLAUDE.md updated with the positions/work-units workflow**,
So that **AI agents understand the data model and can help me build my resume efficiently**.

**Acceptance Criteria:**

**Given** the CLAUDE.md file exists
**When** Story 6.7-6.9 are implemented
**Then** CLAUDE.md is updated to document:
  1. The positions → work units relationship
  2. Commands for managing positions
  3. Inline position creation flags for LLM usage
  4. Complete workflow examples

**Given** an AI agent reads CLAUDE.md
**When** a user asks to add a work experience
**Then** the agent knows to:
  1. Check if position exists in positions.yaml
  2. Create position if needed (using inline flags)
  3. Create work unit with position_id reference
  4. Validate the result

**Given** CLAUDE.md is updated
**When** I inspect the file
**Then** it includes a "Data Model" section explaining:
```markdown
# Data Model

## Positions (positions.yaml)
Employment history with employer, title, dates. Work units reference positions.

## Work Units (work-units/*.yaml)
Individual achievements/accomplishments. Reference a position via `position_id`.

## Relationship
```
Position (1) ← references ← (*) Work Units
```
Work units are grouped under positions for resume rendering.
```

**Given** CLAUDE.md is updated
**When** I inspect the file
**Then** it includes examples for common AI agent tasks:
```markdown
# AI Agent Workflows

## Adding Work Experience (Inline - Preferred for LLM)
```bash