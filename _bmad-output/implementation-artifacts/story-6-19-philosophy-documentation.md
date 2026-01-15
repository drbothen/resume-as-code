# Story 6.19: Resume as Code Philosophy Documentation

## Story Info

- **Epic**: Epic 6 - Executive Resume Template & Profile System
- **Status**: done
- **Priority**: Medium
- **Estimation**: Medium (3-4 story points)
- **Dependencies**: None (documentation can proceed independently)

## User Story

As a **potential user or contributor discovering this project**,
I want **comprehensive documentation explaining the Resume as Code philosophy**,
So that **I understand the "why" behind the approach and can effectively use or contribute to the tool**.

## Background

### The Core Philosophy

Resume as Code treats career data as **structured, queryable truth** rather than prose to be rewritten for each application. The atomic unit is the **Work Unit** — a documented instance of applied capability with problem, actions, outputs, outcomes, and evidence.

Key insights:
- **Resumes are queries** against a capability graph, not documents to be edited
- **Work Units are immutable facts** — what you did doesn't change, only what you select
- **Git-native** — version control, branching, diffs for career data
- **Separation of concerns** — data (Work Units) vs presentation (templates) vs selection (planning)

### Why This Documentation Matters

1. **Onboarding** — New users understand the mental model before diving into commands
2. **Contribution** — Contributors understand design decisions
3. **Differentiation** — Explains why this isn't "just another resume builder"
4. **Reference** — Visual diagrams aid understanding of data flow

## Acceptance Criteria

### AC1: Documentation Folder Structure
**Given** the project repository
**When** documentation is complete
**Then** a `docs/` folder exists with:
```
docs/
├── README.md                    # Index/navigation
├── philosophy.md                # Core philosophy explanation
├── data-model.md                # Work Units, Positions, etc.
├── workflow.md                  # Capture → Plan → Build flow
├── diagrams/
│   ├── data-model.excalidraw
│   ├── data-model.svg           # Exported for markdown embedding
│   ├── workflow-pipeline.excalidraw
│   ├── workflow-pipeline.svg
│   ├── philosophy-concept.excalidraw
│   └── philosophy-concept.svg
└── images/                      # Screenshots, examples
```

### AC2: Philosophy Document
**Given** a user reads `docs/philosophy.md`
**When** they finish reading
**Then** they understand:
- The "resumes as queries" mental model
- Why Work Units are the atomic unit (not jobs, not bullet points)
- The PAR framework (Problem-Action-Result) for accomplishments
- Git-native benefits (versioning, branching, collaboration)
- Separation of data, selection, and presentation

### AC3: Data Model Diagram (Excalidraw)
**Given** the data model diagram
**When** viewed
**Then** it shows:
- **Work Unit** entity with key fields (problem, actions, outcome, metrics)
- **Position** entity with employer, title, dates
- **Certification** and **Education** entities
- **Relationships**: Work Units reference Positions (many-to-one)
- **Config** aggregation: Profile, Certifications, Education, Skills
- Color coding: entities (blue), relationships (arrows), aggregations (dashed)

### AC4: Workflow Pipeline Diagram (Excalidraw)
**Given** the workflow diagram
**When** viewed
**Then** it shows the complete pipeline:
```
┌─────────┐    ┌──────────┐    ┌──────────┐    ┌─────────┐
│ Capture │ → │ Validate │ → │   Plan   │ → │  Build  │
│  (new)  │    │(validate)│    │  (plan)  │    │ (build) │
└─────────┘    └──────────┘    └──────────┘    └─────────┘
     │              │               │               │
     ▼              ▼               ▼               ▼
  work-unit     schema OK?      JD → ranking    PDF/DOCX
   .yaml        content OK?     ↓ selected      manifest
                               WUs + scores
```
- Each stage shows: command name, input, output
- Decision points (validation pass/fail)
- Data flow arrows with labels

