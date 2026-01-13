---
stepsCompleted: ["step-01-validate-prerequisites", "step-02-design-epics", "step-03-create-stories"]
inputDocuments:
  - "_bmad-output/planning-artifacts/prd.md"
  - "_bmad-output/planning-artifacts/architecture.md"
---

# Resume as Code - Epic Breakdown

## Overview

This document provides the complete epic and story breakdown for Resume as Code, decomposing the requirements from the PRD, UX Design if it exists, and Architecture requirements into implementable stories.

## Requirements Inventory

### Functional Requirements

**Work Unit Management (11 requirements)**
- FR1: User can create a new Work Unit using `resume new work-unit`
- FR2: User can select an archetype (incident, greenfield, leadership) when creating a Work Unit
- FR3: User can create a Work Unit with reduced scaffolding using `--from memory` flag
- FR4: System opens scaffolded YAML file in user's editor upon creation
- FR5: User can store Work Units as individual YAML files following naming convention `wu-YYYY-MM-DD-<slug>.yaml`
- FR6: User can validate Work Units against JSON Schema using `resume validate`
- FR7: System provides specific, actionable feedback when validation fails
- FR8: User can list all Work Units using `resume list`
- FR9: User can assign confidence levels (high, medium, low) to Work Units
- FR10: User can add tags/terminology mappings to Work Units
- FR11: User can link evidence (git repos, metrics URLs, artifacts) to Work Units

**Resume Planning (8 requirements)**
- FR12: User can analyze a job description against Work Units using `resume plan --jd <file>`
- FR13: System ranks Work Units against JD using BM25 algorithm
- FR14: System displays selected Work Units with relevance scores and match rationale
- FR15: System displays excluded Work Units with exclusion reasons
- FR16: System identifies skill coverage and gaps against JD requirements
- FR17: System proposes content rewrites with before/after comparison
- FR18: User can save plan output to file using `--output <plan.yaml>`
- FR19: User can re-run plan after Work Unit modifications without mutating original data

**Resume Generation (8 requirements)**
- FR20: User can generate resume outputs using `resume build`
- FR21: System generates PDF output using template rendering
- FR22: System generates DOCX output using template rendering
- FR23: User can build from a saved plan file using `--plan <plan.yaml>`
- FR24: User can build directly from JD using `--jd <file>` (implicit plan)
- FR25: System writes manifest file containing: Work Units included, JD hash, timestamp, scoring weights, template used
- FR26: User can specify output directory using `--output-dir <path>`
- FR27: System outputs to `./dist/` by default

**Configuration (6 requirements)**
- FR28: System reads project configuration from `.resume/config.yaml`
- FR29: System reads user configuration from `~/.config/resume/config.yaml`
- FR30: CLI flags override project config; project config overrides user config; user config overrides defaults
- FR31: User can configure default output directory
- FR32: User can configure scoring weights for ranking
- FR33: User can configure default template selection

**Developer Experience (5 requirements)**
- FR34: User can display help using `resume help` or `resume help <command>`
- FR35: User can output in JSON format using `--format json` for scripting
- FR36: System returns predictable exit codes (0 success, non-zero failure)
- FR37: System provides verbose output using `--verbose` flag
- FR38: System operates non-interactively by default (no blocking prompts in scriptable workflows)

### NonFunctional Requirements

**Performance (4 requirements)**
- NFR1: `resume plan` completes within 3 seconds for typical job descriptions
- NFR2: `resume build` generates PDF and DOCX within 5 seconds
- NFR3: `resume validate` completes within 1 second for all Work Units
- NFR4: CLI startup time is under 500ms

**Reliability (3 requirements)**
- NFR5: Same inputs always produce identical outputs (deterministic generation)
- NFR6: Partial failures don't corrupt existing Work Unit files
- NFR7: Build failures leave no partial output files in `dist/`

**Portability (2 requirements)**
- NFR8: CLI runs on macOS, Linux, and Windows (Python 3.10+)
- NFR9: No platform-specific dependencies for core functionality

### Additional Requirements

**From Architecture Document:**

- **Starter Template**: Modern pyproject.toml from scratch (no cookiecutter) - Full control over dependency versions and structure
- **Project Structure**: src/ layout with resume_as_code package containing cli.py, config.py, models/, services/, providers/, templates/, utils/
- **Technology Stack**: Python 3.10+, Click 8.1+, Pydantic 2.0+, WeasyPrint 60+, python-docx 1.1+, sentence-transformers 2.2+ (with multilingual-e5-large-instruct model), rank-bm25 0.2+, Rich 13+
- **Content Strategy** (Research-Validated 2026-01-10): PAR framework for accomplishments, RAS variant for executives, 5 quantification dimensions (financial, operational, talent, customer, organizational), strong action verb standards
- **Provider Architecture**: Abstract ResumeProvider base class with PDFProvider, DOCXProvider, ATSProvider implementations
- **LLM Integration**: Abstract LLMService interface with NoOpLLMService default (optional [llm] extra)
- **Configuration Hierarchy**: CLI flags → Environment → Project (.resume.yaml) → User (~/.config) → Defaults
- **Naming Conventions**: PEP 8 for Python, snake_case for YAML fields, lowercase-hyphen for CLI options
- **Error Handling**: Custom exception hierarchy (ResumeError → ValidationError, ConfigurationError, RenderError)
- **Output Formatting**: Rich console for human output, --json flag for machine-parseable output
- **Testing Strategy**: pytest with unit/ tests mirroring src/ structure, fixtures/ for test data
- **Pre-commit Hooks**: ruff check + mypy --strict before commits
- **Embedding Cache**: .resume-cache/ directory with pickle serialization for embeddings

### FR Coverage Map

| FR | Epic | Description |
|----|------|-------------|
| FR1 | Epic 2 | Create Work Unit command |
| FR2 | Epic 2 | Archetype selection |
| FR3 | Epic 2 | `--from memory` flag |
| FR4 | Epic 2 | Opens editor with scaffold |
| FR5 | Epic 2 | File storage with naming convention |
| FR6 | Epic 3 | Validate command |
| FR7 | Epic 3 | Actionable validation feedback |
| FR8 | Epic 3 | List command |
| FR9 | Epic 2 | Confidence levels |
| FR10 | Epic 2 | Tags/terminology mappings |
| FR11 | Epic 2 | Evidence linking |
| FR12 | Epic 4 | Plan command with JD |
| FR13 | Epic 4 | BM25 ranking |
| FR14 | Epic 4 | Selected Work Units with scores |
| FR15 | Epic 4 | Excluded Work Units with reasons |
| FR16 | Epic 4 | Skill coverage and gaps |
| FR17 | Epic 4 | Proposed rewrites |
| FR18 | Epic 4 | Save plan to file |
| FR19 | Epic 4 | Re-run plan after modifications |
| FR20 | Epic 5 | Build command |
| FR21 | Epic 5 | PDF output |
| FR22 | Epic 5 | DOCX output |
| FR23 | Epic 5 | Build from saved plan |
| FR24 | Epic 5 | Build directly from JD |
| FR25 | Epic 5 | Manifest file |
| FR26 | Epic 5 | Custom output directory |
| FR27 | Epic 5 | Default dist/ output |
| FR28 | Epic 1 | Project config loading |
| FR29 | Epic 1 | User config loading |
| FR30 | Epic 1 | Config override hierarchy |
| FR31 | Epic 5 | Configure output directory |
| FR32 | Epic 5 | Configure scoring weights |
| FR33 | Epic 5 | Configure template selection |
| FR34 | Epic 1 | Help command |
| FR35 | Epic 1 | JSON output format |
| FR36 | Epic 1 | Predictable exit codes |
| FR37 | Epic 1 | Verbose mode |
| FR38 | Epic 1 | Non-interactive operation |
| (AI Agent) | Epic 1.5 | CLAUDE.md context file (Research-Validated 2026-01-10) |

