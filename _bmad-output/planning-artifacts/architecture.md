---
stepsCompleted: [1, 2, 3, 4, 5, 6, 7, 8]
status: 'complete'
completedAt: '2026-01-10'
inputDocuments:
  - "_bmad-output/planning-artifacts/prd.md"
  - "_bmad-output/planning-artifacts/product-brief-resume-2026-01-09.md"
  - "_bmad-output/planning-artifacts/research/comprehensive-resume-as-code-research-2026-01-09.md"
  - "_bmad-output/planning-artifacts/research/research-backlog-2026-01-09.md"
  - "_bmad-output/analysis/brainstorming-session-2026-01-09.md"
workflowType: 'architecture'
project_name: 'Resume as Code'
user_name: 'Joshua Magady'
date: '2026-01-09'
---

# Architecture Decision Document

_This document builds collaboratively through step-by-step discovery. Sections are appended as we work through each architectural decision together._

---

## 1. Project Context

### 1.1 Project Overview

**Resume as Code** is a CLI-first, git-native tool that treats career data as structured, queryable truth rather than prose to be rewritten. The atomic unit is the **Work Unit** — a documented instance of applied capability with problem, actions, outputs, outcomes, and evidence.

- **Project Level:** Level 1 (Personal Tool / Greenfield)
- **Target User:** Senior technical professionals (staff engineers, architects, security leaders)
- **Core Insight:** Resumes should be queries against a capability graph, not documents to be edited.
- **Release Model:** Personal tool with potential open-source release

### 1.2 Requirements Summary

**Functional Requirements (38 total from PRD):**

| Category | Count | Key Requirements |
|----------|-------|------------------|
| Work Unit Management | 11 | YAML schema, validation, archetypes, evidence linking, listing/search |
| Resume Planning | 8 | BM25 + semantic ranking, explainability, gap analysis, terraform-style plan output |
| Resume Generation | 8 | PDF/DOCX/manifest, templates, provider abstraction |
| Configuration | 6 | Hierarchy: CLI > project > user > defaults |
| Developer Experience | 5 | Help, JSON output, exit codes, non-interactive mode |

**Non-Functional Requirements:**

| Category | Requirement |
|----------|-------------|
| Performance | <3s plan, <5s build, <1s validate, <500ms startup |
| Reliability | Deterministic builds, no data corruption, clean failures |
| Portability | macOS/Linux/Windows, Python 3.10+ |

### 1.3 Technical Constraints (Research-Validated)

| Constraint | Decision | Rationale |
|------------|----------|-----------|
| Data Format | YAML | 40% more readable than JSON, supports comments, excellent git diffs |
| Schema Validation | JSON Schema 2020-12 | Modern draft with better Unicode, `$dynamicRef`, clearer `unevaluatedProperties` |
| Model Validation | Pydantic v2 | `field_validator`, `model_validator`, discriminated unions for type-safe YAML |
| Ranking Algorithm | BM25 + Semantic (hybrid) | Combines keyword precision with conceptual understanding |
| Ranking Fusion | Reciprocal Rank Fusion (RRF) | Standard method for combining BM25 and semantic scores (2025 best practice) |
| RRF Parameter | k=60 | Experimentally determined optimal value; robust across domains (Research-Validated 2026-01-10) |
| PDF Generation | WeasyPrint | Pure Python, no browser overhead, good CSS support |
| DOCX Generation | python-docx/docxtpl | Mature, template-based, cross-platform |
| Templating | Jinja2 | Industry standard, fast, widely understood |
| Embeddings | multilingual-e5-large-instruct | Best accuracy for resume-JD matching; instruction-tuned (2025 research) |
| Embeddings (fallback) | all-MiniLM-L6-v2 | CPU-only/resource-constrained environments |
| Embedding Cache | SQLite + pickle + gzip | Fast, Python-native, 40-60% compression (Research-Validated 2026-01-10) |

### 1.3.1 Hybrid Search Implementation (Research-Validated 2026-01-10)

**RRF Fusion Formula:**
```
RRF_Score(d) = Σ (1 / (k + rank_i(d)))
```
- `k=60` provides robust balance without domain-specific tuning
- Document at rank 1 contributes: 1/61 ≈ 0.0164
- Retrieve `top_k * 2` from each method before fusion
- Use deterministic tie-breaking via secondary doc_id sort

**Embedding Model Instruction Prefixes (CRITICAL):**
| Content Type | Prefix | Example |
|--------------|--------|---------|
| Job Descriptions (indexed) | `"passage: "` | `"passage: Senior Python Developer..."` |
| Work Units (query) | `"query: "` | `"query: Built microservices architecture..."` |

**Model Specifications:**
| Model | Dimensions | Parameters | Memory (fp16) | Latency |
|-------|------------|------------|---------------|---------|
| e5-large-instruct | 1024 | 560M | ~1.1 GB | 30-50ms/query |
| all-MiniLM-L6-v2 | 384 | 22M | ~200 MB | ~15ms/query |

**Cache Key Design:**
Cache keys MUST include model hash to prevent stale embeddings:
```
cache_key = SHA256(model_hash + "::" + normalized_text)
```

**Multi-Field Embedding Strategy (Research-Validated 2026-01-10):**

Single-vector embeddings achieve only 60-70% accuracy for resume-JD matching. Multi-field embeddings with weighted scoring achieve ~95% accuracy.

| Field | Weight | Rationale |
|-------|--------|-----------|
| Experience (PAR combined) | 70% | Primary predictor of role fit |
| Education | 20% | Important for entry-level, less for senior |
| Skills | 5% | Keywords important but often inflated |
| Languages | 5% | Relevant for international roles |

**Implementation:**
```python
def compute_weighted_similarity(resume_embeddings: dict, jd_embeddings: dict) -> float:
    weights = {'experience': 0.70, 'education': 0.20, 'skills': 0.05, 'languages': 0.05}
    return sum(
        weight * cosine_similarity(resume_embeddings[field], jd_embeddings[field])
        for field, weight in weights.items()
        if field in resume_embeddings and field in jd_embeddings
    )
```

### 1.4 Content Strategy Standards (Research-Validated 2026-01-10)

Based on deep research into executive resume best practices, accomplishment framing, and recruiter preferences:

**Accomplishment Framework:**
| Standard | Decision | Rationale |
|----------|----------|-----------|
| Primary Framework | PAR (Problem-Action-Result) | VALIDATED as best practice for resume contexts (2025-2026 research) |
| Interview Framework | STAR | Better for behavioral interviews with more time |
| Executive Variant | RAS (Results-Action-Situation) | Lead with quantified impact for senior roles |
| Modern Formula | Action + Metric + Outcome | Optimized for both ATS and human readers |

