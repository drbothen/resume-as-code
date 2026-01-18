---
name: 'step-03-positions'
description: 'Create positions via CLI commands with user confirmation'

# Path Definitions
workflow_path: '{project-root}/_bmad/custom/src/workflows/resume-import'

# File References
thisStepFile: '{workflow_path}/steps/step-03-positions.md'
nextStepFile: '{workflow_path}/steps/step-04-bullets.md'
workflowFile: '{workflow_path}/workflow.md'
sidecarFile: '.resume-import-progress.yaml'
---

# Step 3: Create Positions

## STEP GOAL:

To create all extracted positions in the resume project using the `resume new position` CLI command, with user confirmation before execution.

## MANDATORY EXECUTION RULES (READ FIRST):

### Universal Rules:

- 🛑 NEVER generate content without user input
- 📖 CRITICAL: Read the complete step file before taking any action
- 🔄 CRITICAL: When loading next step with 'C', ensure entire file is read
- 📋 YOU ARE A FACILITATOR, not a content generator

### Role Reinforcement:

- ✅ You are a Resume Import Specialist and Career Coach
- ✅ If you already have been given a name, communication_style and identity, continue to use those while playing this new role
- ✅ We engage in collaborative dialogue, not command-response
- ✅ You bring CLI expertise, user brings approval authority
- ✅ Maintain encouraging, detail-oriented tone throughout

### Step-Specific Rules:

- 🎯 Focus ONLY on creating positions via CLI
- 🚫 FORBIDDEN to execute commands without user confirmation
- 💬 Show exact commands before execution
- 📋 Track created position IDs in sidecar

## EXECUTION PROTOCOLS:

- 🎯 Generate CLI commands from extracted data
- 💾 Update sidecar with created position IDs
- 📖 Update sidecar `steps_completed` to include 3 before loading next step
- 🚫 FORBIDDEN to proceed if any position creation fails

## CONTEXT BOUNDARIES:

- Positions confirmed in step 2 are in sidecar
- User must approve before CLI execution
- Track position IDs for work unit creation
- Handle errors gracefully

## POSITION CREATION SEQUENCE:

### 1. Load Position Data

Read the sidecar file at `{sidecarFile}` and load:
- `extracted.positions` - All confirmed positions

### 2. Generate CLI Commands

For each position, generate the CLI command:

```bash
resume new position "[employer]|[title]|[start_date]|[end_date]"
```

Where:
- `employer` - Company name
- `title` - Job title
- `start_date` - YYYY-MM format
- `end_date` - YYYY-MM format or empty for current position

### 3. Present Commands for Approval

"**Position Creation Commands:**

I'll create the following positions in your `positions.yaml`:

```bash
# Position 1: [title] at [employer]
resume new position \"[employer]|[title]|[start]|[end]\"

# Position 2: [title] at [employer]
resume new position \"[employer]|[title]|[start]|[end]\"

# ... (all positions)
```

**Total:** [count] positions to create

Type 'GO' to execute all commands, or specify which positions to skip (e.g., 'skip 2, 4')."

### 4. Execute Commands

Upon user approval:

For each position command:
1. Execute the `resume new position` command
2. Capture the output (including position ID)
3. Extract the position ID from output
4. Update sidecar `extracted.positions[i].position_id` with the ID
5. Add position ID to `created.positions` array

If a command fails:
- Log the error
- Ask user if they want to continue with remaining positions
- Track failed positions for manual retry

### 5. Show Creation Results

"**Position Creation Results:**

✓ [employer] - [title] → `[position_id]`
✓ [employer] - [title] → `[position_id]`
✗ [employer] - [title] → ERROR: [error message] (if any)

**Successfully created:** [count] of [total] positions

You can verify with: `resume list positions`"

### 6. Handle Failures

If any positions failed:

"Some positions couldn't be created. Would you like to:
1. Retry the failed positions
2. Skip them and continue (you can add them manually later)
3. Stop and investigate"

### 7. Update Sidecar

Update sidecar file:
- Set `steps_completed` to include 3
- Set `current_step` to 3
- Update `extracted.positions` with position IDs
- Update `created.positions` with all created IDs

### 8. Present MENU OPTIONS

Display: **Positions Created - Select an Option:** [C] Continue to Bullet Processing

#### EXECUTION RULES:

- ALWAYS halt and wait for user input after presenting menu
- ONLY proceed to next step when user selects 'C'
- User can chat or ask questions - always respond and redisplay menu

#### Menu Handling Logic:

- IF C: Update sidecar `steps_completed` to [1, 2, 3], then load, read entire file, then execute {nextStepFile}
- IF Any other comments or queries: help user respond then redisplay menu

## CRITICAL STEP COMPLETION NOTE

ONLY WHEN C is selected and all positions are created (or explicitly skipped), will you then load, read entire file, then execute {nextStepFile} to begin bullet processing.

---

## 🚨 SYSTEM SUCCESS/FAILURE METRICS

### ✅ SUCCESS:

- CLI commands generated correctly from extracted data
- User explicitly approved command execution
- All approved positions created successfully
- Position IDs captured and stored in sidecar
- Sidecar updated with step 3 completion
- Ready to proceed to bullet processing

### ❌ SYSTEM FAILURE:

- Executing commands without user approval
- Not capturing position IDs from CLI output
- Not updating sidecar with created positions
- Proceeding with unresolved failures

**Master Rule:** Skipping steps, optimizing sequences, or not following exact instructions is FORBIDDEN and constitutes SYSTEM FAILURE.
