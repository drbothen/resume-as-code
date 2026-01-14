---
id: work-unit
title: Work Unit
sidebar_position: 1
---

# Work Unit Schema

Work Units are the atomic unit of career data. Each represents a single accomplishment with full context.

## Schema

```yaml
# Required fields
id: string                    # Unique identifier (wu-YYYY-MM-DD-slug)
title: string                 # Achievement headline

# Optional fields
position_id: string           # Reference to positions.yaml
par:                          # Problem-Action-Result structure
  problem: string             # Challenge or context
  actions: string[]           # What you did (list)
  result: string              # Measurable outcome
skills_demonstrated: string[] # Technologies and competencies
tags: string[]                # Categorization tags
quantified_impact: string     # Key metric (e.g., "80% faster")
evidence:                     # Supporting evidence
  links: string[]             # URLs to artifacts
  artifacts: string[]         # File paths
```

## Example

```yaml
# work-units/wu-2024-01-15-deployment-automation.yaml
id: wu-2024-01-15-deployment-automation
position_id: pos-techcorp-senior-engineer
title: Reduced deployment time by 80%

par:
  problem: >
    Manual deployments took 4 hours and caused frequent
    production outages due to human error.
  actions:
    - Designed CI/CD pipeline with GitHub Actions and ArgoCD
    - Implemented blue-green deployment strategy
    - Added automated rollback on health check failure
    - Created deployment runbooks for team
  result: >
    Deployments now take 48 minutes with zero-downtime releases.
    Reduced deployment-related incidents from 5/month to 0.

skills_demonstrated:
  - CI/CD
  - GitHub Actions
  - ArgoCD
  - Kubernetes
  - DevOps

tags:
  - infrastructure
  - automation
  - devops
  - reliability

quantified_impact: "80% reduction in deployment time"

evidence:
  links:
    - https://github.com/company/repo/pull/123
  artifacts:
    - screenshots/deployment-metrics.png
```

## ID Format

Work Unit IDs follow the pattern: `wu-{YYYY-MM-DD}-{slug}`

- **Date**: When the achievement occurred
- **Slug**: Short kebab-case description

Examples:
- `wu-2024-01-15-deployment-automation`
- `wu-2023-08-05-security-audit`
- `wu-2022-11-20-team-leadership`

## PAR Structure

The Problem-Action-Result framework ensures each Work Unit tells a complete story:

### Problem

The challenge, context, or opportunity. Establishes why this work mattered.

**Good**: "Manual deployments took 4 hours and caused frequent outages"
**Bad**: "We needed a CI/CD pipeline"

### Actions

What you specifically did. Use strong action verbs and be specific.

**Good**: "Designed CI/CD pipeline with GitHub Actions"
**Bad**: "Worked on deployment automation"

### Result

The measurable outcome. Include metrics whenever possible.

**Good**: "Deployments now take 48 minutes with zero-downtime releases"
**Bad**: "Improved deployment process"

## Archetypes

Use archetypes to start with a template:

```bash
resume new work-unit --archetype incident
resume new work-unit --archetype greenfield
resume new work-unit --archetype leadership
```

| Archetype | Best For |
|-----------|----------|
| `incident` | Crisis response, debugging |
| `greenfield` | New projects, from-scratch work |
| `leadership` | Team management, mentoring |
| `optimization` | Performance improvements |
| `migration` | System upgrades, platform changes |