## Epic List

### Epic 1: Project Foundation & Developer Experience
**User Outcome:** A working CLI tool with help, error handling, and configuration infrastructure

**FRs Covered:** FR28, FR29, FR30, FR34, FR35, FR36, FR37, FR38

This epic establishes the project foundation including pyproject.toml with full dependency spec, src/resume_as_code/ package structure, Click CLI skeleton, Rich console integration, configuration loader with hierarchy support, and AI agent compatibility features (Research-Validated 2026-01-10: semantic exit codes, JSON output with format versioning, stdout/stderr separation, CLAUDE.md context file).

---

### Epic 2: Work Unit Creation & Capture
**User Outcome:** Users can capture Work Units right after accomplishments happen (Journey 1: "The Capture")

**FRs Covered:** FR1, FR2, FR3, FR4, FR5, FR9, FR10, FR11

This epic delivers the core capture experience: creating Work Units with archetypes (incident, greenfield, leadership), the `--from memory` quick capture flag, editor integration, proper file storage with naming conventions, and rich metadata support (confidence levels, tags, evidence linking).

---

### Epic 3: Work Unit Validation & Discovery
**User Outcome:** Users can validate their Work Units and browse their collection with confidence

**FRs Covered:** FR6, FR7, FR8

This epic provides quality assurance through schema validation with actionable feedback, and discovery through the list command with filtering and JSON output support.

---

### Epic 4: Resume Planning & Explainability
**User Outcome:** Users can run `resume plan` and see exactly what will be included/excluded with reasons (Journey 2: "The Plan")

**FRs Covered:** FR12, FR13, FR14, FR15, FR16, FR17, FR18, FR19

This is the killer feature - the Terraform-style preview that no other resume tool offers. Users analyze job descriptions against their Work Units, see BM25 rankings with relevance scores, understand exclusion reasons, identify skill gaps, review proposed rewrites, and save plans for later use.

---

### Epic 5: Resume Generation & Output
**User Outcome:** Users can generate tailored PDF and DOCX resumes with full provenance

**FRs Covered:** FR20, FR21, FR22, FR23, FR24, FR25, FR26, FR27, FR31, FR32, FR33

This epic completes the workflow with the build command, PDF output via WeasyPrint, DOCX output via python-docx, manifest files for provenance tracking, configurable output directories, and template/scoring configuration options.

---

## Epic 1: Project Foundation & Developer Experience

**Goal:** A working CLI tool with help, error handling, and configuration infrastructure

**FRs Covered:** FR28, FR29, FR30, FR34, FR35, FR36, FR37, FR38

---

### Story 1.1: Project Scaffolding & CLI Skeleton

As a **developer**,
I want **a properly structured Python CLI project with a working entry point**,
So that **I have a foundation to build all resume commands upon**.

**Acceptance Criteria:**

**Given** the project is cloned and dependencies installed
**When** I run `resume --help`
**Then** I see the CLI help output with available commands listed
**And** the exit code is 0

**Given** the project structure exists
**When** I inspect the directory
**Then** I find `pyproject.toml` with all dependencies per Architecture spec
**And** I find `src/resume_as_code/` with `__init__.py`, `__main__.py`, and `cli.py`
**And** I find `schemas/`, `archetypes/`, and `tests/` directories

**Given** I run `python -m resume_as_code`
**When** the module executes
**Then** it behaves identically to the `resume` command

**Technical Notes:**
- Use Click 8.1+ for CLI framework
- Use Hatchling as build backend
- Follow src/ layout per Architecture Section 2.3
- Include dev dependencies: pytest, mypy, ruff, pre-commit

---

### Story 1.2: Rich Console & Output Formatting

As a **developer**,
I want **consistent, formatted CLI output with JSON option for scripting**,
So that **I can read output easily and pipe to other tools when needed**.

**Acceptance Criteria:**

**Given** I run any resume command
**When** the command produces output
**Then** the output uses Rich formatting with colors and symbols
**And** success messages show green checkmarks
**And** warnings show yellow warning symbols
**And** errors show red X symbols

**Given** I run `resume --json <command>`
**When** the command completes
**Then** output is valid JSON with `format_version`, `status`, `command`, `timestamp`, `data`, `errors`, `warnings` fields
**And** no Rich formatting is included in the output
**And** only JSON appears on stdout (no other content)

**Given** I run `resume --verbose <command>`
**When** the command executes
**Then** additional debug information is displayed
**And** file paths being accessed are shown

**Given** I run a command without `--verbose`
**When** the command executes
**Then** only essential output is shown (no debug clutter)

**Given** I run `resume --quiet <command>` (Research-Validated 2026-01-10)
**When** the command completes
**Then** no output is produced
**And** only the exit code indicates success/failure

**Given** any command produces progress or status messages (Research-Validated 2026-01-10)
**When** output is generated
**Then** progress/status goes to stderr (not stdout)
**And** only results/data go to stdout
**And** `--json` mode produces clean JSON on stdout with no stderr noise

**Technical Notes:**
- Create `utils/console.py` with Rich Console singleton
- Implement global `--json`, `--verbose`, and `--quiet` flags on main CLI group
- Use `err_console = Console(stderr=True)` for progress/status/errors
- Use `console` (stdout) for results only
- **AI Agent Compatibility (Research-Validated 2026-01-10):**
  - JSON output MUST include `format_version: "1.0.0"` for schema evolution
  - In `--json` mode, suppress ALL non-JSON output on stdout
  - Progress indicators to stderr only (agents parse stdout)
  - `--quiet` mode enables exit-code-only success checks

---

### Story 1.3: Configuration Hierarchy

As a **user**,
I want **configuration loaded from multiple sources with clear precedence**,
So that **I can set project defaults and override them when needed**.

**Acceptance Criteria:**

**Given** a project config exists at `.resume.yaml`
**When** I run a resume command
**Then** settings from `.resume.yaml` are applied

**Given** a user config exists at `~/.config/resume-as-code/config.yaml`
**When** I run a resume command and no project config exists
**Then** settings from user config are applied

**Given** both project and user configs exist
**When** I run a resume command
**Then** project config values override user config values

**Given** I pass a CLI flag (e.g., `--output-dir ./custom`)
**When** the command executes
**Then** the CLI flag overrides both project and user config

**Given** no config files exist
**When** I run a resume command
**Then** sensible defaults are used (e.g., `output_dir: ./dist`)

**Given** I run `resume config`
**When** the command executes
**Then** I see the current effective configuration with sources indicated