**Executive Resume Standards:**
| Standard | Specification | Rationale |
|----------|---------------|-----------|
| Length | 2-3 pages for senior roles | One-page rule discredited; recruiters prefer 2-page 2.3x more |
| Layout | Single-column preferred | ATS compatibility; 94-97% parsing accuracy |
| Fonts | Sans-serif 10-12pt body | Calibri, Arial, Helvetica recommended |
| Summary | 3-5 sentences, quantified | First thing recruiters see; must establish value |

**Quantification Requirements:**
| Dimension | Description | Example |
|-----------|-------------|---------|
| Financial | Revenue, cost savings, ROI | "Drove $45M in new revenue" |
| Operational | Efficiency, cycle time, quality | "Reduced cycle time by 42%" |
| Talent | Team growth, retention, promotions | "Advanced 7 of 12 reports to senior roles" |
| Customer | Acquisition, retention, NPS | "Improved NPS from 38 to 67" |
| Organizational | Capability building, culture | "Achieved 22% engagement improvement" |

**Action Verb Standards:**
| Category | Recommended | Avoid |
|----------|-------------|-------|
| Strategic | orchestrated, spearheaded, championed, transformed | managed, handled |
| Leadership | cultivated, mentored, mobilized, aligned, unified | was responsible for |
| Impact | accelerated, revolutionized, catalyzed, pioneered | helped, worked on |

**ATS Keyword Optimization (Research-Validated 2026-01-10):**

Modern ATS systems use NLP and ML to evaluate contextual appropriateness—keyword stuffing now produces LOWER scores.

| Metric | Target Range | Warning Threshold |
|--------|--------------|-------------------|
| Keyword Density | 2-3% of word count | >3% triggers spam detection |
| Keyword Coverage | 60-80% of JD keywords | <60% fails relevance |
| Keywords per 500-word resume | 10-15 instances | >15 over-optimized |

**Keyword Placement Priority (highest to lowest):**
1. Professional Summary (3-5 most important keywords)
2. Skills Section (10-15 relevant skills with abbreviations)
3. Experience Bullets (keywords in action context)
4. Education/Certifications (full formal names)

**ATS Platform Behaviors:**
| Platform | Market Share | Key Behavior |
|----------|--------------|--------------|
| Workday | 39% Fortune 500 | NLP-based holistic suitability; ML trained on successful hires |
| Greenhouse | 19.3% | Emphasizes technical detail; rewards specific version numbers |
| Lever | 16.6% | Recognizes word stem variations; weights repeated JD terms |
| iCIMS | 15.3% | Auto-generates skills from experience bullets; tier-based ranking |

**Content Density Guidelines (Research-Validated 2026-01-10):**

Two-page resumes achieve 35% higher interview callback rate (3.45% vs 2.5%).

| Career Stage | Experience | Recommended Length | Optimal Word Count |
|--------------|------------|-------------------|-------------------|
| Entry-Level | 0-5 years | 1 page | 475-600 words |
| Mid-Career | 5-10 years | 1-2 pages | 600-1,000 words |
| Senior | 10-15 years | 2 pages | 800-1,200 words |
| Executive | 15+ years | 2-3 pages | 1,000-1,500 words |

**Bullet Point Standards:**
| Metric | Optimal Range | Research Basis |
|--------|---------------|----------------|
| Bullets per recent role | 4-6 (up to 8) | Interviewed candidates average |
| Bullets per older role (5+ yrs) | 1-2 | Focus on most relevant |
| Characters per bullet | 100-160 | Enough for action + context + result |

**Federal Government (Sept 2025 Policy):** Strict 2-page maximum for all federal positions—exceeding 2 pages = automatic disqualification.

### 1.5 Scope Decisions

| Feature | MVP Status | Notes |
|---------|------------|-------|
| Work Unit CRUD | ✅ In Scope | Core functionality |
| BM25 Ranking | ✅ In Scope | Baseline ranking |
| Semantic Ranking | ✅ In Scope | Hybrid with BM25 |
| LLM Integration | ✅ Hooks Only | Architecture supports, implementation deferred |
| PDF/DOCX Output | ✅ In Scope | Two providers minimum |
| Track Workflow | 🔌 Hooks Only | Architecture supports submission provenance |
| Skill Coverage & Gap Analysis (FR16) | ✅ In Scope | Display coverage/gaps in `resume plan` output |
| LLM-Based Gap Suggestions | ⏸️ Post-MVP | Intelligent recommendations require LLM |
| Web UI | ❌ Out of Scope | CLI-first constraint |

### 1.5 Complexity Assessment

| Factor | Level | Rationale |
|--------|-------|-----------|
| Data Model | Low | Single entity (Work Unit), flat relationships |
| Storage | Low | File-based YAML, no database |
| Business Logic | Medium | Hybrid ranking, validation rules, schema versioning |
| Integration | Medium | LLM hooks, embedding model integration |
| UI/Presentation | Low | CLI only |
| Scale | Low | Single-user, local-first |

**Overall Complexity: Low-Medium** — A well-scoped personal tool with extension points for future capability.

---

## 2. Starter Template & Project Structure

### 2.1 Primary Technology Domain

**CLI Tool (Python)** — Local-first, git-native, single-user tool with file-based storage.

### 2.2 Starter Options Evaluated

| Option | Pros | Cons | Decision |
|--------|------|------|----------|
| Modern pyproject.toml from scratch | Full control, no unused code | Manual setup | ✅ Selected |
| Cookiecutter Python CLI template | Quick scaffolding | May include unused tooling | ❌ Rejected |
| Fork existing resume tool | Existing patterns | Wrong architecture | ❌ Rejected |

**Rationale:** Resume as Code has specific, well-defined requirements. No existing cookiecutter matches this exact stack. Full control over dependency versions and structure is preferred.

### 2.3 Project Structure

```
resume-as-code/
├── pyproject.toml              # PEP 621, all config here
├── uv.lock                     # Lock file (if using uv)
├── README.md
├── LICENSE
├── .gitignore
├── .pre-commit-config.yaml
├── src/
│   └── resume_as_code/
│       ├── __init__.py
│       ├── __main__.py         # python -m resume_as_code
│       ├── cli.py              # Click app entry point
│       ├── config.py           # Configuration hierarchy
│       ├── models/
│       │   ├── __init__.py
│       │   ├── work_unit.py    # Pydantic models
│       │   └── resume.py
│       ├── services/
│       │   ├── __init__.py
│       │   ├── ranker.py       # BM25 + semantic ranking
│       │   ├── validator.py    # JSON Schema validation
│       │   └── llm.py          # LLM integration hooks
│       ├── providers/
│       │   ├── __init__.py
│       │   ├── base.py         # Abstract provider
│       │   ├── pdf.py          # WeasyPrint
│       │   ├── docx.py         # python-docx
│       │   └── ats.py          # ATS-safe variant
│       └── templates/
│           ├── modern.html           # Modern PDF template (Jinja2)
│           ├── executive.html        # Executive 2-3 page template
│           ├── ats-safe.html         # ATS-optimized single-column
│           ├── modern.css
│           ├── executive.css         # Executive styling (professional fonts)
│           └── ats-safe.css          # Minimal ATS styling
├── schemas/
│   └── work-unit.schema.json
├── archetypes/
│   ├── incident.yaml                 # Incident response archetype
│   ├── greenfield.yaml               # New project archetype
│   ├── leadership.yaml               # Leadership impact archetype
│   ├── transformation.yaml           # Executive transformation archetype
│   ├── cultural.yaml                 # Culture change archetype
│   └── strategic.yaml                # Strategic repositioning archetype
└── tests/
    ├── __init__.py
    ├── test_cli.py
    ├── test_ranker.py
    └── test_providers.py
```

