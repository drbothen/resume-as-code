# Story 6.18: Enhanced Plan Command with Full Data Model Preview

## Story Info

- **Epic**: Epic 6 - Executive Resume Template & Profile System
- **Status**: in-review
- **Priority**: Medium
- **Estimation**: Medium (3-4 story points)
- **Dependencies**: Story 6.2 (Certifications), Story 6.6 (Education), Story 6.7 (Positions)

## User Story

As a **resume author preparing a targeted application**,
I want **the plan command to preview ALL data that will appear on my resume**,
So that **I can verify my certifications, education, and employment history match the JD before building**.

## Background

### Gap Analysis (2026-01-12)
Current `plan` command only previews work units and skills. The `build` command additionally loads positions (for grouping), education, and certifications from config. Users have no visibility into whether their certifications/education match JD requirements until after building.

### Architecture Decision
Match certifications and education against JD requirements using keyword extraction:
- JD parser already extracts skills/keywords - extend to identify certification mentions
- Education matching checks degree level and field alignment
- Coverage analysis shows "matched" vs "unmatched" requirements
- Non-destructive: still shows all user's certs/education, just highlights matches

## Acceptance Criteria

### AC1: Position Grouping Preview
**Given** I run `resume plan --jd job-description.txt`
**When** positions.yaml exists with positions
**And** work units have position_id references
**Then** I see a "Position Grouping Preview" section showing:
  - How work units will be grouped by employer
  - Position titles and date ranges
  - Which work units map to which position
  - Count of work units per employer

### AC2: Certifications Analysis
**Given** the JD mentions specific certifications (e.g., "CISSP", "AWS certified")
**When** the plan output is displayed
**Then** I see a "Certifications Analysis" section showing:
  - My certifications that match JD requirements (highlighted green)
  - JD certification requirements I don't have (shown as gaps in red)
  - My certifications not mentioned in JD (shown dimmed, lower priority)

### AC3: Education Analysis
**Given** the JD specifies education requirements (e.g., "BS Computer Science", "Master's degree preferred")
**When** the plan output is displayed
**Then** I see an "Education Analysis" section showing:
  - Whether my education meets/exceeds requirements
  - Degree level match: "exceeds", "meets", "below", or "unknown"
  - Field relevance: "direct" (exact match), "related", or "unrelated"

### AC4: Profile Preview
**Given** I have profile data configured in `.resume.yaml`
**When** the plan output is displayed
**Then** I see a "Profile Preview" section showing:
  - Name and title that will appear on resume
  - Contact info completeness check (email, phone, location, LinkedIn)
  - Summary word count (optimal: 45-75 words)

### AC5: JSON Output
**Given** I run `resume plan --jd file.txt --json`
**When** JSON output is requested
**Then** the response includes all new analysis sections:
```json
{
  "position_grouping": {
    "employers": [
      {
        "name": "IndustrialTech Solutions",
        "positions": [
          {"id": "pos-its-senior", "title": "Senior Engineer", "dates": "2022 - Present"}
        ],
        "work_unit_count": 5
      }
    ],
    "ungrouped_count": 2
  },
  "certifications_analysis": {
    "matched": ["CISSP", "AWS Solutions Architect"],
    "gaps": ["CISM"],
    "additional": ["GICSP"],
    "match_percentage": 67
  },
  "education_analysis": {
    "meets_requirements": true,
    "degree_match": "exceeds",
    "field_relevance": "direct",
    "jd_requirement": "Bachelor's in Computer Science",
    "user_education": "MS Cybersecurity"
  },
  "profile_preview": {
    "name": "Alex Morgan",
    "title": "Senior Platform Security Engineer",
    "contact_complete": true,
    "missing_fields": [],
    "summary_words": 52,
    "summary_status": "optimal"
  }
}
```

