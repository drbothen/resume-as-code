---
id: getting-started
title: Getting Started
sidebar_position: 1
---

# Getting Started with Resume as Code

Resume as Code is a CLI tool that treats your career data as structured, queryable truth. Instead of maintaining multiple static resume documents, you capture accomplishments as **Work Units** and generate tailored resumes on demand.

## Installation

```bash
# Install with pip
pip install resume-as-code

# Or with uv (recommended)
uv pip install resume-as-code
```

## Quick Start

### 1. Initialize Your Project

```bash
# Create a new resume project
mkdir my-resume && cd my-resume
resume init
```

This creates the basic structure:

```
my-resume/
├── .resume.yaml          # Project configuration
├── positions.yaml        # Employment history
├── certifications.yaml   # Certifications
├── education.yaml        # Education
└── work-units/           # Your accomplishments
```

### 2. Add Your Employment History

```bash
# Add a position interactively
resume new position

# Or inline (LLM-optimized)
resume new position "TechCorp|Senior Engineer|2022-01|"
```

### 3. Capture Your Accomplishments

Work Units are the atomic unit of career data. Each represents a single accomplishment with context:

```bash
# Create a work unit with archetype template
resume new work-unit --archetype incident

# Quick capture mode
resume new work-unit \
  --position-id pos-techcorp-senior-engineer \
  --title "Reduced deployment time by 80%"
```

### 4. Generate a Tailored Resume

```bash
# Analyze job description and select best Work Units
resume plan --jd job-description.txt

# Generate resume files
resume build --jd job-description.txt
```

## Core Concepts

### Work Units

Work Units are the building blocks of your resume. Each captures:

- **Problem**: The challenge or context
- **Actions**: What you did (quantified)
- **Result**: The measurable outcome
- **Skills**: Technologies and competencies demonstrated

```yaml
# work-units/wu-2024-01-15-deployment-automation.yaml
id: wu-2024-01-15-deployment-automation
position_id: pos-techcorp-senior-engineer
title: Reduced deployment time by 80%
par:
  problem: Manual deployments took 4 hours and caused frequent outages
  actions:
    - Designed CI/CD pipeline with GitHub Actions
    - Implemented blue-green deployment strategy
    - Added automated rollback on failure
  result: Deployments now take 48 minutes with zero-downtime releases
skills_demonstrated:
  - CI/CD
  - GitHub Actions
  - DevOps
  - Automation
```

### Selection Algorithm

When you run `resume plan`, the tool:

1. Parses the job description for required skills and keywords
2. Ranks your Work Units using BM25 + semantic matching
3. Shows you exactly what will be included and why
4. Identifies skill gaps (what the JD wants that you don't have)

### Output Generation

`resume build` generates professional resumes in multiple formats:

- **PDF**: Using WeasyPrint for beautiful typeset output
- **DOCX**: ATS-friendly Microsoft Word format
- **JSON**: Machine-readable for integrations

## Next Steps

- [Command Reference](/docs/commands/new) - All available commands
- [Data Model](/docs/data-model/work-unit) - Schema documentation
- [Configuration](/docs/configuration) - Customize your setup
- [Examples](/examples) - Real-world usage patterns