### 2.4 pyproject.toml Specification

```toml
[project]
name = "resume-as-code"
version = "0.1.0"
description = "CLI tool for git-native resume generation from structured work units"
readme = "README.md"
requires-python = ">=3.10"
license = { text = "MIT" }
authors = [
  { name = "Joshua Magady" },
]
dependencies = [
  "click>=8.1",
  "pyyaml>=6.0",
  "ruamel.yaml>=0.18",
  "pydantic>=2.0",
  "jsonschema>=4.20",
  "jinja2>=3.1",
  "weasyprint>=60",
  "python-docx>=1.1",
  "docxtpl>=0.16",
  "sentence-transformers>=2.2",  # Use with multilingual-e5-large-instruct model
  "rank-bm25>=0.2",
  "rich>=13",
]

[project.scripts]
resume = "resume_as_code.cli:main"

[project.optional-dependencies]
dev = [
  "pytest>=8.0",
  "pytest-cov",
  "mypy",
  "ruff",
  "pre-commit",
]
llm = [
  "anthropic>=0.25",
  "openai>=1.0",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.ruff]
line-length = 100
target-version = "py310"

[tool.mypy]
python_version = "3.10"
strict = true
```

### 2.5 Architectural Decisions from Starter

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Language | Python 3.10+ | Per PRD portability requirement |
| CLI Framework | Click 8.1+ | Research-validated, mature, stable |
| Package Layout | `src/` layout | Modern best practice, clean imports |
| Build Backend | Hatchling | Simple, modern, minimal config |
| Type Checking | mypy (strict) | Catch errors early |
| Formatting | Ruff | Fast, replaces black+isort+flake8 |
| Testing | pytest | Industry standard |
| LLM Integration | Optional extra `[llm]` | Keeps core lightweight |

### 2.6 Initialization Commands

```bash
# Create project directory
mkdir resume-as-code && cd resume-as-code

# Initialize with uv (recommended)
uv init --lib --python 3.10

# Or with pip/venv (alternative)
python -m venv .venv && source .venv/bin/activate && pip install -e ".[dev]"

# Recommended development setup
uv sync --all-extras
```

**Note:** Project initialization using these commands should be the first implementation story.

---

## 3. Core Architectural Decisions

### 3.1 Decision Priority Analysis

**Critical Decisions (Block Implementation):**
- Work Unit storage pattern
- Schema versioning strategy
- Command structure
- Provider architecture

**Important Decisions (Shape Architecture):**
- Embedding cache strategy
- Output formatting
- LLM integration hooks

**Deferred Decisions (Post-MVP):**
- Entry point plugin system
- Standalone binary distribution
- Gap analysis algorithms

### 3.2 Data Architecture

| Decision | Choice | Rationale |
|----------|--------|-----------|
| **Storage Pattern** | File-per-Unit | Granular git history, parallel editing, clear ownership |
| **Naming Convention** | `wu-{YYYY-MM-DD}-{slug}.yaml` | Chronological sorting, human-readable |
| **Schema Versioning** | Version in document | Self-describing, read-time migration |
| **Embedding Cache** | `.resume-cache/` directory | Hidden, project-local, git-ignorable |
| **Cache Format** | SQLite + pickle + gzip | Fast retrieval, 40-60% compression |
| **Cache Invalidation** | Model hash in cache key | Automatic invalidation on model change |

**File Organization:**
```
work-units/
├── wu-2024-03-15-cloud-migration.yaml
├── wu-2024-02-10-incident-response.yaml
└── wu-2023-11-20-api-gateway.yaml

.resume-cache/
├── intfloat_multilingual-e5-large-instruct/
│   ├── cache.db              # SQLite index with model_hash column
│   └── metadata.json         # Model version, last used, entry count
└── sentence-transformers_all-MiniLM-L6-v2/
    └── ...
```

**Embedding Cache Schema (Research-Validated 2026-01-10):**
```sql
CREATE TABLE embeddings (
    cache_key TEXT PRIMARY KEY,      -- SHA256(model_hash + "::" + normalized_text)
    model_hash TEXT NOT NULL,        -- First 16 chars of model weights hash
    embedding BLOB NOT NULL,         -- gzip(pickle(numpy_array))
    timestamp REAL NOT NULL
);
CREATE INDEX idx_model_hash ON embeddings(model_hash);
```

**Cache Invalidation Strategy:**
- Model hash computed once at initialization from model weights
- Cache lookups require matching model_hash
- `resume cache clear` command removes stale entries
- Old model embeddings automatically ignored (not deleted until explicit clear)

**Work Unit Schema Extensions (Content Strategy - 2026-01-10):**

The Work Unit schema includes executive-level fields for comprehensive impact documentation:

```yaml
# Executive Scope Fields (optional but recommended for senior roles)
scope:
  budget_managed: "$X"           # P&L or budget responsibility
  team_size: N                   # Direct/indirect reports
  revenue_influenced: "$X"       # Revenue impact scope
  geographic_reach: "description" # Regions, countries, sites

# Impact Classification
impact_category:                 # One or more of:
  - financial                    # Revenue, cost, profit
  - operational                  # Efficiency, quality, speed
  - talent                       # Team growth, retention, development
  - customer                     # Acquisition, satisfaction, retention
  - organizational               # Capability, culture, transformation

# Quantification with Context
metrics:
  baseline: "description"        # Before state (required for context)
  outcome: "quantified result"   # After state with numbers
  percentage_change: N%          # Improvement percentage

# Framing Guidance
framing:
  action_verb: "spearheaded"     # Strong verb from approved list
  strategic_context: "why"       # Strategic significance statement
```

**O*NET Competency Integration (Research-Validated 2026-01-10):**

O*NET (Occupational Information Network) provides standardized competency mapping via SOC codes:

```yaml
# Skills with O*NET element mapping
skills:
  - name: "Python"
    onet_element_id: "2.A.1.a"  # Programming knowledge
    proficiency_level: 5        # O*NET uses 1-7 scale
    evidence:
      - type: "certification"
        name: "Python Institute PCAP"
```

