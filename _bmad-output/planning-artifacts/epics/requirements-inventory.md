# Requirements Inventory

## Functional Requirements

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

## NonFunctional Requirements

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

## Additional Requirements

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

## FR Coverage Map

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