### AC6: Graceful Handling - No Positions
**Given** positions.yaml doesn't exist or is empty
**When** the plan command runs
**Then** work units are shown ungrouped (current behavior)
**And** a warning suggests: "Consider adding positions.yaml for employer grouping"
**And** position grouping section is omitted from output

### AC7: Graceful Handling - No Certifications
**Given** no certifications are configured
**When** the JD mentions certifications
**Then** the certifications section shows only gaps
**And** a note: "No certifications configured - add to .resume.yaml"

### AC8: Graceful Handling - No Profile
**Given** profile section is empty or missing in config
**When** the plan command runs
**Then** profile preview shows missing fields
**And** a warning: "Profile incomplete - configure in .resume.yaml"

### AC9: Career Highlights Preview
**Given** I have career_highlights configured in `.resume.yaml`
**When** the plan output is displayed
**Then** I see a "Career Highlights" section showing:
  - List of configured highlights (numbered)
  - Count of highlights configured
  - Warning if more than 4 highlights (research suggests max 4 for optimal impact)

### AC10: Board & Advisory Roles Preview
**Given** I have board_roles configured in `.resume.yaml`
**When** the plan output is displayed
**Then** I see a "Board & Advisory Roles" section showing:
  - Organization name and role title
  - Role type (director, advisory, committee)
  - Date range with current indicator
  - Count of roles and how many are current

### AC11: Publications & Speaking Preview
**Given** I have publications configured in `.resume.yaml`
**When** the plan output is displayed
**Then** I see a "Publications & Speaking" section showing:
  - Speaking engagements grouped together (conference, podcast, webinar)
  - Written works grouped together (article, whitepaper, book)
  - Venue and year for each entry
  - Summary of total publications by type

### AC12: JSON Output - New Executive Sections
**Given** I run `resume plan --jd file.txt --json`
**When** JSON output is requested with career_highlights, board_roles, or publications configured
**Then** the response includes the new sections:
```json
{
  "career_highlights": {
    "highlights": ["Led security transformation...", "Built and scaled team..."],
    "count": 4
  },
  "board_roles": {
    "roles": [
      {
        "organization": "ICS-ISAC",
        "role": "Technical Advisory Board Member",
        "type": "advisory",
        "dates": "2023 - Present",
        "is_current": true
      }
    ],
    "count": 2,
    "current_count": 1
  },
  "publications": {
    "publications": [
      {
        "title": "Securing Industrial Control Systems",
        "type": "conference",
        "venue": "S4 Conference",
        "year": "2024",
        "is_speaking": true
      }
    ],
    "count": 3,
    "speaking_count": 2,
    "written_count": 1
  }
}
```

### AC13: Graceful Handling - No Career Highlights
**Given** career_highlights is not configured or empty
**When** the plan command runs
**Then** a note: "No career highlights configured - add to .resume.yaml for executive resumes"

### AC14: Graceful Handling - No Board Roles
**Given** board_roles is not configured or empty
**When** the plan command runs
**Then** a note: "No board roles configured - add to .resume.yaml for executive resumes"

### AC15: Graceful Handling - No Publications
**Given** publications is not configured or empty
**When** the plan command runs
**Then** a note: "No publications configured - add to .resume.yaml for thought leadership"

## Technical Notes

### Files to Create
1. `src/resume_as_code/services/certification_matcher.py` - New service for JD cert matching ✅
2. `src/resume_as_code/services/education_matcher.py` - New service for JD education matching ✅
3. `tests/unit/test_certification_matcher.py` - Unit tests ✅
4. `tests/unit/test_education_matcher.py` - Unit tests ✅

### Files to Modify
1. `src/resume_as_code/commands/plan.py` - Add new analysis sections (dataclasses defined inline) ✅
2. `tests/integration/test_plan_command.py` - Integration tests for new sections ✅

_Note: Implementation used inline dataclasses in plan.py rather than separate models/plan.py file. JD extraction patterns integrated directly into matcher services._

