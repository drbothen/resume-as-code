---
id: build
title: build
sidebar_position: 7
---

# resume build

Generate resume files from your Work Units and plan.

## Usage

```bash
# Build using existing plan
resume build

# Build with job description (creates plan first)
resume build --jd job-description.txt

# Specify output format
resume build --format pdf --format docx

# Use specific template
resume build --template executive
```

## Output Formats

| Format | Description |
|--------|-------------|
| `pdf` | WeasyPrint-rendered PDF |
| `docx` | ATS-friendly Word document |
| `json` | Machine-readable data |
| `html` | Web-viewable resume |

## Templates

| Template | Best For |
|----------|----------|
| `modern` | General professional use |
| `executive` | Senior/C-level positions |
| `ats-safe` | Applicant tracking systems |
| `academic` | Research/academic positions |

## Output

```
Building resume for: Senior DevOps Engineer at TechCorp
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Using 8 work units from plan
Template: modern

Generated files:
├── dist/resume-techcorp-devops.pdf (142 KB)
├── dist/resume-techcorp-devops.docx (48 KB)
└── dist/manifest.json

Provenance manifest saved to: dist/manifest.json
```

## Options

| Flag | Description |
|------|-------------|
| `--jd FILE` | Job description (runs plan first) |
| `--format FMT` | Output format(s) |
| `--template NAME` | Template to use |
| `--output-dir DIR` | Output directory |

## Manifest (Provenance)

Each build creates a manifest documenting:

- Work units included
- Selection scores
- Build timestamp
- Template used
- Hash of inputs

```json
{
  "build_timestamp": "2024-01-15T10:30:00Z",
  "work_units": ["wu-2024-01-k8s", "wu-2024-02-cicd"],
  "template": "modern",
  "job_description_hash": "sha256:abc123...",
  "files": [
    {"name": "resume.pdf", "size": 142000, "hash": "sha256:def456..."}
  ]
}
```

## Examples

```bash
# Full workflow
resume validate
resume plan --jd job.txt
resume build

# One-shot build
resume build --jd job.txt --template executive --format pdf
```
