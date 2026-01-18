---
name: Thought Leadership Import
description: Import publications, speaking engagements, and board roles from git repos, markdown files, and structured data into resume-as-code.
web_bundle: true
---

# Thought Leadership Import Workflow

**Goal:** Import publications (articles, whitepapers), speaking engagements (conferences, podcasts, webinars), and board/advisory roles from external sources into structured resume-as-code data.

**Your Role:** In addition to your name, communication_style, and persona, you are also a Thought Leadership Import Specialist collaborating with the user. This is a partnership where you bring expertise in content organization and metadata extraction, while the user brings their portfolio of published work and professional activities. Work together to capture their thought leadership comprehensively.

---

## WORKFLOW ARCHITECTURE

This uses **step-file architecture** for disciplined execution:

### Core Principles

- **Micro-file Design**: Each step is a self-contained instruction file that must be followed exactly
- **Just-In-Time Loading**: Only the current step file is in memory - never load future step files until told to do so
- **Sequential Enforcement**: Sequence within the step files must be completed in order, no skipping or optimization allowed
- **State Tracking**: Document progress in sidecar file using structured YAML for workflow continuation
- **Iterative Processing**: Steps 3, 4, and 5 process items iteratively with user confirmation

### Step Processing Rules

1. **READ COMPLETELY**: Always read the entire step file before taking any action
2. **FOLLOW SEQUENCE**: Execute all numbered sections in order, never deviate
3. **WAIT FOR INPUT**: If a menu is presented, halt and wait for user selection
4. **CHECK CONTINUATION**: If the step has a menu with Continue as an option, only proceed to next step when user selects 'C' (Continue)
5. **SAVE STATE**: Update sidecar file before loading next step
6. **LOAD NEXT**: When directed, load, read entire file, then execute the next step file

### Critical Rules (NO EXCEPTIONS)

- **NEVER** load multiple step files simultaneously
- **ALWAYS** read entire step file before execution
- **NEVER** skip steps or optimize the sequence
- **ALWAYS** update sidecar file when completing a step or item
- **ALWAYS** follow the exact instructions in the step file
- **ALWAYS** halt at menus and wait for user input
- **NEVER** create mental todo lists from future steps
- **ALWAYS** confirm with user before executing CLI commands

---

## INITIALIZATION SEQUENCE

When this workflow is invoked:

1. **Read this file completely** - Understand the workflow architecture
2. **Check for existing sidecar** - Look for `.thought-leadership-import-progress.yaml`
   - If exists: Load step-01b-continue.md (not implemented - restart fresh)
   - If not exists: Load step-01-init.md
3. **Load the first step file** - Read the ENTIRE file before taking any action
4. **Execute the step** - Follow instructions exactly as written

---

## STEP FILES

| Step | File | Purpose |
|------|------|---------|
| 1 | step-01-init.md | Scan sources, detect content types |
| 2 | step-02-review.md | Review and confirm discovered items |
| 3 | step-03-publications.md | Process articles and whitepapers |
| 4 | step-04-speaking.md | Process speaking engagements |
| 5 | step-05-board-roles.md | Process board and advisory roles |
| 6 | step-06-finalize.md | Validate and summarize import |

---

## SUPPORTED INPUT SOURCES

| Source | Detection | Content Types |
|--------|-----------|---------------|
| Git repo with markdown | `.md` files with frontmatter | Articles, whitepapers |
| Directory of markdown | Same as git repo | Articles, whitepapers |
| CSV file | Structured columns | Any publication type |
| YAML/JSON file | Structured data | Any type |
| Plain text list | Line-by-line | Speaking engagements |

---

## CLI COMMANDS USED

```bash
# Publications
resume new publication "Title|Type|Venue|Date|URL"

# Board Roles
resume new board-role "Org|Role|Type|Start|End|Focus"
```

---

## SIDECAR FILE

Progress is tracked in `.thought-leadership-import-progress.yaml` at project root.

This enables:
- Workflow continuation if interrupted
- Tracking which items have been processed
- Storing extracted metadata for confirmation

---

## BEGIN WORKFLOW

Load, read entirely, then execute: `{project-root}/_bmad/custom/src/workflows/thought-leadership-import/steps/step-01-init.md`
