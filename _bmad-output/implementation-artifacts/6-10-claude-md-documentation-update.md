# Story 6.10: CLAUDE.md System Documentation Update

Status: ready-for-dev

## Story

As a **user working with Claude Code**,
I want **CLAUDE.md updated with the positions/work-units workflow**,
So that **AI agents understand the data model and can help me build my resume efficiently**.

## Acceptance Criteria

1. **Given** the CLAUDE.md file exists
   **When** Story 6.7-6.9 are implemented
   **Then** CLAUDE.md is updated to document:
     1. The positions → work units relationship
     2. Commands for managing positions
     3. Inline position creation flags for LLM usage
     4. Complete workflow examples

2. **Given** an AI agent reads CLAUDE.md
   **When** a user asks to add a work experience
   **Then** the agent knows to:
     1. Check if position exists in positions.yaml
     2. Create position if needed (using inline flags)
     3. Create work unit with position_id reference
     4. Validate the result

3. **Given** CLAUDE.md is updated
   **When** I inspect the file
   **Then** it includes a "Data Model" section explaining:
   ```markdown
   ## Data Model

   ### Positions (positions.yaml)
   Employment history with employer, title, dates. Work units reference positions.

   ### Work Units (work-units/*.yaml)
   Individual achievements/accomplishments. Reference a position via `position_id`.

   ### Relationship
   ```
   Position (1) ← references ← (*) Work Units
   ```
   Work units are grouped under positions for resume rendering.
   ```

4. **Given** CLAUDE.md is updated
   **When** I inspect the file
   **Then** it includes examples for common AI agent tasks:
   ```markdown
   ## AI Agent Workflows

   ### Adding Work Experience (Inline - Preferred for LLM)
   ```bash
   # Create position and work unit in one command
   resume new work-unit \
     --position "Acme Corp|Senior Engineer|2022-01|" \
     --title "Led migration project reducing costs 40%" \
     --archetype greenfield
   ```

   ### Checking Existing Positions
   ```bash
   resume --json list positions
   ```

   ### Creating Work Unit for Existing Position
   ```bash
   resume new work-unit \
     --position-id pos-acme-senior-engineer \
     --title "Implemented security controls"
   ```
   ```

5. **Given** CLAUDE.md is updated
   **When** I run `resume --help` or read the file
   **Then** the documentation is consistent with actual CLI behavior

## Tasks / Subtasks

