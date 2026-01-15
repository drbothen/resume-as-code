# FR Coverage Map Update

| FR | Epic | Description |
|----|------|-------------|
| FR39 | Epic 6 | Profile configuration |
| FR40 | Epic 6 | Certifications storage |
| FR41 | Epic 6 | Skills curation |
| FR42 | Epic 6 | Executive template |
| FR43 | Epic 6 | Certifications rendering |
| FR44 | Epic 6 | Positions data model (normalized) |
| FR45 | Epic 6 | Position management commands |
| FR46 | Epic 6 | Inline position creation (LLM UX) |
| FR47 | Epic 6 | Certification management commands |
| FR48 | Epic 6 | Education management commands |
| FR49 | Epic 6 | Career Highlights section (CTO/hybrid format) |
| FR50 | Epic 6 | Board & Advisory Roles section |
| FR51 | Epic 6 | Publications & Speaking section |
| FR52 | Epic 6 | Enhanced scope indicators (P&L, revenue, geography) |
| FR53 | Epic 6 | CTO resume template variant |

---

## Story 6.13: Career Highlights Section (CTO/Hybrid Format)

As a **senior executive applying for CTO or board-level positions**,
I want **a Career Highlights section prominently displaying my top achievements**,
So that **recruiters immediately see my business impact before reading detailed experience**.

> **Research Note (2026-01-12):** CTO resume research confirms hybrid format with career highlights achieves higher callback rates for board-level positions. This section appears between Executive Summary and Professional Experience, containing 3-4 bullet points focused on P&L impact, team scale, and strategic outcomes.

**Acceptance Criteria:**

**Given** I configure career highlights in `.resume.yaml`
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

**Given** career highlights exist in config
**When** the executive or CTO template renders
**Then** a "Career Highlights" section appears after Executive Summary
**And** before Professional Experience section
**And** bullets are rendered prominently with strategic styling

**Given** career highlights are rendered
**When** I inspect the PDF
**Then** each highlight is a single impactful line
**And** metrics/numbers are visually emphasized
**And** max 4 highlights are shown (research-validated optimal)

**Given** no career highlights exist in config
**When** the resume is generated
**Then** no Career Highlights section appears (graceful absence)
**And** Executive Summary flows directly into Professional Experience

**Given** I run `resume new highlight`
**When** prompted
**Then** I'm asked for a single-line achievement with metrics
**And** the highlight is added to `career_highlights` array in config

**Given** I run non-interactively (LLM mode):
```bash
resume new highlight --text "$50M revenue growth through digital transformation"
```
**When** the command executes
**Then** the highlight is added without prompts

**Given** I run `resume list highlights`
**When** career highlights exist
**Then** a numbered list shows all highlights with their index:
  | # | Highlight |
  |---|-----------|
  | 0 | $50M revenue growth through digital transformation |
  | 1 | Built engineering org from 12 to 150+ engineers |
**And** JSON output via `--json` includes all highlights with indices

**Given** I run `resume show highlight 0`
**When** the highlight exists at index 0
**Then** the full highlight text displays
**And** character count shows (for length validation)

**Given** I run `resume remove highlight 0`
**When** the highlight exists at index 0
**Then** it is removed from `career_highlights` array
**And** confirmation shows the removed text

**Technical Notes:**
- Add `career_highlights: list[str]` to `ResumeConfig`
- Update `ResumeData` to include career_highlights from config
- Update `templates/executive.html` to render career highlights section:
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
- Create `templates/cto.html` with career highlights as required section
- CSS styling: larger font for highlights, background accent, prominent display
- Validation: warn if highlight exceeds 150 characters (should be concise)
- Max 4 highlights enforced (configurable via `skills.max_highlights: 4`)

---

## Story 6.14: Board & Advisory Roles Section

As a **CTO or executive with board experience**,
I want **a Board & Advisory Roles section on my resume**,
So that **my governance experience and strategic advisory work is visible to recruiters**.

> **Research Note (2026-01-12):** Board presentation experience and advisory roles signal executive maturity to hiring committees. This section is critical for CTO candidates targeting public companies or board-level enterprise positions.

**Acceptance Criteria:**

**Given** I configure board roles in `.resume.yaml`
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

**Given** board roles exist in config
**When** the executive or CTO template renders
**Then** a "Board & Advisory Roles" section appears
**And** roles show: organization, role title, dates, and focus area
**And** current roles display "Present" for end date

**Given** a board role has `type: "director"`
**When** it renders
**Then** it is distinguished from advisory roles (e.g., "Director" vs "Advisor")
**And** director roles appear first (higher governance level)

