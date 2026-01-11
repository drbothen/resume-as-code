---
stepsCompleted: [1, 2, 3, 4, 6, 7, 8, 9, 10, 11]
inputDocuments:
  - _bmad-output/planning-artifacts/product-brief-resume-2026-01-09.md
  - _bmad-output/planning-artifacts/research/comprehensive-resume-as-code-research-2026-01-09.md
  - _bmad-output/analysis/brainstorming-session-2026-01-09.md
workflowType: 'prd'
lastStep: 11
completedDate: '2026-01-09'
---

# Product Requirements Document - Resume as Code

**Author:** Joshua Magady
**Date:** 2026-01-09
**Status:** Complete

---

## Executive Summary

Resume as Code is a personal CLI tool that transforms resume management from document editing to capability querying. Rather than maintaining static resume files, professionals store structured Work Units—atomic accomplishments with causality, constraints, and evidence—and generate tailored resumes on demand through AI-powered selection and template rendering.

The core thesis: **Traditional tools help you sound impressive. This system helps you prove value—then decide how to present it.**

### What Makes This Special

**The `resume plan` Command**

The killer insight is borrowed from Terraform: separate declaration from planning from execution.

Before generating any resume, `resume plan` shows exactly what will happen:
- Which Work Units will be included (with relevance scores)
- Which will be excluded (with reasons)
- What rewrites are proposed (with before/after)
- Which skills match vs. gap against the job description

This inserts human judgment at the critical moment—after AI analysis, before commitment. No other resume tool offers this transparency.

**Supporting Differentiators:**
- **Work Unit as Core Atom**: Events with problem/action/result structure, not job-shaped bullet points
- **Evidence-Linked Accomplishments**: Git repos, metrics dashboards, and artifacts prove claims
- **Multiple Valid Projections**: One canonical truth renders to many tailored outputs (PDF, DOCX, ATS-safe, portfolio HTML)

## Project Classification

| Dimension | Value |
|-----------|-------|
| **Technical Type** | CLI Tool (Python) |
| **Domain** | General / Personal Productivity |
| **Complexity** | Medium |
| **Project Context** | Greenfield - new project |

The CLI architecture supports both interactive workflows (Work Unit capture) and scriptable automation (CI/CD resume generation). The medium complexity reflects AI/ML integration (embeddings, BM25 ranking) balanced against well-researched technical foundations and single-user scope.

---

## Success Criteria

### User Success

**Primary Success Metric:** Consistent, voluntary usage of the tool for real job applications.

**Time Efficiency:**
| Metric | Current State | Target State |
|--------|---------------|--------------|
| Time to tailored resume | 2-3 hours | ~5 minutes |
| Reduction | - | 95%+ |

**Confidence Indicator:**
- User reviews `resume plan` output and feels informed about what's included/excluded
- No more "did I forget something?" anxiety
- Decision fatigue replaced by explainable recommendations

**The "Aha!" Moment:**
Running `resume plan` against a job description and getting a tailored resume in 5 minutes instead of 2 hours—with full visibility into why each Work Unit was selected or excluded.

### Business Success

**For MVP (Personal Tool):**
- Tool is actually used for 10-25 real job applications during an active search
- Time savings validated in practice (not just theory)

**For Future (Open Source / Productized):**
- Clean architecture that others can extend
- Documentation sufficient for community adoption
- No hard-coded personal assumptions blocking reuse

### Technical Success

- `resume plan` produces explainable, actionable output
- PDF and DOCX generation works reliably
- Work Unit schema is stable and validated
- Ranking algorithm produces sensible results against real job descriptions
- Build pipeline completes in seconds, not minutes

### Measurable Outcomes

| Outcome | Target | Validation Method |
|---------|--------|-------------------|
| Tailoring time | <5 minutes | Self-timed during real usage |
| Work Units captured | 15+ minimum | File count |
| Resume formats | PDF + DOCX | Manual verification |
| Plan explainability | Every include/exclude has a reason | Output inspection |

---

## Product Scope

### MVP - Minimum Viable Product

**Must have for MVP:**
- Work Unit YAML schema with JSON Schema validation
- File-per-unit storage with naming convention
- `resume new` - scaffold Work Unit from archetype
- `resume validate` - lint Work Units against schema
- `resume plan --jd <file>` - show what will be included/excluded with reasons
- `resume build --jd <file>` - generate PDF and DOCX
- BM25-based ranking (semantic embeddings deferred)
- 2-3 Work Unit archetypes (incident, greenfield, leadership)
- 15+ Work Units captured to validate the system

