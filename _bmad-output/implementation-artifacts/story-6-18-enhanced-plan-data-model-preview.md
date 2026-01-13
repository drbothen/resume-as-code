# Story 6.18: Enhanced Plan Command with Full Data Model Preview

## Story Info

- **Epic**: Epic 6 - Executive Resume Template & Profile System
- **Status**: ready-for-dev
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

## Technical Notes

### Files to Create
1. `src/resume_as_code/services/certification_matcher.py` - New service for JD cert matching
2. `src/resume_as_code/services/education_matcher.py` - New service for JD education matching
3. `tests/unit/services/test_certification_matcher.py` - Unit tests
4. `tests/unit/services/test_education_matcher.py` - Unit tests

### Files to Modify
1. `src/resume_as_code/commands/plan.py` - Add new analysis sections
2. `src/resume_as_code/models/plan.py` - Extend PlanResult with new fields
3. `src/resume_as_code/services/jd_parser.py` - Add certification/education extraction patterns

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
- [ ] Create `services/certification_matcher.py` with `CertificationMatcher` class
- [ ] Implement `CERT_PATTERNS` with common certification regex patterns
- [ ] Implement `extract_jd_requirements()` to find cert mentions in JD text
- [ ] Implement `match_certifications()` to compare user certs with JD requirements
- [ ] Create `CertificationMatchResult` dataclass for return type
- [ ] Write unit tests in `tests/unit/services/test_certification_matcher.py`

### Task 2: Create EducationMatcher Service
- [ ] Create `services/education_matcher.py` with `EducationMatcher` class
- [ ] Implement `DEGREE_LEVELS` mapping for comparison
- [ ] Implement `FIELD_ALIASES` for field matching (CS includes "computing", etc.)
- [ ] Implement `extract_jd_requirements()` to parse education requirements from JD
- [ ] Implement `match_education()` to compare user education with JD
- [ ] Create `EducationRequirement` and `EducationMatchResult` dataclasses
- [ ] Write unit tests in `tests/unit/services/test_education_matcher.py`

### Task 3: Add Position Grouping to Plan
- [ ] Create `_get_position_grouping()` helper function in `plan.py`
- [ ] Create `PositionGroupingResult`, `EmployerGroup`, `PositionSummary` dataclasses
- [ ] Call position grouping in `plan_command` after ranking
- [ ] Add Rich display for position grouping section
- [ ] Handle graceful fallback when positions.yaml doesn't exist

### Task 4: Add Certifications Analysis to Plan
- [ ] Integrate `CertificationMatcher` in `plan.py`
- [ ] Extract JD cert requirements using matcher
- [ ] Match against `config.certifications`
- [ ] Add Rich display for certifications analysis section
- [ ] Show matched (green), gaps (red), additional (dim)
- [ ] Handle graceful fallback when no certs configured

### Task 5: Add Education Analysis to Plan
- [ ] Integrate `EducationMatcher` in `plan.py`
- [ ] Extract JD education requirements using matcher
- [ ] Match against `config.education`
- [ ] Add Rich display for education analysis section
- [ ] Show degree match and field relevance
- [ ] Handle graceful fallback when no education configured

### Task 6: Add Profile Preview to Plan
- [ ] Create `_get_profile_preview()` helper function in `plan.py`
- [ ] Create `ProfilePreview` dataclass
- [ ] Add Rich display for profile preview section
- [ ] Show completeness status and missing fields
- [ ] Show summary word count with optimal range indicator

### Task 7: Update JSON Output
- [ ] Extend `_output_json()` with new analysis sections
- [ ] Add `position_grouping` to JSON response
- [ ] Add `certifications_analysis` to JSON response
- [ ] Add `education_analysis` to JSON response
- [ ] Add `profile_preview` to JSON response
- [ ] Update `JSONResponse.data` structure documentation

### Task 8: Integration Testing
- [ ] Test plan command with full config (positions, certs, education, profile)
- [ ] Test plan command with partial config (missing sections)
- [ ] Test plan command with empty config
- [ ] Test JSON output format
- [ ] Verify section ordering in Rich output

## Definition of Done

- [ ] All acceptance criteria pass
- [ ] Unit tests for CertificationMatcher (>90% coverage)
- [ ] Unit tests for EducationMatcher (>90% coverage)
- [ ] Integration tests for plan command
- [ ] `uv run pytest` passes
- [ ] `uv run ruff check src tests` passes
- [ ] `uv run ruff format src tests` passes
- [ ] `uv run mypy src --strict` passes
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
