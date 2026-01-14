---
id: position
title: Position
sidebar_position: 2
---

# Position Schema

Positions represent your employment history - employers, titles, and dates. Work Units reference positions via `position_id`.

## Schema

```yaml
# Required fields
id: string          # Unique identifier (pos-employer-title)
employer: string    # Company name
title: string       # Job title
start_date: string  # Start date (YYYY-MM)

# Optional fields
end_date: string    # End date (YYYY-MM) or null for current
scope:              # Executive scope indicators
  revenue: string   # Revenue impact
  team_size: int    # Team size
  direct_reports: int
  budget: string    # Budget managed
  pl: string        # P&L responsibility
  geography: string # Geographic reach
  customers: string # Customer scope
```

## Example

```yaml
# positions.yaml
- id: pos-techcorp-senior-engineer
  employer: TechCorp Industries
  title: Senior Platform Engineer
  start_date: "2022-01"
  end_date: null  # Current position

- id: pos-startup-developer
  employer: StartupXYZ
  title: Software Developer
  start_date: "2019-06"
  end_date: "2021-12"
```

## Executive Position Example

```yaml
- id: pos-bigco-cto
  employer: BigCo Inc
  title: Chief Technology Officer
  start_date: "2020-01"
  end_date: null
  scope:
    revenue: "$500M"
    team_size: 200
    direct_reports: 8
    budget: "$50M"
    pl: "$100M"
    geography: "Global (US, EMEA, APAC)"
    customers: "Fortune 500"
```

## ID Format

Position IDs follow the pattern: `pos-{employer-slug}-{title-slug}`

Examples:
- `pos-techcorp-senior-engineer`
- `pos-google-staff-swe`
- `pos-startup-founding-engineer`

## Relationship to Work Units

Work Units reference positions via `position_id`:

```
Position (1) ←── references ──← Work Units (*)
```

When generating a resume, Work Units are grouped under their positions:

```
TechCorp Industries - Senior Platform Engineer (2022 - Present)
• Reduced deployment time by 80% through CI/CD automation
• Led Kubernetes migration for 50+ microservices
• Implemented observability platform reducing MTTR by 60%
```

## Scope Indicators

For executive and senior roles, scope indicators quantify impact:

| Field | Description | Example |
|-------|-------------|---------|
| `revenue` | Revenue responsibility | "$500M ARR" |
| `team_size` | Total team managed | 200 |
| `direct_reports` | Direct reports | 8 |
| `budget` | Budget managed | "$50M" |
| `pl` | P&L responsibility | "$100M" |
| `geography` | Geographic reach | "Global" |
| `customers` | Customer scope | "Fortune 500" |

These appear in executive resume templates.