**Technical Notes:**
- Create `config.py` for hierarchy loader
- Create `models/config.py` for Pydantic config models
- Precedence: CLI > Environment > Project > User > Defaults
- Support `RESUME_*` environment variables

---

### Story 1.4: Error Handling & Exit Codes

As a **developer integrating resume into scripts**,
I want **predictable exit codes and structured error messages**,
So that **I can handle failures programmatically**.

**Acceptance Criteria:**

**Given** a command succeeds
**When** it completes
**Then** the exit code is 0

**Given** a command fails due to invalid user input (Research-Validated 2026-01-10)
**When** it completes
**Then** the exit code is 1 (user error, correctable)
**And** an error message explains what was wrong

**Given** a command fails due to configuration error (Research-Validated 2026-01-10)
**When** it completes
**Then** the exit code is 2 (configuration error)
**And** an error message explains the config issue

**Given** a command fails due to validation error (Research-Validated 2026-01-10)
**When** it completes
**Then** the exit code is 3 (validation error)
**And** the error includes the file path and validation details

**Given** a command fails due to missing resource (Research-Validated 2026-01-10)
**When** it completes
**Then** the exit code is 4 (resource not found)
**And** the error identifies the missing file or resource

**Given** a command fails due to system/runtime error (Research-Validated 2026-01-10)
**When** it completes
**Then** the exit code is 5 (system error)
**And** the error describes the failure

**Given** I run with `--json` and an error occurs
**When** the command fails
**Then** the JSON output includes `status: "error"` and populated `errors` array
**And** each error has `code`, `message`, `path`, `suggestion`, and `recoverable` fields

**Given** an error is recoverable (Research-Validated 2026-01-10)
**When** the error object is generated
**Then** `recoverable: true` indicates the agent can retry after fixing the issue
**And** `suggestion` provides an actionable fix recommendation

**Given** the CLI is run non-interactively (e.g., in CI or by AI agent)
**When** any command executes
**Then** no interactive prompts block execution (FR38)
**And** all required input comes from flags or environment variables

**Technical Notes:**
- Create exception hierarchy: `ResumeError` → `ValidationError`, `ConfigurationError`, `RenderError`, `NotFoundError`
- **Semantic Exit Codes (Research-Validated 2026-01-10):**
  | Exit Code | Exception Class | Meaning |
  |-----------|-----------------|---------|
  | 0 | (none) | Success |
  | 1 | `UserError` | Invalid flag, missing required argument |
  | 2 | `ConfigurationError` | Invalid config file, missing config |
  | 3 | `ValidationError` | Schema validation failed |
  | 4 | `NotFoundError` | Work unit file not found |
  | 5 | `SystemError` | File I/O error, network failure |
- Each exception class has an `exit_code` attribute
- **Enhanced Error Structure (Research-Validated 2026-01-10):**
  ```python
  @dataclass
  class StructuredError:
      code: str           # "VALIDATION_ERROR", "CONFIG_ERROR", etc.
      message: str        # Human-readable description
      path: str | None    # File path with optional line number
      suggestion: str     # Actionable fix recommendation
      recoverable: bool   # Can agent retry after fixing?
  ```
- Catch exceptions at CLI level and format appropriately

---

### Story 1.5: AI Agent Context Documentation (CLAUDE.md)

As a **user working with Claude Code or other AI coding assistants** (Research-Validated 2026-01-10),
I want **a CLAUDE.md file documenting CLI usage patterns**,
So that **AI agents can effectively use the resume CLI without documentation lookup**.

**Acceptance Criteria:**

**Given** the project is set up
**When** I inspect the project root
**Then** I find a `CLAUDE.md` file (or `.claude/CLAUDE.md`)

**Given** the CLAUDE.md file exists
**When** Claude Code reads the project
**Then** it understands all available CLI commands with examples
**And** it knows the exit codes and their meanings
**And** it knows to use `--json` mode when processing results programmatically

**Given** the CLAUDE.md file is read
**When** an AI agent plans a workflow
**Then** it can construct correct command invocations
**And** it understands the expected output format
**And** it knows common workflow patterns

**Given** the CLI is updated with new commands or options
**When** the release is prepared
**Then** the CLAUDE.md file is updated to reflect changes

**Technical Notes:**
- Create `CLAUDE.md` in project root (discovered by Claude Code)
- Include sections:
  - **Quick Reference**: All commands with one-line descriptions
  - **Common Workflows**: Step-by-step patterns (validate→plan→build)
  - **JSON Mode**: When and how to use `--json`
  - **Exit Codes**: Complete exit code table
  - **Error Handling**: How to interpret and fix common errors
- **Template Content (Research-Validated 2026-01-10):**
  ```markdown
  # Resume-as-Code Project Context

  ## Quick Reference
  - `resume plan --jd <file>` - Analyze JD and select work units
  - `resume build --jd <file>` - Generate resume files
  - `resume validate` - Validate all work units
  - `resume list` - List all work units

  ## Common Workflows
  1. After modifying a work unit: `resume validate`
  2. To preview resume for a job: `resume plan --jd job.txt`
  3. To generate resume: `resume build --jd job.txt`

  ## JSON Mode
  All commands support `--json` for structured output.
  Prefer JSON mode when processing results programmatically.

  ## Exit Codes
  - 0: Success
  - 1: Invalid arguments (user error)
  - 2: Configuration error
  - 3: Validation error
  - 4: Resource not found
  - 5: System error
  ```
- Keep file concise (<100 lines) for LLM context efficiency

---

## Epic 2: Work Unit Creation & Capture

**Goal:** Users can capture Work Units right after accomplishments happen (Journey 1: "The Capture")

**FRs Covered:** FR1, FR2, FR3, FR4, FR5, FR9, FR10, FR11

---

### Story 2.1: Work Unit Schema & Pydantic Model *(Enabling Story)*

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

### Story 2.2: Archetype Templates

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

### Story 2.3: Create Work Unit Command

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

### Story 2.4: Quick Capture Mode

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

### Story 2.5: Work Unit Metadata & Evidence

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

## Epic 3: Work Unit Validation & Discovery

**Goal:** Users can validate their Work Units and browse their collection with confidence

**FRs Covered:** FR6, FR7, FR8

---

### Story 3.1: Validate Command & Schema Validation

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

### Story 3.2: Actionable Validation Feedback

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

### Story 3.3: List Command & Filtering

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

## Epic 4: Resume Planning & Explainability

**Goal:** Users can run `resume plan` and see exactly what will be included/excluded with reasons (Journey 2: "The Plan")

**FRs Covered:** FR12, FR13, FR14, FR15, FR16, FR17, FR18, FR19

---

### Story 4.1: Job Description Parser

As a **developer**,
I want **to extract structured information from job descriptions**,
So that **the ranking algorithm has clean data to work with**.

**Acceptance Criteria:**

**Given** a plain text job description file
**When** the parser processes it
**Then** it extracts a list of skills/technologies mentioned
**And** it extracts key requirements and responsibilities
**And** it identifies experience level indicators (senior, staff, lead, etc.)

**Given** a JD with varied formatting (bullets, paragraphs, sections)
**When** the parser processes it
**Then** it handles all formats gracefully
**And** extracts meaningful content regardless of structure

**Given** a JD file path
**When** I pass it to the parser
**Then** the file is read and parsed
**And** a `JobDescription` model is returned with extracted data

