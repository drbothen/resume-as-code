# Epic 1: Project Foundation & Developer Experience

**Goal:** A working CLI tool with help, error handling, and configuration infrastructure

**FRs Covered:** FR28, FR29, FR30, FR34, FR35, FR36, FR37, FR38

---

## Story 1.1: Project Scaffolding & CLI Skeleton

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

## Story 1.2: Rich Console & Output Formatting

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

## Story 1.3: Configuration Hierarchy

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

## Story 1.4: Error Handling & Exit Codes

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

## Story 1.5: AI Agent Context Documentation (CLAUDE.md)

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