**MVP validates:** "5 minutes to tailored resume with confidence"

### Growth Features (Post-MVP)

- Semantic embeddings for smarter matching (all-MiniLM-L6-v2)
- Embedding-based semantic search across Work Units
- MCP server for Claude/AI agent integration
- Gap analysis against target roles
- ATS-safe PDF variant (single-column, keyword-optimized)
- HTML portfolio output
- Watch mode (`resume build --watch`) for live preview
- Submission provenance tracking (what sent where, when)
- Additional archetypes for faster capture
- `resume import linkedin` with confidence scoring

### Vision (Future)

- Open source release with community themes
- Productization pathway (if demand exists)
- Multi-user support (if productized)
- Integration with job boards / application tracking

---

## User Journeys

### Journey 1: The Capture — "I Don't Have to Remember This Anymore"

**Persona:** Joshua — security engineer who just closed a significant incident

**Opening Scene:**
It's late afternoon. The incident is closed. The retro doc is fresh. The metrics are still on the screen. You've just merged the final PR for the detection pipeline changes. Slack has quieted down. The adrenaline drop has hit.

You already have a terminal open—because you always do.

You're not thinking "resume." You're thinking: *"This was real work. I don't want this to evaporate."*

That's the moment. Not weeks later. Not during job hunting. Right now—while the shape of the problem is still crisp.

**The Friction Today:**
- There's no obvious place to put accomplishments (a resume doc feels wrong; a notes app feels pointless)
- The effort feels disproportionate to the moment ("I'll clean it up later" → later never comes)
- You don't know what level of detail is worth recording
- You don't trust future-you to remember the constraints, tradeoffs, or why this mattered

So the work dissolves into a vague bullet months later—or worse, nothing at all.

**The Journey with Resume as Code:**

You type without overthinking:
```
resume new work-unit
```

The tool opens a scaffolded YAML file with anchoring questions, not a form:
- What problem existed before?
- What constraint made this hard?
- What changed because of your work?

You paste a sentence from the retro, the metric you already know, maybe a link to the PR. No pressure to be elegant.

As you fill it in, something subtle happens. You see the work rendered as problem → action → outcome. Constraints made explicit. Skills emerging instead of being asserted.

And you think: *"Yeah. That's exactly what this was."*

Not pride. Not ego. **Relief.** The system gets the work.

You save, validate, commit. Total time: 5–10 minutes. While it still matters.

**Emotional Arc:** "I should remember this" → "I don't have to remember this anymore."

**Capabilities Revealed:**
- `resume new` command with archetype scaffolding
- Work Unit YAML schema with PAR structure
- Schema validation with helpful feedback
- Git-native workflow integration

---

### Journey 2: The Plan — "Do I Belong in This Room?"

**Persona:** Joshua — considering a Staff-level role shared by a respected peer

**Opening Scene:**
It's not a job board binge. It's a link from a person you respect. Or a Slack post in a private channel. Or a role mentioned casually in a meeting.

You open the JD in a browser tab. You don't scroll yet. Your reaction isn't excitement—it's calibration.

*"This is interesting. Am I actually right for this?"*

Not "can I hack my resume." **"Do I belong in this room?"**

**The Friction Today:**
- A mental inventory of half-remembered projects
- Resume variants scattered across files
- A creeping fear you'll either overreach and feel exposed, or undersell and self-reject
- The problem isn't lack of experience—it's lack of ground truth

So you either procrastinate, over-polish, or quietly close the tab.

**The Journey with Resume as Code:**

You copy the JD, save it as a file, drop into the terminal:
```
resume plan --jd senior-staff-sre.txt
```

The output isn't a resume. It's an evaluation.

**Selections with rationale:**
```
SELECTED:
- wu-2024-06-incident-response
  Match: reliability leadership, incident command
  Evidence: cross-team coordination, quantified recovery
```

Each selection answers: *"Why does this count?"*

**Exclusions (this builds trust):**
```
EXCLUDED:
- wu-2022-feature-xyz
  Reason: feature delivery, low operational scope
```

