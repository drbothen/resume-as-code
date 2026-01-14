# The Resume as Code Philosophy

Resume as Code treats career data as **structured, queryable truth** rather than prose to be rewritten for each application. This document explains why that matters and how it works.

---

## The Problem with Traditional Resumes

Traditional resume management is document-centric:

```
Resume_v1.docx
Resume_v2_tech.docx
Resume_v2_tech_final.docx
Resume_v2_tech_final_FINAL.docx
Resume_v3_mgmt.docx
Resume_for_Google.docx
Resume_for_Amazon.docx
...
```

This approach creates several problems:

### No Single Source of Truth

Your accomplishments exist in dozens of slightly different documents. Which version has that metric you calculated for the Q3 project? Was it 40% or 47% improvement? Good luck finding out.

### Duplicate Effort for Each Application

Every job application means opening a document, copying bullets from other versions, rewording for the specific role, reformatting, and hoping you didn't forget something important.

### No Version Control

Documents get renamed, overwritten, and lost. There's no history, no ability to see what changed, and no way to collaborate without "Resume_v2_Josh_edits.docx" chaos.

### Accomplishments Scattered Across Versions

That achievement from three jobs ago might be in one version but not another. Over time, your best work gets lost in the document graveyard.

### Inconsistent Quality

Some bullets have metrics. Some don't. Some use strong action verbs. Some are vague. Quality depends on how much effort you put in that particular day.

---

## The Resume as Code Solution

Resume as Code inverts the traditional model:

| Traditional | Resume as Code |
|-------------|----------------|
| Documents are the source of truth | **Data** is the source of truth |
| Resumes are edited | Resumes are **generated** |
| Each application starts from scratch | Each application is a **query** |
| Accomplishments scattered | Accomplishments **centralized** |
| No history | **Git-native** history |

### Data-Centric, Not Document-Centric

Instead of maintaining documents, you maintain **Work Units** — structured records of your accomplishments. The resume is generated from this data, not edited as a document.

```yaml
# A Work Unit is a single, documented accomplishment
id: wu-2024-06-15-cicd-pipeline
title: "Reduced deployment time from 4 hours to 48 minutes"
problem:
  statement: "Manual deployment process required 4+ hours and caused frequent errors"
actions:
  - "Designed CI/CD pipeline architecture with GitHub Actions"
  - "Implemented automated testing gates with 95% coverage threshold"
  - "Created rollback automation for failed deployments"
outcome:
  result: "Reduced deployment time by 80% (4 hours → 48 minutes)"
metrics:
  time_reduced_percent: 80
  deployment_frequency: "daily vs weekly"
```

### Separation of Concerns

Resume as Code separates three distinct concerns:

