# Epic 3: Work Unit Validation & Discovery

**Goal:** Users can validate their Work Units and browse their collection with confidence

**FRs Covered:** FR6, FR7, FR8

---

## Story 3.1: Validate Command & Schema Validation

As a **user**,
I want **to validate my Work Units against the schema**,
So that **I catch errors before they cause problems during resume generation**.

**Acceptance Criteria:**

**Given** I run `resume validate`
**When** the command executes
**Then** all Work Units in `work-units/` are validated against the JSON Schema
**And** a summary shows total files checked and pass/fail count

**Given** I run `resume validate path/to/specific-file.yaml`
**When** the command executes
**Then** only that specific file is validated

**Given** I run `resume validate work-units/`
**When** the command executes
**Then** all YAML files in that directory are validated

**Given** all Work Units are valid
**When** validation completes
**Then** exit code is 0
**And** a success message is displayed

**Given** one or more Work Units are invalid
**When** validation completes
**Then** exit code is 1
**And** each invalid file is listed with its errors

**Given** I run `resume validate --json`
**When** validation completes
**Then** output is JSON with `valid_count`, `invalid_count`, and `errors` array

**Technical Notes:**
- Create `commands/validate.py` with Click command
- Create `services/validator.py` for JSON Schema validation
- Use `jsonschema` library for validation
- NFR3: Must complete within 1 second for all Work Units

---

## Story 3.2: Actionable Validation Feedback

As a **user who made a mistake**,
I want **clear, specific error messages that tell me how to fix the problem**,
So that **I can correct issues without guessing**.

**Acceptance Criteria:**

**Given** a Work Unit is missing a required field
**When** validation fails
**Then** the error message includes the field path (e.g., `problem.statement`)
**And** the message states "Missing required field"
**And** a suggestion is provided (e.g., "Add a problem statement describing the challenge")

**Given** a Work Unit has an invalid field type
**When** validation fails
**Then** the error message includes what was expected vs what was found
**And** example of correct format is shown

**Given** a Work Unit has an invalid enum value (e.g., `confidence: super-high`)
**When** validation fails
**Then** the error lists valid options: `high`, `medium`, `low`

**Given** multiple validation errors exist in one file
**When** validation runs
**Then** all errors are reported (not just the first one)
**And** errors are grouped by file

**Given** validation fails
**When** Rich output is used (not `--json`)
**Then** errors are color-coded and formatted for readability
**And** file paths are clickable in supported terminals

**Given** content quality validation is enabled (Research-Validated 2026-01-10)
**When** I run `resume validate --content-quality`
**Then** weak action verbs are flagged (managed, handled, helped, worked on, was responsible for)
**And** missing quantification is warned (outcomes without metrics)
**And** missing baseline context is warned (percentages without before-state)
**And** action verb repetition is flagged (same verb used multiple times)

**Given** a Work Unit uses a weak action verb
**When** content quality validation runs
**Then** the warning includes strong verb alternatives (orchestrated, spearheaded, championed, transformed)

**Given** content density validation is enabled (Research-Validated 2026-01-10)
**When** I run `resume validate --content-density`
**Then** total word count is calculated and compared against optimal ranges
**And** warning if 1-page resume is outside 475-600 words
**And** warning if 2-page resume is outside 800-1,200 words

**Given** bullet point density validation runs (Research-Validated 2026-01-10)
**When** validation checks Work Unit outcomes
**Then** warning if more than 8 bullets per role (recent roles)
**And** warning if fewer than 2 bullets per role
**And** warning if bullet character count is outside 100-160 range

**Given** keyword density validation runs (Research-Validated 2026-01-10)
**When** validation checks against a target JD
**Then** keyword density is calculated (target: 2-3% of word count)
**And** warning if density >3% (triggers spam detection in ATS)
**And** keyword coverage is calculated (target: 60-80% of JD keywords)
**And** warning if coverage <60%

**Technical Notes:**
- Create error formatting utilities in `utils/console.py`
- Map JSON Schema error types to helpful suggestions
- Include line numbers when possible (via ruamel.yaml)
- Structure: `{code, message, path, suggestion}`
- Add content quality validation per Architecture Section 1.4 (Research-Validated 2026-01-10): weak verb detection, quantification checks, baseline context checks, verb diversity checks
- **Content Density Validation (Research-Validated 2026-01-10):**
  - Word count ranges: 475-600 (1-page), 800-1,200 (2-page)
  - Bullet points per role: 4-6 optimal, warn >8 or <2
  - Characters per bullet: 100-160 optimal range
- **Keyword Validation (Research-Validated 2026-01-10):**
  - Keyword density: 2-3% of total word count
  - Keyword coverage: 60-80% of JD keywords
  - Flag missing high-priority keywords (mentioned 2+ times in JD)

---

## Story 3.3: List Command & Filtering

As a **user with many Work Units**,
I want **to browse and filter my collection**,
So that **I can find specific accomplishments quickly**.

**Acceptance Criteria:**

**Given** I run `resume list`
**When** the command executes
**Then** all Work Units are listed in a table format
**And** columns include: ID, Title, Date, Confidence, Tags (truncated)

**Given** I run `resume list --format json`
**When** the command executes
**Then** output is a JSON array of Work Unit summaries

**Given** I run `resume list --filter "tag:python"`
**When** the command executes
**Then** only Work Units with the `python` tag are shown

**Given** I run `resume list --filter "confidence:high"`
**When** the command executes
**Then** only Work Units with high confidence are shown

**Given** I run `resume list --filter "2024"`
**When** the command executes
**Then** Work Units matching "2024" in ID, title, or date are shown

**Given** no Work Units exist
**When** I run `resume list`
**Then** a helpful message is shown: "No Work Units found. Run `resume new work-unit` to create one."

**Given** I run `resume list --sort date`
**When** the command executes
**Then** Work Units are sorted by date (newest first by default)

**Technical Notes:**
- Create `commands/list_cmd.py` (avoid Python keyword `list`)
- Use Rich tables for formatted output
- Support basic filtering with `--filter` flag
- Load Work Units via `work_unit_service.py`

---