**Given** the parser extracts skills
**When** I inspect the output
**Then** skills are normalized (e.g., "Python 3" → "python", "K8s" → "kubernetes")

**Technical Notes:**
- Create `models/job_description.py` with Pydantic model
- Create parsing logic in `services/planner.py`
- Use simple keyword extraction (no ML required for MVP)
- Store raw text plus extracted structured data

---

### Story 4.1.5: Embedding Service & Cache *(Enabling Story)* (Research-Validated 2026-01-10)

As a **system**,
I want **an embedding service with intelligent caching and model versioning**,
So that **semantic search is fast and embeddings remain valid across model updates**.

> **Note:** This is an enabling story that provides infrastructure for Story 4.2 (BM25 Ranking Engine). It does not deliver direct user value but is required for semantic ranking.

**Acceptance Criteria:**

**Given** the embedding service is initialized
**When** I load the model
**Then** the model hash is computed from weights for cache key generation
**And** the hash is stored for all subsequent cache operations

**Given** I request embeddings for text
**When** the text exists in cache with matching model hash
**Then** the cached embedding is returned without recomputation
**And** retrieval completes in <10ms

**Given** I request embeddings for text
**When** the cache miss occurs or model hash differs
**Then** the embedding is computed fresh
**And** the result is stored in cache with current model hash

**Given** the embedding model is updated
**When** I request embeddings for previously cached text
**Then** the old cached embedding is ignored (model hash mismatch)
**And** a fresh embedding is computed and cached

**Given** I run `resume cache clear`
**When** the command completes
**Then** embeddings with stale model hashes are removed
**And** a count of cleared entries is displayed

**Given** the embedding service generates embeddings (Research-Validated 2026-01-10)
**When** I inspect the cache key format
**Then** it uses: `SHA256(model_hash + "::" + normalized_text)`
**And** normalized_text is lowercased and stripped

**Given** the cache storage format (Research-Validated 2026-01-10)
**When** I inspect stored embeddings
**Then** they use SQLite for indexing
**And** pickle for serialization
**And** gzip for compression (40-60% size reduction)

**Technical Notes:**
- Create `services/embedder.py` with EmbeddingService class
- **Model Hash Computation:**
  ```python
  def compute_model_hash(model):
      hasher = hashlib.sha256()
      for name in sorted(model.state_dict().keys()):
          param = model.state_dict()[name]
          hasher.update(param.cpu().numpy().tobytes())
      return hasher.hexdigest()[:16]
  ```
- **Cache Key Generation:**
  ```python
  cache_key = SHA256(f"{model_hash}::{text.strip().lower()}")
  ```
- **SQLite Schema:**
  ```sql
  CREATE TABLE embeddings (
      cache_key TEXT PRIMARY KEY,
      model_hash TEXT NOT NULL,
      embedding BLOB NOT NULL,  -- gzip(pickle(numpy_array))
      timestamp REAL NOT NULL
  );
  CREATE INDEX idx_model_hash ON embeddings(model_hash);
  ```
- Cache location: `.resume-cache/{model_name}/cache.db`
- **Model Selection:**
  - Primary: `intfloat/multilingual-e5-large-instruct` (1024-dim, 560M params)
  - Fallback: `sentence-transformers/all-MiniLM-L6-v2` (384-dim, 22M params)
- **Instruction Prefixes (CRITICAL):**
  - Passages (JDs): `"passage: {text}"`
  - Queries (Work Units): `"query: {text}"`

---

### Story 4.2: BM25 Ranking Engine

As a **system**,
I want **to rank Work Units by relevance to a job description**,
So that **the most relevant accomplishments are selected for the resume**.

**Acceptance Criteria:**

**Given** a set of Work Units and a parsed job description
**When** the ranker processes them
**Then** each Work Unit receives a relevance score (0.0 to 1.0)
**And** Work Units are returned sorted by score (highest first)

**Given** a Work Unit with exact keyword matches to the JD
**When** ranking occurs
**Then** it scores higher than Work Units with partial or no matches

**Given** a Work Unit's title, problem, actions, and outcome fields
**When** the ranker processes it
**Then** all text fields contribute to the relevance score

**Given** the ranking completes
**When** I inspect the results
**Then** each Work Unit has a `match_reasons` list explaining why it ranked where it did

**Given** a typical job description and 15+ Work Units
**When** ranking runs
**Then** it completes within 3 seconds (NFR1)

**Given** the hybrid ranking system uses RRF fusion (Research-Validated 2026-01-10)
**When** BM25 and semantic results are combined
**Then** RRF formula is applied: `RRF_Score(d) = Σ (1 / (k + rank_i(d)))`
**And** k=60 is used as the default parameter
**And** top_k * 2 results are retrieved from each method before fusion
**And** ties are broken deterministically by document ID

**Given** the embedding model requires instruction prefixes (Research-Validated 2026-01-10)
**When** Work Units are encoded for similarity
**Then** they use the `"query: "` prefix
**And** job descriptions use the `"passage: "` prefix
**And** the e5-large-instruct model is loaded with these prefixes applied

**Technical Notes:**
- Create `services/ranker.py` with hybrid BM25 + semantic ranking
- Use `rank-bm25` library for lexical matching
- Use `sentence-transformers` with `multilingual-e5-large-instruct` model for semantic similarity
- Combine scores using Reciprocal Rank Fusion (RRF) with k=60 per Architecture
- **RRF Implementation (Research-Validated 2026-01-10):**
  - Retrieve `top_k * 2` from each method before fusion
  - Apply RRF: `score = 1/(k + rank_bm25) + 1/(k + rank_semantic)`
  - Sort by RRF score descending, then by doc_id for deterministic tie-breaking
- **Embedding Prefixes (CRITICAL):**
  - Job descriptions: `"passage: {text}"`
  - Work Units: `"query: {text}"`
- Build corpus from Work Unit text fields
- Return scores normalized to 0.0-1.0 range

---

### Story 4.3: Plan Command & Selection Display

As a **user**,
I want **to run `resume plan` and see which Work Units will be included**,
So that **I know exactly what my resume will contain before generating it**.

**Acceptance Criteria:**

**Given** I run `resume plan --jd senior-engineer.txt`
**When** the command executes
**Then** I see a "SELECTED" section with Work Units that will be included
**And** each selected Work Unit shows: ID, title, relevance score, match reasons

**Given** the plan displays selected Work Units
**When** I review the output
**Then** Work Units are ordered by relevance score (highest first)
**And** scores are displayed as percentages (e.g., "87% match")

**Given** I run `resume plan --jd file.txt --top 5`
**When** the command executes
**Then** only the top 5 Work Units are selected

**Given** no `--top` flag is provided
**When** the plan runs
**Then** a sensible default is used (e.g., top 8 or score threshold)

**Given** I run the plan command
**When** output is displayed
**Then** Rich formatting makes selections easy to scan
**And** match reasons are indented under each Work Unit

**Given** I run `resume plan --jd file.txt` (Research-Validated 2026-01-10)
**When** the plan displays content analysis
**Then** I see total word count with optimal range comparison
**And** I see estimated page count
**And** I see average bullets per role (optimal: 4-6)
**And** I see average characters per bullet (optimal: 100-160)

