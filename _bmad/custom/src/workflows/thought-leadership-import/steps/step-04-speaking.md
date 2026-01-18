---
name: 'step-04-speaking'
description: 'Import speaking engagements (conferences, webinars, podcasts) via CLI'

# Path Definitions
workflow_path: '{project-root}/_bmad/custom/src/workflows/thought-leadership-import'

# File References
thisStepFile: '{workflow_path}/steps/step-04-speaking.md'
nextStepFile: '{workflow_path}/steps/step-05-board-roles.md'
workflowFile: '{workflow_path}/workflow.md'
sidecarFile: '.thought-leadership-import-progress.yaml'
---

# Step 4: Import Speaking Engagements

## STEP GOAL:

To create publication entries for all confirmed speaking engagements (conferences, webinars, podcasts) using the resume CLI, eliciting any missing metadata.

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
- You bring expertise in content organization
- Maintain helpful, detail-oriented tone throughout

### Step-Specific Rules:

- Process speaking engagements iteratively with user confirmation
- FORBIDDEN to execute commands without user approval
- Elicit missing metadata before creating
- Track created items in sidecar

## EXECUTION PROTOCOLS:

- Process one speaking engagement at a time
- Elicit missing date, venue, or URL
- Show CLI command before execution
- Update sidecar after each creation

## CONTEXT BOUNDARIES:

- Speaking engagements confirmed in step 2 are in sidecar
- Items marked 'skipped' should be skipped
- Uses `resume new publication` with speaking-specific types

## SPEAKING IMPORT SEQUENCE:

### 1. Load Speaking Data

Read the sidecar file and load:
- `discovered.speaking` - All confirmed speaking engagements
- Filter to only items with status: pending

If no speaking engagements to import:
"**No speaking engagements to import.** Moving to board roles..."
Skip to menu options.

### 2. Check for Missing Metadata

For each pending speaking engagement, identify missing fields:
- title (required) - Talk title
- type (required: conference, webinar, podcast)
- venue (required) - Event/show name
- date (recommended)
- url (optional) - Link to recording

### 3. Process Each Speaking Engagement

For each speaking engagement with status: pending:

**If metadata is complete:**

"**Speaking Engagement [n] of [total]:**

- **Title:** [title]
- **Type:** [type]
- **Venue:** [venue/event name]
- **Date:** [date]
- **URL:** [url or 'none']

Command to execute:
```bash
resume new publication \"[title]|[type]|[venue]|[date]|[url]\"
```

Type 'GO' to create, 'EDIT' to modify, or 'SKIP' to skip this engagement."

**If metadata is incomplete:**

"**Speaking Engagement [n] of [total]:**

- **Title:** [title]
- **Type:** [type or '?']
- **Venue:** [venue or '?']
- **Date:** [date or '?']
- **URL:** [url or 'none']

**Missing information needed:**

For speaking engagements, I need:
- **Venue/Event:** The conference, podcast show, or webinar series name
- **Date:** When you presented (YYYY-MM or YYYY-MM-DD)
[List any other missing fields]

Please provide the missing details, or type 'SKIP' to skip this engagement."

Wait for user input. Once complete, show the command and ask for confirmation.

### 4. Execute CLI Command

Upon user typing 'GO':

```bash
resume new publication "[title]|[type]|[venue]|[date]|[url]"
```

Note: Speaking engagements use the `publication` command with types: conference, webinar, podcast.

Capture output and verify success.

Update sidecar:
- Set speaking item status to 'created'
- Add to `created.speaking` array

Show result:
"**Created:** [title] at [venue] ([type])"

### 5. Handle Edits

If user types 'EDIT':
- Ask which field to edit
- Update the value
- Re-display the command for confirmation

### 6. Handle Skip

If user types 'SKIP':
- Update sidecar: set status to 'skipped'
- Continue to next speaking engagement

### 7. Show Progress

After each speaking engagement:
"**Progress:** [completed] of [total] speaking engagements processed"

### 8. Speaking Import Summary

After all speaking engagements processed:

"**Speaking Engagement Import Complete!**

| Status | Count |
|--------|-------|
| Created | [count] |
| Skipped | [count] |

**Speaking Engagements Created:**
- [title 1] at [venue 1] ([type])
- [title 2] at [venue 2] ([type])
..."

### 9. Update Sidecar

Update sidecar file:
- Set `steps_completed` to include 4
- Set `current_step` to 4
- Update all speaking engagement statuses

### 10. Present MENU OPTIONS

Display: **Speaking Engagements Complete - Select an Option:** [C] Continue to Board Roles

#### EXECUTION RULES:

- ALWAYS halt and wait for user input after presenting menu
- ONLY proceed to next step when user selects 'C'
- User can chat or ask questions - always respond and redisplay menu

#### Menu Handling Logic:

- IF C: Update sidecar `steps_completed` to [1, 2, 3, 4], then load, read entire file, then execute {nextStepFile}
- IF user asks questions: Respond helpfully, then redisplay menu

## CRITICAL STEP COMPLETION NOTE

ONLY WHEN C is selected and all speaking engagements are processed will you update sidecar and load {nextStepFile} to begin importing board roles.

---

## SYSTEM SUCCESS/FAILURE METRICS

### SUCCESS:

- All pending speaking engagements processed
- Missing metadata elicited from user
- CLI commands executed with user approval
- Progress tracked in sidecar
- Summary shows accurate counts

### SYSTEM FAILURE:

- Executing commands without user approval
- Skipping engagements without user consent
- Not eliciting missing metadata
- Not updating sidecar after each creation
- Batch processing without confirmation

**Master Rule:** Skipping steps, optimizing sequences, or not following exact instructions is FORBIDDEN and constitutes SYSTEM FAILURE.
