# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Git Commit Guidelines

When creating git commits, do NOT include:
- The "Generated with Claude Code" line
- The "Co-Authored-By: Claude" line
- Any other AI attribution in commit messages

### Conventional Commits Format

All commits MUST follow https://www.conventionalcommits.org/:

```
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

### Required: Type

| Type     | Purpose                      |
|----------|------------------------------|
| feat     | New feature (MINOR version)  |
| fix      | Bug fix (PATCH version)      |
| docs     | Documentation only           |
| style    | Code style (no logic change) |
| refactor | Neither fix nor feature      |
| perf     | Performance improvement      |
| test     | Adding/fixing tests          |
| build    | Build system/dependencies    |
| ci       | CI configuration             |
| chore    | Other non-src/test changes   |

### Required: Description

- Use imperative, present tense ("add" not "added")
- Do NOT capitalize the first letter
- Do NOT end with a period

### Optional: Scope

Enclose in parentheses after type: `feat(api): add endpoint`

### Optional: Body

- Separate from description with a blank line
- Explain motivation and contrast with previous behavior

### Optional: Footer

- `Refs: #123` - Issue references
- `Closes: #123` - Issues closed by commit
- `BREAKING CHANGE:` - Breaking change description

### Breaking Changes

Indicate with either:
1. `!` after type/scope: `feat(api)!: remove endpoint`
2. Footer: `BREAKING CHANGE: endpoint removed and replaced with accounts`

## Git Workflow (Git Flow)

This project uses **Git Flow** branching strategy. Follow these rules:

### Branch Structure

| Branch | Purpose | Create from |
|--------|---------|-------------|
| `main` | Production releases only | - |
| `develop` | Integration branch (default working branch) | `main` |
| `feature/*` | New features | `develop` |
| `fix/*` | Bug fixes | `develop` |
| `spike/*` | Research spikes | `develop` |
| `hotfix/*` | Emergency production fixes | `main` |
| `release/*` | Release preparation | `develop` |

### Rules

1. **NEVER commit directly to `main`** - blocked by pre-commit hook
2. **Always branch from `develop`** for new work
3. **Use conventional commits** - enforced by pre-commit hook

### Branch Naming

```
feature/story-X.X-short-description
fix/issue-123-short-description
spike/XXX-topic
hotfix/issue-456-critical-fix
release/vX.X.X
```

### Creating a Branch

```bash
git checkout develop
git pull origin develop
git checkout -b feature/story-1.2-config-registry
```

### After Work is Complete

Create a PR to merge into `develop` (not `main`).

---

## Releasing

See [RELEASING.md](RELEASING.md) for the full release process.

### Quick Reference

| Method | When to Use |
|--------|-------------|
| **Prepare-Release workflow** | Standard releases (auto-version from commits) |
| **Release workflow dispatch** | Quick release when `__version__.py` is updated |
| **Git tag push** | Local control with `git tag v0.2.0 && git push --tags` |

### Version Script

```bash
# Check what version bump would be applied
python scripts/release/bump_version.py

# Preview changelog
python scripts/release/generate_changelog.py --version 0.2.0
```

---

## Package Management (uv)

This project uses **uv** for dependency management. Always prefix Python commands with `uv run`:

```bash
uv run pytest                      # Run tests
uv run pytest tests/unit/ -v       # Run specific tests
uv run ruff check src tests --fix  # Lint with auto-fix
uv run ruff format src tests       # Format code
uv run mypy src --strict           # Type check
uv run python -c "..."             # Run Python code
uv run resume --help               # Run the CLI
```

**Do NOT use bare `python`, `pytest`, `ruff`, or `mypy` commands** - they won't have access to the project's virtual environment.

---

## Resume CLI Reference

CLI tool for git-native resume generation from structured Work Units.

### Quick Reference

