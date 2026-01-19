<p align="center">
  <img src="https://raw.githubusercontent.com/drbothen/resume-as-code/main/assets/brand/lockup-horizontal.png" alt="Resume as Code" width="280">
</p>

<p align="center">
  <a href="https://pypi.org/project/resume-as-code/"><img alt="PyPI - Version" src="https://img.shields.io/pypi/v/resume-as-code?color=blue"></a>
  <a href="https://pypi.org/project/resume-as-code/"><img alt="PyPI - Python Version" src="https://img.shields.io/pypi/pyversions/resume-as-code"></a>
  <a href="https://github.com/drbothen/resume-as-code/blob/main/LICENSE"><img alt="License" src="https://img.shields.io/github/license/drbothen/resume-as-code"></a>
</p>

# Resume as Code

> Treat your career data as structured, queryable truth.

CLI tool for git-native resume generation from structured Work Units.

## The Philosophy

Your career accomplishments are **immutable facts** — what you've done doesn't change. But every job application requires a different view of your experience.

Resume as Code inverts the traditional model: instead of editing documents, you maintain structured **Work Units** and generate targeted resumes as **queries** against your capability graph. The resume becomes a view, not a source of truth.

[Read the full philosophy](./docs/philosophy.md)

## Features

- **Work Unit Capture** — Record accomplishments with Problem-Action-Result structure and archetype templates
- **Schema Validation** — Ensure data quality with actionable feedback on weak verbs, missing metrics, and incomplete fields
- **Hybrid Ranking** — BM25 keyword matching + semantic similarity for intelligent Work Unit selection
- **Skill Coverage Analysis** — See which skills are covered and identify gaps before submitting
- **Multiple Output Formats** — Generate PDF and DOCX with consistent formatting
- **Executive Templates** — CTO/VP-level templates with career highlights, board roles, and publications
- **Position Management** — Track employment history with scope indicators (revenue, team size, P&L)
- **Certification Tracking** — Manage credentials with expiration status monitoring
- **Full Provenance** — Manifest tracks exactly which Work Units were included and why

## Quick Start

### Installation

**From PyPI (recommended):**

```bash
pip install resume-as-code
```

**With optional features:**

```bash
# LLM-powered features (anthropic, openai)
pip install resume-as-code[llm]

# NLP features (spacy)
pip install resume-as-code[nlp]

# All optional dependencies
pip install resume-as-code[llm,nlp]
```

**From source (development):**

```bash
git clone https://github.com/drbothen/resume-as-code
cd resume-as-code
uv sync --all-extras
```

**macOS PDF Generation** — WeasyPrint requires system libraries:

```bash
brew install pango cairo
export DYLD_LIBRARY_PATH="$(brew --prefix)/lib:$DYLD_LIBRARY_PATH"
```

### Initialize Your Resume Project

```bash
# Initialize with placeholders (non-interactive)
resume init --non-interactive

# Or interactive mode for guided setup
resume init
```

### Create Your First Work Unit

```bash
# Interactive mode with archetype template
resume new work-unit --archetype greenfield
```

### Validate Your Data

```bash
resume validate
```

### Generate a Resume

```bash
# Preview what will be selected
resume plan --jd job-description.txt

# Generate PDF and DOCX
resume build --jd job-description.txt
```

Check `dist/` for your generated resume files.

## Command Reference

### Resource Creation

| Command | Description |
|---------|-------------|
| `resume new work-unit` | Create a Work Unit (use `--archetype` for templates) |
| `resume new position` | Create an employment position |
| `resume new certification` | Add a professional certification |
| `resume new education` | Add an education entry |
| `resume new publication` | Add a publication or speaking engagement |
| `resume new board-role` | Add a board or advisory position |
| `resume new highlight` | Add a career highlight (executive format) |

### Resource Management

| Command | Description |
|---------|-------------|
| `resume list` | List all Work Units (supports filtering) |
| `resume list positions` | List employment positions |
| `resume list certifications` | List certifications with expiration status |
| `resume list education` | List education entries |
| `resume list highlights` | List career highlights |
| `resume list board-roles` | List board and advisory roles |
| `resume list publications` | List publications and speaking engagements |
| `resume show work-unit <id>` | Show Work Unit details |
| `resume show position <id>` | Show position details |
| `resume show certification <name>` | Show certification details |
| `resume show education <degree>` | Show education entry details |
| `resume show highlight <index>` | Show career highlight details |
| `resume show board-role <org>` | Show board role details |
| `resume show publication <title>` | Show publication details |
| `resume remove work-unit <id>` | Remove a Work Unit |
| `resume remove position <id>` | Remove a position |
| `resume remove certification <name>` | Remove a certification |
| `resume remove education <degree>` | Remove an education entry |
| `resume remove highlight <index>` | Remove a career highlight |
| `resume remove board-role <org>` | Remove a board role |
| `resume remove publication <title>` | Remove a publication |