**Given** I run `resume plan --jd file.txt` (Research-Validated 2026-01-10)
**When** the plan displays keyword analysis
**Then** I see keyword density percentage (optimal: 2-3%)
**And** I see keyword coverage percentage (optimal: 60-80%)
**And** I see list of missing high-priority JD keywords
**And** I see keyword placement analysis (which sections contain key terms)

**Given** the plan identifies keyword issues (Research-Validated 2026-01-10)
**When** keyword coverage is below 60%
**Then** missing keywords are highlighted with JD occurrence count
**And** suggestions for Work Unit sections to add keywords are provided

**Technical Notes:**
- Create `commands/plan.py` with Click command
- Wire together JD parser, ranker, and display
- Add `--top N` flag for selection count
- Consider `--threshold 0.5` for score-based cutoff
- **Content Analysis Output (Research-Validated 2026-01-10):**
  ```
  📊 Content Analysis:
     Total Word Count: 742 (optimal: 800-1,200 for 2-page)
     Estimated Pages: 1.8
     Avg Bullets/Role: 5.2 (optimal: 4-6)
     Avg Chars/Bullet: 148 (optimal: 100-160)
  ```
- **Keyword Analysis Output (Research-Validated 2026-01-10):**
  ```
  🔑 Keyword Analysis:
     Density: 2.4% (optimal: 2-3%)
     Coverage: 73% (15/20 JD keywords found)

     Missing High-Priority Keywords:
     - "Kubernetes" (mentioned 3x in JD)
     - "CI/CD" (mentioned 2x in JD)
  ```

---

### Story 4.4: Exclusion Reasoning

As a **user**,
I want **to see which Work Units were excluded and why**,
So that **I trust the system isn't hiding relevant experience**.

**Acceptance Criteria:**

**Given** I run `resume plan --jd file.txt`
**When** the command executes
**Then** I see an "EXCLUDED" section after the selected Work Units
**And** each excluded Work Unit shows: ID, title, and exclusion reason

**Given** a Work Unit is excluded due to low relevance
**When** the exclusion is displayed
**Then** the reason states "Low relevance score (23%)" or similar

**Given** a Work Unit is excluded due to being outside top N
**When** the exclusion is displayed
**Then** the reason states "Below selection threshold" with its score shown

**Given** I run `resume plan --jd file.txt --show-excluded`
**When** the command executes
**Then** the excluded section is shown (it may be hidden by default)

**Given** exclusions are displayed
**When** I review them
**Then** I can identify Work Units that might need terminology updates
**And** I understand why the system made its choices

**Technical Notes:**
- Extend `commands/plan.py` to show exclusions
- Add `--show-excluded` flag (default: show top 5 exclusions)
- Format exclusion reasons clearly
- This builds trust through transparency

---

### Story 4.5: Skill Coverage & Gap Analysis

As a **user considering a job**,
I want **to see which JD requirements I cover and where I have gaps**,
So that **I can honestly assess my fit for the role**.

**Acceptance Criteria:**

**Given** I run `resume plan --jd file.txt`
**When** the command executes
**Then** I see a "COVERAGE" section showing skills/requirements from the JD
**And** each requirement shows: covered (✓), weak (△), or gap (✗)

**Given** a JD requirement is strongly matched by selected Work Units
**When** coverage is displayed
**Then** it shows ✓ with the matching Work Unit IDs

**Given** a JD requirement has partial matches
**When** coverage is displayed
**Then** it shows △ with "Weak signal" and relevant Work Unit IDs

**Given** a JD requirement has no matches in any Work Units
**When** coverage is displayed
**Then** it shows ✗ as a gap
**And** no judgment is implied (just factual reporting)

**Given** I run `resume plan --jd file.txt --json`
**When** the command executes
**Then** coverage data is included in the JSON output
**And** gaps are clearly enumerated

**Technical Notes:**
- Extract requirements from JD during parsing
- Cross-reference with Work Unit skills/tags
- Display as a coverage matrix or list
- This is the "Do I belong in this room?" feature from Journey 2

---

### Story 4.6: Plan Persistence

As a **user**,
I want **to save my plan and reload it later**,
So that **I can review, modify, and use it for resume generation**.

**Acceptance Criteria:**

**Given** I run `resume plan --jd file.txt --output plan.yaml`
**When** the command completes
**Then** the plan is saved to `plan.yaml`
**And** the file contains: JD hash, selected Work Units, scores, timestamp

**Given** a saved plan file exists
**When** I run `resume plan --load plan.yaml`
**Then** the plan is displayed without re-running ranking

**Given** I modify a Work Unit after saving a plan
**When** I re-run `resume plan --jd file.txt`
**Then** new rankings reflect the modifications
**And** the original plan file is unchanged

**Given** I run `resume build --plan plan.yaml`
**When** the build executes
**Then** it uses the selections from the saved plan (Epic 5)

**Given** a plan is saved
**When** I inspect the YAML file
**Then** it is human-readable and could be manually edited if needed

**Technical Notes:**
- Define plan file schema in `models/resume.py`
- Include JD hash for change detection
- Store Work Unit IDs and scores
- Enable `resume build` to consume plan files (Story 5.x)

---

**FR17 (Proposed Rewrites) Note:** This feature requires LLM integration which is marked as "hooks only" for MVP per Architecture. Recommend deferring to post-MVP or implementing as a stub that shows "Rewrite suggestions require LLM configuration."

---

## Epic 5: Resume Generation & Output

**Goal:** Users can generate tailored PDF and DOCX resumes with full provenance

**FRs Covered:** FR20, FR21, FR22, FR23, FR24, FR25, FR26, FR27, FR31, FR32, FR33

---

### Story 5.1: Resume Data Model & Template System

As a **developer**,
I want **a structured resume data model and template infrastructure**,
So that **providers can render consistent output across formats**.

**Acceptance Criteria:**

**Given** the models directory exists
**When** I inspect `models/resume.py`
**Then** I find a `ResumeData` model with: contact info, summary, work units, skills
**And** I find a `ResumeSection` model for grouping content

**Given** selected Work Units from a plan
**When** I build a ResumeData instance
**Then** Work Units are transformed into resume-ready format
**And** problem/action/outcome becomes achievement bullets

**Given** the templates directory exists
**When** I inspect `templates/modern.html`
**Then** I find a Jinja2 template for PDF rendering
**And** it uses `{{ resume.name }}`, `{{ resume.sections }}`, etc.

**Given** a ResumeData instance and a template
**When** Jinja2 renders the template
**Then** all placeholders are replaced with actual data
**And** the output is valid HTML

**Given** the template system
**When** I create a new template
**Then** I only need to create HTML/CSS files
**And** the provider automatically discovers and uses them

**Given** executive templates exist (Research-Validated 2026-01-10)
**When** I inspect `templates/executive.html`
**Then** I find a 2-3 page layout optimized for senior professionals
**And** it uses results-first bullet formatting (RAS: Results-Action-Situation)
**And** it displays scope indicators (budget, team size, revenue) when present
**And** it includes a professional summary section

**Given** ATS-safe executive template exists
**When** I inspect `templates/ats-executive.html`
**Then** I find a single-column layout for maximum ATS compatibility
**And** it uses standard section headers (Professional Summary, Work Experience, Skills)
**And** formatting prioritizes parseability over visual design