| Command | Description |
|---------|-------------|
| `resume --help` | Show all commands |
| `resume --version` | Show version |
| `resume config` | Show current configuration |
| `resume init` | Initialize new resume project |
| `resume init --non-interactive` | Quick setup with placeholders |
| `resume init --force` | Reinitialize (backs up existing config) |
| `resume new position` | Create new employment position |
| `resume new position "Employer\|Title\|Start\|End"` | Inline position creation |
| `resume list positions` | List all positions |
| `resume show position <id>` | Show position details |
| `resume remove position <id>` | Remove a position |
| `resume new work-unit` | Create new Work Unit |
| `resume new work-unit --position "..."` | Create with inline position |
| `resume list` | List all Work Units |
| `resume list -f tag:aws -s date` | Filter and sort Work Units |
| `resume show work-unit <id>` | Show work unit details |
| `resume remove work-unit <id>` | Remove a work unit |
| `resume new certification` | Create new certification |
| `resume new certification "Name\|Issuer\|Date\|Expires"` | Inline certification |
| `resume list certifications` | List all certifications with status |
| `resume show certification <name>` | Show certification details |
| `resume remove certification <name>` | Remove a certification |
| `resume new education` | Create new education entry |
| `resume new education "Degree\|Institution\|Year\|Honors"` | Inline education creation |
| `resume list education` | List all education entries |
| `resume new board-role` | Create new board/advisory role |
| `resume new board-role "Org\|Role\|Type\|Start\|End\|Focus"` | Inline board role creation |
| `resume list board-roles` | List all board roles |
| `resume new publication` | Create new publication/speaking |
| `resume new publication "Title\|Type\|Venue\|Date\|URL"` | Inline publication creation |
| `resume list publications` | List all publications |
| `resume new highlight --text "..."` | Create career highlight |
| `resume list highlights` | List all career highlights |
| `resume cache stats` | Show embedding cache statistics |
| `resume cache clear` | Clear stale cache entries |
| `resume validate` | Validate ALL resource types (comprehensive) |
| `resume validate work-units [PATH]` | Validate Work Units against schema |
| `resume validate positions` | Validate positions.yaml |
| `resume validate certifications` | Validate certifications |
| `resume validate education` | Validate education entries |
| `resume validate publications` | Validate publications |
| `resume validate board-roles` | Validate board roles |
| `resume validate highlights` | Validate career highlights |
| `resume validate config` | Validate .resume.yaml configuration |
| `resume plan --jd <file>` | Analyze JD, select Work Units |
| `resume build --jd <file>` | Generate resume files |
| `resume migrate --status` | Show schema version and migration status |
| `resume migrate --dry-run` | Preview migration changes |
| `resume migrate` | Apply schema migrations (prompts for confirmation) |
| `resume migrate --yes` | Apply migrations without confirmation prompt |
| `resume migrate --rollback <backup>` | Restore from backup directory |
| `resume migrate --shard <type>` | Convert single-file to directory mode |

### Validate Command

The validate command validates all resource types by default, or specific types via subcommands.

**Subcommands:**
- `work-units [PATH]` - Validate Work Units (supports PATH argument and content flags)
- `positions` - Validate positions.yaml
- `certifications` - Validate certifications (checks date <= expires)
- `education` - Validate education entries
- `publications` - Validate publications
- `board-roles` - Validate board roles (checks start_date <= end_date)
- `highlights` - Validate career highlights
- `config` - Validate .resume.yaml configuration

**Work Units Subcommand Options:**

| Flag | Description |
|------|-------------|
| `--content-quality` | Check content quality (weak verbs, quantification) |
| `--content-density` | Check content density (bullet length) |
| `--check-positions` | Validate position_id references exist in positions.yaml |

**Examples:**
```bash
resume validate                           # Validate ALL resources
resume validate work-units                # Validate only work units
resume validate work-units --check-positions  # With position validation
resume validate certifications            # Validate only certifications
resume --json validate                    # JSON output for all resources
resume --json validate positions          # JSON output for positions only
```

### Plan Command Options