**Confidence Fields for Partial Recall (Research-Validated 2026-01-10):**

For accomplishments from years ago where exact metrics are uncertain:

```yaml
result:
  metric: "Reduced deployment time by approximately 60%"
  confidence: "estimated"  # exact | estimated | approximate | order_of_magnitude
  confidence_note: "Exact metrics unavailable; estimate based on team recollection"
```

| Confidence Level | Usage | Validation Behavior |
|------------------|-------|---------------------|
| `exact` | Verified with documentation/evidence | No warning |
| `estimated` | Based on reasonable calculation | Info note |
| `approximate` | Rough recollection | Warning: consider refining |
| `order_of_magnitude` | Only general scale known | Warning: may lack credibility |

**Validation Extensions:**
- Weak verb detection (managed, helped, worked on → suggest stronger alternatives)
- Missing quantification warning (no numbers in outcome)
- Missing baseline context warning (outcome without before state)
- Scope completeness check for executive-level roles
- Action verb diversity check (avoid repetition across Work Units)
- Keyword density calculation (warn if outside 2-3% range)
- Content density validation (word count, bullet count, character count per bullet)
- Confidence field validation (require for older accomplishments without evidence)

### 3.3 CLI Interface Design

| Decision | Choice | Rationale |
|----------|--------|-----------|
| **Command Structure** | Flat commands | Simple, discoverable, matches PRD scope |
| **Output Formatting** | Rich + `--json` flag | Human-friendly default, machine-parseable option |
| **Exit Codes** | Semantic codes | Category-based (see table below) |

**AI Agent Compatibility (Research-Validated 2026-01-10):**

All commands MUST be optimized for AI coding assistant consumption (Claude Code, Copilot, etc.):

| Requirement | Implementation | Rationale |
|-------------|----------------|-----------|
| JSON Output | `--json` flag on ALL commands | Machine-parseable structured output |
| Non-Interactive | No prompts by default | AI agents cannot respond to prompts |
| Stdout/Stderr Separation | Results→stdout, Progress→stderr | Agents parse stdout only |
| Dry-Run Support | `--dry-run` on destructive commands | Safe agent exploration |
| Complete Help | Self-documenting `--help` | Agents discover capabilities |
| Quiet Mode | `--quiet` flag (exit code only) | Success/failure checks |

**Semantic Exit Codes:**

| Exit Code | Category | Example |
|-----------|----------|---------|
| 0 | Success | Command completed successfully |
| 1 | User error (correctable) | Invalid flag, missing required argument |
| 2 | Configuration error | Invalid config file, missing config |
| 3 | Validation error | Schema validation failed |
| 4 | Resource not found | Work unit file not found |
| 5 | System/runtime error | File I/O error, network failure |

**Standard Flags (all commands):**
```
--json              Machine-readable JSON output
--quiet, -q         Suppress output, exit code only
--verbose, -v       Detailed debug output
--help, -h          Show complete help
--version           Show version
```

**Command Surface:**
```
resume new [--archetype TYPE]     # Create Work Unit
resume validate [PATH...]         # Validate Work Units
resume list [--filter EXPR]       # List Work Units
resume plan --jd FILE             # Preview resume selection
resume build [--format FORMAT]    # Generate resume artifacts
resume config [KEY] [VALUE]       # Manage configuration
resume cache clear                # Clear stale embedding cache
resume migrate [--status|--dry-run|--rollback]  # Schema migrations
```

### 3.4 Provider Architecture

| Decision | Choice | Rationale |
|----------|--------|-----------|
| **Pattern** | Abstract base class | Simple, Python-native, sufficient for MVP |
| **Interface** | `ResumeProvider.render()` | Single responsibility |
| **Discovery** | Explicit registration | No magic, clear dependencies |

**Provider Interface:**
```python
class ResumeProvider(ABC):
    @abstractmethod
    def render(self, data: ResumeData, config: ProviderConfig) -> bytes:
        """Render resume data to output format."""
        pass

    @abstractmethod
    def validate(self, data: ResumeData) -> list[ValidationError]:
        """Validate data before rendering."""
        pass
```

**MVP Providers:**
- `PDFProvider` — WeasyPrint, modern template
- `ATSProvider` — WeasyPrint, ATS-safe template
- `DOCXProvider` — python-docx, editable format

### 3.5 LLM Integration Architecture

| Decision | Choice | Rationale |
|----------|--------|-----------|
| **Pattern** | Abstract service interface | Swap implementations, defer commitment |
| **Default** | No-op implementation | Core works without LLM |
| **Activation** | Optional `[llm]` extra | Keeps core lightweight |

**Service Interface:**
```python
class LLMService(ABC):
    @abstractmethod
    def extract_work_unit(self, raw_text: str) -> WorkUnitDraft:
        """Extract structured Work Unit from unstructured text."""
        pass

    @abstractmethod
    def rewrite_for_audience(self, content: str, audience: str) -> str:
        """Adapt content for specific audience."""
        pass

class NoOpLLMService(LLMService):
    """Default implementation that raises NotConfigured."""
    pass
```

### 3.6 Build & Distribution

| Decision | Choice | Rationale |
|----------|--------|-----------|
| **Primary** | PyPI package | Standard Python distribution |
| **Install Method** | pipx recommended | Isolated environment, global command |
| **Binary** | Deferred | Complex, large output, low priority |

**Installation:**
```bash
# Recommended
pipx install resume-as-code

# Alternative
pip install resume-as-code

# Development (uv recommended)
uv sync --all-extras
```

### 3.7 Configuration Hierarchy

| Level | Location | Precedence |
|-------|----------|------------|
| CLI flags | `--option VALUE` | Highest |
| Environment | `RESUME_*` | High |
| Project | `.resume.yaml` | Medium |
| User | `~/.config/resume-as-code/config.yaml` | Low |
| Defaults | Built-in | Lowest |

### 3.8 Schema Migration System (Story 9.1)

The schema migration system provides automatic detection and migration of outdated schemas, allowing users to upgrade without manually editing YAML files or losing data.

**Migration Framework Architecture:**

| Component | Location | Responsibility |
|-----------|----------|----------------|
| Version Constants | `migrations/__init__.py` | `CURRENT_SCHEMA_VERSION`, `LEGACY_VERSION` |
| Base Classes | `migrations/base.py` | `Migration` ABC, `MigrationResult`, `MigrationContext` |
| Registry | `migrations/registry.py` | `@register_migration` decorator, path resolution |
| Backup System | `migrations/backup.py` | Pre-migration backup, restore functionality |
| YAML Handler | `migrations/yaml_handler.py` | Comment-preserving YAML operations (ruamel.yaml) |
| CLI Command | `commands/migrate.py` | `resume migrate` with --status, --dry-run, --rollback |

