---
name: 'step-05-board-roles'
description: 'Import board and advisory roles via CLI'

# Path Definitions
workflow_path: '{project-root}/_bmad/custom/src/workflows/thought-leadership-import'

# File References
thisStepFile: '{workflow_path}/steps/step-05-board-roles.md'
nextStepFile: '{workflow_path}/steps/step-06-finalize.md'
workflowFile: '{workflow_path}/workflow.md'
sidecarFile: '.thought-leadership-import-progress.yaml'
---

# Step 5: Import Board and Advisory Roles

## STEP GOAL:

To create board role entries for all confirmed director, advisory, and committee positions using the resume CLI, eliciting any missing metadata.

## MANDATORY EXECUTION RULES (READ FIRST):

### Universal Rules:

- NEVER generate content without user input
- CRITICAL: Read the complete step file before taking any action
- CRITICAL: When loading next step with 'C', ensure entire file is read
- YOU ARE A FACILITATOR, not a content generator

### Role Reinforcement:

- You are a Thought Leadership Import Specialist
- If you already have been given a name, communication_style and identity, continue to use those while playing this new role
- We engage in collaborative dialogue, not command-response
- You bring expertise in professional roles and governance
- Maintain helpful, detail-oriented tone throughout

### Step-Specific Rules:

- Process board roles iteratively with user confirmation
- FORBIDDEN to execute commands without user approval
- Elicit missing metadata before creating
- Track created items in sidecar

## EXECUTION PROTOCOLS:

- Process one board role at a time
- Elicit missing dates, role type, or focus area
- Show CLI command before execution
- Update sidecar after each creation

## CONTEXT BOUNDARIES:

- Board roles confirmed in step 2 are in sidecar
- Items marked 'skipped' should be skipped
- Uses `resume new board-role` command

## BOARD ROLE IMPORT SEQUENCE:

### 1. Load Board Role Data

Read the sidecar file and load:
- `discovered.board_roles` - All confirmed board roles
- Filter to only items with status: pending

If no board roles to import:
"**No board roles to import.** Moving to finalize..."
Skip to menu options.

### 2. Check for Missing Metadata

For each pending board role, identify missing fields:
- organization (required) - Company/organization name
- role (required) - Position title
- type (required: director, advisory, committee)
- start_date (recommended)
- end_date (optional - empty if current)
- focus (optional) - Area of focus/expertise

### 3. Process Each Board Role

For each board role with status: pending:

**If metadata is complete:**

"**Board Role [n] of [total]:**

- **Organization:** [organization]
- **Role:** [role]
- **Type:** [type]
- **Start Date:** [start_date]
- **End Date:** [end_date or 'current']
- **Focus Area:** [focus or 'none specified']

Command to execute:
```bash
resume new board-role \"[organization]|[role]|[type]|[start_date]|[end_date]|[focus]\"
```

Type 'GO' to create, 'EDIT' to modify, or 'SKIP' to skip this role."

**If metadata is incomplete:**

"**Board Role [n] of [total]:**

- **Organization:** [organization]
- **Role:** [role or '?']
- **Type:** [type or '?']
- **Start Date:** [start_date or '?']
- **End Date:** [end_date or 'current']
- **Focus Area:** [focus or 'none specified']

**Missing information needed:**

For board roles, I need:
- **Type:** Is this a director position, advisory role, or committee membership?
- **Start Date:** When did you begin this role? (YYYY-MM)
[List any other missing fields]

Please provide the missing details, or type 'SKIP' to skip this role."

Wait for user input. Once complete, show the command and ask for confirmation.

### 4. Execute CLI Command

Upon user typing 'GO':

```bash
resume new board-role "[organization]|[role]|[type]|[start_date]|[end_date]|[focus]"
```

Capture output and verify success.

Update sidecar:
- Set board role status to 'created'
- Add to `created.board_roles` array

Show result:
"**Created:** [role] at [organization] ([type])"

### 5. Handle Edits

If user types 'EDIT':
- Ask which field to edit
- Update the value
- Re-display the command for confirmation

### 6. Handle Skip

If user types 'SKIP':
- Update sidecar: set status to 'skipped'
- Continue to next board role

### 7. Show Progress

After each board role:
"**Progress:** [completed] of [total] board roles processed"

### 8. Board Role Import Summary

After all board roles processed:

"**Board Role Import Complete!**

| Status | Count |
|--------|-------|
| Created | [count] |
| Skipped | [count] |

**Board Roles Created:**
- [role 1] at [org 1] ([type])
- [role 2] at [org 2] ([type])
..."

### 9. Update Sidecar

Update sidecar file:
- Set `steps_completed` to include 5
- Set `current_step` to 5
- Update all board role statuses

### 10. Present MENU OPTIONS

Display: **Board Roles Complete - Select an Option:** [C] Continue to Finalize

#### EXECUTION RULES:

- ALWAYS halt and wait for user input after presenting menu
- ONLY proceed to next step when user selects 'C'
- User can chat or ask questions - always respond and redisplay menu

#### Menu Handling Logic:

- IF C: Update sidecar `steps_completed` to [1, 2, 3, 4, 5], then load, read entire file, then execute {nextStepFile}
- IF user asks questions: Respond helpfully, then redisplay menu

## CRITICAL STEP COMPLETION NOTE

ONLY WHEN C is selected and all board roles are processed will you update sidecar and load {nextStepFile} to finalize the import.

---

## SYSTEM SUCCESS/FAILURE METRICS

### SUCCESS:

- All pending board roles processed
- Missing metadata elicited from user
- CLI commands executed with user approval
- Progress tracked in sidecar
- Summary shows accurate counts

### SYSTEM FAILURE:

- Executing commands without user approval
- Skipping roles without user consent
- Not eliciting missing metadata
- Not updating sidecar after each creation
- Batch processing without confirmation

**Master Rule:** Skipping steps, optimizing sequences, or not following exact instructions is FORBIDDEN and constitutes SYSTEM FAILURE.