| Flag | Description |
|------|-------------|
| `-j, --jd PATH` | Path to job description file |
| `-o, --output PATH` | Save plan to file |
| `-l, --load PATH` | Load and display saved plan |
| `-t, --top INTEGER` | Number of top Work Units to select (default: 8) |
| `--show-excluded` | Show top 5 excluded Work Units with reasons |
| `--show-all-excluded` | Show all excluded Work Units with reasons |
| `--strict-positions` | Validate position_id references exist (fail on invalid) |
| `--allow-gaps` | Allow employment gaps in resume (pure relevance filtering) |
| `--no-allow-gaps` | Guarantee at least one bullet per position (default behavior) |
| `-y, --years INTEGER` | Limit work history to last N years (overrides config) |

### Build Command Options

| Flag | Description |
|------|-------------|
| `-p, --plan PATH` | Path to saved plan file |
| `-j, --jd PATH` | Path to job description file (creates implicit plan) |
| `-f, --format [pdf\|docx\|all]` | Output format(s) to generate |
| `-o, --output-dir PATH` | Output directory (default: dist) |
| `-n, --name TEXT` | Base filename for output (default: 'resume') |
| `-t, --template TEXT` | Template to use for rendering |
| `--templates-dir PATH` | Custom templates directory (supplements built-in templates) |
| `--strict-positions` | Validate position_id references exist (fail on invalid) |
| `--tailored-notice` | Include footer notice that resume is tailored for role |
| `--no-tailored-notice` | Exclude footer notice (overrides config) |
| `--allow-gaps` | Allow employment gaps in resume (pure relevance filtering) |
| `--no-allow-gaps` | Guarantee at least one bullet per position (default behavior) |
| `-y, --years INTEGER` | Limit work history to last N years (overrides config) |

**Config-based tailored notice options** (in `.resume.yaml`):
```yaml
tailored_notice: true  # Enable footer notice by default
tailored_notice_text: "Custom message here"  # Optional custom text
```
Default text: "This resume highlights experience most relevant to this role. Full details available upon request."

**Config-based employment continuity options** (in `.resume.yaml`):
```yaml
employment_continuity: minimum_bullet  # Default: ensure 1 bullet per position
# employment_continuity: allow_gaps    # Alternative: pure relevance filtering with gap warnings
```
When using `allow_gaps`, the CLI will detect and warn about employment gaps >3 months.

**Config-based work history duration** (in `.resume.yaml`):
```yaml
history_years: 10  # Limit work history to last 10 years (null = unlimited)
```
When set, only positions with `end_date` within the last N years (or current positions with no `end_date`) are included. Work units associated with filtered positions are also excluded. CLI `--years` flag overrides this config value.

**Config-based template options** (in `.resume.yaml`):
```yaml
template_options:
  group_employer_positions: true  # Default: group multiple positions at same employer
```
When enabled (default), multiple positions at the same employer are rendered under a single employer heading with nested roles showing career progression. Set to `false` for traditional separate position rendering.

**Config-based custom templates directory** (in `.resume.yaml`):
```yaml
templates_dir: ./my-templates  # Path to custom templates directory
```
Custom templates supplement built-in templates. When a template name is requested:
1. First checks `templates_dir` for the template
2. Falls back to built-in templates if not found
3. Custom templates can extend built-in templates using Jinja2 `{% extends "executive.html" %}`

CLI flag `--templates-dir` overrides the config value.

**DOCX-specific template configuration** (in `.resume.yaml`):
```yaml
docx:
  template: branded  # DOCX template name (without .docx extension)
```
DOCX template resolution priority:
1. CLI `--template` flag (applies to all formats)
2. Config `docx.template` (DOCX-specific override)
3. Config `default_template` (fallback)
4. Programmatic generation (if no template found)

DOCX templates use docxtpl (Jinja2-based) for templating. Template search order:
1. `{templates_dir}/docx/{template_name}.docx` (custom templates)
2. Built-in `templates/docx/{template_name}.docx`

If the specified template is not found, the system falls back to programmatic DOCX generation with a warning.

### Migrate Command Options