- [ ] Task 1: Analyze current CLAUDE.md structure (AC: #5)
  - [ ] 1.1: Read existing CLAUDE.md to understand current structure
  - [ ] 1.2: Identify where new sections should be inserted
  - [ ] 1.3: Plan section ordering for LLM context efficiency

- [ ] Task 2: Add Data Model section (AC: #3)
  - [ ] 2.1: Add "## Data Model" heading after CLI Reference
  - [ ] 2.2: Document Positions (positions.yaml) structure
  - [ ] 2.3: Document Work Units and position_id relationship
  - [ ] 2.4: Add relationship diagram (ASCII)
  - [ ] 2.5: Explain grouping behavior for resume rendering

- [ ] Task 3: Add Position Management section (AC: #1, #2)
  - [ ] 3.1: Add "## Position Management" heading
  - [ ] 3.2: Document `resume new position` command (interactive)
  - [ ] 3.3: Document `resume list positions` command
  - [ ] 3.4: Document `resume show position <id>` command
  - [ ] 3.5: Document position ID format: `pos-{employer-slug}-{title-slug}`

- [ ] Task 4: Add AI Agent Workflows section (AC: #2, #4)
  - [ ] 4.1: Add "## AI Agent Workflows" heading
  - [ ] 4.2: Add "Adding Work Experience (Inline)" example
  - [ ] 4.3: Add "Checking Existing Positions" example with JSON
  - [ ] 4.4: Add "Creating Work Unit for Existing Position" example
  - [ ] 4.5: Add common patterns table:
    - "I want to add my job history" → create positions first
    - "I just accomplished something" → quick capture with position reference
    - "Generate resume for this job" → plan + build workflow

- [ ] Task 5: Add Complete Workflow Example (AC: #1, #4)
  - [ ] 5.1: Add "## Complete Example: Building Resume from Scratch" section
  - [ ] 5.2: Document full workflow: create profile → positions → work units → plan → build
  - [ ] 5.3: Show both interactive and non-interactive approaches

- [ ] Task 6: Add Troubleshooting section (AC: #2)
  - [ ] 6.1: Add "## Troubleshooting" heading
  - [ ] 6.2: Document "Work unit has no position" warning resolution
  - [ ] 6.3: Document position ID lookup workflow

- [ ] Task 7: Update existing sections (AC: #5)
  - [ ] 7.1: Update Quick Reference table with position commands
  - [ ] 7.2: Update Common Workflows section with position workflow
  - [ ] 7.3: Ensure all examples use actual command syntax

- [ ] Task 8: Review and optimize (AC: #5)
  - [ ] 8.1: Verify file is under 150 lines for LLM context efficiency
  - [ ] 8.2: Ensure section ordering prioritizes most common operations
  - [ ] 8.3: Verify consistency with actual CLI behavior
  - [ ] 8.4: Run spell check on documentation

## Dev Notes

### Architecture Compliance

This story is a documentation-only update to CLAUDE.md. No code changes are required. The goal is to enable AI agents (especially Claude Code) to understand the positions/work-units data model and assist users efficiently.

**Critical Rules from project-context.md:**
- Keep CLAUDE.md concise for LLM context efficiency (< 150 lines)
- Use actual command syntax from implemented CLI
- Document JSON mode patterns for programmatic parsing

### CLAUDE.md Structure (Post-Update)

```markdown
# CLAUDE.md

## Git Commit Guidelines     (existing)
## Git Workflow              (existing)
## Package Management        (existing)
## Resume CLI Reference      (existing - update)

## Data Model                (NEW - Task 2)
### Positions
### Work Units
### Relationship

## Position Management       (NEW - Task 3)
### Commands
### Position ID Format

## AI Agent Workflows        (NEW - Task 4)
### Adding Work Experience
### Checking Positions
### Creating Work Units
### Common Patterns

## Complete Example          (NEW - Task 5)

## Troubleshooting           (NEW - Task 6)
```

### Quick Reference Table Updates

Add to existing Quick Reference table:

| Command | Description |
|---------|-------------|
| `resume new position` | Create new position (interactive) |
| `resume list positions` | List all positions |
| `resume show position <id>` | Show position details |
| `resume new work-unit --position "..."` | Create with inline position |
| `resume new work-unit --position-id <id>` | Create with existing position |

### Data Model Documentation

```markdown
## Data Model

### Positions (positions.yaml)
Employment history - employers, titles, dates. Each position has a unique ID.

```yaml
# positions.yaml
- id: pos-techcorp-senior-engineer
  employer: TechCorp Industries
  title: Senior Platform Engineer
  start_date: "2022-01"
  end_date: null  # current position
```

### Work Units (work-units/*.yaml)
Individual achievements referencing positions via `position_id`.

```yaml
# work-units/wu-ics-assessment.yaml
id: wu-2024-01-30-ics-assessment
position_id: pos-techcorp-senior-engineer  # References position
title: "Led ICS security assessment..."
```

### Relationship
```
Position (1) ←── references ──← Work Units (*)
```

Resume groups work units under positions for rendering:
```
TechCorp Industries - Senior Platform Engineer (2022-Present)
• Achievement from work unit 1
• Achievement from work unit 2
```
```

### AI Agent Workflow Examples

```markdown
## AI Agent Workflows

### Adding Work Experience (Inline - Preferred for LLM)
```bash
# Create position and work unit in one command
resume new work-unit \
  --position "Acme Corp|Senior Engineer|2022-01|" \
  --title "Led migration project reducing costs 40%" \
  --archetype greenfield
```

### Checking Existing Positions
```bash
resume --json list positions
```

### Creating Work Unit for Existing Position
```bash
resume new work-unit \
  --position-id pos-acme-senior-engineer \
  --title "Implemented security controls"
```

### Common Patterns
| User Request | Agent Action |
|--------------|--------------|
| "Add my job history" | Create positions first with `resume new position` |
| "I just accomplished X" | Quick capture: `resume new work-unit --position "..."` |
| "Generate resume for this job" | `resume plan --jd file.txt && resume build` |
```

### Troubleshooting Documentation

```markdown
## Troubleshooting

### "Work unit has no position" warning
Work units can optionally reference positions. To resolve:
1. Check existing positions: `resume list positions`
2. If position exists, add `position_id` to work unit
3. If not, create position: `resume new position`

### Position ID lookup
```bash
# Find position ID for existing employer/title
resume --json list positions | jq '.data[] | select(.employer | contains("TechCorp"))'
```
```

### Dependencies

This story REQUIRES:
- Story 6.7 (Positions Data Model) - Must understand position schema
- Story 6.8 (Position Management Commands) - Must document actual commands
- Story 6.9 (Inline Position Creation) - Must document --position flag

This story ENABLES:
- Future AI agents to efficiently assist with resume building
- Users to understand the complete workflow

### Files to Modify

**Modified Files:**
- `CLAUDE.md` - Add Data Model, Position Management, AI Agent Workflows sections

### Verification

```bash
# After implementation, verify:

# 1. Check file length (should be < 150 lines ideally, max 200)
wc -l CLAUDE.md

# 2. Verify no broken markdown
# (manual review)

# 3. Test documented commands match actual CLI
uv run resume --help
uv run resume new position --help
uv run resume list positions --help
uv run resume new work-unit --help

# 4. Verify JSON examples work
uv run resume --json list positions
```

### Content Size Guidelines

To maintain LLM context efficiency:
- Keep total CLAUDE.md under 150 lines if possible (max 200)
- Use tables for command references (compact)
- Use code blocks sparingly - one example per pattern
- Link to external docs for detailed explanations if needed
- Prioritize most common workflows first

### References

- [Source: epics.md#Story 6.10](_bmad-output/planning-artifacts/epics.md)
- [Story 6.7: Positions Data Model](6-7-positions-data-model-employment-history.md)
- [Story 6.8: Position Management Commands](6-8-position-management-commands.md)
- [Story 6.9: Inline Position Creation](6-9-inline-position-creation.md)

## Dev Agent Record

### Agent Model Used

{{agent_model_name_version}}

### Debug Log References

### Completion Notes List

### File List