Seeing exclusions is calming. It tells you the system is not trying to flatter you.

**Coverage gaps (without judgment):**
```
WEAK SIGNALS:
- Explicit org-level technical strategy
- Multi-year system ownership
```

This is not a rejection. It's a diagnostic.

You lean back. Not because it says "yes" or "no"—but because you're no longer guessing. You know where you're strong, where the story is thin, what's real vs implied.

*"Okay. I can apply to this honestly."* Or: *"Not yet. And now I know why."*

**Emotional Arc:** Uncertainty → Clarity. The product is confidence, not resumes.

**Capabilities Revealed:**
- `resume plan` command with JD input
- Selection/exclusion with explainable rationale
- Skill coverage analysis and gap detection
- Confidence scoring for honest self-assessment

---

### Journey 3: The Recovery — "I Can Fix This"

**Persona:** Joshua — mid-application, realizing something's off

**Opening Scene:**
You run the plan. And something feels... off.

The top-ranked Work Unit isn't that important. The system didn't surface that project. Or the JD keeps saying "platform strategy" and nothing lights up.

Your gut says: *"This isn't wrong—but it's incomplete."*

This is the danger moment.

**The Friction Today:**
- Start editing bullets directly
- Copy-paste from old resumes
- Try to remember details under pressure
- Slowly detach from the truth
- Stop trusting the system—because there is no system

**The Journey with Resume as Code:**

**Case 1: Missing Work Unit**
The plan shows:
```
GAP DETECTED:
JD emphasizes: platform-level detection strategy
No Work Units directly match this scope.
```

Instead of panic:
```
resume new work-unit --from memory
```

The scaffold prompts: Timeframe? What system changed? What decision did you own?

You save it as `confidence: medium`. Now the system knows it exists.

**Case 2: Terminology Mismatch**
The JD says "SRE." Your Work Units say "platform reliability."
```
LOW MATCH CONFIDENCE:
- Terminology mismatch detected
  Suggested mapping: SRE ↔ platform reliability
```

You add a tag. Not rewriting—just aligning language.

**Case 3: Wrong Emphasis**
You realize the system emphasized something that doesn't define you. You adjust impact weight, domain tags, confidence level. Rerun the plan. The system adapts—without mutating history.

Instead of spiraling, you feel: *"Okay. I can fix this."*

No blank page. No rewrite. No lying to yourself. Just course correction.

**Emotional Arc:** Panic → Control. The system proves it's not brittle.

**Capabilities Revealed:**
- Quick Work Unit creation with `--from memory` flag
- Confidence levels for incomplete captures
- Terminology mapping and tagging
- Re-ranking without data mutation
- Gap detection with actionable guidance

---

### Journey Requirements Summary

| Journey | Core Capability | Supporting Features |
|---------|-----------------|---------------------|
| **Capture** | `resume new` with scaffolding | Archetypes, validation, git workflow |
| **Plan** | `resume plan` with explainability | Selection rationale, exclusion reasoning, gap analysis |
| **Recovery** | Quick capture + re-ranking | Confidence levels, tagging, terminology mapping |

**The Throughline:**
1. Capture happens when truth is fresh
2. Plan happens when judgment matters
3. Recovery happens without panic

**The Real Product:** Confidence under uncertainty.

---

## Innovation & Novel Patterns

### Core Innovation: `resume plan`

The killer insight is borrowed from Infrastructure as Code: **separate declaration from planning from execution**.

No resume tool in the market offers a preview of what will be generated before generation. `resume plan` is the first implementation of Terraform-style explainability applied to resume tailoring.

**Why this matters:**
- Traditional resume tools are black boxes—edit, export, hope
- `resume plan` inserts human judgment at the critical moment: after AI analysis, before commitment
- Users see exactly what's included, excluded, and why—then decide

### Paradigm Shift: Resume as Query

| Traditional Model | Resume as Code Model |
|-------------------|----------------------|
| Resume is a document | Resume is a query result |
| Tailoring = rewriting | Tailoring = selection + ranking |
| Source of truth = the .docx file | Source of truth = Work Units |
| "What sounds impressive?" | "What's relevant and true?" |

### Validation Approach

The innovation validates itself through usage:
- If `resume plan` output is sensible for real JDs → ranking works
- If users don't bypass to manual editing → the model is trusted
- If 5-minute tailoring is achieved → time savings validated