| Flag | Description |
|------|-------------|
| `--status` | Show current schema version vs latest, migration availability |
| `--dry-run` | Preview what changes would be made without modifying files |
| `--rollback <backup>` | Restore project files from backup directory |
| `--shard <type>` | Convert single-file to directory mode (certifications, publications, education, board-roles, highlights) |
| `-y, --yes` | Skip confirmation prompt (for non-interactive use) |

The migrate command detects legacy configs (no `schema_version` field) as v1.0.0 and offers migration to the latest schema version. Migrations:
- Create automatic backups before modifying files
- Preserve YAML comments and formatting
- Are idempotent (safe to run multiple times)

**Directory sharding** (`--shard`): Converts single-file storage (e.g., `certifications.yaml`) to per-item files in a directory (e.g., `certifications/cert-2023-06-aws.yaml`). This enables fine-grained version control and reduces merge conflicts for power users with many items.

### List Command Options

| Flag | Description |
|------|-------------|
| `-f, --filter TEXT` | Filter Work Units (tag:value, confidence:value, archetype:value, or free text) |
| `-s, --sort [date\|title\|confidence]` | Sort field (default: date) |
| `-r, --reverse` | Reverse sort order (ascending) |
| `--stats` | Show archetype distribution statistics |
| `-v, --verbose` | Show source file paths (for directory mode resources) |

### Global Flags

| Flag | Description |
|------|-------------|
| `--config FILE` | Path to custom config file (overrides .resume.yaml) |
| `--json` | Output in JSON format for programmatic parsing |
| `-v, --verbose` | Show verbose debug output |
| `-q, --quiet` | Suppress all output, exit code only |

### Common Workflows

```bash
# Check configuration
resume config

# With JSON output for parsing
resume --json config

# Create position + work unit (LLM-optimized)
resume new work-unit \
  --position "Acme Corp|Senior Engineer|2022-01|" \
  --title "Led migration project"

# Create Work Unit with archetype template
resume new work-unit --archetype incident

# Validate → Plan → Build
resume validate
resume plan --jd job-description.txt
resume build --jd job-description.txt

# Build with custom filename and output directory
resume build --jd job.txt --name john-doe-cto --output-dir ./applications/acme/

# Build with custom templates directory
resume build --jd job.txt --templates-dir ./my-templates --template branded

# Generate test resume from jmagady-resume data (requires pango for PDF)
cd /Users/jmagady/Dev/jmagady-resume && \
  DYLD_LIBRARY_PATH=/opt/homebrew/lib \
  uv run --project /Users/jmagady/Dev/resume resume build --jd test-jd.txt --format pdf -o dist
```

### JSON Mode

Use `--json` for structured output. Response format:

```json
{
  "format_version": "1.0.0",
  "status": "success|error",
  "command": "config",
  "timestamp": "ISO-8601",
  "data": {},
  "warnings": [],
  "errors": []
}
```

### Exit Codes

| Code | Meaning | Recoverable |
|------|---------|-------------|
| 0 | Success | - |
| 1 | User error (invalid input) | Yes |
| 2 | Configuration error | Yes |
| 3 | Validation error | Yes |
| 4 | Resource not found | Yes |
| 5 | System error | No |

### Error Format

```json
{
  "code": "VALIDATION_ERROR",
  "message": "Missing required field",
  "path": "work-units/file.yaml:12",
  "suggestion": "Add 'title' field",
  "recoverable": true
}
```

### Retry Pattern

1. Check `recoverable: true` in error response
2. Apply the `suggestion` fix
3. Re-run command

### File Locations

| Path | Purpose |
|------|---------|
| `.resume.yaml` | Project config (schema_version, output settings) |
| `~/.config/resume-as-code/config.yaml` | User config |
| `work-units/*.yaml` | Work Unit files |
| `positions.yaml` | Employment positions (employers, titles, dates) |
| `profile.yaml` | Contact info, title, summary |
| `certifications.yaml` | Professional credentials (or `certifications/` directory) |
| `education.yaml` | Academic credentials (or `education/` directory) |
| `publications.yaml` | Articles and speaking (or `publications/` directory) |
| `board-roles.yaml` | Advisory positions (or `board-roles/` directory) |
| `highlights.yaml` | Career summary bullets (or `highlights/` directory) |
| `dist/` | Generated output |