### AC5: Philosophy Concept Map (Excalidraw)
**Given** the philosophy concept diagram
**When** viewed
**Then** it visualizes the core insight:
```
        Traditional Approach              Resume as Code
        ──────────────────────           ─────────────────

        ┌────────────────┐               ┌─────────────────┐
        │  Resume v1.docx │              │   Work Units    │
        │  Resume v2.docx │      →       │   (immutable    │
        │  Resume v3.docx │              │    facts)       │
        └────────────────┘               └────────┬────────┘
               │                                  │
               ▼                                  ▼
        "Edit document                    "Query capability
         for each job"                    graph for each job"
                                                 │
                                                 ▼
                                         ┌──────────────┐
                                         │  plan --jd   │
                                         │  (selection) │
                                         └──────┬───────┘
                                                │
                                                ▼
                                         ┌──────────────┐
                                         │    build     │
                                         │ (generation) │
                                         └──────────────┘
```
- Contrast: document-centric vs data-centric
- Shows: immutability, querying, separation of concerns

### AC6: Data Model Document
**Given** a user reads `docs/data-model.md`
**When** they finish reading
**Then** they understand:
- Work Unit schema and required/optional fields
- Position model and how Work Units reference positions
- Certification and Education models
- Configuration hierarchy (project, user, defaults)
- Schema versioning strategy

### AC7: Workflow Document
**Given** a user reads `docs/workflow.md`
**When** they finish reading
**Then** they understand:
- The four-stage pipeline (Capture → Validate → Plan → Build)
- Each command's purpose, inputs, and outputs
- How ranking works (BM25 + semantic, RRF fusion)
- How to interpret plan output (scores, coverage, gaps)
- Output formats and provenance (manifest)

### AC8: Documentation Index
**Given** a user visits `docs/README.md`
**When** they view the page
**Then** they see:
- Quick overview of Resume as Code
- Table of contents with links to all docs
- "Getting Started" pointer to main README
- Links to diagrams with preview thumbnails

## Technical Notes

### Excalidraw Diagram Creation

Use the BMAD Excalidraw workflows for consistent diagram creation:
- `/bmad:bmm:workflows:create-excalidraw-diagram` for general architecture
- `/bmad:bmm:workflows:create-excalidraw-dataflow` for workflow pipeline

### Diagram Export

Export both `.excalidraw` (editable) and `.svg` (embeddable):
```bash
# Excalidraw CLI or manual export
# SVG for markdown embedding: ![Data Model](diagrams/data-model.svg)
```

### Philosophy.md Structure

```markdown
# The Resume as Code Philosophy

## The Problem with Traditional Resumes
- Document-centric: each resume is a new document
- No single source of truth
- Duplicate effort for each application
- No version control
- Accomplishments scattered across versions

## The Resume as Code Solution
- Data-centric: Work Units are the source of truth
- Resumes are generated, not edited
- Git-native: full history, branching, collaboration
- Separation of concerns: data vs selection vs presentation

## Core Concepts

### Work Units: The Atomic Unit
- Not jobs (too coarse)
- Not bullet points (too fine)
- A complete accomplishment with context

### The PAR Framework
- Problem: What challenge did you face?
- Action: What did you do?
- Result: What was the outcome (quantified)?

### Resumes as Queries
- Your capability graph is fixed (what you've done)
- Each job description is a query against that graph
- The plan command finds the best matches
- The build command renders the selection

## Benefits
1. **Never lose an accomplishment** — Work Units are permanent
2. **Consistent quality** — Schema validation ensures completeness
3. **Targeted applications** — Ranking optimizes for each JD
4. **Audit trail** — Manifest shows exactly what was included
5. **AI-ready** — Structured data for LLM assistance
```

### Data Model Document Structure

```markdown
# Data Model

## Overview
[Embed data-model.svg diagram]

## Work Unit
The atomic unit of career accomplishment.

### Required Fields
- `id`: Unique identifier (wu-YYYY-MM-DD-slug)
- `title`: One-line summary
- `problem.statement`: The challenge faced
- `actions`: What you did (list)
- `outcome.result`: The quantified result

### Optional Fields
- `position_id`: Reference to Position
- `tags`: Categorization keywords
- `skills_demonstrated`: Skills with proficiency
- `metrics`: Quantified impact data
- `evidence`: Links to artifacts

## Position
Employment record that Work Units reference.

### Fields
- `id`: Unique identifier (pos-employer-title)
- `employer`: Company name
- `title`: Job title
- `start_date`, `end_date`: YYYY-MM format
- `location`: Optional
- `promoted_from`: Career progression tracking

## Certification
Professional credentials.

## Education
Academic credentials.

## Configuration
Project and user settings.
```

