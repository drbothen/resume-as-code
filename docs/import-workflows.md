# Import Workflows

Resume as Code includes two BMAD workflows for importing existing career data. Use these when migrating from traditional resumes or consolidating thought leadership content.

---

## Overview

| Workflow | Slash Command | Purpose |
|----------|---------------|---------|
| **Resume Import** | `/resume-import` | Import positions, work units, certifications, education from resume documents |
| **Thought Leadership Import** | `/thought-leadership-import` | Import publications, speaking engagements, board roles from git repos and files |

---

## When to Use Import Workflows

### Resume Import

Use when you have an **existing resume document** and want to migrate to resume-as-code:

- Traditional DOCX or PDF resume
- LinkedIn profile export
- Plain text or Markdown resume
- Any document with your job history

**What it imports:**
- Employment positions (employer, title, dates)
- Work unit bullets (transformed to PAR format)
- Certifications
- Education

### Thought Leadership Import

Use when you have **external content** demonstrating industry expertise:

- Git repo with published articles (markdown files)
- Speaking engagement history (CSV, YAML, or text list)
- Board and advisory positions
- Podcast appearances

**What it imports:**
- Publications (articles, whitepapers, books)
- Speaking engagements (conferences, webinars, podcasts)
- Board/advisory roles (director, advisory, committee)

---

## Resume Import Workflow

### Supported Input Formats

| Format | Description |
|--------|-------------|
| **DOCX** | Microsoft Word documents (most common) |
| **PDF** | Portable Document Format |
| **TXT** | Plain text files |
| **Markdown** | `.md` files |
| **LinkedIn Export** | CSV files from LinkedIn data export |

### Workflow Steps

1. **Init** — Load and parse resume document
2. **Review** — Confirm extracted positions, certifications, education
3. **Create Positions** — Batch create positions via CLI
4. **Process Bullets** — Transform bullets to PAR format with elicitation
5. **Supporting Data** — Create certifications, education, career highlights
6. **Finalize** — Validate and summarize

### PAR Transformation

The workflow transforms vague resume bullets into structured PAR (Problem-Action-Result) format:

**Before (typical resume bullet):**
> "Managed cloud infrastructure and deployments"

**After (PAR format):**
- **Problem:** Legacy deployment process caused 4-hour release windows and frequent rollbacks
- **Action:** Implemented CI/CD pipeline with automated testing and blue-green deployments
- **Result:** Reduced deployment time to 15 minutes with zero-downtime releases

### Elicitation

For weak bullets (missing metrics or outcomes), the workflow asks clarifying questions:

- What challenge prompted this work?
- What was the scale or scope?
- Do you have any numbers? (%, $, time saved)
- What was the specific result or benefit?

### Example Usage

```bash
# Start the workflow (in Claude Code)
/resume-import

# Provide your resume path when prompted
~/Documents/my-resume.docx
```

---

## Thought Leadership Import Workflow

### Supported Input Sources

| Source | Detection | Content Types |
|--------|-----------|---------------|
| **Git repo** | `.md` files with YAML frontmatter | Articles, whitepapers |
| **Directory** | Markdown files | Articles, whitepapers |
| **CSV file** | Structured columns | Any publication type |
| **YAML/JSON** | Structured data | Any type |
| **Plain text** | Line-by-line | Speaking engagements |

### Workflow Steps

1. **Init** — Scan sources, detect content types
2. **Review** — Confirm discovered items, add missing entries
3. **Publications** — Import articles and whitepapers
4. **Speaking** — Import conferences, webinars, podcasts
5. **Board Roles** — Import advisory and director positions
6. **Finalize** — Validate and summarize

### Metadata Extraction

The workflow extracts metadata from markdown frontmatter:

```yaml
---
title: "Building Resilient Distributed Systems"
date: 2024-03-15
tags: [architecture, resilience, distributed-systems]
---
```

Or from filename patterns:
```
2024-03-15-building-resilient-systems.md
```

### Publication Types

| Type | Description | CLI Command |
|------|-------------|-------------|
| `article` | Blog posts, online articles | `resume new publication` |
| `whitepaper` | Technical documents | `resume new publication` |
| `book` | Books or book chapters | `resume new publication` |
| `conference` | Conference presentations | `resume new publication` |
| `webinar` | Webinar presentations | `resume new publication` |
| `podcast` | Podcast appearances | `resume new publication` |

### Board Role Types

