# Claude Code CLI Friendliness & AI Agent Integration Patterns

**Date:** 2026-01-10
**Researcher:** Claude Code Assistant
**Research Type:** Deep Research via Perplexity
**Topic Covered:** RB-064

---

## Executive Summary

This research provides comprehensive guidance for designing the Resume-as-Code CLI to be optimally used by Claude Code and other AI coding assistants. Key findings:

1. **JSON output is essential** - Every command must support `--json` for structured, machine-parseable output
2. **Semantic exit codes** - Exit codes must communicate error categories, not just success/failure
3. **Non-interactive by default** - No prompts; all input via flags/environment variables
4. **Stdout/stderr separation** - Results to stdout, status/errors to stderr
5. **Self-documenting help** - Complete `--help` output that agents can parse
6. **MCP integration consideration** - Model Context Protocol for deeper agent integration
7. **Idempotent operations** - Same input always produces same result

---

## Key Findings

### 1. Output Formatting for LLM Consumption

**JSON as Primary Machine Format:**
- JSON is the de facto standard for machine-readable CLI output
- When `--json` flag is provided, suppress ALL non-JSON output
- Include version information in JSON output for schema evolution

**Output Mode Flags:**
| Flag | Behavior | Use Case |
|------|----------|----------|
| `--json` | Complete structured JSON | Agent consumption |
| `--quiet` | No output, exit code only | Success/failure check |
| `--verbose` | Detailed debug information | Troubleshooting |
| (default) | Human-readable Rich output | Interactive use |

**Critical Rule:** These flags must be orthogonal - `--json --dry-run` should output JSON describing what *would* happen.

**Recommended Output Structure:**
```json
{
  "format_version": "1.0.0",
  "status": "success",
  "command": "plan",
  "data": {
    "selected_work_units": [...],
    "keyword_analysis": {...}
  },
  "warnings": [],
  "errors": []
}
```

### 2. Error Handling for AI Agents

**Semantic Exit Codes:**
| Exit Code | Category | Example |
|-----------|----------|---------|
| 0 | Success | Command completed successfully |
| 1 | User error (correctable) | Invalid flag, missing required argument |
| 2 | Configuration error | Invalid config file, missing config |
| 3 | Validation error | Schema validation failed |
| 4 | Resource not found | Work unit file not found |
| 5 | System/runtime error | File I/O error, network failure |
| 127 | Command not found | Missing dependency |
| 143 | Terminated by signal | SIGTERM received |

**Structured Error Output:**
```json
{
  "status": "error",
  "exit_code": 3,
  "errors": [
    {
      "code": "VALIDATION_ERROR",
      "message": "Missing required field 'problem.statement'",
      "path": "work-units/wu-2024-03-15-api.yaml:12",
      "suggestion": "Add a problem statement describing the challenge you solved",
      "recoverable": true
    }
  ]
}
```

**Error Handling Rules:**
- Write errors to stderr, not stdout
- Include `recoverable` flag so agents know if retry makes sense
- Provide `suggestion` field with actionable fix
- Include file path and line number when applicable

### 3. Non-Interactive Operation

**Critical for AI Agents:**
- CLI must NEVER prompt for input when all required information is provided
- All configuration via: CLI flags > Environment variables > Config files
- Provide `--yes` or `--force` flags for operations that would normally prompt

**Environment Variable Support:**
```bash
RESUME_OUTPUT_DIR=./dist
RESUME_DEFAULT_TEMPLATE=modern
RESUME_EMBEDDING_MODEL=multilingual-e5-large-instruct
RESUME_JSON_OUTPUT=true  # Default to JSON mode
```

**Non-Interactive Validation:**
```bash
# Good - agent can invoke without prompts
resume new work-unit --archetype incident --title "API Outage" --editor false

# Bad - would prompt for archetype if not provided
resume new work-unit  # prompts "Select archetype..."
```

### 4. Stdout/Stderr Separation

**Convention:**
| Stream | Content |
|--------|---------|
| stdout | Command results, data output, JSON response |
| stderr | Progress indicators, warnings, errors, debug info |

**Why This Matters:**
- Agents can parse stdout for results without filtering noise
- Progress can still be shown to humans via stderr
- `2>/dev/null` captures just results; `2>&1` gets everything