**Migration Design Principles:**

| Principle | Implementation |
|-----------|----------------|
| **Idempotency** | All migrations must be safe to run multiple times |
| **Atomicity** | Migrations either fully complete or fail with backup preserved |
| **Comment Preservation** | ruamel.yaml preserves all YAML comments |
| **Manual Rollback** | Backups preserved for user-initiated `--rollback` |
| **Post-validation** | Config validated after migration to catch errors |

**Version Detection:**
```python
# Projects without schema_version field are detected as v1.0.0 (legacy)
def detect_schema_version(project_path: Path) -> str:
    config = project_path / ".resume.yaml"
    if not config.exists():
        return LEGACY_VERSION
    data = load_yaml(config)
    return data.get("schema_version", LEGACY_VERSION)
```

**Migration Path Resolution:**
```python
# Registry chains migrations automatically
# v1.0.0 → v2.0.0 → v3.0.0 applied in sequence
migrations = get_migration_path("1.0.0", "3.0.0")
# Returns [MigrationV1ToV2, MigrationV2ToV3]
```

**Backup Scope:**

The backup includes all core resume data files:
- `.resume.yaml` (config, profile, certifications, education, etc.)
- `positions.yaml` (employment history)
- `work-units/` (individual achievements)

Files NOT included (by design): `templates/`, `dist/`, `.git/`, docs

**CLI Command Options:**

| Flag | Description |
|------|-------------|
| `--status` | Show current vs latest version, migration availability |
| `--dry-run` | Preview changes without modifying files |
| `--rollback <backup>` | Restore from backup directory |
| `--json` | Machine-readable JSON output |

**Adding New Migrations:**

1. Create `migrations/v{N}_to_v{N+1}.py`
2. Implement `Migration` subclass with `check_applicable()`, `preview()`, `apply()`
3. Use `@register_migration` decorator
4. Update `CURRENT_SCHEMA_VERSION` in `migrations/__init__.py`
5. Import new migration in `migrations/__init__.py`

### 3.9 Track Workflow Hooks (Deferred)

Architecture supports future submission tracking:

```python
class SubmissionTracker(ABC):
    @abstractmethod
    def record(self, submission: Submission) -> None:
        """Record a resume submission."""
        pass

# Hook point in build command
def build_resume(...):
    # ... generate resume ...
    if tracker := get_tracker():
        tracker.record(Submission(...))
```

**Deferred to post-MVP** — architecture ready, implementation not required.

---

## 4. Implementation Patterns & Consistency Rules

### 4.1 Conflict Points Identified

| Category | Conflict Risk | Example |
|----------|---------------|---------|
| Naming | High | `work_unit.py` vs `WorkUnit.py` vs `workunit.py` |
| YAML Fields | High | `skills_demonstrated` vs `skillsDemonstrated` |
| Error Handling | Medium | Exceptions vs Result types vs return codes |
| Logging | Medium | print() vs logging module vs Rich console |
| Testing | Medium | pytest vs unittest, file location |

### 4.2 Naming Patterns

**Python Code (PEP 8 Compliant):**

| Element | Convention | Example |
|---------|------------|---------|
| Modules | snake_case | `work_unit.py`, `ranker.py` |
| Classes | PascalCase | `WorkUnit`, `ResumeProvider` |
| Functions | snake_case | `load_work_units()`, `rank_by_jd()` |
| Constants | UPPER_SNAKE | `DEFAULT_CONFIG`, `MAX_RETRIES` |
| Private | Leading underscore | `_internal_helper()` |

**YAML Fields (Work Units & Config):**

| Element | Convention | Example |
|---------|------------|---------|
| Field names | snake_case | `skills_demonstrated`, `time_ended` |
| Enum values | lowercase-hyphen | `in-progress`, `high-impact` |
| IDs | prefix-date-slug | `wu-2024-03-15-cloud-migration` |

**CLI Interface:**

| Element | Convention | Example |
|---------|------------|---------|
| Commands | lowercase | `resume plan`, `resume build` |
| Options | lowercase-hyphen | `--job-description`, `--output-format` |
| Short options | Single letter | `-j`, `-o`, `-v` |
| Env vars | UPPER_SNAKE with prefix | `RESUME_CONFIG_PATH` |

### 4.3 Structure Patterns

**Module Organization:**

```
src/resume_as_code/
├── cli.py              # Entry point only, delegates to commands
├── commands/           # One file per command group
│   ├── __init__.py
│   ├── work_unit.py    # new, validate, list
│   ├── plan.py         # plan command
│   └── build.py        # build command
├── models/             # Pydantic models only
├── services/           # Business logic
├── providers/          # Output providers
└── utils/              # Pure utility functions
```

**Test Organization:**

```
tests/
├── conftest.py         # Shared fixtures
├── test_cli.py         # CLI integration tests
├── unit/               # Unit tests mirror src/
│   ├── test_models.py
│   ├── test_ranker.py
│   └── test_validator.py
└── fixtures/           # Test data files
    ├── work-units/
    └── job-descriptions/
```

### 4.4 Format Patterns

**CLI Output (Rich):**

```python
# Success
console.print("[green]✓[/green] Work unit created: wu-2024-03-15-cloud-migration")

# Warning
console.print("[yellow]⚠[/yellow] Missing quantified outcome in wu-2024-03-15-cloud-migration")

# Error
console.print("[red]✗[/red] Validation failed: missing required field 'problem.statement'")
```

**JSON Output Mode (Research-Validated 2026-01-10):**

All JSON output MUST include `format_version` for schema evolution and AI agent compatibility:

```json
{
    "format_version": "1.0.0",
    "status": "success",
    "command": "plan",
    "timestamp": "2026-01-10T14:32:00Z",
    "data": { },
    "warnings": [],
    "errors": []
}
```

**Valid Status Values:**
| Status | Meaning |
|--------|---------|
| `success` | Command completed normally |
| `error` | Command failed with errors |
| `dry_run` | Dry-run preview (no changes made) |

**Stdout/Stderr Separation (Research-Validated 2026-01-10):**

| Stream | Content |
|--------|---------|
| stdout | Command results, data output, JSON response |
| stderr | Progress indicators, warnings, debug info |

```python
# Correct implementation
console = Console()          # stdout for results
err_console = Console(stderr=True)  # stderr for status

# In JSON mode - ONLY JSON to stdout
if json_output:
    print(json.dumps(result))  # stdout
else:
    console.print(rich_table)  # stdout

# Progress ALWAYS to stderr
err_console.print("[dim]Processing 15 work units...[/dim]")
```

**Error Objects (Research-Validated 2026-01-10):**

Enhanced structure with `recoverable` flag for AI agent retry logic:

```json
{
    "code": "VALIDATION_ERROR",
    "message": "Missing required field 'problem.statement'",
    "path": "work-units/wu-2024-03-15-api.yaml:12",
    "suggestion": "Add a problem statement describing the challenge you solved",
    "recoverable": true
}
```