**Given** no board roles exist in config
**When** the resume is generated
**Then** no Board & Advisory section appears (graceful absence)

**Given** I run `resume new board-role`
**When** prompted
**Then** I'm asked for:
  1. Organization name (required)
  2. Role title (required)
  3. Type: director, advisory, committee (select)
  4. Start date (YYYY-MM)
  5. End date (YYYY-MM or blank for current)
  6. Focus area (optional description)

**Given** I run non-interactively (LLM mode):
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

**Given** I run `resume list board-roles`
**When** board roles exist
**Then** a formatted table shows all roles with status (Active/Past)
**And** JSON output via `--json` includes all fields

**Given** I run `resume show board-role "Tech Nonprofit"`
**When** the board role exists (partial match on organization)
**Then** detailed information displays:
  - Organization: Tech Nonprofit Foundation
  - Role: Board Advisor
  - Type: Advisory
  - Dates: 2023-01 - Present
  - Focus: Technology strategy and digital transformation
  - Status: Active
**And** JSON output via `--json` includes all fields

**Given** I run `resume remove board-role "Tech Nonprofit"`
**When** the board role exists (partial match on organization)
**Then** confirmation prompt shows role details
**And** upon confirmation, role is removed from config
**And** success message confirms removal

**Technical Notes:**
- Create `models/board_role.py`:
  ```python
  class BoardRole(BaseModel):
      organization: str
      role: str
      type: Literal["director", "advisory", "committee"] = "advisory"
      start_date: str  # YYYY-MM format
      end_date: str | None = None  # None = current
      focus: str | None = None
      display: bool = True
  ```
- Add `board_roles: list[BoardRole]` to `ResumeConfig`
- Update `ResumeData` to include board roles from config
- Update templates to render board section:
  ```html
  {% if resume.board_roles %}
  <section class="board-roles">
    <h2>Board & Advisory Roles</h2>
    {% for role in resume.board_roles %}
    <div class="board-entry">
      <strong>{{ role.organization }}</strong> - {{ role.role }}
      <span class="dates">{{ role.start_date[:4] }} - {{ role.end_date[:4] if role.end_date else "Present" }}</span>
      {% if role.focus %}<p class="focus">{{ role.focus }}</p>{% endif %}
    </div>
    {% endfor %}
  </section>
  {% endif %}
  ```
- Section placement: after Certifications, before Education (or as configured)
- Create commands for board role management: `new`, `list`, `remove`

---

## Story 6.15: Publications & Speaking Engagements

As a **thought leader with public visibility**,
I want **a Publications & Speaking section on my resume**,
So that **my industry influence and expertise are visible to hiring committees**.

> **Research Note (2026-01-12):** Publications and conference speaking demonstrate thought leadership and industry visibility, particularly valuable for executive candidates where public presence matters.

**Acceptance Criteria:**

**Given** I configure publications in `.resume.yaml`
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

**Given** publications exist in config
**When** the executive or CTO template renders
**Then** a "Publications & Speaking" section appears
**And** entries are grouped by type or displayed chronologically
**And** URLs are clickable in PDF output

**Given** a publication has `type: "conference"`
**When** it renders
**Then** it displays as speaking engagement: "DEF CON 30 (2022) - Securing Industrial Control Systems"

**Given** a publication has `type: "article"` or `"whitepaper"`
**When** it renders
**Then** it displays as written work: "Zero Trust Architecture Implementation Guide, Company Technical Blog (2023)"

**Given** no publications exist in config
**When** the resume is generated
**Then** no Publications section appears (graceful absence)

**Given** I run `resume new publication`
**When** prompted
**Then** I'm asked for:
  1. Title (required)
  2. Type: conference, article, whitepaper, book, podcast, webinar (select)
  3. Venue/publisher (required)
  4. Date (YYYY-MM)
  5. URL (optional)

**Given** I run non-interactively (LLM mode):
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

**Given** I run `resume list publications`
**When** publications exist
**Then** a formatted table shows all entries sorted by date
**And** JSON output via `--json` includes all fields

**Given** I run `resume show publication "Securing Industrial"`
**When** the publication exists (partial match on title)
**Then** detailed information displays:
  - Title: Securing Industrial Control Systems at Scale
  - Type: Conference
  - Venue: DEF CON 30
  - Date: 2022-08
  - URL: https://example.com/talk (clickable)
**And** JSON output via `--json` includes all fields

**Given** I run `resume remove publication "Securing Industrial"`
**When** the publication exists (partial match on title)
**Then** confirmation prompt shows publication details
**And** upon confirmation, publication is removed from config
**And** success message confirms removal