**Implementation:**
```python
# Correct
console = Console()          # stdout for results
err_console = Console(stderr=True)  # stderr for status

# In JSON mode
if json_output:
    print(json.dumps(result))  # stdout
else:
    console.print(rich_table)  # stdout

# Progress always to stderr
err_console.print("[dim]Processing 15 work units...[/dim]")
```

### 5. Help System for Agent Discovery

**Self-Documenting Help:**
Help output should be complete enough for agents to use commands correctly without external docs.

**Required Elements:**
1. Command description (one line)
2. Full usage syntax with all flags
3. Required vs optional flag distinction
4. Default values shown explicitly
5. Valid enum values listed
6. Examples of common usage

**Example Help Output:**
```
resume plan - Analyze job description and select relevant work units

USAGE:
  resume plan --jd <file> [OPTIONS]

REQUIRED:
  --jd, -j <file>         Job description file (text or YAML)

OPTIONS:
  --top <n>               Number of work units to select (default: 8)
  --threshold <float>     Minimum relevance score 0.0-1.0 (default: 0.3)
  --output, -o <file>     Save plan to file (YAML format)
  --json                  Output as JSON (default: false)
  --quiet                 Suppress output, exit code only
  --verbose               Show detailed ranking information

EXAMPLES:
  resume plan --jd senior-engineer.txt
  resume plan --jd job.yaml --top 5 --output plan.yaml
  resume plan --jd job.txt --json | jq '.data.selected_work_units'

EXIT CODES:
  0  Success
  1  Invalid arguments
  4  Job description file not found
  5  No work units found in work-units/
```

### 6. Command Architecture for Agents

**Flat Commands with Consistent Flags:**
| Pattern | Recommendation |
|---------|----------------|
| Command structure | Flat or shallow nesting (max 2 levels) |
| Flag naming | Consistent across all commands |
| Required args | Via flags, not positional |
| Output format | `--json`, `--format` on all commands |

**Standard Flags (every command):**
```
--json              Machine-readable JSON output
--quiet, -q         Suppress output, exit code only
--verbose, -v       Detailed output
--help, -h          Show help
--version           Show version
```

**Flag Naming Consistency:**
```bash
# Good - consistent across commands
resume plan --jd file.txt --output plan.yaml
resume build --plan plan.yaml --output-dir ./dist

# Bad - inconsistent naming
resume plan --job-description file.txt --out plan.yaml
resume build --plan plan.yaml --destination ./dist
```

### 7. Dry-Run and Preview Modes

**Essential for Safe Agent Operation:**
```bash
resume build --jd job.txt --dry-run --json
```

Output:
```json
{
  "status": "dry_run",
  "would_create": [
    {"path": "dist/resume.pdf", "size_estimate": "45KB"},
    {"path": "dist/resume.docx", "size_estimate": "32KB"},
    {"path": "dist/manifest.yaml", "size_estimate": "2KB"}
  ],
  "work_units_selected": 6,
  "template": "modern"
}
```

**Dry-Run Requirements:**
- Must accurately reflect what would happen
- Should execute as much as possible without side effects
- Output same structure as real execution, with `status: "dry_run"`

### 8. Progress and Streaming Output