**Work Unit Filtering** — The `resume list` command supports filtering:

```bash
# Filter by tag
resume list --filter tag:kubernetes

# Filter by confidence level
resume list --filter confidence:high

# Free text search (ID, title, date)
resume list --filter "migration"

# Combine filters (AND logic)
resume list --filter tag:aws --filter confidence:high
```

### Validation and Generation

| Command | Description |
|---------|-------------|
| `resume validate` | Validate Work Units against schema |
| `resume validate --content-quality` | Check weak verbs and quantification |
| `resume validate --content-density` | Check bullet point character limits |
| `resume validate --check-positions` | Verify position references exist |
| `resume plan --jd <file>` | Preview Work Unit selection for a JD |
| `resume plan --top <n>` | Select top N Work Units (default: 8) |
| `resume plan --show-excluded` | Show top 5 excluded Work Units with reasons |
| `resume plan --output <file>` | Save plan to file for later use |
| `resume plan --load <file>` | Load and display a saved plan |
| `resume build --jd <file>` | Generate resume files |
| `resume build --plan <file>` | Build from a saved plan file |
| `resume build --format <type>` | Output format: pdf, docx, or all |
| `resume build --template <name>` | Template to use (modern, executive) |

### Utility Commands

| Command | Description |
|---------|-------------|
| `resume config` | View current configuration |
| `resume config --list` | Show all config values with sources |
| `resume cache stats` | Show embedding cache statistics |
| `resume cache clear` | Clear stale cache entries |

### Schema Migration

| Command | Description |
|---------|-------------|
| `resume migrate --status` | Show current schema version and migration status |
| `resume migrate --dry-run` | Preview changes without modifying files |
| `resume migrate` | Apply schema migrations (with confirmation) |
| `resume migrate --rollback <backup>` | Restore from backup directory |

Migrations automatically detect legacy configs (no `schema_version` field) and offer to upgrade them. Backups are created before any changes.

### Global Flags

| Flag | Description |
|------|-------------|
| `--json` | Output in JSON format for scripting |
| `-v, --verbose` | Show verbose debug output |
| `-q, --quiet` | Suppress output, exit code only |
| `-y, --yes` | Skip confirmation prompts (remove commands) |

## Work Unit Archetypes

Archetypes are pre-filled templates that provide structure and guidance for common achievement types. Each archetype includes PAR (Problem-Action-Result) prompts, example text, and relevant fields.

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

### Using Archetypes

```bash
# Interactive mode (opens editor with template)
resume new work-unit --archetype greenfield

# Non-interactive with title (for LLM/scripting)
resume new work-unit --archetype incident \
  --title "Resolved P1 database outage" \
  --position-id pos-techcorp-engineer \
  --no-edit
```

## Examples

### Creating Work Units for Different Scenarios

```bash
# Project from scratch
resume new work-unit --archetype greenfield \
  --title "Built multi-region deployment platform"

# Incident response
resume new work-unit --archetype incident \
  --title "Resolved P1 outage affecting 50K users"

# Leadership/team building
resume new work-unit --archetype leadership \
  --title "Scaled engineering team from 5 to 25 engineers"

# Cost optimization
resume new work-unit --archetype optimization \
  --title "Reduced cloud spend by 40% through right-sizing"

# Platform migration
resume new work-unit --archetype migration \
  --title "Led zero-downtime migration to Kubernetes"
```

### Creating Position History

```bash
# Pipe-separated format (LLM-friendly)
resume new position "TechCorp|Senior Platform Engineer|2022-01|"

# With executive scope indicators
resume new position \
  --employer "Acme Corp" \
  --title "CTO" \
  --start-date 2020-01 \
  --scope-revenue "\$500M" \
  --scope-team-size 150 \
  --scope-pl "\$100M"
```

### Linking Work Units to Positions

```bash
# Check position IDs
resume --json list positions | jq '.[].id'

# Create work unit linked to position
resume new work-unit \
  --position-id pos-techcorp-senior-platform-engineer \
  --title "Reduced deployment time by 80%"

# Or create both together
resume new work-unit \
  --position "StartupXYZ|Lead Engineer|2023-01|" \
  --title "Led cloud migration saving \$2M annually"
```

