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

