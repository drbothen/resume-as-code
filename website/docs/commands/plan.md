---
id: plan
title: plan
sidebar_position: 6
---

# resume plan

Analyze a job description and select the best Work Units for your resume.

## Usage

```bash
# Plan with job description file
resume plan --jd job-description.txt

# From clipboard (macOS)
pbpaste | resume plan --jd -

# With verbose output
resume plan --jd job.txt -v
```

## How It Works

1. **Parse JD**: Extracts skills, keywords, and requirements
2. **Score Work Units**: Uses BM25 + semantic matching
3. **Rank & Select**: Orders by relevance score
4. **Gap Analysis**: Identifies missing skills

## Output

```
Resume Plan for: Senior DevOps Engineer at TechCorp
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Selected Work Units (8):
┌──────────────────────────────────────────────────────────────┐
│ Score  Title                                    Position      │
├──────────────────────────────────────────────────────────────┤
│ 0.89   Led Kubernetes migration                TechCorp      │
│ 0.85   Reduced deployment time by 80%          TechCorp      │
│ 0.78   Implemented observability platform      StartupXYZ    │
│ 0.72   Built CI/CD pipeline                    TechCorp      │
│ 0.68   Automated infrastructure provisioning   TechCorp      │
│ 0.65   Led SOC2 compliance initiative          TechCorp      │
│ 0.58   Designed disaster recovery plan         StartupXYZ    │
│ 0.52   Mentored junior engineers               TechCorp      │
└──────────────────────────────────────────────────────────────┘

Skill Coverage:
✓ Kubernetes (3 work units)
✓ CI/CD (4 work units)
✓ AWS (2 work units)
✓ Terraform (2 work units)
✗ ArgoCD (0 work units) ← Gap

Excluded Work Units (4):
├── wu-2023-01-frontend-redesign (Score: 0.12) - Not relevant
├── wu-2022-08-mobile-app (Score: 0.08) - Different domain
└── ... 2 more

Plan saved to: .resume-plan.json
```

## Options

| Flag | Description |
|------|-------------|
| `--jd FILE` | Job description file (required) |
| `-v, --verbose` | Show detailed scoring |
| `--min-score FLOAT` | Minimum relevance score (default: 0.3) |
| `--max-units INT` | Maximum work units (default: 15) |

## Plan Persistence

The plan is saved to `.resume-plan.json` and used by `resume build`.

```json
{
  "job_title": "Senior DevOps Engineer",
  "company": "TechCorp",
  "selected_work_units": [
    {"id": "wu-2024-01-k8s", "score": 0.89}
  ],
  "skill_coverage": {
    "matched": ["Kubernetes", "CI/CD"],
    "gaps": ["ArgoCD"]
  }
}
```

## Customizing Selection

Override the automatic selection:

```bash
# Include specific work unit regardless of score
resume plan --jd job.txt --include wu-2024-special-project

# Exclude specific work unit
resume plan --jd job.txt --exclude wu-2023-irrelevant

# Adjust weights
resume plan --jd job.txt --skill-weight 0.6
```
