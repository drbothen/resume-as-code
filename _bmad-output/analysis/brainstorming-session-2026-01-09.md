---
stepsCompleted: [1, 2, 3, 4]
inputDocuments: []
session_topic: 'Resume as Code - comprehensive exploration of data format, templating, export, features, architecture, and UX'
session_goals: 'Generate research-worthy ideas across data formats, feature possibilities, and technical approaches'
selected_approach: 'ai-recommended'
techniques_used: ['First Principles Thinking', 'Morphological Analysis', 'Cross-Pollination']
ideas_generated: 25
themes_identified: 7
research_items: 18
context_file: 'project-context-template.md'
project_context: 'Personal tool - single user, own resume stored in repo'
session_active: false
workflow_completed: true
---

# Brainstorming Session Results

**Facilitator:** Joshua Magady
**Date:** 2026-01-09
**Project:** Resume as Code

---

## Session Overview

**Topic:** Resume as Code - comprehensive exploration of data format, templating, export, features, architecture, and UX

**Goals:** Generate research-worthy ideas across data formats, feature possibilities, and technical approaches

### Context

- **Project Type:** Personal productivity tool
- **Scope:** Single-user (Joshua's own resume)
- **Key Concept:** Machine-readable, git-native resume storage with template-based export to Word/PDF
- **Future Enhancement:** Semi-tailored versions for different job applications

### Approach

- **Method:** AI-Recommended Techniques
- **Techniques Used:** First Principles Thinking → Morphological Analysis → Cross-Pollination

---

## Technique 1: First Principles Thinking

### Core Discovery: The Work Unit Atom

Traditional resume atoms (roles, jobs, bullets, skills) fail because they're either too coarse, too abstract, or lack causality.

**The Right Atom:** A **Work Unit** - "a documented instance of applied capability that produced measurable or narratable change."

### Work Unit Schema (Draft)

```yaml
id: wu-2023-ccmp-ingest
context:
  domain: industrial cybersecurity
  system: MSS ingestion pipeline
  constraints:
    - safety-critical
    - regulated environment
    - limited headcount
problem:
  statement: >
    Client telemetry ingestion was inconsistent and brittle,
    causing missed detections and analyst rework.
inputs:
  signals:
    - client requirements
    - tool limitations
    - alert volume metrics
actions:
  - designed vector-based ingestion pipeline
  - implemented schema normalization
  - introduced IaC-based deployment
skills_demonstrated:
  - systems architecture
  - OT security
  - infrastructure as code
  - data engineering
outputs:
  artifacts:
    - ingestion pipeline
    - deployment code
    - runbooks
outcomes:
  impact:
    - 40% reduction in ingestion failures
    - improved alert fidelity
    - faster client onboarding
evidence:
  - repo: git://mss/ingestion
  - doc: confluence://runbook
time:
  started: 2023-02
  ended: 2023-05
```

### Key Insights

| Insight | Implication |
|---------|-------------|
| **Resume = Query, not document** | Output is a view; source is the graph |
| **Value is emergent** | Skills, seniority, narrative emerge from aggregating Work Units |
| **Career = Graph** | Not a list of jobs, but a queryable graph of applied capabilities |
| **Litmus Test** | "Would this prove value without job titles?" |

---

## Technique 2: Morphological Analysis

### Parameters Explored (8 Dimensions)

| Parameter | Decision |
|-----------|----------|
| **Data Format** | YAML |
| **Storage Structure** | One file per Work Unit, flat + naming convention |
| **Template Engine** | Jinja2 + HTML/CSS → PDF |
| **Output Formats** | PDF, Word, HTML |
| **Query Mechanism** | Natural language + JD input |
| **Tailoring Approach** | JD matching + weight/scoring |
| **Tooling Language** | Python |
| **AI Integration** | Full pipeline + MCP server |

### Storage Convention

```
/work-units/
  wu_2024-06-15_ccmp_ingestion-hardening__ot-telemetry.yaml
  wu_2025-01-03_ai-triage-agent__alert-routing.yaml
```

**Rules:**
- Flat now, year-sharded later only if 1k+ files
- Never by domain (tags are your folders)
- Filename for humans, ID for machines
- Primary keys live inside YAML

### MVP vs Future Scope

| Stage | MVP | Future |
|-------|-----|--------|
| **Capture** | Raw input → Work Unit YAML + suggested tags | |
| **Selection** | Score/rank Work Units against JD (explainable) | |
| **Generation** | Selected units → PDF/HTML/DOCX | |
| **Translation** | Light rewriting, style profiles | |
| **Gap Analysis** | | Requires competency model |
| **Coaching** | | Path inference, recommendations |

### MCP Server Tools

**Read (must-have):**
- `list_work_units(filters)` - date, tags, domains, impact-type
- `get_work_unit(id)` - fetch details

**Write (MVP, gated):**
- `draft_work_unit(raw_input, sources=[])` - returns draft + missing fields
- `validate_work_unit(yaml_or_path)` - schema + linting

**Generate (core demo):**
- `rank_work_units(jd, top_k, weights)` - ranked IDs + explanation
- `generate_resume(jd, audience, template, formats)` - artifacts + manifest

**Analysis (future):**
- `analyze_gaps(target_role|competency_model)`
- `recommend_next_work_units(strategy)`

### Critical Design Decision

> **"Explanations as first-class output"**

Every AI selection/rewrite includes a manifest:
- What was selected
- Why (signals + weights)
- What was rewritten (diff-ish)
- What was omitted and why

**This makes it auditable, not "hallucination as a service."**

---

## Technique 3: Cross-Pollination

### Domain 1: Infrastructure as Code (Terraform)

| IaC Pattern | Resume System Adaptation |
|-------------|--------------------------|
| **Plan before apply** | `resume plan --jd file.txt` - shows inclusions, exclusions, rewrites, risk flags |
| **State file** | Submission provenance - track artifact lineage (what, to whom, when, from which units) |
| **Modules** | Work Unit Archetypes - snap retroactively, not forced templates |
| **Providers** | Output Providers - PDF, DOCX, ATS-safe, LinkedIn |
| **Import** | Draft ingestion with confidence flags from LinkedIn, existing resumes |

**Meta-Pattern Stolen:**
> **Separate declaration, planning, and application.**

| Layer | Resume System |
|-------|---------------|
| Declaration | Work Units (truth) |
| Planning | Resume Plan (preview & explain) |
| Application | Generate & export artifacts |
| State | Submission provenance |

**Critical Adaptation:**
> Resumes are persuasive, not deterministic. Embrace non-determinism: multiple valid plans, tunable weights, explainability over correctness.

### Domain 2: Static Site Generators (Hugo, Jekyll)

| SSG Pattern | Resume System Adaptation |
|-------------|--------------------------|
| **Content/layout separation** | Work Units + Themes (already aligned) |
| **Front matter** | Reserved vs freeform keys in YAML |
| **Shortcodes** | Semantic components at render-time (`{{ impact_block }}`) |
| **Build pipeline** | `resume build --jd x --theme y` with `--watch` mode |
| **Themes** | Constrained presentation control (never controls content selection) |
| **Taxonomies** | Many-to-many, non-hierarchical tags (skills, domains, constraints) |
| **Data files** | `/data/skills/`, `/data/companies/` for central definitions |
| **Archetypes** | `resume new work-unit --archetype incident` |

**Critical Avoidance:**
> "Content as prose-first" - Work Units are machine-first, human-readable.

**Synthesis Insight:**
> **"Content should be boring. Rendering should be expressive."**

### Domain 3: JSON Resume & Existing Tools

**JSON Resume:** Export target, not foundation. Lossy projection for compatibility.

| Capability | JSON Resume | Work Units |
|------------|-------------|------------|
| Atomicity | Job-centric | Event-centric |
| Causality | No | Yes |
| Constraints | No | Yes |
| Evidence | No | Yes |
| Provenance | No | Yes |

**ATS Systems:** Adversarial, build constrained provider.
- Flatten Work Units into role-shaped clusters
- Duplicate keywords shamelessly
- Label honestly: "Optimized for parsing, not persuasion"

**The Gap Being Filled:**

| Traditional Tools | This System |
|-------------------|-------------|
| Resume-first | Truth-first |
| Presentation-driven | Data-driven |
| Role-centric | Event-centric |
| Prose as source | Structure as source |
| AI as copy editor | AI as query engine |
| One canonical resume | Many valid projections from one canonical truth |

---

## Idea Organization by Theme

### Theme 1: Foundational Philosophy

- Work Unit = Core Atom
- Resume = Query (output is a view)
- Value is Emergent (skills, seniority from aggregation)
- Content Boring, Rendering Expressive
- Litmus Test: "Would this prove value without job titles?"

**Positioning:** Version-controlled, queryable capability ledger with multiple render targets.

### Theme 2: Data Architecture

- Format: YAML
- Storage: One file per Work Unit, flat + naming
- Schema: Reserved keys + freeform
- Data Files: `/data/skills/`, `/data/companies/`
- Taxonomies: Many-to-many, non-hierarchical

### Theme 3: Pipeline Architecture

- Declaration → Planning → Application → State
- `resume plan` previews before generation
- `resume build` produces artifacts
- Submission provenance tracks lineage

### Theme 4: AI Integration

- Capture: Raw input → Work Unit YAML
- Selection: Rank against JD (explainable)
- Generation: Selected units → outputs
- Translation: Style profiles (exec, hiring manager, ATS)
- Explanations as first-class output

### Theme 5: MCP Server Interface

- 6 MVP tools (list, get, draft, validate, rank, generate)
- Future: search, summarize, analyze_gaps, recommend

### Theme 6: Output Providers

- PDF (Modern) - beautiful, expressive
- PDF (ATS-Safe) - single-column, keyword-dense
- DOCX - recruiter compatibility
- HTML - portfolio/web
- JSON Resume - interoperability

### Theme 7: Tooling & UX

- `resume plan` (from Terraform)
- `resume build --watch` (from SSGs)
- `resume new work-unit --archetype` (from Hugo)
- `resume import linkedin` (with confidence flags)
- Archetypes: incident, greenfield, scaling, leadership

---

## Breakthrough Concepts

| Concept | Significance |
|---------|--------------|
| **"Resume as Query"** | Transforms the entire mental model |
| **Work Unit Archetypes** | Capture accelerators + query boosters |
| **Explanations as First-Class** | Auditability, trust, transparency |
| **Submission Provenance** | Track artifact lineage without CRM scope creep |
| **Multiple Valid Projections** | Non-determinism as feature |
| **`resume plan`** | Differentiator from every resume tool |

---

## Prioritized Research Backlog

### Immediate (MVP Foundation)

| # | Item | Rationale |
|---|------|-----------|
| 1 | Finalize Work Unit YAML schema | Everything depends on this |
| 2 | Build `draft_work_unit` capture flow | "If capture sucks, nothing else matters" |
| 3 | Implement `rank_work_units` scoring | Core demo capability |
| 4 | Design `resume plan` output format | Key differentiator |
| 5 | Build PDF output provider | Primary deliverable |
| 6 | Create 2-3 Work Unit archetypes | Bootstrap content creation |

### Near-Term (Complete MVP)

| # | Item |
|---|------|
| 7 | Implement `resume build` pipeline |
| 8 | Build ATS-safe provider with constraints |
| 9 | Design submission provenance schema |
| 10 | Create archetype scaffolding (`resume new`) |
| 11 | Implement `validate_work_unit` linting |
| 12 | Build DOCX output provider |

### Future (Post-MVP)

| # | Item |
|---|------|
| 13 | JSON Resume export provider |
| 14 | LinkedIn import with confidence scoring |
| 15 | Embedding-based semantic search |
| 16 | Gap analysis with competency models |
| 17 | `--watch` mode for live preview |
| 18 | HTML portfolio provider |

---

## Session Summary

### Achievements

- **Foundational Model:** Defined Work Unit atom that's strictly more powerful than any existing resume schema
- **Architecture Decisions:** Locked 8 parameters with clear rationale
- **Pattern Library:** Stole 15+ patterns from IaC, SSGs, and existing tools
- **Research Backlog:** Created prioritized 18-item implementation roadmap
- **Positioning:** Articulated "capability ledger with render targets"

### Key Thesis

> Traditional tools help you sound impressive.
> This system helps you prove value—then decide how to present it.

### Design Principle

> Content should be boring. Rendering should be expressive.

---

## Next Steps

1. **Research Phase:** Execute `/bmad:bmm:workflows:research` to investigate existing tools, data formats, and technical approaches
2. **Product Brief:** Execute `/bmad:bmm:workflows:create-product-brief` to crystallize vision
3. **PRD:** Move to planning phase with PM agent

---

*Session facilitated using AI-Recommended techniques: First Principles Thinking → Morphological Analysis → Cross-Pollination*

*Generated by BMAD Brainstorming Workflow*