### CertificationMatcher Service
```python
# src/resume_as_code/services/certification_matcher.py
class CertificationMatcher:
    """Match user certifications against JD requirements."""

    # Common certification patterns (case-insensitive)
    CERT_PATTERNS = [
        r'\b(CISSP|CISM|CISA|CEH|OSCP|GICSP|GSEC|GCIH)\b',  # Security certs
        r'\bAWS\s+(Solutions?\s+Architect|Developer|SysOps|DevOps)',  # AWS
        r'\b(CKA|CKAD|CKS)\b',  # Kubernetes
        r'\b(PMP|CAPM|CSM|PSM|SAFe)\b',  # Project/Agile
        r'\b(CCNA|CCNP|CCIE)\b',  # Cisco
        r'\bAzure\s+(Administrator|Developer|Solutions?\s+Architect)',  # Azure
        r'\bGCP\s+(Professional|Associate)',  # GCP
    ]

    def extract_jd_requirements(self, jd_text: str) -> list[str]:
        """Extract certification names mentioned in JD."""
        ...

    def match_certifications(
        self,
        user_certs: list[Certification],
        jd_certs: list[str],
    ) -> CertificationMatchResult:
        """Compare user certs to JD requirements."""
        ...

@dataclass
class CertificationMatchResult:
    matched: list[str]  # User certs that match JD
    gaps: list[str]  # JD certs user doesn't have
    additional: list[str]  # User certs not in JD
    match_percentage: int
```

### EducationMatcher Service
```python
# src/resume_as_code/services/education_matcher.py
class EducationMatcher:
    """Match user education against JD requirements."""

    DEGREE_LEVELS = {
        'associate': 1,
        'bachelor': 2, 'bs': 2, 'ba': 2,
        'master': 3, 'ms': 3, 'ma': 3, 'mba': 3,
        'doctorate': 4, 'phd': 4, 'doctor': 4,
    }

    FIELD_ALIASES = {
        'computer science': ['cs', 'computing', 'informatics', 'software'],
        'engineering': ['electrical', 'software engineering', 'systems'],
        'cybersecurity': ['security', 'information security', 'infosec'],
        'business': ['administration', 'management', 'mba'],
    }

    def extract_jd_requirements(self, jd_text: str) -> EducationRequirement | None:
        """Extract education requirements from JD text."""
        ...

    def match_education(
        self,
        user_education: list[Education],
        jd_req: EducationRequirement | None,
    ) -> EducationMatchResult:
        """Compare user education to JD requirements."""
        ...

@dataclass
class EducationRequirement:
    degree_level: str | None  # bachelor, master, etc.
    field: str | None  # computer science, engineering, etc.
    is_required: bool  # vs "preferred"

@dataclass
class EducationMatchResult:
    meets_requirements: bool
    degree_match: Literal["exceeds", "meets", "below", "unknown"]
    field_relevance: Literal["direct", "related", "unrelated", "unknown"]
    jd_requirement_text: str | None
    best_match_education: str | None
```

### Position Grouping Logic
Reuse existing `PositionService.group_by_employer()` method:
```python
def _get_position_grouping(
    selected_work_units: list[dict],
    config: ResumeConfig,
) -> PositionGroupingResult:
    """Group selected work units by position/employer."""
    position_service = PositionService(config.positions_path)
    positions = position_service.load_positions()

    # Group work units by position_id
    grouped: dict[str, list[str]] = {}  # position_id -> work_unit_ids
    ungrouped: list[str] = []

    for wu in selected_work_units:
        pos_id = wu.get("position_id")
        if pos_id and pos_id in positions:
            if pos_id not in grouped:
                grouped[pos_id] = []
            grouped[pos_id].append(wu.get("id"))
        else:
            ungrouped.append(wu.get("id"))

    # Group positions by employer
    employer_groups = position_service.group_by_employer(
        [positions[pid] for pid in grouped]
    )

    return PositionGroupingResult(
        employers=[
            EmployerGroup(
                name=employer,
                positions=[
                    PositionSummary(
                        id=pos.id,
                        title=pos.title,
                        dates=pos.format_date_range(),
                        work_unit_count=len(grouped.get(pos.id, [])),
                    )
                    for pos in pos_list
                ],
            )
            for employer, pos_list in employer_groups.items()
        ],
        ungrouped_count=len(ungrouped),
    )
```

