---
id: remove
title: remove
sidebar_position: 4
---

# resume remove

Remove resources from your resume project.

## Subcommands

### resume remove work-unit

Remove a work unit file.

```bash
resume remove work-unit wu-2024-01-15-deployment-automation
```

Prompts for confirmation unless `--force` is used.

### resume remove position

Remove an employment position.

```bash
resume remove position pos-techcorp-senior-engineer
```

**Warning:** This does not automatically remove associated work units.

### resume remove certification

Remove a certification.

```bash
# By exact name
resume remove certification "AWS Solutions Architect"

# By partial match
resume remove certification "AWS"
```

### resume remove education

Remove an education entry.

```bash
resume remove education "MIT"
```

## Options

| Flag | Description |
|------|-------------|
| `--force` | Skip confirmation prompt |

## Examples

```bash
# Remove with confirmation
resume remove work-unit wu-2024-01-15-test

# Force removal (no prompt)
resume remove work-unit wu-2024-01-15-test --force
```

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 4 | Resource not found |