**Technical Notes:**
- Create `models/resume.py` with ResumeData, ResumeSection
- Create `templates/modern.html` and `templates/modern.css`
- Create `templates/executive.html` and `templates/executive.css` per Architecture Section 1.4
- Create `templates/ats-executive.html` for ATS-optimized single-column layout
- Use Jinja2 for template rendering
- Templates are provider-agnostic (HTML for PDF, could extend for others)
- Executive templates support 2-3 page layouts with scope indicator display (Research-Validated 2026-01-10)

---

### Story 5.2: PDF Provider (WeasyPrint)

As a **user**,
I want **to generate a professional PDF resume**,
So that **I have a polished document ready for submission**.

**Acceptance Criteria:**

**Given** a ResumeData instance
**When** the PDFProvider renders it
**Then** a PDF file is generated
**And** the PDF is properly formatted with styles from CSS

**Given** the modern template
**When** a PDF is generated
**Then** it has professional typography and layout
**And** sections are clearly delineated
**And** it fits standard letter/A4 page sizes

**Given** I run `resume build --format pdf`
**When** the build completes
**Then** `dist/resume.pdf` is created
**And** the file is a valid PDF document

**Given** a Work Unit with a long outcome description
**When** the PDF is generated
**Then** text wraps appropriately
**And** page breaks occur at sensible locations

**Given** the PDF generation
**When** it completes
**Then** it finishes within 5 seconds (NFR2)

**Technical Notes:**
- Create `providers/pdf.py` with PDFProvider class
- Use WeasyPrint for HTML→PDF conversion
- Load CSS from `templates/modern.css`
- Handle fonts and page sizing

---

### Story 5.3: DOCX Provider (python-docx)

As a **user**,
I want **to generate an editable DOCX resume**,
So that **I can make final tweaks or submit where Word format is required**.

**Acceptance Criteria:**

**Given** a ResumeData instance
**When** the DOCXProvider renders it
**Then** a DOCX file is generated
**And** the document has proper Word formatting

**Given** I run `resume build --format docx`
**When** the build completes
**Then** `dist/resume.docx` is created
**And** the file opens correctly in Microsoft Word and Google Docs

**Given** the generated DOCX
**When** I open it in Word
**Then** headings use proper Word heading styles
**And** bullet points are actual Word bullets (not text dashes)
**And** the document is editable

**Given** I run `resume build` without `--format`
**When** the build completes
**Then** both PDF and DOCX are generated by default

**Technical Notes:**
- Create `providers/docx.py` with DOCXProvider class
- Use python-docx for document generation
- Apply consistent styling (fonts, spacing)
- Consider docxtpl for template-based approach

---

### Story 5.4: Build Command

As a **user**,
I want **to generate my resume with a single command**,
So that **I get output files ready for job applications**.

**Acceptance Criteria:**

**Given** I run `resume build --plan plan.yaml`
**When** the build executes
**Then** Work Units specified in the plan are used
**And** output files are generated in `dist/`

**Given** I run `resume build --jd senior-engineer.txt`
**When** the build executes
**Then** an implicit plan is generated (same as `resume plan`)
**And** output files are generated based on that plan

**Given** I run `resume build` with no arguments
**When** the build executes
**Then** an error message explains that `--plan` or `--jd` is required

**Given** I run `resume build --jd file.txt --format pdf`
**When** the build completes
**Then** only PDF output is generated (no DOCX)

**Given** I run `resume build --jd file.txt --output-dir ./applications/google/`
**When** the build completes
**Then** output files are written to the specified directory
**And** the directory is created if it doesn't exist

**Given** the build succeeds
**When** I check the exit code
**Then** it is 0

**Given** the build fails (e.g., missing template)
**When** I check the exit code
**Then** it is non-zero
**And** no partial output files are left in `dist/` (NFR7)

**Technical Notes:**
- Create `commands/build.py` with Click command
- Support `--plan`, `--jd`, `--format`, `--output-dir` flags
- Wire together planner, providers, and file output
- Clean up on failure (atomic writes)

---

### Story 5.5: Manifest & Provenance

As a **user**,
I want **a manifest file with every build**,
So that **I know exactly what went into each resume version**.

**Acceptance Criteria:**

**Given** a build completes successfully
**When** I check the output directory
**Then** I find `manifest.yaml` alongside the resume files

**Given** I inspect the manifest
**When** I read its contents
**Then** I see: timestamp, Work Unit IDs included, JD file hash, template used, scoring weights

**Given** I build two resumes from different JDs
**When** I compare their manifests
**Then** I can see exactly what differed between them

**Given** the manifest includes Work Unit IDs
**When** I review it later
**Then** I can trace back to the exact Work Units used

**Given** the same inputs (JD, Work Units, config)
**When** I run build twice
**Then** the output is identical (NFR5 - deterministic)
**And** manifests have different timestamps but same content hash

**Technical Notes:**
- Create `providers/manifest.py` with ManifestProvider
- Include SHA256 hash of JD content
- Store Work Unit IDs with their scores
- Add resume-as-code version number

---

### Story 5.6: Output Configuration

As a **user**,
I want **to configure output preferences**,
So that **I can customize defaults without CLI flags every time**.

**Acceptance Criteria:**

**Given** I set `output_dir: ./resumes` in `.resume.yaml`
**When** I run `resume build --jd file.txt`
**Then** output goes to `./resumes/` instead of `./dist/`

**Given** I set `default_template: ats-safe` in config
**When** I run `resume build --jd file.txt`
**Then** the ATS-safe template is used
**And** I can override with `--template modern`

**Given** I set `scoring_weights` in config
**When** the ranker runs
**Then** custom weights are applied to ranking factors

**Given** I run `resume config output_dir ./custom`
**When** the command completes
**Then** the project config is updated with the new value

**Given** I run `resume config --list`
**When** the command executes
**Then** I see all current configuration values with their sources

**Technical Notes:**
- Extend `config.py` to support output preferences
- Add `--template` flag to build command
- Support scoring weight configuration (title_weight, skills_weight, etc.)
- Implement `resume config` command for viewing/setting config

---

## Epic 6: Executive Resume Template & Profile System

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

### Story 6.1: Profile Configuration & Contact Info Loading

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

### Story 6.2: Certifications Model & Storage

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

### Story 6.3: Skills Curation Service

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

### Story 6.4: Executive Resume Template

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

### Story 6.5: Template Certifications Section

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

### Story 6.6: Education Model & Rendering

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

### Story 6.7: Positions Data Model & Employment History (Normalized Architecture)

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

### Story 6.8: Position Management Commands (Human-Friendly UX)

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

### Story 6.9: Inline Position Creation (LLM-Optimized UX)

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

### Story 6.10: CLAUDE.md System Documentation Update

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
## Data Model

### Positions (positions.yaml)
Employment history with employer, title, dates. Work units reference positions.

### Work Units (work-units/*.yaml)
Individual achievements/accomplishments. Reference a position via `position_id`.

### Relationship
```
Position (1) ← references ← (*) Work Units
```
Work units are grouped under positions for resume rendering.
```

**Given** CLAUDE.md is updated
**When** I inspect the file
**Then** it includes examples for common AI agent tasks:
```markdown
## AI Agent Workflows