**Technical Notes:**
- Create `models/publication.py`:
  ```python
  class Publication(BaseModel):
      title: str
      type: Literal["conference", "article", "whitepaper", "book", "podcast", "webinar"]
      venue: str  # Conference name, publisher, blog name
      date: str  # YYYY-MM format
      url: HttpUrl | None = None
      display: bool = True
  ```
- Add `publications: list[Publication]` to `ResumeConfig`
- Update `ResumeData` to include publications from config
- Update templates to render publications section:
  ```html
  {% if resume.publications %}
  <section class="publications">
    <h2>Publications & Speaking</h2>
    {% for pub in resume.publications %}
    <div class="pub-entry">
      {% if pub.url %}<a href="{{ pub.url }}">{% endif %}
      <strong>{{ pub.title }}</strong>
      {% if pub.url %}</a>{% endif %}
      , {{ pub.venue }} ({{ pub.date[:4] }})
    </div>
    {% endfor %}
  </section>
  {% endif %}
  ```
- Section placement: optional, typically after Board Roles or at end
- Group by type option: speaking engagements vs written publications
- Create commands for publication management: `new`, `list`, `remove`

---

## Story 6.16: Enhanced Scope Indicators (P&L, Revenue, Geography)

As a **CTO or senior executive**,
I want **enhanced scope indicators with P&L, revenue, and geographic reach**,
So that **my leadership scale is immediately visible for each position**.

> **Research Note (2026-01-12):** CTO resume research confirms that P&L responsibility, revenue impact, and geographic scope are the most important metrics for executive positions. These must appear prominently for every position.

**Acceptance Criteria:**

**Given** a position in `positions.yaml` has scope fields
**When** the config is:
```yaml
positions:
  pos-acme-cto:
    employer: "Acme Corporation"
    title: "Chief Technology Officer"
    start_date: "2020-01"
    scope:
      revenue: "$500M"
      team_size: 200
      direct_reports: 15
      budget: "$50M"
      pl_responsibility: "$100M"
      geography: "Global (15 countries)"
```
**Then** the position loads and validates successfully
**And** scope indicators are available for template rendering

**Given** a position has scope data
**When** the executive or CTO template renders
**Then** scope appears as a prominent line below the position title:
```
$500M revenue | 200+ engineers | $50M technology budget | Global (15 countries)
```

**Given** a position has `pl_responsibility` field
**When** the scope line is formatted
**Then** P&L appears first (most important for CTO): "$100M P&L responsibility"

**Given** a position has only some scope fields
**When** the scope line is formatted
**Then** only populated fields appear (graceful handling)
**And** fields are pipe-separated with consistent styling

**Given** work units have scope data (legacy)
**When** the resume renders
**Then** work unit scope data is merged/overridden by position scope
**And** position scope takes precedence for the position-level display

**Given** I run `resume new position`
**When** prompted
**Then** I'm optionally asked for scope data:
  1. Revenue impact (e.g., "$500M")
  2. Team size (number)
  3. Direct reports (number)
  4. Budget managed (e.g., "$50M")
  5. P&L responsibility (e.g., "$100M")
  6. Geographic reach (e.g., "Global", "EMEA", "North America")

**Given** I run non-interactively (LLM mode):
```bash
resume new position \
  --employer "Acme Corp" \
  --title "CTO" \
  --start-date 2020-01 \
  --scope-revenue "$500M" \
  --scope-team-size 200 \
  --scope-budget "$50M" \
  --scope-pl "$100M" \
  --scope-geography "Global (15 countries)"
```
**When** the command executes
**Then** the position is created with all scope fields

**Technical Notes:**
- Enhance `models/position.py` with scope sub-model:
  ```python
  class PositionScope(BaseModel):
      revenue: str | None = None  # e.g., "$500M"
      team_size: int | None = None  # Total engineers/team members
      direct_reports: int | None = None  # Direct reports count
      budget: str | None = None  # e.g., "$50M technology budget"
      pl_responsibility: str | None = None  # P&L amount
      geography: str | None = None  # e.g., "Global", "APAC", "15 countries"
      customers: str | None = None  # e.g., "500K users", "Fortune 500 clients"

  class Position(BaseModel):
      # ... existing fields ...
      scope: PositionScope | None = None
  ```
