---
stepsCompleted: [1, 2, 3, 4, 5, 6]
status: complete
inputDocuments:
  - "_bmad-output/analysis/brainstorming-session-2026-01-09.md"
  - "_bmad-output/planning-artifacts/research/comprehensive-resume-as-code-research-2026-01-09.md"
  - "_bmad-output/planning-artifacts/research/research-backlog-2026-01-09.md"
date: 2026-01-09
author: Joshua Magady
---

# Product Brief: Resume as Code

## Executive Summary

**Resume as Code** is a git-native system for capturing, querying, and projecting a person's real work into credible, audience-specific narratives—without rewriting, distortion, or loss of truth.

The core insight: there is no durable, queryable representation of a person's applied capability over time. Career truth lives fragmented across PRs, docs, incident retros, performance reviews, and memory—none of it structured, durable, or reusable. Traditional resumes collapse years of nuanced work into job titles, date ranges, and bullets, destroying causality, context, constraints, and evidence. Every new job application forces manual, error-prone rewrites that drift from truth.

Resume as Code solves this by treating a career like a system, not a story. The atomic unit is a **Work Unit**—a documented instance of applied capability with problem, actions, outputs, outcomes, and evidence. Resumes become projections from this queryable truth, not the truth itself. AI serves as compiler and query engine (selecting, ranking, explaining) rather than copywriter (rewriting, hallucinating).

The primary users are senior technical professionals—staff engineers, architects, security leaders, technical founders—whose non-linear careers and systems-level impact are systematically misrepresented by traditional resume formats.

**Key differentiators:**
- **Work Unit as core atom** (not jobs) preserves causality and evidence
- **Terraform-style `plan` command** previews selections with explanations before generation
- **Explainable AI** shows why content was included, excluded, or rewritten
- **Git-native provenance** tracks artifact lineage without platform lock-in
- **Multiple valid projections** from one canonical truth

---

## Core Vision

### Problem Statement

There is no durable, queryable representation of a person's applied capability over time.

Career truth lives in too many places—PRs, docs, incident retros, performance reviews, Slack threads, notebooks, memory. None of it is structured, durable, or reusable. When it's time to communicate that value, professionals are forced to reconstruct it from fragments, losing fidelity with each translation.

### Problem Impact

**For individuals:**
- Resumes are lossy projections that destroy causality, context, constraints, and evidence
- Tailoring is manual, repetitive, and error-prone—every new JD forces a rewrite
- No system of record exists for "what I've actually done"
- Anxiety and uncertainty before applications; guessing what "sounds impressive"

**For senior technical professionals specifically:**
- Best work is contextual and invisible
- Impact is distributed across systems, not contained in roles
- Resume advice is optimized for early-career, role-linear candidates
- Non-linear careers and systems-thinking are systematically undervalued

### Why Existing Solutions Fall Short

| Solution Category | Gap |
|-------------------|-----|
| **Resume builders** (Canva, Resume.io) | Format-first; no underlying structure or intelligence |
| **AI resume tools** (Teal, Rezi) | Cosmetic rewriting; hallucination risk; no auditability |
| **JSON Resume ecosystem** | Job-centric atom; loses causality, constraints, evidence |
| **ATS optimizers** (Jobscan) | Keyword stuffing; optimizes for machines, not truth |
| **All existing tools** | No `plan` preview, no provenance tracking, no explainable selection |

The gap: every tool treats the resume as the source of truth. None treat it as a projection from a richer, queryable system.

### Proposed Solution

Resume as Code is a personal capability ledger with multiple render targets.

**Core architecture:**
- **Work Units** as the atomic unit—structured records of applied capability (problem → actions → outputs → outcomes → evidence)
- **YAML storage**, one file per Work Unit, git-native and human-readable
- **Queryable corpus** that can be filtered, ranked, and projected
- **AI-powered selection** using BM25 + semantic similarity, with full explainability
- **Multiple output providers** (PDF, DOCX, HTML, ATS-safe) from one source of truth

**Key workflows:**
1. **Capture**: Raw input → structured Work Unit YAML
2. **Plan**: `resume plan --jd file.txt` → preview inclusions, exclusions, rewrites with explanations
3. **Build**: `resume build` → generate artifacts from selected Work Units
4. **Track**: Submission provenance without CRM scope creep

**Philosophy:**
- Career as system, not story
- Resume as projection, not truth
- AI as compiler and query engine, not copywriter
- Content should be boring; rendering should be expressive

### Key Differentiators