### Adding Work Experience (Inline - Preferred for LLM)
```bash
# Create position and work unit in one command
resume new work-unit \
  --position "Acme Corp|Senior Engineer|2022-01|" \
  --title "Led migration project reducing costs 40%" \
  --archetype greenfield
```

### Checking Existing Positions
```bash
resume --json list positions
```

### Creating Work Unit for Existing Position
```bash
resume new work-unit \
  --position-id pos-acme-senior-engineer \
  --title "Implemented security controls"
```
```

**Given** CLAUDE.md is updated
**When** I run `resume --help` or read the file
**Then** the documentation is consistent with actual CLI behavior

**Technical Notes:**
- Update existing CLAUDE.md with new sections:
  1. **Data Model** - Explain positions ↔ work units relationship
  2. **Position Management** - Commands for positions
  3. **AI Agent Workflows** - Inline flags and JSON mode patterns
  4. **Complete Example** - Full workflow from scratch
- Keep file under 150 lines for LLM context efficiency
- Ensure examples use actual command syntax
- Add common patterns section:
  - "I want to add my job history" → create positions first
  - "I just accomplished something" → quick capture with position reference
  - "Generate resume for this job" → plan + build workflow
- Update existing sections to reference position model where relevant
- Add troubleshooting: "Work unit has no position" warning resolution

---

### Story 6.11: Certification Management Commands

As a **user with professional certifications**,
I want **interactive commands to manage my certifications**,
So that **I can easily add, update, and remove credentials without editing YAML**.

**Acceptance Criteria:**

**Given** I run `resume new certification`
**When** prompted
**Then** I'm asked for:
  1. Certification name (required)
  2. Issuing organization (optional)
  3. Date obtained (YYYY-MM)
  4. Expiration date (YYYY-MM or blank for no expiration)
  5. Credential ID (optional)
  6. Verification URL (optional)

**Given** I complete the certification prompts
**When** the certification is created
**Then** it is added to the `certifications` array in `.resume.yaml`
**And** confirmation shows: "Added certification: AWS Solutions Architect - Professional"

**Given** I run `resume list certifications`
**When** certifications exist
**Then** a formatted table shows:
  | Name | Issuer | Date | Expires | Status |
  |------|--------|------|---------|--------|
  | AWS Solutions Architect | AWS | 2024-06 | 2027-06 | Active |
  | CISSP | ISC² | 2023-01 | 2026-01 | Expires Soon |

**Given** a certification expires within 90 days
**When** listed
**Then** status shows "Expires Soon" with yellow highlighting

**Given** a certification has expired
**When** listed
**Then** status shows "Expired" with red highlighting
**And** a suggestion: "Consider renewing or hiding with `resume config certifications[0].display false`"

**Given** I run `resume remove certification "CISSP"`
**When** the certification exists
**Then** it is removed from `.resume.yaml`
**And** confirmation shows: "Removed certification: CISSP"

**Given** I run `resume show certification "AWS Solutions"`
**When** the certification exists (partial match on name)
**Then** detailed information displays:
  - Name: AWS Solutions Architect - Professional
  - Issuer: Amazon Web Services
  - Date: 2024-06
  - Expires: 2027-06
  - Credential ID: ABC123XYZ
  - URL: (if present)
  - Status: Active
**And** JSON output via `--json` includes all fields

**Given** I run non-interactively (LLM mode):
```bash
resume new certification \
  --name "AWS Solutions Architect - Professional" \
  --issuer "Amazon Web Services" \
  --date 2024-06 \
  --expires 2027-06 \
  --credential-id "ABC123XYZ"
```
**When** the command executes
**Then** the certification is added without prompts

**Given** I run `resume --json list certifications`
**When** certifications exist
**Then** JSON output includes all certification fields
**And** includes computed `status` field (active/expires_soon/expired)

**Technical Notes:**
- Extend `commands/new.py` with `new certification` subcommand
- Extend `commands/list_cmd.py` with `list certifications` subcommand
- Extend `commands/show.py` with `show certification` subcommand
- Extend `commands/remove.py` with `remove certification` subcommand
- Support pipe-separated format: `"Name|Issuer|Date|Expires"`
- Follow CLI Resource Management Pattern in CLAUDE.md
- Certification status calculation:
  ```python
  def get_status(cert: Certification) -> str:
      if not cert.expires:
          return "active"
      expires = parse_date(cert.expires)
      if expires < today:
          return "expired"
      if expires < today + timedelta(days=90):
          return "expires_soon"
      return "active"
  ```
- Use Rich prompts for interactive input
- Support `--non-interactive` fallback with all fields as flags
- Config file update: read → modify → write `.resume.yaml`

---

### Story 6.12: Education Management Commands

As a **user**,
I want **interactive commands to manage my education history**,
So that **I can easily add degrees without editing YAML**.

**Acceptance Criteria:**

**Given** I run `resume new education`
**When** prompted
**Then** I'm asked for:
  1. Degree/program name (required)
  2. Institution name (required)
  3. Graduation year (YYYY)
  4. Honors/distinction (optional)
  5. GPA (optional)

**Given** I complete the education prompts
**When** the education entry is created
**Then** it is added to the `education` array in `.resume.yaml`
**And** confirmation shows: "Added education: BS Computer Science, UT Austin (2012)"

**Given** I run `resume list education`
**When** education entries exist
**Then** a formatted table shows:
  | Degree | Institution | Year | Honors |
  |--------|-------------|------|--------|
  | BS Computer Science | UT Austin | 2012 | Magna Cum Laude |
  | MS Cybersecurity | Georgia Tech | 2018 | |

**Given** I run `resume remove education "BS Computer Science"`
**When** the education entry exists
**Then** it is removed from `.resume.yaml`
**And** confirmation shows: "Removed education: BS Computer Science"

**Given** I run `resume show education "BS Computer Science"`
**When** the education entry exists
**Then** detailed information displays:
  - Degree: BS Computer Science
  - Institution: UT Austin
  - Year: 2012
  - Honors: Magna Cum Laude
  - GPA: 3.8 (if present)
**And** JSON output via `--json` includes all fields

**Given** I run non-interactively (LLM mode):
```bash
resume new education \
  --degree "Master of Science in Cybersecurity" \
  --institution "Georgia Tech" \
  --year 2018