### Profile Completeness Check
```python
def _get_profile_preview(config: ResumeConfig) -> ProfilePreview:
    """Generate profile preview with completeness check."""
    profile = config.profile
    missing = []

    if not profile.name:
        missing.append("name")
    if not profile.email:
        missing.append("email")
    if not profile.phone:
        missing.append("phone")
    if not profile.location:
        missing.append("location")
    if not profile.linkedin:
        missing.append("linkedin")

    summary_words = len(profile.summary.split()) if profile.summary else 0
    if summary_words < 45:
        summary_status = "too_short"
    elif summary_words > 75:
        summary_status = "too_long"
    else:
        summary_status = "optimal"

    return ProfilePreview(
        name=profile.name,
        title=profile.title,
        contact_complete=len(missing) == 0,
        missing_fields=missing,
        summary_words=summary_words,
        summary_status=summary_status,
    )
```

## Tasks

### Task 1: Create CertificationMatcher Service
- [x] Create `services/certification_matcher.py` with `CertificationMatcher` class
- [x] Implement `CERT_PATTERNS` with common certification regex patterns
- [x] Implement `extract_jd_requirements()` to find cert mentions in JD text
- [x] Implement `match_certifications()` to compare user certs with JD requirements
- [x] Create `CertificationMatchResult` dataclass for return type
- [x] Write unit tests in `tests/unit/test_certification_matcher.py`

### Task 2: Create EducationMatcher Service
- [x] Create `services/education_matcher.py` with `EducationMatcher` class
- [x] Implement `DEGREE_LEVELS` mapping for comparison
- [x] Implement `FIELD_ALIASES` for field matching (CS includes "computing", etc.)
- [x] Implement `extract_jd_requirements()` to parse education requirements from JD
- [x] Implement `match_education()` to compare user education with JD
- [x] Create `EducationRequirement` and `EducationMatchResult` dataclasses
- [x] Write unit tests in `tests/unit/test_education_matcher.py`

### Task 3: Add Position Grouping to Plan
- [x] Create `_get_position_grouping()` helper function in `plan.py`
- [x] Create `PositionGroupingResult`, `EmployerGroup`, `PositionSummary` dataclasses
- [x] Call position grouping in `plan_command` after ranking
- [x] Add Rich display for position grouping section
- [x] Handle graceful fallback when positions.yaml doesn't exist

### Task 4: Add Certifications Analysis to Plan
- [x] Integrate `CertificationMatcher` in `plan.py`
- [x] Extract JD cert requirements using matcher
- [x] Match against `config.certifications`
- [x] Add Rich display for certifications analysis section
- [x] Show matched (green), gaps (red), additional (dim)
- [x] Handle graceful fallback when no certs configured

### Task 5: Add Education Analysis to Plan
- [x] Integrate `EducationMatcher` in `plan.py`
- [x] Extract JD education requirements using matcher
- [x] Match against `config.education`
- [x] Add Rich display for education analysis section
- [x] Show degree match and field relevance
- [x] Handle graceful fallback when no education configured

### Task 6: Add Profile Preview to Plan
- [x] Create `_get_profile_preview()` helper function in `plan.py`
- [x] Create `ProfilePreview` dataclass
- [x] Add Rich display for profile preview section
- [x] Show completeness status and missing fields
- [x] Show summary word count with optimal range indicator