**Directory mode**: Resources can optionally use per-item files in directories instead of single YAML files. Use `resume migrate --shard <type>` to convert. Directory mode enables fine-grained git history and reduces merge conflicts.

---

## Data Model

### Positions (positions.yaml)

Employment history - employers, titles, dates. Each position has a unique ID.

```yaml
- id: pos-techcorp-senior-engineer
  employer: TechCorp Industries
  title: Senior Platform Engineer
  start_date: "2022-01"
  end_date: null  # current position
```

### Work Units (work-units/*.yaml)

Individual achievements referencing positions via `position_id`.

```yaml
id: wu-2024-01-30-ics-assessment
position_id: pos-techcorp-senior-engineer  # References position
title: "Led ICS security assessment..."
```

### Relationship

```
Position (1) ←── references ──← Work Units (*)
```

Resume groups work units under positions for rendering:
```
TechCorp Industries - Senior Platform Engineer (2022-Present)
• Achievement from work unit 1
• Achievement from work unit 2
```

---

## Position Management

### Commands

| Command | Description |
|---------|-------------|
| `resume new position` | Create position (interactive or pipe-separated) |
| `resume new position "Employer\|Title\|Start\|End"` | Inline creation |
| `resume list positions` | List all positions |
| `resume show position <id>` | Show position details |
| `resume remove position <id>` | Remove a position (prompts for confirmation) |

### Position ID Format

Auto-generated: `pos-{employer-slug}-{title-slug}`

Example: `pos-techcorp-senior-engineer`

### Scope Flags (Executive Positions)

For executive-level positions with leadership scale indicators:

| Flag | Description |
|------|-------------|
| `--scope-revenue` | Revenue impact (e.g., "$500M") |
| `--scope-team-size` | Team size (number) |
| `--scope-direct-reports` | Direct reports count |
| `--scope-budget` | Budget managed (e.g., "$50M") |
| `--scope-pl` | P&L responsibility (e.g., "$100M") |
| `--scope-geography` | Geographic reach (e.g., "Global", "EMEA") |
| `--scope-customers` | Customer scope (e.g., "Fortune 500", "500K users") |

Example:
```bash
resume new position \
  --employer "Acme Corp" \
  --title "CTO" \
  --start-date 2020-01 \
  --scope-pl "$100M" \
  --scope-revenue "$500M" \
  --scope-team-size 200 \
  --scope-budget "$50M" \
  --scope-geography "Global"
```

---

## Certification Management

### Commands

| Command | Description |
|---------|-------------|
| `resume new certification` | Create certification (interactive or pipe-separated) |
| `resume new certification "Name\|Issuer\|Date\|Expires"` | Inline creation |
| `resume list certifications` | List all certifications with expiration status |
| `resume show certification <name>` | Show certification details (partial match supported) |
| `resume remove certification <name>` | Remove by name (partial match supported) |

### Status Indicators

`list certifications` shows expiration status:
- **Active** - Valid certification
- **Expires Soon** - Expires within 90 days
- **Expired** - Past expiration date

---

## Work Unit Management

### Commands

| Command | Description |
|---------|-------------|
| `resume new work-unit` | Create work unit (interactive or with flags) |
| `resume list` | List all work units |
| `resume show work-unit <id>` | Show work unit details (PAR, skills, tags) |
| `resume remove work-unit <id>` | Remove work unit file |

### Work Unit ID Format

Files stored as: `work-units/{id}.yaml`

Example: `wu-2024-01-30-ics-assessment`

### Work Unit Creation Flags