### Risk Mitigation

| Risk | Mitigation |
|------|------------|
| BM25 ranking produces poor results | Explainability makes bad outputs debuggable; user can override |
| Users don't trust AI selection | Transparency builds trust; exclusion reasoning is shown |
| Work Unit capture is too much friction | Archetypes + scaffolding reduce friction; capture happens when truth is fresh |

### Competitive Moat

This innovation is defensible because:
1. No existing tool has this architecture (validated via research)
2. The approach requires rethinking the data model (Work Units, not bullets)
3. Explainability is a feature, not an afterthought—it's built into the core loop

---

## CLI Tool Specific Requirements

### Command Structure

**Pattern:** `resume <command> [options]` (git-style, single binary)

```
resume
├── new
│   └── work-unit [--archetype <type>] [--from memory]
├── plan --jd <file> [--output <plan.yaml>]
├── build [--plan <plan.yaml>] [--jd <file>] [--output-dir <path>]
├── validate [<path>...]
├── list [--format json|table]
└── help [<command>]
```

**Why git-style:**
- Matches mental model of a *system*, not a one-off generator
- Implies state, history, and workflows
- Supports growth without fragmentation (`resume doctor`, `resume lint`, `resume export`)
- Avoids binary sprawl (no `resume-plan`, `resume-build` separate binaries)
- Clean piping and automation for Makefiles / CI / cron

**Explicitly avoid in v1:**
- Deep nesting
- Verbose aliases
- "Wizard-only" flows
- Interactive as a separate mode (interactivity happens *inside* commands)

### Configuration Hierarchy

**Override order (highest → lowest precedence):**

| Level | Location | Purpose |
|-------|----------|---------|
| CLI flags | `--output-dir ./foo` | One-off overrides |
| Project config | `.resume/config.yaml` | Git-tracked project settings |
| User/global config | `~/.config/resume/config.yaml` | Personal preferences |
| Built-in defaults | (hardcoded) | Sensible fallbacks |

**Project config (`.resume/`):**
- Git-native, travels with the repo
- Templates, taxonomies, scoring weights, output defaults
- Makes the repo the system of record

**User config (`~/.config/resume/`):**
- Personal preferences (editor, default formats)
- AI provider config (if any)
- Not checked into version control

**Invariant:** If `.resume/` exists, this is a Resume as Code project.

### Output Directory

**Default:** `./dist/`

**Why `dist/`:**
- Familiar from build tools (SSGs, JS bundlers, IaC)
- Clearly "derived artifacts"
- Easy to `.gitignore`
- Signals: safe to delete, always reproducible

**Output structure:**
```
dist/
├── resume.pdf
├── resume.docx
└── manifest.yaml
```

**Manifest file:** Critical for trust and provenance. Contains:
- Work Units included (with IDs)
- JD hash
- Timestamp
- Scoring weights used
- Template applied

**Override via:**
- CLI: `resume build --output-dir ./applications/google/`
- Config: `output.dir: ./dist`

### Scripting Support

**Design principle:** The CLI should feel like a **build tool**, not a chatbot.

| Attribute | Requirement |
|-----------|-------------|
| Predictable | Same inputs → same outputs |
| Scriptable | Clean exit codes, parseable output (`--format json`) |
| Explainable | Every decision visible via `--verbose` or plan output |
| Calm under pressure | No surprise prompts blocking automation |

**Interactivity is a layer, not the foundation.**

Interactive prompts (e.g., in `resume new`) are opt-in enhancements, never blocking for scriptable workflows.

### Implementation Considerations

**Technology stack (from research):**
- Python CLI (Click framework recommended)
- WeasyPrint for PDF generation
- python-docx for DOCX generation
- JSON Schema for Work Unit validation
- BM25 for ranking (MVP), embeddings (Growth)

**File conventions:**
- Work Units: `work-units/wu-YYYY-MM-DD-<slug>.yaml`
- Config: `.resume/config.yaml`
- Output: `dist/resume.{pdf,docx}` + `dist/manifest.yaml`

---

## Functional Requirements

### Work Unit Management