- Update `services/position_service.py` with scope formatting:
  ```python
  def format_scope_line(position: Position) -> str | None:
      if not position.scope:
          return None
      parts = []
      if position.scope.pl_responsibility:
          parts.append(f"{position.scope.pl_responsibility} P&L")
      if position.scope.revenue:
          parts.append(f"{position.scope.revenue} revenue")
      if position.scope.team_size:
          parts.append(f"{position.scope.team_size}+ engineers")
      if position.scope.budget:
          parts.append(f"{position.scope.budget} budget")
      if position.scope.geography:
          parts.append(position.scope.geography)
      return " | ".join(parts) if parts else None
  ```
- Update templates to display scope prominently:
  ```html
  {% if entry.scope_line %}
  <p class="scope-indicators">{{ entry.scope_line }}</p>
  {% endif %}
  ```
- CSS: scope indicators use accent color, slightly smaller font, displayed on single line
- Update `positions.schema.json` with scope object
- Update `resume new position` command with scope flags

---

## Story 6.17: CTO Resume Template Variant

As a **CTO targeting board-level enterprise positions**,
I want **a CTO-specific resume template optimized for executive hiring**,
So that **my resume follows research-validated best practices for CTO candidates**.

> **Research Note (2026-01-12):** CTO resume layout research confirms Classic Executive (reverse chronological) or Hybrid format is optimal for board-level positions. The CTO template combines both with Career Highlights section.

**Acceptance Criteria:**

**Given** I run `resume build --jd file.txt --template cto`
**When** the resume is generated
**Then** the layout follows CTO resume best practices:
  - Name prominently displayed (22pt)
  - Professional title "Chief Technology Officer" below name
  - Contact info on single line with separators
  - Executive summary (3-5 sentences, business impact focus)
  - Career Highlights section (3-4 bullets, P&L/team/revenue metrics)
  - Professional Experience with prominent scope indicators
  - Board & Advisory Roles section (if populated)
  - Certifications section
  - Education section (brief, after experience)
  - Publications/Speaking (if populated)