### Task 7: Update JSON Output
- [x] Extend `_output_json()` with new analysis sections
- [x] Add `position_grouping` to JSON response
- [x] Add `certifications_analysis` to JSON response
- [x] Add `education_analysis` to JSON response
- [x] Add `profile_preview` to JSON response
- [x] Update `JSONResponse.data` structure documentation

### Task 8: Integration Testing
- [x] Test plan command with full config (positions, certs, education, profile)
- [x] Test plan command with partial config (missing sections)
- [x] Test plan command with empty config
- [x] Test JSON output format
- [x] Verify section ordering in Rich output

### Task 9: Add Career Highlights Preview to Plan
- [x] Create `_get_career_highlights_preview()` helper function in `plan.py`
- [x] Create `CareerHighlightsPreview` dataclass
- [x] Add Rich display for career highlights section
- [x] Show numbered list of highlights with count
- [x] Handle graceful fallback when no highlights configured

### Task 10: Add Board Roles Preview to Plan
- [x] Create `_get_board_roles_preview()` helper function in `plan.py`
- [x] Create `BoardRolesPreview` and `BoardRoleSummary` dataclasses
- [x] Add Rich display for board roles section
- [x] Show organization, role, type, dates, current indicator
- [x] Handle graceful fallback when no board roles configured

### Task 11: Add Publications Preview to Plan
- [x] Create `_get_publications_preview()` helper function in `plan.py`
- [x] Create `PublicationsPreview` and `PublicationSummary` dataclasses
- [x] Add Rich display for publications section
- [x] Group by speaking vs written works
- [x] Handle graceful fallback when no publications configured

### Task 12: Update JSON Output for New Sections
- [x] Add `career_highlights` to JSON response
- [x] Add `board_roles` to JSON response
- [x] Add `publications` to JSON response

## Definition of Done

- [x] All acceptance criteria pass
- [x] Unit tests for CertificationMatcher (>90% coverage)
- [x] Unit tests for EducationMatcher (>90% coverage)
- [x] Integration tests for plan command
- [x] `uv run pytest` passes
- [x] `uv run ruff check src tests` passes
- [x] `uv run ruff format src tests` passes
- [x] `uv run mypy src --strict` passes
- [ ] Code reviewed

## Test Scenarios

### Test 1: Full Config Plan
```bash
# With positions.yaml, certifications, education, profile configured
resume plan --jd examples/jd/senior-engineer.txt
# Expect: All 4 new sections displayed
```

### Test 2: Minimal Config Plan
```bash
# With only work units, no positions/certs/education
resume plan --jd examples/jd/senior-engineer.txt
# Expect: Warnings for missing sections, graceful display
```

### Test 3: JSON Output Validation
```bash
resume plan --jd examples/jd/senior-engineer.txt --json | jq '.data.certifications_analysis'
# Expect: Valid JSON with matched/gaps/additional arrays
```

### Test 4: Cert Matching Accuracy
```python
def test_cert_matcher_finds_cissp_in_jd():
    matcher = CertificationMatcher()
    jd_text = "Requires CISSP or CISM certification"
    certs = matcher.extract_jd_requirements(jd_text)
    assert "CISSP" in certs
    assert "CISM" in certs
```

### Test 5: Education Matching
```python
def test_education_matcher_ms_exceeds_bs():
    matcher = EducationMatcher()
    jd_req = EducationRequirement(degree_level="bachelor", field="computer science")
    user_edu = [Education(degree="MS Computer Science", institution="MIT", year="2020")]
    result = matcher.match_education(user_edu, jd_req)
    assert result.degree_match == "exceeds"
    assert result.field_relevance == "direct"
```

## Notes

- Section order in Rich output: Profile → Position Grouping → (existing sections) → Certifications → Education
- JSON output preserves all existing fields, adds new ones alongside
- Color scheme: green=match, yellow=warning, red=gap, dim=additional/unmatched
- Don't break existing plan functionality - all new sections are additive