```
**When** the command executes
**Then** the education entry is added without prompts

**Given** I run `resume --json list education`
**When** education entries exist
**Then** JSON output includes all education fields

**Given** education entries are rendered on resume
**When** the user has 10+ years experience
**Then** education appears after experience (industry standard)
**And** this ordering is handled by templates, not this story

**Technical Notes:**
- Extend `commands/new.py` with `new education` subcommand
- Extend `commands/list_cmd.py` with `list education` subcommand
- Extend `commands/show.py` with `show education` subcommand
- Extend `commands/remove.py` with `remove education` subcommand
- Use Rich prompts for interactive input
- Support pipe-separated format: `"Degree|Institution|Year|Honors"`
- Config file update: read → modify → write `.resume.yaml`
- Reuse patterns from Story 6.11 (certifications)
- Follow CLI Resource Management Pattern in CLAUDE.md

---

## FR Coverage Map Update

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

### Story 6.13: Career Highlights Section (CTO/Hybrid Format)

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

### Story 6.14: Board & Advisory Roles Section

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

### Story 6.15: Publications & Speaking Engagements

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

### Story 6.16: Enhanced Scope Indicators (P&L, Revenue, Geography)

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

### Story 6.17: CTO Resume Template Variant

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

### Story 6.18: Enhanced Plan Command with Full Data Model Preview

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

## Epic 6 Dependencies Updated

```
Story 6.1 (Profile) ─────────────────────────────────────────────┐
Story 6.2 (Certifications) ──────────────────────────────────────┤
Story 6.3 (Skills Curation) ─────────────────────────────────────┤
Story 6.6 (Education) ───────────────────────────────────────────┼──► Story 6.4 (Executive Template)
Story 6.7 (Positions) ───────────────────────────────────────────┤          │
Story 6.13 (Career Highlights) ──────────────────────────────────┤          │
Story 6.14 (Board Roles) ────────────────────────────────────────┤          ▼
Story 6.15 (Publications) ───────────────────────────────────────┤   Story 6.17 (CTO Template)
Story 6.16 (Enhanced Scope) ─────────────────────────────────────┘
                                                                           │
Story 6.2 (Certifications) ──────────────────────────────────────┐         │
Story 6.6 (Education) ───────────────────────────────────────────┼──► Story 6.18 (Enhanced Plan)
Story 6.7 (Positions) ───────────────────────────────────────────┘

Story 6.19 (Philosophy Documentation) ──► Independent (can start anytime)
```

---

### Story 6.19: Resume as Code Philosophy Documentation

As a **potential user or contributor discovering this project**,
I want **comprehensive documentation explaining the Resume as Code philosophy**,
So that **I understand the "why" behind the approach and can effectively use or contribute to the tool**.

**Acceptance Criteria:**

**Given** the project repository
**When** documentation is complete
**Then** a `docs/` folder exists with:
```
docs/
├── README.md                    # Index/navigation
├── philosophy.md                # Core philosophy explanation
├── data-model.md                # Work Units, Positions, etc.
├── workflow.md                  # Capture → Plan → Build flow
└── diagrams/
    ├── data-model.excalidraw    # Entity relationships
    ├── workflow-pipeline.excalidraw  # 4-stage pipeline
    └── philosophy-concept.excalidraw # Traditional vs RaC comparison
```

**Given** a user reads `docs/philosophy.md`
**When** they finish reading
**Then** they understand:
- The "resumes as queries against capability graph" mental model
- Why Work Units are the atomic unit (not jobs, not bullet points)
- The PAR framework (Problem-Action-Result)
- Git-native benefits (versioning, branching, collaboration)
- Separation of data, selection, and presentation

**Given** the data model diagram (Excalidraw)
**When** viewed
**Then** it shows:
- Work Unit, Position, Certification, Education entities
- Relationships with cardinality (Work Units → Position is many-to-one)
- Config aggregation (Profile, Skills, etc.)

**Given** the workflow pipeline diagram (Excalidraw)
**When** viewed
**Then** it shows:
- Four stages: Capture → Validate → Plan → Build
- Command names, inputs, outputs at each stage
- Data flow arrows with labels

**Given** the philosophy concept diagram (Excalidraw)
**When** viewed
**Then** it contrasts:
- Traditional approach (document-centric, multiple resume files)
- Resume as Code approach (data-centric, queries against capability graph)

**Technical Notes:**
- Use BMAD Excalidraw workflows for diagram creation
- Export both `.excalidraw` (editable) and `.svg` (embeddable)
- Keep documentation evergreen — avoid version-specific details
- Cross-link all documents from index
- Update main README.md with link to docs folder

---

### Story 6.20: Comprehensive README Update

As a **developer discovering the Resume as Code repository**,
I want **a comprehensive README that explains what the tool does and how to use it**,
So that **I can quickly understand the value proposition and get started**.

**Dependencies:** Story 6.19 (Philosophy Documentation) - for docs/ folder links

**Acceptance Criteria:**

**Given** the updated README.md
**When** viewed on GitHub
**Then** it includes these sections:
1. Title with tagline + philosophy teaser
2. Key Features list (8-10 features)
3. Quick Start guide (install → create → validate → plan → build)
4. Command Reference (all commands with flags and examples)
5. Examples section (practical workflows)
6. Configuration section (hierarchy, .resume.yaml example)
7. Documentation link (→ docs/)
8. Contributing section (dev setup, code quality, git flow)
9. License

**Given** a new user follows the Quick Start
**When** they complete it
**Then** they have:
- Installed the tool
- Created their first Work Unit
- Run validation
- Generated a resume from a sample JD

**Given** the Command Reference section
**When** viewed
**Then** it documents all commands:
- `resume new work-unit` - Create Work Units
- `resume validate` - Schema validation
- `resume list` - List Work Units
- `resume plan --jd FILE` - Preview selection
- `resume build --jd FILE` - Generate resume
- `resume config` - Configuration management
- `resume cache clear` - Cache management

**Technical Notes:**
- Keep README under 500 lines — link to docs/ for details
- All code examples must be copy-pasteable and tested
- Use tables for flag documentation
- Add badges (Python version, license) for visual appeal

---

### Story 6.21: GitHub Pages Marketing Site (Docusaurus)

As a **potential user discovering Resume as Code**,
I want **a polished marketing website that showcases the tool's capabilities**,
So that **I can understand its value, see it in action, and decide to adopt it**.

**Dependencies:** Story 6.19 (Philosophy Documentation) - content and diagrams source

**Acceptance Criteria:**

**Given** the Docusaurus site is deployed
**When** a user visits the site
**Then** they see:
- **Hero Section**: Tagline, value proposition, CTAs (Get Started, GitHub)
- **Features**: 8 key features with icons and descriptions
- **Philosophy**: "Resumes as queries" explanation with embedded diagrams
- **Interactive Demos**: Work Unit Builder, Plan Simulator, Output Preview
- **Documentation**: Searchable docs (Getting Started, Commands, Data Model)
- **Examples**: Runnable code snippets with expected output

**Given** the Demo page
**When** a user interacts with it
**Then** they can:
- Build a sample Work Unit with real-time YAML preview
- Run a mock plan against sample JD and Work Units
- Preview how Work Units render to resume bullets
- Copy generated YAML to clipboard

**Given** the site is deployed
**When** accessed
**Then**:
- Available at `https://[username].github.io/resume-as-code/`
- Mobile responsive (hamburger nav, touch-friendly)
- Lighthouse score 90+ (performance, accessibility)
- Automated deployment via GitHub Actions

**Technical Notes:**
- Use Docusaurus classic template
- Interactive demos built with React components
- Monaco editor for code input/preview
- Port existing docs/ content to Docusaurus format
- Local search (or Algolia if available)
- GitHub Actions workflow for automated deployment

**Site Structure:**
```
Home (Hero + Marketing)
├── Features
├── Philosophy (with Excalidraw diagrams)
├── Demo (3 interactive demos)
├── Docs/
│   ├── Getting Started
│   ├── Commands
│   ├── Data Model
│   └── Configuration
├── Examples
└── GitHub (external)
```