**Given** the CTO template renders
**When** I inspect the PDF
**Then** it uses professional typography (Calibri or Arial)
**And** single-column layout for ATS compatibility
**And** strategic use of bold for metrics and numbers
**And** accent color limited to section dividers (#2c3e50 navy)
**And** 1-inch margins on all sides
**And** 2 pages maximum (research-validated)

**Given** positions have scope data
**When** the CTO template renders
**Then** scope indicators appear prominently under each position:
```
$500M revenue | 200+ engineers | $50M technology budget | Global
```

**Given** career highlights exist
**When** the CTO template renders
**Then** Career Highlights appears after Executive Summary
**And** before Professional Experience
**And** uses prominent styling with business-impact focus

**Given** board roles exist
**When** the CTO template renders
**Then** Board & Advisory Roles appears after Certifications
**And** demonstrates governance and strategic advisory experience

**Given** the resume exceeds 2 pages
**When** the PDF is generated
**Then** a warning is displayed: "CTO resumes should be 2 pages maximum"
**And** content is still rendered (user decides what to trim)

**Given** I run `resume build --jd file.txt --template executive`
**When** compared to `--template cto`
**Then** executive uses same structure but Career Highlights is optional
**And** both share the same CSS styling
**And** CTO template has Career Highlights as expected/prominent

**Technical Notes:**
- Create `templates/cto.html` extending executive template:
  ```html
  {% extends "executive.html" %}

  {% block after_summary %}
  {# Career Highlights is required/prominent for CTO #}
  {% if resume.career_highlights %}
  <section class="career-highlights cto-emphasis">
    <h2>Career Highlights</h2>
    <ul class="highlights-list">
      {% for highlight in resume.career_highlights %}
      <li>{{ highlight }}</li>
      {% endfor %}
    </ul>
  </section>
  {% endif %}
  {% endblock %}

  {% block after_certifications %}
  {# Board roles prominent for CTO #}
  {% if resume.board_roles %}
  <section class="board-roles">
    <h2>Board & Advisory Roles</h2>
    ...
  </section>
  {% endif %}
  {% endblock %}
  ```
- Create `templates/cto.css` with CTO-specific styling:
  - Career Highlights with accent background
  - Scope indicators with larger font
  - Board roles with governance-level styling
- Register "cto" template in provider
- Add page count warning logic to build command
- Section ordering for CTO:
  1. Header
  2. Executive Summary
  3. Career Highlights (CTO-specific)
  4. Professional Experience (with scope)
  5. Certifications
  6. Board & Advisory Roles
  7. Education
  8. Publications/Speaking (optional)
- Wireframe reference: `_bmad-output/excalidraw-diagrams/cto-resume-wireframe.excalidraw`

---

## Story 6.18: Enhanced Plan Command with Full Data Model Preview

As a **resume author preparing a targeted application**,
I want **the plan command to preview ALL data that will appear on my resume**,
So that **I can verify my certifications, education, and employment history match the JD before building**.

> **Gap Analysis (2026-01-12):** Current `plan` command only previews work units and skills. The `build` command additionally loads positions (for grouping), education, and certifications from config. Users have no visibility into whether their certifications/education match JD requirements until after building.

**Architecture Decision:**

Match certifications and education against JD requirements using keyword extraction:
- JD parser already extracts skills/keywords - extend to identify certification mentions
- Education matching checks degree level and field alignment
- Coverage analysis shows "matched" vs "unmatched" requirements
- Non-destructive: still shows all user's certs/education, just highlights matches

**Acceptance Criteria:**

**Given** I run `resume plan --jd job-description.txt`
**When** the plan output is displayed
**Then** I see a "Position Grouping Preview" section showing:
  - How work units will be grouped by employer
  - Position titles and date ranges
  - Which work units map to which position

**Given** the JD mentions specific certifications (e.g., "CISSP", "AWS certified")
**When** the plan output is displayed
**Then** I see a "Certifications Analysis" section showing:
  - My certifications that match JD requirements (highlighted)
  - JD certification requirements I don't have (gaps)
  - My certifications not mentioned in JD (still listed, lower priority)

**Given** the JD specifies education requirements (e.g., "BS Computer Science")
**When** the plan output is displayed
**Then** I see an "Education Analysis" section showing:
  - Whether my education meets/exceeds requirements
  - Degree level match (BS, MS, PhD)
  - Field relevance (Computer Science, related field, unrelated)

**Given** I have profile data configured
**When** the plan output is displayed
**Then** I see a "Profile Preview" section showing:
  - Name and title that will appear
  - Contact info completeness check
  - Summary word count and readability note

**Given** I run `resume plan --jd file.txt --json`
**When** JSON output is requested
**Then** the response includes:
```json
{
  "position_grouping": {
    "employers": [
      {
        "name": "IndustrialTech Solutions",
        "positions": [...],
        "work_unit_count": 5
      }
    ]
  },
  "certifications_analysis": {
    "matched": ["CISSP", "AWS Solutions Architect"],
    "gaps": ["CISM"],
    "additional": ["GICSP"]
  },
  "education_analysis": {
    "meets_requirements": true,
    "degree_match": "exceeds",
    "field_relevance": "direct"
  },
  "profile_preview": {
    "name": "Alex Morgan",
    "title": "Senior Platform Security Engineer",
    "contact_complete": true,
    "summary_words": 45
  }
}
```

**Given** positions.yaml doesn't exist or is empty
**When** the plan command runs
**Then** work units are shown ungrouped (current behavior)
**And** a warning suggests: "Consider adding positions.yaml for employer grouping"

**Given** no certifications are configured
**When** the JD mentions certifications
**Then** the certifications section shows only gaps
**And** a note: "No certifications configured - add to .resume.yaml"

**Technical Notes:**
- Extend `plan.py` to load positions, education, certifications from config
- Create `services/certification_matcher.py`:
  ```python
  class CertificationMatcher:
      CERT_PATTERNS = [
          r'\b(CISSP|CISM|CISA|CEH|OSCP)\b',
          r'\bAWS\s+(Solutions\s+Architect|Developer|SysOps)',
          r'\b(PMP|CAPM|CSM|PSM)\b',
          # ... common certification patterns
      ]

      def extract_jd_requirements(self, jd_text: str) -> list[str]
      def match_certifications(self, user_certs: list, jd_certs: list) -> MatchResult
  ```
- Create `services/education_matcher.py`:
  ```python
  class EducationMatcher:
      DEGREE_LEVELS = {'associate': 1, 'bachelor': 2, 'master': 3, 'doctorate': 4}
      FIELD_ALIASES = {
          'computer science': ['cs', 'computing', 'informatics'],
          'engineering': ['electrical', 'software', 'systems'],
          # ...
      }

      def extract_jd_requirements(self, jd_text: str) -> EducationReq
      def match_education(self, user_edu: list, jd_req: EducationReq) -> MatchResult
  ```
- Update `PlanResult` model to include new analysis sections
- Position grouping logic can reuse `ResumeData.from_work_units()` grouping
- Output formatting: use color/bold for matches, dim for gaps

**Dependencies:**
- Story 6.2 (Certifications Model) - for cert data structure
- Story 6.6 (Education Model) - for education data structure
- Story 6.7 (Positions Model) - for position grouping logic

---