1. **Data** — Your Work Units, positions, certifications (what you did)
2. **Selection** — Which accomplishments to include (what's relevant)
3. **Presentation** — How to render the output (how it looks)

This separation means you can:
- Update your data once, reflect it everywhere
- Swap selection algorithms without touching data
- Change templates without re-entering information

### Git-Native by Design

Your career data lives in version-controlled YAML files:

```
work-units/
├── wu-2024-06-15-cicd-pipeline.yaml
├── wu-2024-03-22-security-audit.yaml
├── wu-2023-11-08-team-scaling.yaml
└── ...
```

This gives you:
- **Full history** — See how your career data evolved
- **Branching** — Experiment with different career narratives
- **Diffing** — Compare versions to see what changed
- **Collaboration** — Multiple people can suggest edits via PRs

---

## Core Concepts

### Work Units: The Atomic Unit

The Work Unit is the fundamental building block — not jobs (too coarse) and not bullet points (too fine).

**Why not jobs?**
Jobs are containers, not accomplishments. "Software Engineer at Company X" tells you nothing about what was achieved.

**Why not bullet points?**
Bullet points are presentation, not data. They lack structure, context, and metadata needed for intelligent selection.

**Work Units are complete accomplishments:**
- What problem existed
- What actions you took
- What results you achieved
- What skills you demonstrated
- What metrics prove the impact

Each Work Unit is self-contained — it can stand alone on a resume without additional context.

### The PAR Framework

Every Work Unit follows the **Problem-Action-Result** framework:

| Component | Question | Example |
|-----------|----------|---------|
| **Problem** | What challenge did you face? | "Manual deployments took 4 hours" |
| **Action** | What did you do? | "Built CI/CD pipeline with GitHub Actions" |
| **Result** | What was the outcome? | "Reduced deployment time by 80%" |

This framework ensures every accomplishment tells a complete story:
- **Context** — Why it mattered (Problem)
- **Contribution** — What you did (Action)
- **Impact** — What changed (Result)

### Resumes as Queries

Here's the key insight:

**Your capability graph is fixed** — what you've done doesn't change. Your Work Units are immutable facts about your past.

**Each job description is a query** against that graph. Different jobs want different subsets of your experience.

The `resume plan` command is literally a query:

```bash
# This is a query against your capability graph
resume plan --jd senior-platform-engineer.txt
```

The output shows which Work Units best match the job requirements, with relevance scores:

```
Selected Work Units:
✓ [0.87] wu-2024-06-15-cicd-pipeline
✓ [0.82] wu-2024-03-22-security-audit
✓ [0.75] wu-2023-11-08-team-scaling
```

You're not editing a document — you're selecting from a pre-existing pool of accomplishments.

---

## Benefits

### 1. Never Lose an Accomplishment

Every Work Unit is a permanent record. Even if you don't include it in a particular resume, it exists in your repository. Years later, you can still find that metric or that project description.

### 2. Consistent Quality

Schema validation ensures every Work Unit meets minimum standards:
- Required fields are present
- Problem and result are documented
- Metrics are captured when available

You can't create a half-baked bullet point — the system enforces completeness.

### 3. Targeted Applications

The ranking algorithm (BM25 + semantic matching) finds Work Units that match each job description. You're not guessing what to include — the relevance is calculated.

### 4. Audit Trail

The manifest shows exactly what was included in each generated resume:

```yaml
# dist/manifest.yaml
generated: 2024-06-15T14:32:00Z
target_position: "Senior Platform Engineer at TechCorp"
work_units_included:
  - wu-2024-06-15-cicd-pipeline
  - wu-2024-03-22-security-audit
selection_method: "BM25 + semantic, RRF fusion"
```

You can always explain why something was or wasn't included.

### 5. AI-Ready

Structured data is machine-readable. AI assistants can:
- Suggest improvements to Work Units
- Help draft new Work Units from notes
- Identify gaps in your coverage
- Generate cover letters from selected Work Units

The YAML format makes this trivial — there's nothing to parse or interpret.

---

## The Mental Model

Think of Resume as Code like this:

| Analogy | Traditional Resume | Resume as Code |
|---------|-------------------|----------------|
| **Database** | Single denormalized table | Normalized entities |
| **Code** | Monolithic script | Modular architecture |
| **Documents** | Word doc per version | Source of truth + generation |
| **Photography** | Print per photo | RAW files + processing |

You maintain the canonical source (Work Units), then generate views (resumes) as needed. The generation is deterministic — same inputs always produce the same output.

---

## Getting Started

Ready to try it? Here's the quick path:

1. **Capture** your first Work Unit:
   ```bash
   resume new work-unit
   ```

2. **Validate** your Work Units:
   ```bash
   resume validate
   ```

3. **Plan** for a job description:
   ```bash
   resume plan --jd job-posting.txt
   ```

4. **Build** your resume:
   ```bash
   resume build --jd job-posting.txt
   ```

See the [Workflow Guide](./workflow.md) for details on each stage.

---

*Next: [Data Model](./data-model.md) — Learn the building blocks in detail.*
