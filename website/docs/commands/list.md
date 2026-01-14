---
id: list
title: list
sidebar_position: 2
---

# resume list

List resources in your resume project.

## Subcommands

### resume list (work-units)

List all work units.

```bash
# Default: list work units
resume list

# With JSON output
resume --json list
```

**Output:**

```
Work Units (12 total)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ID                                    Title                          Position
wu-2024-01-15-deployment-auto...     Reduced deployment time by 80%  TechCorp
wu-2024-02-10-security-audit...      Led SOC2 compliance initiative  TechCorp
...
```

### resume list positions

List all employment positions.

```bash
resume list positions
```

**Output:**

```
Positions (3 total)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ID                              Employer        Title              Period
pos-techcorp-senior-engineer   TechCorp        Senior Engineer    2022-01 - Present
pos-startup-developer          StartupXYZ      Developer          2019-06 - 2021-12
pos-bigco-intern               BigCo           Intern             2018-05 - 2018-08
```

### resume list certifications

List certifications with status.

```bash
resume list certifications
```

**Output:**

```
Certifications (2 total)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Name                         Issuer    Issued      Expires     Status
AWS Solutions Architect      Amazon    2024-01     2027-01     Active
CISSP                        ISC2      2023-06     2026-06     Expires Soon
```

### resume list education

List education entries.

```bash
resume list education
```

## Options

| Flag | Description |
|------|-------------|
| `--json` | Output as JSON (global flag) |

## JSON Output

```json
{
  "format_version": "1.0.0",
  "status": "success",
  "command": "list",
  "data": [
    {
      "id": "wu-2024-01-15-deployment-automation",
      "title": "Reduced deployment time by 80%",
      "position_id": "pos-techcorp-senior-engineer"
    }
  ]
}
```