| Flag | Description |
|------|-------------|
| `-a, --archetype` | Template: cultural, greenfield, incident, leadership, migration, minimal, optimization, strategic, transformation |
| `-t, --title TEXT` | Work Unit title (used to generate ID slug) |
| `--position TEXT` | Create/reuse position: 'Employer\|Title\|Start\|End' |
| `-p, --position-id TEXT` | Position ID to associate with |
| `--problem TEXT` | Problem statement (min 20 chars) |
| `--action TEXT` | Action taken (repeatable, min 10 chars each) |
| `--result TEXT` | Outcome result (min 10 chars) |
| `--impact TEXT` | Quantified impact (optional) |
| `--skill TEXT` | Skill demonstrated (repeatable) |
| `--tag TEXT` | Tag for filtering (repeatable) |
| `--start-date TEXT` | Start date (YYYY-MM-DD or YYYY-MM) |
| `--end-date TEXT` | End date (YYYY-MM-DD or YYYY-MM) |
| `--from-memory` | Quick capture mode with minimal template |
| `--no-edit` | Don't open editor after creation |

### Work Unit Archetypes

Archetypes are pre-filled templates for common achievement types. Each provides PAR (Problem-Action-Result) structure with guidance and examples.

| Archetype | Use Case | Best For |
|-----------|----------|----------|
| `greenfield` | New system/feature built from scratch | Launching products, building platforms, creating new capabilities |
| `incident` | Production incident response | Outages, security events, escalations, on-call heroics |
| `optimization` | Performance or cost improvements | Reducing latency, cutting costs, improving efficiency |
| `migration` | System/data migration projects | Cloud migrations, platform upgrades, technology transitions |
| `leadership` | Team building and mentorship | Hiring, growing teams, developing talent, culture initiatives |
| `transformation` | Large-scale organizational change | Digital transformation, process overhauls, major initiatives |
| `strategic` | Strategic initiatives and planning | Roadmap definition, architecture decisions, cross-org alignment |
| `cultural` | Culture and values initiatives | DEI programs, engagement improvements, organizational health |
| `minimal` | Quick capture with basic structure | Fast notes when you'll fill in details later |

### Archetype Usage

```bash
# Interactive mode (opens editor with template)
resume new work-unit --archetype greenfield

# Non-interactive (LLM-optimized) - requires title and position
resume new work-unit --archetype incident \
  --title "Resolved P1 database outage" \
  --position-id pos-techcorp-engineer \
  --no-edit

# With inline position creation
resume new work-unit --archetype optimization \
  --title "Reduced API latency by 60%" \
  --position "TechCorp|Senior Engineer|2022-01|" \
  --no-edit
```

### When to Use Each Archetype

| User Describes... | Recommended Archetype |
|-------------------|----------------------|
| "I built a new system/feature" | `greenfield` |
| "I fixed a production issue" | `incident` |
| "I improved performance/reduced costs" | `optimization` |
| "I migrated to a new platform" | `migration` |
| "I grew/led a team" | `leadership` |
| "I led a major company initiative" | `transformation` |
| "I defined strategy/architecture" | `strategic` |
| "I improved team culture/DEI" | `cultural` |
| "Quick note, will add details later" | `minimal` |

---

## Board Role Management

For executive resumes - track board positions and advisory roles.

### Commands

| Command | Description |
|---------|-------------|
| `resume new board-role` | Create board role (interactive or pipe-separated) |
| `resume new board-role "Org\|Role\|Type\|Start\|End\|Focus"` | Inline creation |
| `resume list board-roles` | List all board and advisory roles |
| `resume show board-role <org>` | Show board role details (partial match) |
| `resume remove board-role <org>` | Remove by organization name (partial match) |

### Board Role Types

| Type | Description |
|------|-------------|
| `director` | Board of Directors position |
| `advisory` | Advisory board or technical advisor |
| `committee` | Committee member |

### Pipe-Separated Format

```bash
resume new board-role "CyberShield Ventures|Technical Advisor|advisory|2022-03||AI/ML strategy"
```

---

## Publication Management

Track publications, conference talks, and speaking engagements. Supports JD-relevant curation via topics and abstracts.

### Commands