**For Long-Running Commands:**
- Progress to stderr (doesn't interfere with JSON parsing)
- Use simple, parseable progress format

**Progress Format:**
```
[progress] step=1/5 message="Loading work units"
[progress] step=2/5 message="Computing embeddings"
[progress] step=3/5 message="Ranking against JD"
[progress] step=4/5 message="Generating content"
[progress] step=5/5 message="Writing output files"
```

**Or structured progress events:**
```json
{"event": "progress", "step": 1, "total": 5, "message": "Loading work units"}
{"event": "progress", "step": 2, "total": 5, "message": "Computing embeddings"}
```

### 9. MCP Integration Consideration

**Model Context Protocol (MCP):**
- Emerging standard for agent-tool communication
- Allows tools to advertise capabilities in structured form
- Enables richer error handling and data exchange

**MCP Server Pattern (Post-MVP):**
```python
# resume-as-code could expose MCP server
# Allowing Claude Code to invoke tools directly

@mcp_tool
def plan_resume(jd_path: str, top_n: int = 8) -> PlanResult:
    """Analyze job description and select relevant work units."""
    ...
```

**For MVP:** Design CLI with MCP compatibility in mind:
- Structured JSON output matches MCP tool response format
- Error structures align with MCP error conventions
- Help/discovery info could be exposed as MCP tool descriptions

### 10. CLAUDE.md Integration

**Project Context File:**
Create `.claude/CLAUDE.md` or `CLAUDE.md` in project root:

```markdown
# Resume-as-Code Project Context

## Quick Reference
- `resume plan --jd <file>` - Analyze JD and select work units
- `resume build --jd <file>` - Generate resume files
- `resume validate` - Validate all work units
- `resume list` - List all work units

## Common Workflows
1. After modifying a work unit: `resume validate`
2. To preview resume for a job: `resume plan --jd job.txt`
3. To generate resume: `resume build --jd job.txt`

## JSON Mode
All commands support `--json` for structured output.
Prefer JSON mode when processing results programmatically.

## Exit Codes
- 0: Success
- 1: Invalid arguments
- 3: Validation error
- 4: File not found
- 5: System error
```

---

## Integration Recommendations for Resume-as-Code

### Architecture Updates (Section 3.3 CLI Interface Design)

**Add to Technical Constraints:**
```yaml
AI Agent Compatibility:
  - All commands support --json flag
  - Semantic exit codes (0-5 range)
  - Non-interactive by default
  - Stdout/stderr separation
  - Complete --help documentation
```

**Update CLI Output Formatting:**
```python
# JSON output structure (all commands)
{
  "format_version": "1.0.0",
  "status": "success" | "error" | "dry_run",
  "command": "<command_name>",
  "timestamp": "<ISO8601>",
  "data": { ... },
  "warnings": [],
  "errors": []
}
```

### Epic Updates

**Story 1.2 (Rich Console & Output Formatting):**
Add acceptance criteria:
- `--json` flag produces valid JSON with no other output on stdout
- Progress/status messages go to stderr only
- JSON output includes `format_version` field

**Story 1.4 (Error Handling & Exit Codes):**
Update exit code specification:
- 0: Success
- 1: Invalid arguments (correctable user error)
- 2: Configuration error
- 3: Validation error
- 4: Resource not found
- 5: System/runtime error

Add error structure requirements:
- `code`, `message`, `path`, `suggestion`, `recoverable` fields

**All Command Stories:**
Add standard acceptance criteria:
- Supports `--json` flag for structured output
- Supports `--quiet` flag for silent operation
- Supports `--dry-run` where applicable
- Works non-interactively when all required flags provided

### New Story: CLAUDE.md Project Context

**Story 1.5: AI Agent Context Documentation**

As a **user working with Claude Code**,
I want **a CLAUDE.md file documenting CLI usage patterns**,
So that **Claude Code can effectively use the resume CLI**.

**Acceptance Criteria:**
- CLAUDE.md exists in project root
- Documents all CLI commands with examples
- Lists exit codes and their meanings
- Provides common workflow patterns
- Includes JSON mode guidance

---

## Implementation Checklist

### Phase 1: Core CLI Infrastructure
- [ ] Implement `--json` flag on main CLI group
- [ ] Implement stderr for all progress/status output
- [ ] Define exit code enum with semantic values
- [ ] Create structured error format
- [ ] Add `format_version` to all JSON output

### Phase 2: Command Updates
- [ ] All commands support `--json`
- [ ] All commands support `--quiet`
- [ ] Destructive commands support `--dry-run`
- [ ] All commands work non-interactively
- [ ] Complete `--help` for all commands

### Phase 3: Documentation
- [ ] Create CLAUDE.md template
- [ ] Document exit codes in README
- [ ] Document JSON output schemas
- [ ] Add examples for common agent workflows

### Phase 4: Future (Post-MVP)
- [ ] Consider MCP server implementation
- [ ] Add `resume introspect` command for capability discovery
- [ ] Evaluate streaming progress format

---

## Research Sources Summary

- InfoQ: "The Agentic Terminal" (2025) - CLI agent patterns
- InfoQ: "AI Agent CLI" (2025) - CLI design for AI
- Anthropic: Claude Code Best Practices - Agent patterns
- AWS CLI Documentation - JSON output patterns
- HashiCorp Terraform - Versioned JSON output format
- Model Context Protocol Specification - MCP integration
- Agentic Patterns: CLI-First Skill Design
- GitHub CLI/Copilot CLI - Agent-friendly CLI design

---

*Research completed 2026-01-10*