| Differentiator | Why It Matters |
|----------------|----------------|
| **Work Unit atom** | Preserves causality, context, constraints, evidence—what job-centric models lose |
| **`resume plan` command** | Terraform-inspired preview; no other tool offers this |
| **Explainable AI** | Every selection includes why; auditable, not "hallucination as a service" |
| **Git-native provenance** | Own your data, history, and narrative; portable, not platform-locked |
| **JD-driven ranking** | Tailoring is algorithmic, not manual; consistent, not error-prone |
| **Multiple valid projections** | Non-determinism as feature; same truth, different audiences |

**Unfair advantage:** The insight that resumes should be queries against a capability graph, not documents to be edited. This reframes the entire problem space.

---

## Target Users

### Primary Users

**Persona: Alex Rivera**
*Staff Engineer / Principal-leaning Architect*

**Profile:**
Alex is a senior technical professional operating at the intersection of Platform Engineering, Security Architecture, and Distributed Systems. They've accumulated 12+ years of experience through a deliberately non-linear career trajectory: backend development → infrastructure → incident response → platform engineering → security architecture. Each transition was driven by curiosity and the work that needed doing, not a pre-planned ladder climb.

**Current Role & Context:**
- Operates at staff/principal level with systems-level impact
- Work spans organizational boundaries—influencing architecture decisions, mentoring engineers, shaping security posture, and firefighting critical incidents
- Impact is contextual, invisible, and distributed—rarely contained in a single project or role
- Responsibilities include: cross-team technical leadership, architectural decision-making, security reviews, incident command, and capability building

**Problem Experience:**
Alex's relationship with resumes is adversarial:
- **Can't tell the same story twice**: Every job description demands a different framing of the same underlying work
- **Best work resists bullet points**: The most impactful contributions—preventing disasters, shaping culture, building platforms others build on—are inherently hard to quantify
- **Tailoring feels like cognitive debt**: Each application requires mentally reconstructing "what did I actually do?" from scattered fragments
- **Context collapse**: Traditional resume formats destroy the causality, constraints, and nuance that made the work meaningful
- **Advice gap**: Resume guidance is optimized for early-career, role-linear candidates—not systems-thinkers with portfolio careers

**Current Workarounds:**
- Maintains multiple resume versions in Google Docs (with inconsistent updates)
- Dreads the "update your resume" task—knows it will take hours
- Relies on memory and improvisation during tailoring
- Accepts that the written resume will never capture their actual capability

**What Success Looks Like:**
- **Functional**: Capture work once, query it many times. Generate tailored resumes in minutes, not hours.
- **Emotional**: Confidence that the output reflects reality. No anxiety about what's missing or misrepresented.
- **Strategic**: A personal capability ledger that grows over time—owned, portable, durable.

**Key Insight:**
Alex is the "hardest customer"—if Resume as Code works for Alex's non-linear, systems-level career, it will work for the broader population of senior technical professionals.

---

### Secondary Users

**Design Constraint (Not Customer): Hiring Managers / Recruiters**
- They never touch the system—they receive its outputs
- Their expectations and ATS requirements shape output format constraints
- Understanding their scanning patterns informs rendering decisions
- They are a constraint to satisfy, not a customer to delight

**Second-Wave Users: "Future Alex"**
- Earlier-career engineers who haven't yet felt the pain of resume entropy
- They'll discover the system when they realize their career is becoming non-linear
- Lower initial urgency, but same eventual need
- May enter through simpler use cases (first job search, internal promotion case)

