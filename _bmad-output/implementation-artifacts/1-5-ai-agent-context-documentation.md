# Story 1.5: AI Agent Context Documentation (CLAUDE.md)

Status: ready-for-dev

## Story

As a **user working with Claude Code or other AI coding assistants**,
I want **a CLAUDE.md file documenting CLI usage patterns**,
So that **AI agents can effectively use the resume CLI without documentation lookup**.

## Acceptance Criteria

1. **Given** the project is set up
   **When** I inspect the project root
   **Then** I find a `CLAUDE.md` file (or `.claude/CLAUDE.md`)

2. **Given** the CLAUDE.md file exists
   **When** Claude Code reads the project
   **Then** it understands all available CLI commands with examples
   **And** it knows the exit codes and their meanings
   **And** it knows to use `--json` mode when processing results programmatically

3. **Given** the CLAUDE.md file is read
   **When** an AI agent plans a workflow
   **Then** it can construct correct command invocations
   **And** it understands the expected output format
   **And** it knows common workflow patterns

4. **Given** the CLI is updated with new commands or options
   **When** the release is prepared
   **Then** the CLAUDE.md file is updated to reflect changes

## Tasks / Subtasks

- [ ] Task 1: Create CLAUDE.md file structure (AC: #1)
  - [ ] 1.1: Create `CLAUDE.md` in project root
  - [ ] 1.2: Add project header and purpose section
  - [ ] 1.3: Keep file concise (<100 lines for LLM context efficiency)

- [ ] Task 2: Document Quick Reference section (AC: #2)
  - [ ] 2.1: List all CLI commands with one-line descriptions
  - [ ] 2.2: Include command syntax and required flags
  - [ ] 2.3: Show common flag combinations

- [ ] Task 3: Document Common Workflows section (AC: #3)
  - [ ] 3.1: Document validate → plan → build workflow
  - [ ] 3.2: Document work unit creation workflow
  - [ ] 3.3: Document configuration workflow
  - [ ] 3.4: Include step-by-step examples

- [ ] Task 4: Document JSON Mode section (AC: #2)
  - [ ] 4.1: Explain when to use `--json` flag
  - [ ] 4.2: Document JSON response structure
  - [ ] 4.3: Show parsing examples

- [ ] Task 5: Document Exit Codes section (AC: #2)
  - [ ] 5.1: Create complete exit code table
  - [ ] 5.2: Explain recoverable vs non-recoverable errors
  - [ ] 5.3: Document error handling patterns for agents

- [ ] Task 6: Document Error Handling section (AC: #2, #3)
  - [ ] 6.1: Explain structured error format
  - [ ] 6.2: Show how to interpret and fix common errors
  - [ ] 6.3: Include retry logic guidance

- [ ] Task 7: Add maintenance notes (AC: #4)
  - [ ] 7.1: Add comment about keeping CLAUDE.md in sync
  - [ ] 7.2: Document update process for new commands

- [ ] Task 8: Code quality verification
  - [ ] 8.1: Verify CLAUDE.md is valid markdown
  - [ ] 8.2: Verify all documented commands exist
  - [ ] 8.3: Test examples work as documented

## Dev Notes

### Architecture Compliance

This story creates documentation optimized for LLM consumption. Keep content concise and actionable.

**Source:** [Architecture Section 3.3 - AI Agent Compatibility](_bmad-output/planning-artifacts/architecture.md#33-cli-interface-design)
**Source:** [epics.md#Story 1.5](_bmad-output/planning-artifacts/epics.md)

### Dependencies

This story SHOULD be implemented after:
- Story 1.1 (Project Scaffolding) - Commands exist
- Story 1.2 (Rich Console) - JSON mode exists
- Story 1.4 (Error Handling) - Exit codes defined

However, it CAN be created with placeholder content and updated as commands are implemented.

### CLAUDE.md Template

**`CLAUDE.md`:**

```markdown
# Resume-as-Code Project Context

CLI tool for git-native resume generation from structured Work Units.

## Quick Reference

| Command | Description |
|---------|-------------|
| `resume --help` | Show all commands |
| `resume --version` | Show version |
| `resume new work-unit` | Create new Work Unit |
| `resume validate [PATH]` | Validate Work Units |
| `resume list` | List all Work Units |
| `resume plan --jd <file>` | Analyze JD, select Work Units |
| `resume build --jd <file>` | Generate resume files |
| `resume config` | Show current configuration |

## Common Workflows

### 1. Validate → Plan → Build
```bash
# Validate all Work Units first
resume validate

# Preview what will be included
resume plan --jd job-description.txt

# Generate resume files
resume build --jd job-description.txt
```

### 2. Create Work Unit
```bash
# Interactive creation with archetype
resume new work-unit --archetype incident

# Quick capture mode
resume new work-unit --from-memory --title "Quick win"
```

### 3. Check Configuration
```bash
# Show effective config with sources
resume config

# JSON format for parsing
resume --json config
```

## JSON Mode

Use `--json` for structured output when processing programmatically.

```bash
resume --json validate
resume --json plan --jd job.txt
resume --json config
```

### Response Structure
```json
{
  "format_version": "1.0.0",
  "status": "success|error",
  "command": "validate",
  "timestamp": "ISO-8601",
  "data": {},
  "warnings": [],
  "errors": []
}
```

## Exit Codes

| Code | Meaning | Recoverable |
|------|---------|-------------|
| 0 | Success | - |
| 1 | User error (invalid args) | Yes |
| 2 | Configuration error | Yes |
| 3 | Validation error | Yes |
| 4 | Resource not found | Yes |
| 5 | System error | No |

## Error Handling

Errors include actionable suggestions:

```json
{
  "code": "VALIDATION_ERROR",
  "message": "Missing required field",
  "path": "work-units/file.yaml:12",
  "suggestion": "Add problem.statement field",
  "recoverable": true
}
```

### Retry Pattern
1. Check `recoverable: true`
2. Apply `suggestion`
3. Re-run command

## File Locations

| Path | Purpose |
|------|---------|
| `.resume.yaml` | Project config |
| `~/.config/resume-as-code/config.yaml` | User config |
| `work-units/*.yaml` | Work Unit files |
| `dist/` | Generated output |
```

### Key Design Principles

1. **Concise**: Under 100 lines for LLM context efficiency
2. **Actionable**: Every section helps agent execute tasks
3. **Complete**: Covers all commands, exit codes, errors
4. **Scannable**: Tables and code blocks for quick parsing
5. **Examples**: Real command examples, not abstract descriptions

### Content Guidelines

**DO Include:**
- Command syntax with required flags
- Exit code table
- JSON response structure
- Common workflow patterns
- Error handling guidance
- File location reference

**DO NOT Include:**
- Implementation details
- Architecture explanations
- Development instructions
- Verbose descriptions
- Historical context

### LLM Context Efficiency

The CLAUDE.md file should be optimized for LLM consumption:

| Metric | Target | Rationale |
|--------|--------|-----------|
| Total lines | <100 | Fits in context window |
| Words | <800 | Minimal token usage |
| Code examples | 5-10 | Enough to demonstrate patterns |
| Tables | 3-4 | Quick reference format |

### Maintenance Process

When adding new commands:

1. Add to Quick Reference table
2. Add workflow example if applicable
3. Update exit codes if new error types
4. Verify file stays under 100 lines
5. Test examples work

### Project Structure After This Story

```
resume-as-code/
├── CLAUDE.md                 # NEW: AI agent context file
├── pyproject.toml
├── src/
│   └── resume_as_code/
│       └── ...
└── ...
```

### Testing Requirements

**Manual Verification:**

1. Open project in Claude Code
2. Ask: "What commands are available?"
3. Verify Claude correctly identifies commands from CLAUDE.md

4. Ask: "How do I validate my Work Units?"
5. Verify Claude provides correct `resume validate` command

6. Ask: "What does exit code 3 mean?"
7. Verify Claude explains validation error

**Automated Verification:**

```bash
# Verify CLAUDE.md exists
test -f CLAUDE.md && echo "CLAUDE.md exists"

# Verify it's valid markdown (basic check)
cat CLAUDE.md | head -1 | grep -q "^#" && echo "Valid markdown header"

# Count lines (should be <100)
wc -l CLAUDE.md
```

### Example Usage by AI Agent

When an AI agent reads this project, it should be able to:

```
User: "Validate my work units and show me any errors"

Agent thinking:
- CLAUDE.md says: `resume validate [PATH]`
- For errors, use `--json` for structured output
- Check exit code: 0=success, 3=validation error

Agent executes:
resume --json validate

Agent interprets:
- If exit code 0: "All work units are valid"
- If exit code 3: Parse errors array, explain each issue
```

### References

- [Source: architecture.md#Section 3.3 - AI Agent Compatibility](_bmad-output/planning-artifacts/architecture.md)
- [Source: epics.md#Story 1.5](_bmad-output/planning-artifacts/epics.md)
- [Source: project-context.md](_bmad-output/project-context.md)

## Dev Agent Record

### Agent Model Used

{{agent_model_name_version}}

### Debug Log References

### Completion Notes List

### File List

