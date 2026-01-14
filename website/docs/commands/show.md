---
id: show
title: show
sidebar_position: 3
---

# resume show

Show detailed information about a specific resource.

## Subcommands

### resume show work-unit

Show detailed work unit information.

```bash
resume show work-unit wu-2024-01-15-deployment-automation
```

**Output:**

```
Work Unit: wu-2024-01-15-deployment-automation
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Title: Reduced deployment time by 80%
Position: TechCorp - Senior Engineer

PAR (Problem-Action-Result):
├── Problem: Manual deployments took 4 hours and caused frequent outages
├── Actions:
│   • Designed CI/CD pipeline with GitHub Actions
│   • Implemented blue-green deployment strategy
│   • Added automated rollback on failure
└── Result: Deployments now take 48 minutes with zero-downtime releases

Skills Demonstrated:
  CI/CD, GitHub Actions, DevOps, Automation

Tags: infrastructure, automation, devops
```

### resume show position

Show position details with associated work units.

```bash
resume show position pos-techcorp-senior-engineer
```

**Output:**

```
Position: pos-techcorp-senior-engineer
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Employer: TechCorp
Title: Senior Engineer
Period: 2022-01 - Present (2 years, 1 month)

Scope (Executive):
├── Revenue: $500M
├── Team Size: 50
└── Budget: $2M

Associated Work Units (5):
├── wu-2024-01-15-deployment-automation
├── wu-2024-02-10-security-audit
├── wu-2023-08-05-performance-optimization
├── wu-2023-06-20-api-redesign
└── wu-2023-04-01-team-onboarding
```

### resume show certification

Show certification details.

```bash
resume show certification "AWS Solutions"
```

Supports partial matching on certification names.

### resume show education

Show education entry details.

```bash
resume show education "MIT"
```

## Options

| Flag | Description |
|------|-------------|
| `--json` | Output as JSON (global flag) |