**Explicitly Out of Scope:**
- Entry-level candidates (simpler needs, different problem space)
- Non-technical professionals (different career ontology)
- HR/recruiters as direct users (they're downstream consumers)
- Career coaches (different workflow, advisory relationship)

---

### User Journey

**Trigger Moments:**
1. **Compelling role appears**: A job posting lands that's worth pursuing—Alex realizes their current resume doesn't tell the right story
2. **Performance/promotion cycle**: Need to articulate impact for annual review or promotion packet—evidence is scattered
3. **Career recalibration**: Transition moments (new domain, new company, new level) force reconstruction of "what have I actually done?"

**Discovery:**
Alex encounters Resume as Code through developer communities, technical blogs, or word-of-mouth from peers who share the "resume as projection, not truth" insight. The Terraform-inspired language resonates immediately.

**First Experience:**
- Runs `resume new` to scaffold their first Work Unit from a recent accomplishment
- Sees raw, unstructured input transformed into structured YAML with problem, actions, outputs, outcomes
- **First "Aha!" moment**: "Oh—this is how I should have been thinking about my work all along"

**Core Usage:**
- Captures Work Units as accomplishments happen (or during periodic reflection)
- Runs `resume plan --jd <file>` when targeting a specific role
- Reviews the selection rationale: why content was included, excluded, or reframed
- Generates tailored outputs with confidence in provenance

**Value Realization:**
- **Second "Aha!" moment**: Running a query against accumulated Work Units and seeing a coherent, tailored narrative emerge—one that Alex didn't have to manually construct
- The system "remembers" things Alex forgot, surfaces relevant work they wouldn't have thought to include
- Tailoring drops from hours to minutes

**Long-term Integration:**
- Work Unit capture becomes part of regular reflection practice
- The corpus grows into a personal capability ledger—career history as queryable data
- Resume generation becomes a non-event: query, review, export
- The anxiety around job applications transforms into confidence in preparation

---

## Success Metrics

### User Success: How Alex Knows It's Working

**Primary Success Signal:**
Alex reaches for Resume as Code *before* they're actively job searching. This is the tell—the system has become proactive infrastructure, not reactive tooling.

**Observable Behavior Changes:**

| Before | After |
|--------|-------|
| Avoids updating resume until forced | Captures work close to when it happens |
| Rewrites from scratch under time pressure | Never rewrites the same achievement twice |
| Second-guesses overselling/underselling | Treats resumes as generated artifacts, not primary documents |
| No single place represents work accurately | Uses the system proactively, not reactively |

**Concrete Deltas:**

*Time & Effort:*
- Before: 2–4 hours to update or tailor a resume; high cognitive load
- After: <10 minutes to generate a tailored resume; effort spent reviewing plan, not writing
- **Metric**: Time-to-first-draft for a new JD drops by an order of magnitude

*Coverage & Completeness:*
- Before: Resume reflects 30–50% of meaningful work; recency bias dominates
- After: Work Units accumulate; resumes pull from years of captured impact
- **Metric**: Number of captured Work Units grows steadily; new resumes reuse existing units

*Confidence & Trust:*
- Before: "I hope this sounds right"
- After: "I know exactly where this came from"
- **Metric proxies**: Rarely edits generated bullets for truth (only tone); can explain why each bullet is present; stops keeping parallel resume variants

**Workflow Integration Signals (Not Shelfware):**
- Work Units created after incidents, major projects, performance reviews
- Repo shows regular, small commits (not giant resume rewrites)
- Used for: performance reviews, promotion packets, career reflection
- **Strongest signal**: Resume as Code becomes the system of record for career—not a downstream artifact generator

---

### Business Objectives

**Project Intent: Personal Tool with Potential Release**

*If personal tool only:*
Success = permanent adoption by the builder.
- "This replaced my old resume docs"
- "I trust this more than my memory"
- "I wouldn't go back, even if no one else ever used it"

*Concrete personal success criteria:*
- ≥20–30 Work Units captured
- Multiple resumes generated from them
- Used for at least one non-job-search purpose (perf review, promotion packet)
- Mild discomfort imagining losing the repo

*If released (even quietly):*
Signal quality over vanity metrics.

**Meaningful adoption signals:**
- People fork and commit Work Units, not just star
- Issues ask about modeling work, not formatting
- PRs extend schemas, providers, or scoring—not themes
- People blog about thinking differently about their career

**Less important:**
- Raw GitHub stars
- Pretty screenshots
- "AI resume" hype

**Release success signal:**
Other senior engineers say: *"This matches how I already think about my work—I just didn't have a system for it."*

---

### Key Performance Indicators

**Must-Work-Flawlessly (Non-Negotiable):**

| Capability | Criteria |
|------------|----------|
| **Work Unit integrity** | Schema stable; validation strict; no silent mutation of source data |
| **Explainability** | Selection logic inspectable; resume plans understandable; no black-box decisions |
| **Deterministic builds** | Same inputs → same outputs; no spooky action at a distance |
| **Provider isolation** | ATS constraints never leak into core data; templates never influence selection logic |

**Nice-to-Have (Not Blocking v1):**
- Fancy scoring models
- Deep gap analysis
- UI polish
- Exotic importers

**Craft Pride Criteria:**
- Data model feels inevitable in hindsight
- System rewards precision, not verbosity
- Codebase is boring in the right places
- Entire system explainable on a whiteboard
- **Gut check**: Would trust this system to represent you in a high-stakes situation

---

### Success Definition (Anchor Statement)

> **Resume as Code is successful when it becomes the trusted, durable system of record for a person's applied capability—and resumes become disposable outputs instead of precious artifacts.**

Everything else—features, polish, release—supports that.

---

## MVP Scope

### Core Features

**Essential Workflows (Non-Negotiable):**

| Workflow | MVP Scope | What It Delivers |
|----------|-----------|------------------|
| **Capture** | Manual YAML + AI-assisted drafting + LinkedIn import + validation | First "aha!": "This is my work—cleanly represented" |
| **Plan** | Simple scoring + explainability | Selection reasoning users can inspect and trust |
| **Build** | PDF + ATS-safe providers | Credible, submittable artifacts |

**Capture (Multiple Entry Points):**
- `resume new work-unit` scaffold command (manual path)
- AI-assisted drafting from raw input (accelerated path)
- LinkedIn data import with confidence scoring (cold-start path)
- Schema validation with clear error messages
- TODOs for missing fields

*Rationale for including AI-assisted capture and LinkedIn import in MVP:*
- Both reduce friction at the critical first "aha!" moment
- LinkedIn import solves cold-start problem (bootstrapping 5-10 Work Units)
- AI-assisted capture makes ongoing capture sustainable
- Without these, capture feels like work—and adoption dies

**Plan (Explainability > Sophistication):**
- Keyword overlap (BM25-style)
- Tag matching
- Recency weighting
- *Semantic embeddings can layer in later*

**Plan output must include:**
- Selected Work Units with reasoning
- Excluded Work Units with reasoning
- Confidence flags ("weak match", "inferred skill")

*Key insight: If the plan is understandable, users forgive a dumb model. If it's opaque, they won't trust a smart one.*

**Build (Two Providers, One Template Each):**
- Human-readable PDF (for humans)
- ATS-safe text/DOCX (for machines)
- One clean, credible template per provider
- *The contrast demonstrates the system's power*

**Minimum Useful Configuration:**
- Import LinkedIn data OR capture 5–10 real Work Units manually
- Paste a JD
- See which units are chosen and why
- Produce a resume you'd actually submit

---

### Out of Scope for MVP

**Explicitly Deferred: Track Workflow**
- Submission provenance does not create the first "aha!"
- Easy to bolt on later
- Risks CRM scope creep
- **MVP substitute**: `manifest.yaml` per build (JD hash, selected units, template used) + git commits

**Hard "No" for v1:**

| Feature | Why Not |
|---------|---------|
| Gap analysis | Adds complexity, doesn't improve trust loop |
| Career level inference | Nice-to-have, not core |
| Visual UI | CLI-first is the right constraint |
| SaaS hosting | Scope explosion |
| Fancy scoring models | Explainability matters more than sophistication |
| Theme marketplaces | One template per provider is enough |
| Collaborative features | Single-user is the right constraint |

**Gut-check question for every feature idea:**
> *Does this make the system more trustworthy as a system of record—or just more impressive as a demo?*
> If it's the second, it's not MVP.

---

### MVP Success Criteria

**Two Required "Aha!" Moments (Both Needed, In Order):**

1. **First "Aha!" (Absolute Minimum):**
   - *"This is my work—cleanly and honestly represented."*
   - Triggered by: Capturing a Work Unit (via manual, AI-assisted, or import), seeing it structured, feeling relief not friction
   - *If capture doesn't feel grounding, nothing else matters*

2. **Second "Aha!" (The Hook):**
   - *"I didn't rewrite anything—and this is a better resume."*
   - Triggered by: Plan + Build together, seeing coherent reframing, trusting the output
   - *If MVP delivers only one of these, it's incomplete*

**Testable Success Gates:**
- [ ] 5–10 Work Units captured (via any path) and validated
- [ ] JD pasted, plan generated with visible reasoning
- [ ] Resume produced that you'd actually submit
- [ ] Both PDF and ATS-safe outputs work
- [ ] No manual rewriting required between plan and build

---

### Future Vision

**Post-MVP Enhancements (Ordered by Value):**

| Phase | Capability | Why It Matters |
|-------|------------|----------------|
| **v1.1** | Track workflow (submission provenance) | Closes the loop without CRM creep |
| **v1.2** | Semantic embeddings for scoring | Better matching without sacrificing explainability |
| **v2** | Gap analysis | Proactive career development |
| **v2+** | Additional themes/templates | Visual variety |
| **Future** | Portfolio/HTML provider | Public-facing capability narrative |

**Long-Term Vision:**
If wildly successful, Resume as Code becomes:
- The standard for how senior technical professionals think about and represent their careers
- A personal capability ledger that outlasts any job, platform, or format
- The system that makes "update your resume" a non-event

**Expansion Possibilities:**
- Open-source ecosystem (community Work Unit archetypes, themes, providers)
- Integration with performance review systems
- Team/org adoption for internal mobility

---

### MVP Definition (Crisp and Testable)

> **Resume as Code v1** is a CLI-first, git-native tool that lets a senior technical professional capture applied work as structured Work Units (manually, via AI-assisted drafting, or via LinkedIn import), query those units against a job description with explainable selection, and generate both ATS-safe and human-readable resumes—without rewriting or distorting the source of truth.

If v1 does that well, it succeeds.