### Using JSON Output for Scripting

```bash
# Get work units as JSON
resume --json list | jq '.data[] | .id'

# Validate and check for errors
resume --json validate
if [ $? -ne 0 ]; then echo "Validation failed"; fi

# Plan and extract selected work units
resume --json plan --jd job.txt | jq '.selected_work_units[].id'
```

### Adding Certifications and Education

```bash
# Certification with expiration
resume new certification "CISSP|ISC2|2023-06|2026-06"

# Education
resume new education "BS Computer Science|UT Austin|2012|Magna Cum Laude"
```

## Configuration

### Project Configuration (`.resume.yaml`)

```yaml
# Profile (resume header)
profile:
  name: "Your Name"
  email: "you@example.com"
  phone: "+1-555-123-4567"
  location: "Austin, TX"
  linkedin: https://linkedin.com/in/yourprofile
  github: https://github.com/yourhandle
  title: "Senior Software Engineer"

# Output settings
output_dir: ./dist
default_format: both  # pdf, docx, or both
default_template: modern

# Ranking weights (adjust for different JD styles)
scoring_weights:
  bm25_weight: 1.0      # Keyword matching
  semantic_weight: 1.0  # Meaning similarity

# Skills curation
skills:
  max_display: 15
  exclude:
    - "Microsoft Office"
  prioritize:
    - "Kubernetes"
    - "AWS"

# Executive format additions
career_highlights:
  - "Led $500M digital transformation"
  - "Built engineering org from 15 to 150"

certifications:
  - name: "AWS Solutions Architect"
    issuer: "Amazon"
    date: "2023-01"

education:
  - degree: "BS Computer Science"
    institution: "UT Austin"
    year: "2012"
```

### Configuration Hierarchy

Resume as Code loads configuration from multiple sources (highest priority first):

1. **CLI flags** — `--output-dir ./custom`
2. **Environment variables** — `RESUME_OUTPUT_DIR`
3. **Project config** — `.resume.yaml` in project root
4. **User config** — `~/.config/resume-as-code/config.yaml`
5. **Defaults** — Built-in defaults

See [Data Model Reference](./docs/data-model.md) for complete schema documentation.

## Documentation

For detailed documentation, see the [docs/](./docs/) folder:

| Document | Description |
|----------|-------------|
| [Philosophy](./docs/philosophy.md) | Why "Resume as Code" works — the data-centric approach |
| [Data Model](./docs/data-model.md) | Work Units, Positions, and entity schemas |
| [Workflow](./docs/workflow.md) | The Capture → Validate → Plan → Build pipeline |
| [Template Authoring](./docs/template-authoring.md) | Creating custom resume templates |

## Development

### Setup

```bash
# Clone repository
git clone https://github.com/drbothen/resume-as-code
cd resume-as-code

# Install dependencies
uv sync --all-extras

# Run tests
uv run pytest

# Code quality
uv run ruff check src tests --fix
uv run ruff format src tests
uv run mypy src --strict
```

### Project Structure

```
src/resume_as_code/
├── commands/     # CLI commands (Click)
├── models/       # Pydantic data models
├── services/     # Business logic
├── providers/    # Output generation (PDF, DOCX)
└── utils/        # Utility functions
```

## Contributing

### Development Workflow

1. **Fork and clone** the repository
2. **Create a feature branch** from `develop`: `git checkout -b feature/your-feature`
3. **Make changes** with tests
4. **Run quality checks**: `uv run ruff check && uv run mypy src --strict && uv run pytest`
5. **Submit a PR** to `develop`

### Code Quality Requirements

- Type hints on all public functions (`mypy --strict` must pass)
- Tests for new functionality (`pytest` with good coverage)
- Linting compliance (`ruff check` with zero errors)
- Conventional commit messages

### Commit Message Format

```
<type>(<scope>): <description>

feat(cli): add --format flag to build command
fix(ranking): handle empty job descriptions
docs(readme): add configuration examples
```

Types: `feat`, `fix`, `docs`, `style`, `refactor`, `perf`, `test`, `build`, `ci`, `chore`

### Branch Strategy

- `main` — Production releases
- `develop` — Integration branch (PR target)
- `feature/*` — New features
- `fix/*` — Bug fixes
- `spike/*` — Research and exploration
- `hotfix/*` — Emergency production fixes
- `release/*` — Release preparation

## License

MIT License — see [LICENSE](LICENSE)