| Field | Type | Description |
|-------|------|-------------|
| `code` | string | Error category identifier (VALIDATION_ERROR, CONFIG_ERROR, etc.) |
| `message` | string | Human-readable error description |
| `path` | string | File path with optional line number |
| `suggestion` | string | Actionable fix recommendation |
| `recoverable` | boolean | If true, agent can retry after fixing the issue |

### 4.5 Error Handling Patterns

**Exception Hierarchy:**

```python
class ResumeError(Exception):
    """Base exception for all resume-as-code errors."""
    exit_code: int = 1

class ValidationError(ResumeError):
    """Schema or content validation failed."""
    exit_code: int = 1

class ConfigurationError(ResumeError):
    """Configuration is invalid or missing."""
    exit_code: int = 2

class RenderError(ResumeError):
    """Output generation failed."""
    exit_code: int = 1
```

**CLI Error Handling Pattern:**

```python
@cli.command()
def plan(...):
    try:
        # ... business logic ...
    except ValidationError as e:
        console.print(f"[red]✗[/red] {e.message}")
        raise SystemExit(e.exit_code)
    except ResumeError as e:
        console.print(f"[red]Error:[/red] {e}")
        raise SystemExit(e.exit_code)
```

### 4.6 Logging Patterns

**Use Rich Console, Not logging:**

```python
from rich.console import Console

console = Console()
err_console = Console(stderr=True)

# Normal output
console.print("Processing 5 work units...")

# Verbose output (only with -v)
if verbose:
    console.print(f"[dim]Loading {path}...[/dim]")

# Errors to stderr
err_console.print("[red]Error:[/red] File not found")
```

### 4.7 Testing Patterns

**Test Naming:**

```python
# Pattern: test_{function}_{scenario}_{expected}
def test_validate_work_unit_missing_problem_raises_error():
    ...

def test_rank_work_units_returns_sorted_by_relevance():
    ...
```

**CLI Testing:**

```python
from click.testing import CliRunner

def test_plan_command_shows_selections():
    runner = CliRunner()
    result = runner.invoke(cli, ["plan", "--jd", "test.txt"])
    assert result.exit_code == 0
    assert "Work Units to Include" in result.output
```

### 4.8 Enforcement Guidelines

**All AI Agents MUST:**

1. Run `ruff check` and `ruff format` before considering code complete
2. Run `mypy --strict` with zero errors
3. Include tests for any new functionality
4. Follow the exception hierarchy for errors
5. Use Rich console for output, never print()
6. Use snake_case for all YAML fields

**Pattern Verification:**

- Pre-commit hooks run ruff + mypy
- CI runs full test suite
- Code review checks pattern compliance

---

## 5. Project Structure & Boundaries

### 5.1 Complete Project Directory Structure

```
resume-as-code/
├── .github/
│   └── workflows/
│       └── ci.yml                    # pytest + ruff + mypy on push
├── .gitignore
├── .pre-commit-config.yaml
├── LICENSE
├── README.md
├── pyproject.toml
│
├── src/
│   └── resume_as_code/
│       ├── __init__.py               # Package metadata (__version__)
│       ├── __main__.py               # python -m resume_as_code entry
│       ├── cli.py                    # Click app, command registration
│       ├── config.py                 # Configuration hierarchy loader
│       │
│       ├── commands/
│       │   ├── __init__.py
│       │   ├── new.py                # resume new [--archetype]
│       │   ├── validate.py           # resume validate [PATH...]
│       │   ├── list_cmd.py           # resume list [--filter]
│       │   ├── plan.py               # resume plan --jd FILE
│       │   ├── build.py              # resume build [--format]
│       │   └── config_cmd.py         # resume config [KEY] [VALUE]
│       │
│       ├── models/
│       │   ├── __init__.py
│       │   ├── work_unit.py          # WorkUnit Pydantic model
│       │   ├── resume.py             # ResumeData, ResumeSection
│       │   ├── job_description.py    # JobDescription model
│       │   └── config.py             # Config Pydantic models
│       │
│       ├── services/
│       │   ├── __init__.py
│       │   ├── work_unit_service.py  # CRUD operations for Work Units
│       │   ├── validator.py          # JSON Schema validation
│       │   ├── ranker.py             # BM25 + semantic hybrid ranking
│       │   ├── planner.py            # Plan generation logic
│       │   ├── embedder.py           # Embedding generation & caching
│       │   └── llm.py                # LLMService abstract + NoOp
│       │
│       ├── migrations/               # Schema migration system (Story 9.1)
│       │   ├── __init__.py           # Version constants
│       │   ├── base.py               # Migration ABC, MigrationResult, MigrationContext
│       │   ├── registry.py           # Migration registry, version detection
│       │   ├── backup.py             # Backup and restore functions
│       │   ├── yaml_handler.py       # Comment-preserving YAML (ruamel.yaml)
│       │   └── v1_to_v2.py           # First migration implementation
│       │
│       ├── providers/
│       │   ├── __init__.py
│       │   ├── base.py               # ResumeProvider ABC
│       │   ├── pdf.py                # PDFProvider (WeasyPrint)
│       │   ├── docx.py               # DOCXProvider (python-docx)
│       │   ├── ats.py                # ATSProvider (ATS-safe PDF)
│       │   └── manifest.py           # ManifestProvider (JSON metadata)
│       │
│       ├── templates/
│       │   ├── modern.html           # Modern PDF template (Jinja2)
│       │   ├── ats-safe.html         # ATS-optimized template
│       │   ├── modern.css            # PDF styling
│       │   └── ats-safe.css          # Minimal ATS styling
│       │
│       └── utils/
│           ├── __init__.py
│           ├── console.py            # Rich console singleton
│           ├── paths.py              # Path resolution utilities
│           └── yaml_io.py            # YAML read/write with ruamel
│
├── schemas/
│   ├── work-unit.schema.json         # JSON Schema v1
│   └── config.schema.json            # Configuration schema
│
├── archetypes/
│   ├── incident.yaml                 # Incident response archetype
│   ├── greenfield.yaml               # New project archetype
│   ├── migration.yaml                # Migration project archetype
│   ├── leadership.yaml               # Leadership impact archetype
│   └── optimization.yaml             # Performance/cost archetype
│
├── tests/
│   ├── __init__.py
│   ├── conftest.py                   # Shared pytest fixtures
│   ├── test_cli.py                   # CLI integration tests
│   │
│   ├── unit/
│   │   ├── __init__.py
│   │   ├── test_work_unit.py         # WorkUnit model tests
│   │   ├── test_validator.py         # Validation tests
│   │   ├── test_ranker.py            # Ranking algorithm tests
│   │   ├── test_embedder.py          # Embedding tests
│   │   └── test_providers.py         # Provider tests
│   │
│   └── fixtures/
│       ├── work-units/
│       │   ├── valid-complete.yaml   # Full valid Work Unit
│       │   ├── valid-minimal.yaml    # Minimal valid Work Unit
│       │   └── invalid-missing.yaml  # Missing required fields
│       └── job-descriptions/
│           ├── staff-engineer.txt
│           └── security-lead.txt
│
└── docs/
    └── schemas/                      # Schema documentation (auto-generated)
```