- **FR1:** User can create a new Work Unit using `resume new work-unit`
- **FR2:** User can select an archetype (incident, greenfield, leadership) when creating a Work Unit
- **FR3:** User can create a Work Unit with reduced scaffolding using `--from memory` flag
- **FR4:** System opens scaffolded YAML file in user's editor upon creation
- **FR5:** User can store Work Units as individual YAML files following naming convention `wu-YYYY-MM-DD-<slug>.yaml`
- **FR6:** User can validate Work Units against JSON Schema using `resume validate`
- **FR7:** System provides specific, actionable feedback when validation fails
- **FR8:** User can list all Work Units using `resume list`
- **FR9:** User can assign confidence levels (high, medium, low) to Work Units
- **FR10:** User can add tags/terminology mappings to Work Units
- **FR11:** User can link evidence (git repos, metrics URLs, artifacts) to Work Units

### Resume Planning

- **FR12:** User can analyze a job description against Work Units using `resume plan --jd <file>`
- **FR13:** System ranks Work Units against JD using BM25 algorithm
- **FR14:** System displays selected Work Units with relevance scores and match rationale
- **FR15:** System displays excluded Work Units with exclusion reasons
- **FR16:** System identifies skill coverage and gaps against JD requirements
- **FR17:** System proposes content rewrites with before/after comparison *(Deferred to post-MVP - requires LLM integration)*
- **FR18:** User can save plan output to file using `--output <plan.yaml>`
- **FR19:** User can re-run plan after Work Unit modifications without mutating original data

### Resume Generation

- **FR20:** User can generate resume outputs using `resume build`
- **FR21:** System generates PDF output using template rendering
- **FR22:** System generates DOCX output using template rendering
- **FR23:** User can build from a saved plan file using `--plan <plan.yaml>`
- **FR24:** User can build directly from JD using `--jd <file>` (implicit plan)
- **FR25:** System writes manifest file containing: Work Units included, JD hash, timestamp, scoring weights, template used
- **FR26:** User can specify output directory using `--output-dir <path>`
- **FR27:** System outputs to `./dist/` by default

### Configuration

- **FR28:** System reads project configuration from `.resume/config.yaml`
- **FR29:** System reads user configuration from `~/.config/resume/config.yaml`
- **FR30:** CLI flags override project config; project config overrides user config; user config overrides defaults
- **FR31:** User can configure default output directory
- **FR32:** User can configure scoring weights for ranking
- **FR33:** User can configure default template selection

### Developer Experience

- **FR34:** User can display help using `resume help` or `resume help <command>`
- **FR35:** User can output in JSON format using `--format json` for scripting
- **FR36:** System returns predictable exit codes (0 success, non-zero failure)
- **FR37:** System provides verbose output using `--verbose` flag
- **FR38:** System operates non-interactively by default (no blocking prompts in scriptable workflows)

---

## Non-Functional Requirements

### Performance

- **NFR1:** `resume plan` completes within 3 seconds for typical job descriptions
- **NFR2:** `resume build` generates PDF and DOCX within 5 seconds
- **NFR3:** `resume validate` completes within 1 second for all Work Units
- **NFR4:** CLI startup time is under 500ms

### Reliability

- **NFR5:** Same inputs always produce identical outputs (deterministic generation)
- **NFR6:** Partial failures don't corrupt existing Work Unit files
- **NFR7:** Build failures leave no partial output files in `dist/`

### Portability

- **NFR8:** CLI runs on macOS, Linux, and Windows (Python 3.10+)
- **NFR9:** No platform-specific dependencies for core functionality

---

## Out of Scope

The following are explicitly **not** part of MVP:

- Semantic embeddings and vector search (Growth feature)
- MCP server for AI agent integration (Growth feature)
- Gap analysis against target roles (Growth feature)
- ATS-safe PDF variant (Growth feature)
- HTML portfolio output (Growth feature)
- Watch mode for live preview (Growth feature)
- LinkedIn import (Growth feature)
- Multi-user support (Vision feature)
- Job board integrations (Vision feature)

---

## Dependencies and Constraints

### Technical Dependencies

- Python 3.10+ runtime
- WeasyPrint for PDF generation (requires system dependencies on some platforms)
- python-docx for DOCX generation

### Constraints

- Single-user, local-first architecture (no server component)
- File-based storage only (no database)
- BM25 ranking algorithm for MVP (no ML model inference)

---

## Open Questions

*No blocking open questions identified during discovery.*

---
