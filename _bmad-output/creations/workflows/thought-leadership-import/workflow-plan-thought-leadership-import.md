---
stepsCompleted: [1, 2, 3, 4, 6, 7, 8]
---

# Workflow Creation Plan: thought-leadership-import

## Initial Project Context

- **Module:** custom
- **Target Location:** _bmad/custom/src/workflows/thought-leadership-import/
- **Created:** 2026-01-17

## Workflow Overview

**Purpose:** Import publications, speaking engagements, and board/advisory roles from external sources (git repos, markdown files, CSV lists) into resume-as-code data.

**Problem Solved:** Users with thought leadership content spread across git repos, personal websites, or event lists want to import this data without manually creating each entry.

**Target Users:** Resume-as-code users with external thought leadership content

## Key Features

1. **Git Repo Scanning** - Find markdown articles with frontmatter metadata
2. **Publication Extraction** - Identify articles, whitepapers, book chapters
3. **Speaking Detection** - Find conference talks, webinars, podcasts
4. **Board Role Import** - Import advisory and board positions
5. **Metadata Elicitation** - Ask for missing information (dates, venues, URLs)
6. **CLI Integration** - Use `resume new publication`, `resume new board-role`

## Workflow Concept

```
┌─────────────────────────────────────────────────────────────────┐
│               thought-leadership-import workflow                 │
├─────────────────────────────────────────────────────────────────┤
│  Step 1: Init                                                    │
│  ├─ Accept source path (git repo, directory, CSV file)          │
│  ├─ Scan for content (markdown files, structured data)          │
│  └─ Detect content types (articles, talks, roles)               │
├─────────────────────────────────────────────────────────────────┤
│  Step 2: Review Structure                                        │
│  ├─ Present discovered publications                              │
│  ├─ Present discovered speaking engagements                      │
│  ├─ Present discovered board roles                               │
│  └─ User confirms/edits before proceeding                        │
├─────────────────────────────────────────────────────────────────┤
│  Step 3: Process Publications (Iterative)                        │
│  ├─ For each publication, extract/elicit metadata                │
│  ├─ Confirm type (article, whitepaper, book)                     │
│  └─ Create via resume CLI with user confirmation                 │
├─────────────────────────────────────────────────────────────────┤
│  Step 4: Process Speaking (Iterative)                            │
│  ├─ For each talk, extract/elicit metadata                       │
│  ├─ Confirm type (conference, webinar, podcast)                  │
│  └─ Create via resume CLI with user confirmation                 │
├─────────────────────────────────────────────────────────────────┤
│  Step 5: Process Board Roles (Optional)                          │
│  ├─ For each role, extract/elicit metadata                       │
│  ├─ Confirm type (director, advisory, committee)                 │
│  └─ Create via resume CLI with user confirmation                 │
├─────────────────────────────────────────────────────────────────┤
│  Step 6: Finalize                                                │
│  ├─ Run validation                                               │
│  ├─ Show import summary                                          │
│  └─ Suggest next steps                                           │
└─────────────────────────────────────────────────────────────────┘
```

## Detailed Requirements

### Supported Input Sources

| Source Type | Detection Method | Content Types |
|-------------|------------------|---------------|
| Git repo with markdown | Scan for `.md` files with frontmatter | Articles, whitepapers |
| Directory of markdown | Same as git repo | Articles, whitepapers |
| CSV file | Parse columns for publication data | Any publication type |
| YAML/JSON file | Parse structured data | Any type |
| Plain text list | Line-by-line parsing | Speaking engagements |

### Publication Types (from resume CLI)

| Type | Description | Typical Source |
|------|-------------|----------------|
| `article` | Published article | Git repo markdown |
| `whitepaper` | Technical whitepaper | Git repo markdown |
| `book` | Book or book chapter | Manual entry |
| `conference` | Conference presentation | Events list |
| `webinar` | Webinar presentation | Events list |
| `podcast` | Podcast appearance | Media list |

### Board Role Types (from resume CLI)

| Type | Description |
|------|-------------|
| `director` | Board of Directors position |
| `advisory` | Advisory board or technical advisor |
| `committee` | Committee member |

### Metadata Extraction

**From Markdown Frontmatter:**
```yaml
---
title: "Building Resilient Systems"
date: 2024-03-15
tags: [architecture, resilience]
type: article
venue: "Tech Blog"  # optional
url: "https://..."   # optional
---
```

**From Filename Pattern:**
- `2024-03-15-building-resilient-systems.md` → date + title slug

**Elicitation for Missing Data:**
- Publication type (if not specified)
- Venue/publisher
- URL (if not included)
- Date (if not in frontmatter or filename)

## Tools Configuration

| Tool | Included | Purpose |
|------|----------|---------|
| File I/O | Yes | Read markdown, CSV, YAML files |
| Sidecar File | Yes | Track import progress |
| Advanced Elicitation | Yes | Fill in missing metadata |
| Web Research | Optional | Verify publication details |

## Workflow Structure

| Step | Name | Purpose | User Input |
|------|------|---------|------------|
| 1 | Init | Scan sources, detect content | Source path |
| 2 | Review | Confirm discovered items | Medium |
| 3 | Publications | Process articles/whitepapers | Per-item confirm |
| 4 | Speaking | Process talks/podcasts | Per-item confirm |
| 5 | Board Roles | Process advisory positions | Per-item confirm |
| 6 | Finalize | Validate and summarize | None |

## File Structure

```
_bmad/custom/src/workflows/thought-leadership-import/
├── workflow.md
├── steps/
│   ├── step-01-init.md
│   ├── step-02-review.md
│   ├── step-03-publications.md
│   ├── step-04-speaking.md
│   ├── step-05-board-roles.md
│   └── step-06-finalize.md
└── templates/
    └── sidecar-template.yaml
```

## Skill Registration

| Field | Value |
|-------|-------|
| **Skill ID** | `bmad:custom:workflows:thought-leadership-import` |
| **Manifest File** | `_bmad/_config/workflow-manifest.csv` |
| **Module** | custom |

### Invocation

```bash
/thought-leadership-import
```
