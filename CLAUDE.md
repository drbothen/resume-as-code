# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Git Commit Guidelines

When creating git commits, do NOT include:
- The "Generated with Claude Code" line
- The "Co-Authored-By: Claude" line
- Any other AI attribution in commit messages

### Conventional Commits Format

All commits MUST follow https://www.conventionalcommits.org/:

```
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

### Required: Type

| Type     | Purpose                      |
|----------|------------------------------|
| feat     | New feature (MINOR version)  |
| fix      | Bug fix (PATCH version)      |
| docs     | Documentation only           |
| style    | Code style (no logic change) |
| refactor | Neither fix nor feature      |
| perf     | Performance improvement      |
| test     | Adding/fixing tests          |
| build    | Build system/dependencies    |
| ci       | CI configuration             |
| chore    | Other non-src/test changes   |

### Required: Description

- Use imperative, present tense ("add" not "added")
- Do NOT capitalize the first letter
- Do NOT end with a period

### Optional: Scope

Enclose in parentheses after type: `feat(api): add endpoint`

### Optional: Body

- Separate from description with a blank line
- Explain motivation and contrast with previous behavior

### Optional: Footer

- `Refs: #123` - Issue references
- `Closes: #123` - Issues closed by commit
- `BREAKING CHANGE:` - Breaking change description

### Breaking Changes

Indicate with either:
1. `!` after type/scope: `feat(api)!: remove endpoint`
2. Footer: `BREAKING CHANGE: endpoint removed and replaced with accounts`

## Git Workflow (Git Flow)

This project uses **Git Flow** branching strategy. Follow these rules:

### Branch Structure

| Branch | Purpose | Create from |
|--------|---------|-------------|
| `main` | Production releases only | - |
| `develop` | Integration branch (default working branch) | `main` |
| `feature/*` | New features | `develop` |
| `fix/*` | Bug fixes | `develop` |
| `spike/*` | Research spikes | `develop` |
| `hotfix/*` | Emergency production fixes | `main` |
| `release/*` | Release preparation | `develop` |

### Rules

1. **NEVER commit directly to `main`** - blocked by pre-commit hook
2. **Always branch from `develop`** for new work
3. **Use conventional commits** - enforced by pre-commit hook

### Branch Naming

```
feature/story-X.X-short-description
fix/issue-123-short-description
spike/XXX-topic
hotfix/issue-456-critical-fix
release/vX.X.X
```

### Creating a Branch

```bash
git checkout develop
git pull origin develop
git checkout -b feature/story-1.2-config-registry
```

### After Work is Complete

Create a PR to merge into `develop` (not `main`).

---

## Resume CLI Reference

CLI tool for git-native resume generation from structured Work Units.

### Quick Reference

| Command | Description |
|---------|-------------|
| `resume --help` | Show all commands |
| `resume --version` | Show version |
| `resume config` | Show current configuration |
| `resume test-errors --type <type>` | Test error handling (dev tool) |
| `resume test-output` | Test output formatting (dev tool) |
| `resume new work-unit` | Create new Work Unit (planned) |
| `resume validate [PATH]` | Validate Work Units (planned) |
| `resume list` | List all Work Units (planned) |
| `resume plan --jd <file>` | Analyze JD, select Work Units (planned) |
| `resume build --jd <file>` | Generate resume files (planned) |

### Global Flags

| Flag | Description |
|------|-------------|
| `--json` | Output in JSON format for programmatic parsing |
| `-v, --verbose` | Show verbose debug output |
| `-q, --quiet` | Suppress all output, exit code only |

### Common Workflows

```bash
# Check configuration
resume config

# With JSON output for parsing
resume --json config

# Create Work Unit (when available)
resume new work-unit --archetype incident
resume new work-unit --from-memory --title "Quick win"

# Validate → Plan → Build (when available)
resume validate
resume plan --jd job-description.txt
resume build --jd job-description.txt
```

### JSON Mode

Use `--json` for structured output. Response format:

```json
{
  "format_version": "1.0.0",
  "status": "success|error",
  "command": "config",
  "timestamp": "ISO-8601",
  "data": {},
  "warnings": [],
  "errors": []
}
```

### Exit Codes

| Code | Meaning | Recoverable |
|------|---------|-------------|
| 0 | Success | - |
| 1 | User error (invalid input) | Yes |
| 2 | Configuration error | Yes |
| 3 | Validation error | Yes |
| 4 | Resource not found | Yes |
| 5 | System error | No |

### Error Format

```json
{
  "code": "VALIDATION_ERROR",
  "message": "Missing required field",
  "path": "work-units/file.yaml:12",
  "suggestion": "Add 'title' field",
  "recoverable": true
}
```

### Retry Pattern

1. Check `recoverable: true` in error response
2. Apply the `suggestion` fix
3. Re-run command

### File Locations

| Path | Purpose |
|------|---------|
| `.resume.yaml` | Project config |
| `~/.config/resume-as-code/config.yaml` | User config |
| `work-units/*.yaml` | Work Unit files |
| `dist/` | Generated output |

<!-- Keep CLAUDE.md in sync when adding new commands. Update Quick Reference table and add workflow examples. -->