### 5.2 Architectural Boundaries

**Command Layer Boundary:**
- Commands in `commands/` delegate to services
- Commands handle CLI I/O only (parsing, output formatting)
- Commands never contain business logic
- All commands use shared `utils/console.py` for output

**Service Layer Boundary:**
- Services in `services/` own all business logic
- Services are independent of CLI (testable in isolation)
- Services communicate via Pydantic models only
- No direct file I/O except through `work_unit_service.py`

**Provider Layer Boundary:**
- Providers in `providers/` handle output format generation
- Providers receive `ResumeData` model, return `bytes`
- Providers are stateless and interchangeable
- Template loading is provider responsibility

**Model Layer Boundary:**
- Models in `models/` are pure data structures
- Models handle validation via Pydantic
- No business logic in models
- Models are the contract between layers

### 5.3 Requirements to Structure Mapping

**FR Category: Work Unit Management (11 requirements)**

| Requirement | Primary Location | Secondary |
|-------------|------------------|-----------|
| FR-WUM-001: YAML format | `models/work_unit.py` | `utils/yaml_io.py` |
| FR-WUM-002: JSON Schema | `schemas/work-unit.schema.json` | `services/validator.py` |
| FR-WUM-003: Archetypes | `archetypes/*.yaml` | `commands/new.py` |
| FR-WUM-004: Evidence linking | `models/work_unit.py` | — |
| FR-WUM-005: Create command | `commands/new.py` | `services/work_unit_service.py` |
| FR-WUM-006: Validate command | `commands/validate.py` | `services/validator.py` |
| FR-WUM-007-011: List/Search | `commands/list_cmd.py` | `services/work_unit_service.py` |

**FR Category: Resume Planning (8 requirements)**

| Requirement | Primary Location | Secondary |
|-------------|------------------|-----------|
| FR-PLAN-001: Relevance ranking | `services/ranker.py` | — |
| FR-PLAN-002: BM25 ranking | `services/ranker.py` | — |
| FR-PLAN-003: Semantic ranking | `services/embedder.py` | `services/ranker.py` |
| FR-PLAN-004: Explainability | `services/planner.py` | `commands/plan.py` |
| FR-PLAN-005: Preview mode | `commands/plan.py` | — |
| FR-PLAN-006-008: Plan output | `commands/plan.py` | `models/resume.py` |

**FR Category: Resume Generation (8 requirements)**

| Requirement | Primary Location | Secondary |
|-------------|------------------|-----------|
| FR-GEN-001: PDF output | `providers/pdf.py` | `templates/modern.*` |
| FR-GEN-002: DOCX output | `providers/docx.py` | — |
| FR-GEN-003: Template system | `templates/*.html` | `providers/base.py` |
| FR-GEN-004: Provider abstraction | `providers/base.py` | — |
| FR-GEN-005-008: Build command | `commands/build.py` | `providers/*.py` |

**FR Category: Configuration (6 requirements)**

| Requirement | Primary Location | Secondary |
|-------------|------------------|-----------|
| FR-CFG-001-006: Config hierarchy | `config.py` | `models/config.py` |

**FR Category: Developer Experience (5 requirements)**

| Requirement | Primary Location | Secondary |
|-------------|------------------|-----------|
| FR-DX-001: Help | `cli.py` | All `commands/*.py` |
| FR-DX-002: JSON output | `utils/console.py` | All commands |
| FR-DX-003: Exit codes | All `commands/*.py` | `models/errors.py` |
| FR-DX-004-005: Non-interactive | `cli.py` | — |

### 5.4 Cross-Cutting Concerns

**Error Handling:**
```
models/errors.py → Exception hierarchy
commands/*.py → Catch and format errors
utils/console.py → Error display formatting
```

**Configuration:**
```
config.py → Load hierarchy
models/config.py → Config validation
commands/config_cmd.py → User interface
~/.config/resume-as-code/config.yaml → User config file
.resume.yaml → Project config file
```

**Embedding Cache:**
```
.resume-cache/
├── embeddings.pkl → Cached embeddings (gitignored)
└── manifest.json → Cache metadata

services/embedder.py → Cache management
```

### 5.5 Integration Points

**Internal Data Flow:**
```
Job Description (text)
        ↓
   [planner.py] → parse JD
        ↓
work-units/*.yaml
        ↓
   [ranker.py] → BM25 scores
        ↓
   [embedder.py] → semantic scores
        ↓
   [planner.py] → combine, select, explain
        ↓
   ResumeData model
        ↓
   [providers/*.py] → render
        ↓
   PDF/DOCX/Manifest output
```

**External Integrations (Deferred):**
- LLM Service: `services/llm.py` → Anthropic/OpenAI APIs
- Track Workflow: `services/tracker.py` (future) → Submission storage

### 5.6 File Organization Patterns

**Configuration Files (Root):**
- `pyproject.toml` — Single source of truth for project config
- `.pre-commit-config.yaml` — Git hooks
- `.gitignore` — Excludes `.resume-cache/`, `*.egg-info`, etc.

**Source Organization:**
- One command file per CLI command
- One model file per domain concept
- One service file per capability
- One provider file per output format

**Test Organization:**
- `test_cli.py` — Integration tests via CliRunner
- `unit/*.py` — Mirror src/ structure
- `fixtures/` — Reusable test data

### 5.7 Development Workflow Integration

**Local Development:**
```bash
uv sync --all-extras        # Install dependencies
uv run pytest               # Run tests
uv run ruff check . --fix   # Lint and fix
uv run mypy src             # Type check
```

**Pre-commit Hooks:**
```yaml
# .pre-commit-config.yaml
repos:
  - repo: local
    hooks:
      - id: ruff
        name: ruff
        entry: ruff check --fix
        language: system
        types: [python]
      - id: mypy
        name: mypy
        entry: mypy src
        language: system
        pass_filenames: false
```

**CI Pipeline:**
```yaml
# .github/workflows/ci.yml
- ruff check src tests
- mypy src --strict
- pytest --cov=resume_as_code
```

---

## 6. Architecture Validation Results

### 6.1 Coherence Validation ✅

**Decision Compatibility:**
All technology choices form a coherent Python CLI stack:
- Python 3.10+ → Click 8.1+ → Pydantic 2.0+ → WeasyPrint 60+
- All libraries are actively maintained and commonly used together
- No conflicting dependencies identified

