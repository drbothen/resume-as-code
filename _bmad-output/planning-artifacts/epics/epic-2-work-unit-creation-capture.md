# Epic 2: Work Unit Creation & Capture

**Goal:** Users can capture Work Units right after accomplishments happen (Journey 1: "The Capture")

**FRs Covered:** FR1, FR2, FR3, FR4, FR5, FR9, FR10, FR11

---

## Story 2.1: Work Unit Schema & Pydantic Model *(Enabling Story)*

As a **developer**,
I want **a well-defined Work Unit data structure with validation**,
So that **all Work Units follow a consistent, validated format**.

> **Note:** This is an enabling story that provides infrastructure for user-facing stories 2.3-2.5. It does not deliver direct user value but is required for subsequent stories.

**Acceptance Criteria:**

**Given** the schemas directory exists
**When** I inspect `schemas/work-unit.schema.json`
**Then** I find a valid JSON Schema with required fields: `id`, `title`, `problem`, `actions`, `outcome`
**And** optional fields include: `time_started`, `time_ended`, `skills_demonstrated`, `confidence`, `tags`, `evidence`

**Given** the Work Unit Pydantic model exists
**When** I create a WorkUnit instance with valid data
**Then** the model validates successfully
**And** all fields are properly typed

**Given** I create a WorkUnit with missing required fields
**When** validation runs
**Then** a ValidationError is raised with specific field information

**Given** the Work Unit has a `problem` field
**When** I inspect the schema
**Then** `problem` contains `statement` (required) and optional `constraints`, `context`

**Given** the Work Unit has an `outcome` field
**When** I inspect the schema
**Then** `outcome` contains `result` (required) and optional `quantified_impact`, `business_value`

**Given** the Work Unit schema supports executive-level content (Research-Validated 2026-01-10)
**When** I inspect the schema
**Then** optional `scope` fields exist: `budget_managed`, `team_size`, `revenue_influenced`, `geographic_reach`
**And** optional `impact_category` supports: `financial`, `operational`, `talent`, `customer`, `organizational`
**And** optional `metrics` supports: `baseline`, `outcome`, `percentage_change`
**And** optional `framing` supports: `action_verb`, `strategic_context`

**Given** the Work Unit schema supports confidence for partial recall (Research-Validated 2026-01-10)
**When** I inspect the schema
**Then** optional `confidence` field in result supports: `exact`, `estimated`, `approximate`, `order_of_magnitude`
**And** optional `confidence_note` provides explanation for non-exact values

**Given** the Work Unit schema supports O*NET competency mapping (Research-Validated 2026-01-10)
**When** I inspect the skills structure
**Then** optional `onet_element_id` links skills to O*NET taxonomy (e.g., "2.A.1.a")
**And** optional `proficiency_level` uses 1-7 scale per O*NET standard

**Given** evidence types require validation (Research-Validated 2026-01-10)
**When** I inspect the Pydantic model
**Then** evidence uses discriminated unions with `type` field as discriminator
**And** each evidence type (repository, metrics, publication) has type-specific fields

**Technical Notes:**
- Create `schemas/work-unit.schema.json` per Architecture Section 3.2
- Create `models/work_unit.py` with Pydantic v2 model
- Use snake_case for all YAML field names
- Schema version field for future migrations
- Include executive-level fields as optional (scope, impact_category, metrics, framing) per Architecture Section 1.4
- **Pydantic v2 Validation Patterns (Research-Validated 2026-01-10):**
  - Use `@field_validator` for action verb strength checking
  - Use `@model_validator(mode='after')` for cross-field validation (result requires metric)
  - Use discriminated unions for evidence types:
    ```python
    Evidence = Annotated[
        Union[RepositoryEvidence, MetricsEvidence, PublicationEvidence],
        Field(discriminator='type')
    ]
    ```
- Add confidence levels for partial recall: `exact | estimated | approximate | order_of_magnitude`
- Add O*NET element ID support for skills standardization

---

## Story 2.2: Archetype Templates

As a **user**,
I want **pre-built templates for common work types**,
So that **I have guidance on what to capture for different situations**.

**Acceptance Criteria:**

**Given** the archetypes directory exists
**When** I inspect `archetypes/incident.yaml`
**Then** I find a template optimized for incident response stories
**And** it includes prompts for: detection, response actions, resolution, prevention measures

**Given** I inspect `archetypes/greenfield.yaml`
**When** I read the template
**Then** I find a template optimized for new project/feature stories
**And** it includes prompts for: problem identified, solution designed, implementation approach, outcomes

**Given** I inspect `archetypes/leadership.yaml`
**When** I read the template
**Then** I find a template optimized for leadership/influence stories
**And** it includes prompts for: challenge, stakeholders influenced, approach taken, organizational impact