## Tasks

### Task 1: Create Documentation Folder Structure
- [ ] Create `docs/` directory
- [ ] Create `docs/diagrams/` subdirectory
- [ ] Create `docs/images/` subdirectory
- [ ] Create `docs/README.md` index file

### Task 2: Write Philosophy Document
- [ ] Create `docs/philosophy.md`
- [ ] Write "The Problem with Traditional Resumes" section
- [ ] Write "The Resume as Code Solution" section
- [ ] Write "Core Concepts" section (Work Units, PAR, Queries)
- [ ] Write "Benefits" section
- [ ] Review for clarity and completeness

### Task 3: Create Data Model Diagram
- [ ] Use Excalidraw to create entity-relationship diagram
- [ ] Include Work Unit, Position, Certification, Education entities
- [ ] Show relationships with cardinality
- [ ] Show Config aggregation
- [ ] Export as `.excalidraw` and `.svg`
- [ ] Save to `docs/diagrams/data-model.*`

### Task 4: Create Workflow Pipeline Diagram
- [ ] Use Excalidraw to create pipeline flow diagram
- [ ] Show 4 stages: Capture → Validate → Plan → Build
- [ ] Include command names, inputs, outputs at each stage
- [ ] Show data flow between stages
- [ ] Export as `.excalidraw` and `.svg`
- [ ] Save to `docs/diagrams/workflow-pipeline.*`

### Task 5: Create Philosophy Concept Diagram
- [ ] Use Excalidraw to create concept comparison diagram
- [ ] Show traditional (document-centric) vs Resume as Code (data-centric)
- [ ] Visualize "queries against capability graph" concept
- [ ] Export as `.excalidraw` and `.svg`
- [ ] Save to `docs/diagrams/philosophy-concept.*`

### Task 6: Write Data Model Document
- [ ] Create `docs/data-model.md`
- [ ] Embed data model diagram
- [ ] Document Work Unit schema with field descriptions
- [ ] Document Position, Certification, Education models
- [ ] Document Configuration hierarchy
- [ ] Include example YAML snippets

### Task 7: Write Workflow Document
- [ ] Create `docs/workflow.md`
- [ ] Embed workflow pipeline diagram
- [ ] Document each stage with examples
- [ ] Explain ranking algorithm (BM25 + semantic, RRF)
- [ ] Explain plan output interpretation
- [ ] Document output formats and manifest

### Task 8: Complete Documentation Index
- [ ] Finalize `docs/README.md`
- [ ] Add table of contents with links
- [ ] Add diagram preview thumbnails
- [ ] Add "Getting Started" section
- [ ] Cross-link all documents

### Task 9: Update Main README
- [ ] Add link to `docs/` folder from main README.md
- [ ] Add "Documentation" section if not present
- [ ] Consider adding philosophy teaser to main README

## Definition of Done

- [ ] All documents created and complete
- [ ] All 3 Excalidraw diagrams created with SVG exports
- [ ] Documentation index links all pages
- [ ] Main README links to docs folder
- [ ] Documents render correctly on GitHub
- [ ] Spelling/grammar checked
- [ ] Technical accuracy verified against codebase

## Style Guidelines

### Writing Style
- Clear, concise prose
- Use active voice
- Explain "why" not just "what"
- Include concrete examples
- Use diagrams to supplement text

### Diagram Style
- Consistent color scheme (blue entities, gray relationships)
- Clear labels on all elements
- Left-to-right or top-to-bottom flow
- Adequate whitespace
- Accessible colors (avoid red-green only distinctions)

### Markdown Style
- Use headers consistently (# for title, ## for sections)
- Use code blocks for examples
- Use tables for structured data
- Include alt text for images

## Notes

- Diagrams should be created using Excalidraw for easy editing
- SVG exports allow embedding in markdown without external dependencies
- Consider dark mode compatibility for diagrams
- Documentation should be evergreen — avoid version-specific details that change frequently
