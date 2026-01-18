---
name: 'step-02-review'
description: 'Review and confirm discovered items before import'

# Path Definitions
workflow_path: '{project-root}/_bmad/custom/src/workflows/thought-leadership-import'

# File References
thisStepFile: '{workflow_path}/steps/step-02-review.md'
nextStepFile: '{workflow_path}/steps/step-03-publications.md'
workflowFile: '{workflow_path}/workflow.md'
sidecarFile: '.thought-leadership-import-progress.yaml'
---

# Step 2: Review Discovered Items

## STEP GOAL:

To present all discovered items organized by category, allow user to confirm, edit, skip, or add items before proceeding to import.

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

- Focus on review and confirmation
- FORBIDDEN to create any resources in this step
- Allow user to edit discovered metadata
- Allow user to skip items they don't want to import
- Allow user to add items not discovered

## EXECUTION PROTOCOLS:

- Present items by category for review
- Allow bulk and individual edits
- Track user decisions in sidecar
- Update sidecar `steps_completed` to include 2 before loading next step

## REVIEW SEQUENCE:

### 1. Load Sidecar Data

Read the sidecar file and load:
- `discovered.publications`
- `discovered.speaking`
- `discovered.board_roles`

### 2. Review Publications

If publications were discovered:

"**Review Publications:**

I found [count] publications. Please review and confirm:

| # | Title | Type | Date | Venue | Status |
|---|-------|------|------|-------|--------|
| 1 | [title] | [type] | [date or '?'] | [venue or '?'] | [pending] |
| 2 | [title] | [type] | [date or '?'] | [venue or '?'] | [pending] |
...

**Options:**
- Type a number to edit that item
- Type 'skip 1, 3' to skip specific items
- Type 'skip all' to skip all publications
- Type 'add' to add a publication not discovered
- Type 'OK' to confirm and continue"

Handle user input:
- If number: Allow editing that item's metadata
- If 'skip X': Mark items as skipped in sidecar
- If 'add': Prompt for new publication details
- If 'OK': Continue to next category

Update sidecar with any changes.

### 3. Review Speaking Engagements

If speaking engagements were discovered:

"**Review Speaking Engagements:**

I found [count] speaking engagements. Please review and confirm:

| # | Title | Type | Date | Venue | Status |
|---|-------|------|------|-------|--------|
| 1 | [title] | [type] | [date or '?'] | [venue or '?'] | [pending] |
...

**Options:**
- Type a number to edit that item
- Type 'skip 1, 3' to skip specific items
- Type 'skip all' to skip all speaking engagements
- Type 'add' to add a speaking engagement not discovered
- Type 'OK' to confirm and continue"

Handle user input similarly to publications.

### 4. Review Board Roles

If board roles were discovered:

"**Review Board/Advisory Roles:**

I found [count] board/advisory roles. Please review and confirm:

| # | Organization | Role | Type | Start | End | Status |
|---|--------------|------|------|-------|-----|--------|
| 1 | [org] | [role] | [type] | [start] | [end or 'current'] | [pending] |
...

**Options:**
- Type a number to edit that item
- Type 'skip 1, 3' to skip specific items
- Type 'skip all' to skip all board roles
- Type 'add' to add a board role not discovered
- Type 'OK' to confirm and continue"

Handle user input similarly.

### 5. Handle Manual Additions

When user types 'add' for any category:

**For Publications:**
"Please provide the publication details:
- **Title:** (required)
- **Type:** article, whitepaper, or book
- **Venue:** Where it was published
- **Date:** YYYY-MM or YYYY-MM-DD
- **URL:** Link to the publication (optional)

You can provide as: `Title | Type | Venue | Date | URL`"

**For Speaking:**
"Please provide the speaking engagement details:
- **Title:** (required)
- **Type:** conference, webinar, or podcast
- **Venue:** Event or show name
- **Date:** YYYY-MM or YYYY-MM-DD
- **URL:** Link to recording (optional)

You can provide as: `Title | Type | Venue | Date | URL`"

**For Board Roles:**
"Please provide the board role details:
- **Organization:** (required)
- **Role:** Your title/position
- **Type:** director, advisory, or committee
- **Start Date:** YYYY-MM
- **End Date:** YYYY-MM or leave empty if current
- **Focus Area:** What you focus on (optional)

You can provide as: `Org | Role | Type | Start | End | Focus`"

Add to sidecar `discovered` section with status: pending.

### 6. Show Review Summary

"**Review Complete!**

**Items to Import:**

| Category | To Import | Skipped |
|----------|-----------|---------|
| Publications | [count] | [count] |
| Speaking | [count] | [count] |
| Board Roles | [count] | [count] |

**Total to import:** [count]

Items marked with '?' for date or venue will prompt for details during import."

### 7. Update Sidecar

Update sidecar file:
- Set `steps_completed` to include 2
- Set `current_step` to 2
- Update all item statuses (pending, skipped)
- Add any manually added items

### 8. Present MENU OPTIONS

Display: **Review Complete - Select an Option:** [C] Continue to Import Publications

#### EXECUTION RULES:

- ALWAYS halt and wait for user input after presenting menu
- ONLY proceed to next step when user selects 'C'
- User can chat or ask questions - always respond and redisplay menu

#### Menu Handling Logic:

- IF C: Update sidecar `steps_completed` to [1, 2], then load, read entire file, then execute {nextStepFile}
- IF user asks questions: Respond helpfully, then redisplay menu

## CRITICAL STEP COMPLETION NOTE

ONLY WHEN C is selected and review is complete will you update sidecar and load {nextStepFile} to begin importing publications.

---

## SYSTEM SUCCESS/FAILURE METRICS

### SUCCESS:

- All categories presented for review
- User able to edit, skip, or add items
- Sidecar updated with user decisions
- Summary shows accurate counts
- Sidecar updated with step 2 completion

### SYSTEM FAILURE:

- Skipping category reviews
- Not allowing edits or additions
- Creating resources in this step
- Not updating sidecar with changes
- Proceeding without user confirmation

**Master Rule:** Skipping steps, optimizing sequences, or not following exact instructions is FORBIDDEN and constitutes SYSTEM FAILURE.
