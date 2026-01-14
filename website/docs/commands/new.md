---
id: new
title: new
sidebar_position: 1
---

# resume new

Create new resources (positions, work-units, certifications, education).

## Subcommands

### resume new position

Create a new employment position.

```bash
# Interactive mode
resume new position

# Pipe-separated format
resume new position "Employer|Title|Start|End"

# With flags
resume new position \
  --employer "TechCorp" \
  --title "Senior Engineer" \
  --start-date 2022-01 \
  --end-date ""  # Empty for current position
```

**Options:**

| Flag | Description |
|------|-------------|
| `--employer` | Company name |
| `--title` | Job title |
| `--start-date` | Start date (YYYY-MM) |
| `--end-date` | End date (YYYY-MM or empty for current) |

**Executive Scope Flags:**

| Flag | Description |
|------|-------------|
| `--scope-revenue` | Revenue impact (e.g., "$500M") |
| `--scope-team-size` | Team size (number) |
| `--scope-direct-reports` | Direct reports count |
| `--scope-budget` | Budget managed |
| `--scope-pl` | P&L responsibility |
| `--scope-geography` | Geographic reach |

### resume new work-unit

Create a new work unit.

```bash
# Interactive mode with archetype
resume new work-unit --archetype incident

# Quick capture with position
resume new work-unit \
  --position "TechCorp|Senior Engineer|2022-01|" \
  --title "Reduced deployment time by 80%"

# Existing position
resume new work-unit \
  --position-id pos-techcorp-senior-engineer \
  --title "Led security audit"
```

**Options:**

| Flag | Description |
|------|-------------|
| `--archetype` | Template archetype (incident, greenfield, leadership) |
| `--position` | Inline position (creates if not exists) |
| `--position-id` | Existing position ID |
| `--title` | Work unit title |

### resume new certification

Create a new certification.

```bash
# Pipe-separated
resume new certification "AWS Solutions Architect|Amazon|2024-01|2027-01"

# With flags
resume new certification \
  --name "AWS Solutions Architect" \
  --issuer "Amazon" \
  --date 2024-01 \
  --expires 2027-01
```

### resume new education

Create a new education entry.

```bash
# Pipe-separated
resume new education "BS Computer Science|MIT|2015|Magna Cum Laude"

# With flags
resume new education \
  --degree "BS Computer Science" \
  --institution "MIT" \
  --year 2015 \
  --honors "Magna Cum Laude"
```

## Examples

```bash
# Complete new hire workflow
resume new position "Acme Corp|Staff Engineer|2023-06|"
resume new work-unit \
  --position-id pos-acme-staff-engineer \
  --archetype greenfield \
  --title "Architected new payment system"
```