**Pattern Consistency:**
- PEP 8 naming conventions align with Python ecosystem standards
- snake_case YAML fields match Python attribute conventions
- Rich console output aligns with modern CLI best practices
- pytest patterns are industry standard

**Structure Alignment:**
- src/ layout supports clean packaging and imports
- Service layer isolation enables unit testing
- Provider abstraction supports future output formats
- Clear separation between CLI, business logic, and I/O

### 6.2 Requirements Coverage Validation ✅

**Functional Requirements (38 total):**

| Category | Count | Coverage |
|----------|-------|----------|
| Work Unit Management | 11 | 100% |
| Resume Planning | 8 | 100% |
| Resume Generation | 8 | 100% |
| Configuration | 6 | 100% |
| Developer Experience | 5 | 100% |

**Non-Functional Requirements:**

| NFR | Architectural Support |
|-----|----------------------|
| Performance (<3s plan) | Embedding cache, BM25 pre-indexing |
| Performance (<5s build) | WeasyPrint (no browser), template caching |
| Performance (<1s validate) | Local JSON Schema, no network calls |
| Reliability | Deterministic file operations, atomic writes |
| Portability | Pure Python, no system dependencies except fonts |

### 6.3 Implementation Readiness Validation ✅

**Decision Completeness:**
- All 8 critical decisions documented with versions
- Rationale provided for each decision
- Deferred decisions explicitly marked (binary dist, gap analysis)

**Structure Completeness:**
- Complete project tree with 40+ files defined
- Every file has a clear purpose annotation
- All directories have explicit organization rules

**Pattern Completeness:**
- Naming conventions cover Python, YAML, CLI, and env vars
- Error handling hierarchy defined with exit codes
- Testing patterns with naming conventions and fixtures
- Logging patterns with Rich console integration

### 6.4 Gap Analysis Results

**Critical Gaps:** None identified

**Important Gaps (address early in implementation):**

1. **Work Unit Schema**: First implementation story should create `schemas/work-unit.schema.json` with all fields
2. **Archetype Definitions**: Define which fields each archetype pre-fills

**Nice-to-Have (post-MVP):**
- Pre-commit hook for work unit validation
- VS Code workspace settings
- Development container definition

### 6.5 Architecture Completeness Checklist

**✅ Requirements Analysis**
- [x] Project context thoroughly analyzed (Level 1, Personal Tool)
- [x] Scale and complexity assessed (Low-Medium)
- [x] Technical constraints identified (Python 3.10+, CLI-first)
- [x] Cross-cutting concerns mapped (config, errors, logging)

**✅ Architectural Decisions**
- [x] Critical decisions documented with versions
- [x] Technology stack fully specified (pyproject.toml)
- [x] Integration patterns defined (Provider ABC, LLM Service)
- [x] Performance considerations addressed (caching, lazy load)

**✅ Implementation Patterns**
- [x] Naming conventions established (PEP 8, snake_case YAML)
- [x] Structure patterns defined (one file per concern)
- [x] Communication patterns specified (models as contracts)
- [x] Process patterns documented (error hierarchy, Rich output)

**✅ Project Structure**
- [x] Complete directory structure defined
- [x] Component boundaries established (4-layer architecture)
- [x] Integration points mapped (internal data flow)
- [x] Requirements to structure mapping complete (all 38 FRs)

### 6.6 Architecture Readiness Assessment

**Overall Status:** ✅ READY FOR IMPLEMENTATION

**Confidence Level:** HIGH

**Key Strengths:**
1. Clean separation of concerns (Command → Service → Model → Provider)
2. Testable in isolation (services independent of CLI)
3. Extensible (Provider ABC, LLM Service hooks)
4. Well-documented patterns prevent AI agent conflicts
5. All 38 functional requirements mapped to specific files

**Areas for Future Enhancement:**
1. Plugin system for custom providers (post-MVP)
2. Binary distribution with PyInstaller (if demand exists)
3. Gap analysis algorithms for missing skills (Phase 2)

### 6.7 Implementation Handoff

**AI Agent Guidelines:**

1. Follow all architectural decisions exactly as documented
2. Use implementation patterns consistently across all components
3. Respect project structure and layer boundaries
4. Run `ruff check` and `mypy --strict` before completing any task
5. Use Rich console for all output, never print()
6. Follow the exception hierarchy for all errors

**First Implementation Priority:**
```bash
# 1. Initialize project structure
mkdir resume-as-code && cd resume-as-code
uv init --lib --python 3.10

# 2. Create pyproject.toml per Section 2.4
# 3. Create src/resume_as_code/ package structure
# 4. Create schemas/work-unit.schema.json
```

**Implementation Sequence:**
1. Project scaffolding + pyproject.toml
2. Work Unit schema + Pydantic models
3. CLI skeleton with Click
4. `resume new` + `resume validate` commands
5. `resume plan` with BM25 ranking
6. `resume build` with PDF provider
7. Semantic ranking integration
8. DOCX provider + ATS variant

---

## 7. Architecture Completion Summary

### Workflow Completion

**Architecture Decision Workflow:** COMPLETED ✅
**Total Steps Completed:** 8
**Date Completed:** 2026-01-10
**Document Location:** `_bmad-output/planning-artifacts/architecture.md`

### Final Architecture Deliverables

**Complete Architecture Document**
- All architectural decisions documented with specific versions
- Implementation patterns ensuring AI agent consistency
- Complete project structure with all files and directories
- Requirements to architecture mapping
- Validation confirming coherence and completeness

**Implementation Ready Foundation**
- 8 core architectural decisions made
- 6 implementation pattern categories defined
- 4 architectural layers specified (Command → Service → Model → Provider)
- 38 functional requirements fully supported

**AI Agent Implementation Guide**
- Technology stack with verified versions (Python 3.10+, Click 8.1+, Pydantic 2.0+)
- Consistency rules that prevent implementation conflicts
- Project structure with clear boundaries
- Integration patterns and communication standards

### Quality Assurance Checklist

**✅ Architecture Coherence**
- [x] All decisions work together without conflicts
- [x] Technology choices are compatible
- [x] Patterns support the architectural decisions
- [x] Structure aligns with all choices

**✅ Requirements Coverage**
- [x] All 38 functional requirements are supported
- [x] All non-functional requirements are addressed
- [x] Cross-cutting concerns are handled
- [x] Integration points are defined

**✅ Implementation Readiness**
- [x] Decisions are specific and actionable
- [x] Patterns prevent agent conflicts
- [x] Structure is complete and unambiguous
- [x] Examples are provided for clarity

---

**Architecture Status:** READY FOR IMPLEMENTATION ✅

**Next Phase:** Begin implementation using the architectural decisions and patterns documented herein.

**Document Maintenance:** Update this architecture when major technical decisions are made during implementation.