| Command | Description |
|---------|-------------|
| `resume new publication` | Create publication (interactive or pipe-separated) |
| `resume new publication "Title\|Type\|Venue\|Date\|URL"` | Inline creation |
| `resume new publication --topic python --topic aws` | Create with topic tags |
| `resume new publication --abstract "..."` | Create with abstract for semantic matching |
| `resume list publications` | List all publications and speaking engagements |
| `resume show publication <title>` | Show publication details (partial match) |
| `resume remove publication <title>` | Remove by title (partial match) |

### Publication Creation Flags

| Flag | Description |
|------|-------------|
| `--topic, -t` | Topic tag for JD matching (repeatable) |
| `--abstract, -a` | Brief description for semantic matching (max 500 chars) |

### Publication Types

| Type | Description |
|------|-------------|
| `conference` | Conference presentation |
| `article` | Published article |
| `whitepaper` | Technical whitepaper |
| `book` | Book or book chapter |
| `podcast` | Podcast appearance |
| `webinar` | Webinar presentation |

### Pipe-Separated Format

```bash
# Basic format
resume new publication "Zero Trust Architecture|conference|RSA Conference|2022-06|"

# Extended format with topics and abstract
resume new publication "Zero Trust Architecture|conference|RSA Conference|2022-06||kubernetes,security|Deep dive into zero trust patterns."
```

Extended format: `"Title|Type|Venue|Date|URL|Topics|Abstract"` where Topics is comma-separated.

### JD-Relevant Curation

When building with `--jd`, publications are scored and filtered by relevance:

- **40% semantic similarity** - Abstract + title + venue vs JD text
- **40% topic overlap** - Topics matched against JD skills/keywords
- **20% recency bonus** - Publications in last 3 years preferred

Configure in `.resume.yaml`:
```yaml
curation:
  publications_max: 3        # Max publications to include (default: 3)
  min_relevance_score: 0.1   # Minimum score threshold (default: 0.1)
```

---

## Career Highlight Management

Top-line achievements for executive summary sections.

### Commands

| Command | Description |
|---------|-------------|
| `resume new highlight --text "..."` | Create highlight (non-interactive) |
| `resume new highlight` | Create highlight (interactive) |
| `resume list highlights` | List all career highlights |
| `resume show highlight <index>` | Show highlight by index (0-indexed) |
| `resume remove highlight <index>` | Remove highlight by index (0-indexed) |

### Example

```bash
resume new highlight --text "Led digital transformation generating \$50M revenue through AI/ML initiatives"
```

---

## Cache Management

Manage the embedding cache used for semantic matching.

### Commands

| Command | Description |
|---------|-------------|
| `resume cache stats` | Show cache statistics (entries, size) |
| `resume cache clear` | Clear stale or all cache entries |

---

## AI Agent Workflows

### Initializing New Project

```bash
# Quick setup with placeholders (non-interactive)
resume init --non-interactive

# Check if already initialized
resume config
```

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

### Common Patterns

| User Request | Agent Action |
|--------------|--------------|
| "Start a new resume project" | Initialize: `resume init --non-interactive` |
| "Add my job history" | Create positions: `resume new position "..."` |
| "I just accomplished something" | Quick capture: `resume new work-unit --position "..."` |
| "Generate resume for this job" | `resume plan --jd file.txt && resume build` |

---

## Complete Example: Building Resume from Scratch

### Non-Interactive (LLM-optimized)

```bash
# 1. Initialize project (creates .resume.yaml, work-units/, positions.yaml)
resume init --non-interactive

# 2. Create positions (your job history)
resume new position "TechCorp|Senior Engineer|2022-01|"
resume new position "StartupXYZ|Software Developer|2019-06|2021-12"

# 3. Add work units (achievements)
resume new work-unit \
  --position-id pos-techcorp-senior-engineer \
  --title "Reduced deployment time by 80%" \
  --problem "Manual deployments took 4 hours" \
  --action "Built CI/CD pipeline with GitHub Actions" \
  --result "Deployments now take 48 minutes"

# 4. Validate and generate
resume validate                                    # Validate all resources
resume validate work-units --check-positions       # Validate work units with position refs
resume plan --jd job-description.txt
resume build --jd job-description.txt
```