| Type | Description | CLI Command |
|------|-------------|-------------|
| `director` | Board of Directors | `resume new board-role` |
| `advisory` | Advisory board, technical advisor | `resume new board-role` |
| `committee` | Committee membership | `resume new board-role` |

### Example Usage

```bash
# Start the workflow (in Claude Code)
/thought-leadership-import

# Provide source paths when prompted
~/repos/my-blog, ~/documents/speaking-history.csv
```

---

## Workflow Integration

Both import workflows integrate with the standard Resume as Code pipeline:

```
┌─────────────────────────────────────────────────────────────────┐
│                    IMPORT (One-time migration)                   │
│  ┌─────────────────┐    ┌──────────────────────────────┐        │
│  │ /resume-import  │    │ /thought-leadership-import   │        │
│  │                 │    │                              │        │
│  │ • Positions     │    │ • Publications               │        │
│  │ • Work Units    │    │ • Speaking                   │        │
│  │ • Certifications│    │ • Board Roles                │        │
│  │ • Education     │    │                              │        │
│  └────────┬────────┘    └──────────────┬───────────────┘        │
│           │                            │                         │
│           └────────────┬───────────────┘                         │
│                        ▼                                         │
└─────────────────────────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                    ONGOING (Regular workflow)                    │
│                                                                  │
│   Capture ──▶ Validate ──▶ Plan ──▶ Build                       │
│                                                                  │
│   resume new work-unit   resume validate   resume plan --jd     │
│   resume new publication                   resume build --jd    │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Typical Migration Flow

1. **Run `/resume-import`** with your existing resume
   - Creates positions and work units
   - Adds certifications and education

2. **Run `/thought-leadership-import`** with your content sources
   - Adds publications from blog/articles repo
   - Adds speaking engagements
   - Adds board/advisory roles

3. **Validate** the imported data
   ```bash
   resume validate --check-positions
   ```

4. **Continue with normal workflow**
   - Add new work units as accomplishments happen
   - Generate tailored resumes with `resume plan` and `resume build`

---

## Progress Tracking

Both workflows use sidecar files to track progress:

| Workflow | Sidecar File |
|----------|--------------|
| Resume Import | `.resume-import-progress.yaml` |
| Thought Leadership Import | `.thought-leadership-import-progress.yaml` |

If interrupted, restart the workflow and it will detect the sidecar file, allowing you to continue from where you left off.

---

## Installation in New Projects

These workflows are custom BMAD workflows. To use them in a new repository:

### Prerequisites

1. **BMAD must be installed** — Run the BMAD installer in your project
2. **Resume CLI must be available** — The workflows use `resume` commands

### Installation Steps

1. **Copy the workflow directories:**

```bash
# From this repository to your new project
cp -r _bmad/custom/src/workflows/resume-import \
      /path/to/new-project/_bmad/custom/src/workflows/

cp -r _bmad/custom/src/workflows/thought-leadership-import \
      /path/to/new-project/_bmad/custom/src/workflows/
```

2. **Register in workflow-manifest.csv:**

Add these lines to `_bmad/_config/workflow-manifest.csv` in your new project:

```csv
"resume-import","Parse existing resume documents (DOCX, PDF, TXT, Markdown, LinkedIn exports) and transform them into structured resume-as-code data with proper PAR (Problem-Action-Result) formatting.","custom","_bmad/custom/src/workflows/resume-import/workflow.md"
"thought-leadership-import","Import publications, speaking engagements, and board roles from git repos, markdown files, and structured data into resume-as-code.","custom","_bmad/custom/src/workflows/thought-leadership-import/workflow.md"
```

3. **Start a new Claude Code session** — Skills are loaded at session start

4. **Verify installation:**
```bash
# In Claude Code
/resume-import
/thought-leadership-import
```

### Directory Structure

After installation, your project should have:

```
your-project/
├── _bmad/
│   ├── _config/
│   │   └── workflow-manifest.csv  # Updated with new entries
│   └── custom/
│       └── src/
│           └── workflows/
│               ├── resume-import/
│               │   ├── workflow.md
│               │   ├── steps/
│               │   └── templates/
│               └── thought-leadership-import/
│                   ├── workflow.md
│                   ├── steps/
│                   └── templates/
```

---

## Tips

1. **Start with resume import** — Get your job history in first
2. **Review carefully** — The import extracts what it can; verify accuracy
3. **Embrace elicitation** — Answering questions improves bullet quality
4. **Add metrics** — Quantified results make stronger work units
5. **Don't import everything** — Skip irrelevant or outdated entries
6. **Validate after import** — Run `resume validate` to check data quality