**Given** any archetype template
**When** I validate it against the Work Unit schema
**Then** it passes validation (with placeholder values)
**And** it includes helpful comments guiding the user

**Given** executive-level archetypes exist (Research-Validated 2026-01-10)
**When** I inspect `archetypes/transformation.yaml`
**Then** I find a template for executive transformation initiatives
**And** it includes prompts for: strategic vision, cross-functional scope, quantified business outcomes

**Given** I inspect `archetypes/cultural.yaml`
**When** I read the template
**Then** I find a template for cultural/organizational leadership
**And** it includes prompts for: talent development, organizational impact, soft accomplishment quantification

**Given** I inspect `archetypes/strategic.yaml`
**When** I read the template
**Then** I find a template for strategic repositioning initiatives
**And** it includes prompts for: market positioning, competitive analysis, business model impact

**Technical Notes:**
- Create `archetypes/incident.yaml`, `greenfield.yaml`, `leadership.yaml`
- Include YAML comments with guidance (ruamel.yaml preserves comments)
- Each archetype pre-fills relevant fields with example text
- Add `archetypes/migration.yaml` and `archetypes/optimization.yaml` per Architecture
- Add `archetypes/transformation.yaml`, `cultural.yaml`, `strategic.yaml` per Architecture Section 1.4 (Research-Validated 2026-01-10)

---

## Story 2.3: Create Work Unit Command

As a **user**,
I want **to create a new Work Unit with a single command**,
So that **I can capture accomplishments quickly while they're fresh**.

**Acceptance Criteria:**

**Given** I run `resume new work-unit`
**When** the command executes
**Then** I am prompted to select an archetype (or use default)
**And** a new YAML file is created with the naming convention `wu-YYYY-MM-DD-<slug>.yaml`
**And** my configured editor opens with the scaffolded file

**Given** I run `resume new work-unit --archetype incident`
**When** the command executes
**Then** the incident archetype template is used
**And** no archetype prompt is shown

**Given** I run `resume new work-unit` and provide a title
**When** the file is created
**Then** the slug is derived from the title (lowercase, hyphenated)
**And** the file is placed in `work-units/` directory

**Given** the `work-units/` directory doesn't exist
**When** I create my first Work Unit
**Then** the directory is created automatically

**Given** I have `$EDITOR` or `$VISUAL` set
**When** the Work Unit is created
**Then** that editor opens the file
**And** if neither is set, a helpful message is shown

**Technical Notes:**
- Create `commands/new.py` with Click command
- Create `services/work_unit_service.py` for file operations
- Use `click.edit()` or subprocess for editor launch
- Generate slug from title using simple rules (lowercase, replace spaces with hyphens)

---

## Story 2.4: Quick Capture Mode

As a **user in a hurry**,
I want **a minimal capture mode for when I just need to jot something down**,
So that **friction doesn't stop me from capturing important work**.

**Acceptance Criteria:**

**Given** I run `resume new work-unit --from-memory`
**When** the command executes
**Then** a minimal template is used (fewer fields, less guidance)
**And** the `confidence` field is pre-set to `medium`

**Given** I use `--from-memory` mode
**When** the file is created
**Then** only essential fields are scaffolded: `title`, `problem.statement`, `actions`, `outcome.result`
**And** optional fields are present but commented out

**Given** I run `resume new work-unit --from-memory --title "Quick win"`
**When** the command executes
**Then** the title is pre-filled
**And** the editor opens immediately without prompts

**Technical Notes:**
- Add `--from-memory` flag to `resume new work-unit`
- Create minimal template variant
- Pre-set confidence to indicate this is a quick capture
- Still validate against schema on save

---

## Story 2.5: Work Unit Metadata & Evidence

As a **user**,
I want **to enrich Work Units with confidence levels, tags, and evidence links**,
So that **I can indicate certainty and provide proof of my claims**.

**Acceptance Criteria:**

**Given** a Work Unit YAML file
**When** I set `confidence: high`
**Then** the value is validated as one of: `high`, `medium`, `low`

**Given** a Work Unit YAML file
**When** I add tags like `tags: [python, incident-response, leadership]`
**Then** the tags are stored as a list of strings
**And** they can be used for filtering later

**Given** a Work Unit YAML file
**When** I add evidence links
**Then** I can specify `evidence` as a list with `type`, `url`, and optional `description`
**And** valid types include: `git_repo`, `metrics`, `document`, `artifact`, `other`

**Given** I validate a Work Unit with invalid confidence value
**When** validation runs
**Then** a clear error message indicates valid options

**Given** I validate a Work Unit with evidence
**When** the evidence has a `url` field
**Then** basic URL format validation is performed

**Technical Notes:**
- Extend Work Unit schema with confidence enum
- Add tags as array of strings
- Add evidence as array of objects with type/url/description
- Update Pydantic model with these fields

---