### Interactive (Human-friendly)

```bash
# 1. Initialize project (prompts for profile info)
resume init

# 2. Create position (prompts for each field)
resume new position

# 3. Create work unit (opens editor with template)
resume new work-unit --archetype greenfield

# 4. Validate and generate
resume validate                                    # Validate all resources
resume plan --jd job-description.txt
resume build --jd job-description.txt
```

---

## Troubleshooting

### "Work unit has no position" warning

Work units can optionally reference positions. To resolve:
1. Check existing positions: `resume list positions`
2. If position exists, add `position_id` to work unit YAML
3. If not, create position: `resume new position "..."`

### Position ID lookup

```bash
# Find position ID for employer
resume --json list positions | jq '.data[] | select(.employer | contains("TechCorp"))'
```

---

## CLI Resource Management Pattern

When implementing new resource types (models stored in `.resume.yaml` or external files), **always implement all four CRUD commands** for consistency:

### Required Commands (CRUD)

| Command | Pattern | Description |
|---------|---------|-------------|
| `new <resource>` | `resume new <resource>` | Create (interactive + pipe-separated) |
| `list <resources>` | `resume list <resources>` | List all (plural subcommand name) |
| `show <resource>` | `resume show <resource> <id>` | Show details of one |
| `remove <resource>` | `resume remove <resource> <id>` | Delete one |

### Implementation Checklist

For each new resource type, implement:

1. **`new` subcommand** in `commands/new.py`
   - Interactive mode with Rich prompts
   - Non-interactive mode with `--field` flags
   - Pipe-separated format: `"Field1|Field2|Field3"`
   - Validation before saving

2. **`list` subcommand** in `commands/list_cmd.py`
   - Rich table output (human-friendly)
   - JSON output via `--json` flag
   - Count summary at bottom

3. **`show` subcommand** in `commands/show.py`
   - Detailed view of single resource
   - Rich formatted output
   - JSON output via `--json` flag
   - Related resources (e.g., work units for position)

4. **`remove` subcommand** in `commands/remove.py`
   - Confirmation prompt (unless `--force`)
   - Partial match support for name-based lookups
   - Exit code 4 (NOT_FOUND) if resource doesn't exist

### Current Resource Coverage

| Resource | `new` | `list` | `show` | `remove` | Notes |
|----------|:-----:|:------:|:------:|:--------:|-------|
| work-unit | ✓ | ✓ | ✓ | ✓ | Complete |
| position | ✓ | ✓ | ✓ | ✓ | Complete |
| certification | ✓ | ✓ | ✓ | ✓ | Complete |
| education | ✓ | ✓ | ✓ | ✓ | Complete |
| board-role | ✓ | ✓ | ✓ | ✓ | Complete |
| publication | ✓ | ✓ | ✓ | ✓ | Complete |
| highlight | ✓ | ✓ | ✓ | ✓ | Complete |

### Naming Conventions

- Subcommand names use **singular** form: `new position`, `show certification`
- List subcommand uses **plural** form: `list positions`, `list certifications`
- Resource IDs use slug format: `pos-employer-title`, `wu-YYYY-MM-DD-slug`

### Pipe-Separated Format

For LLM-optimized non-interactive creation:

```bash
# Pattern: "Required1|Required2|Optional1|Optional2"
resume new position "Employer|Title|Start|End"
resume new certification "Name|Issuer|Date|Expires"
resume new education "Degree|Institution|Year|Honors"
resume new board-role "Org|Role|Type|Start|End|Focus"
resume new publication "Title|Type|Venue|Date|URL"
resume new publication "Title|Type|Venue|Date|URL|Topics|Abstract"  # Extended format
# highlight uses --text flag instead:
resume new highlight --text "Achievement text here"
```

- Empty trailing fields can be omitted
- Use empty string for optional middle fields: `"Name|Issuer||Expires"`
- Publication topics are comma-separated: `"...|python,aws,kubernetes|..."`

<!-- Keep CLAUDE.md in sync when adding new commands. Update Quick Reference table and add workflow examples. -->
