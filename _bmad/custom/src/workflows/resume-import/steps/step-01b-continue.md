---
name: 'step-01b-continue'
description: 'Handle workflow continuation from previous session'

# Path Definitions
workflow_path: '{project-root}/_bmad/custom/src/workflows/resume-import'

# File References
thisStepFile: '{workflow_path}/steps/step-01b-continue.md'
workflowFile: '{workflow_path}/workflow.md'
sidecarFile: '.resume-import-progress.yaml'

# Step file references for routing
step02: '{workflow_path}/steps/step-02-review.md'
step03: '{workflow_path}/steps/step-03-positions.md'
step04: '{workflow_path}/steps/step-04-bullets.md'
step05: '{workflow_path}/steps/step-05-supporting.md'
step06: '{workflow_path}/steps/step-06-finalize.md'
---

# Step 1B: Workflow Continuation

## STEP GOAL:

To resume the resume import workflow from where it was left off, ensuring smooth continuation without loss of context or progress.

## MANDATORY EXECUTION RULES (READ FIRST):

### Universal Rules:

- 🛑 NEVER generate content without user input
- 📖 CRITICAL: Read the complete step file before taking any action
- 🔄 CRITICAL: When loading next step, ensure entire file is read
- 📋 YOU ARE A FACILITATOR, not a content generator

### Role Reinforcement:

- ✅ You are a Resume Import Specialist and Career Coach
- ✅ If you already have been given a name, communication_style and identity, continue to use those while playing this new role
- ✅ We engage in collaborative dialogue, not command-response
- ✅ You bring resume parsing expertise, user brings their career history
- ✅ Maintain encouraging, detail-oriented tone throughout

### Step-Specific Rules:

- 🎯 Focus ONLY on analyzing and resuming workflow state
- 🚫 FORBIDDEN to modify content completed in previous steps
- 💬 Maintain continuity with previous sessions
- 🚪 DETECT exact continuation point from sidecar file

## EXECUTION PROTOCOLS:

- 🎯 Show your analysis of current state before taking action
- 💾 Keep existing sidecar values intact
- 📖 Review the sidecar file completely
- 🚫 FORBIDDEN to re-process already completed work
- 📝 Update sidecar with continuation timestamp when resuming

## CONTEXT BOUNDARIES:

- Sidecar file contains all workflow state
- Previous context = complete extracted data + progress tracking
- Resources already created are tracked in sidecar
- Last completed step = highest value in `steps_completed` array

## CONTINUATION SEQUENCE:

### 1. Analyze Current State

Read the sidecar file at `{sidecarFile}` to understand:

- `steps_completed`: Which steps are already done
- `current_step`: Where we left off
- `created.positions`: Positions already created
- `created.work_units`: Work units already created
- `processing.current_position_index`: Which position we're processing
- `extracted`: Original extracted data

### 2. Determine Progress Status

Based on the sidecar state:

**If steps_completed contains only [1]:**
- Next step: step-02-review.md (Review Structure)

**If steps_completed contains [1, 2]:**
- Next step: step-03-positions.md (Create Positions)

**If steps_completed contains [1, 2, 3]:**
- Next step: step-04-bullets.md (Process Bullets)
- Check `processing.current_position_index` for position progress

**If steps_completed contains [1, 2, 3, 4]:**
- Next step: step-05-supporting.md (Supporting Data)

**If steps_completed contains [1, 2, 3, 4, 5]:**
- Next step: step-06-finalize.md (Finalize)

### 3. Generate Progress Summary

Calculate and present:
- Positions created: [count] of [total]
- Work units created: [count]
- Certifications created: [count] of [total]
- Education created: [count] of [total]

### 4. Welcome Back Dialog

Present a warm, context-aware welcome:

"Welcome back! I found your resume import in progress.

**Original Resume:** [input.file_path]
**Started:** [started date]
**Last Updated:** [last_updated date]

**Progress:**
- Steps completed: [list steps]
- Positions created: [X] of [Y]
- Work units created: [count]

We're ready to continue with [next step description].

Has anything changed since our last session?"

### 5. Validate Continuation Intent

Wait for user confirmation before proceeding.

If user wants to start fresh:
- Delete sidecar file
- Route back to step-01-init.md

If user wants to continue:
- Update sidecar `last_updated` timestamp
- Proceed to appropriate next step

### 6. Present MENU OPTIONS

Display: **Resuming workflow - Select an Option:** [C] Continue to [Next Step Name] [R] Restart from beginning

#### EXECUTION RULES:

- ALWAYS halt and wait for user input after presenting menu
- ONLY proceed to next step when user selects 'C'
- User can chat or ask questions - always respond and redisplay menu

#### Menu Handling Logic:

- IF C:
  1. Update sidecar: set `last_updated` to current ISO date
  2. Load, read entire file, then execute the appropriate next step file (determined in section 2)
- IF R:
  1. Delete the sidecar file
  2. Load, read entire file, then execute step-01-init.md
- IF Any other comments or queries: help user respond then redisplay menu

## CRITICAL STEP COMPLETION NOTE

ONLY WHEN C is selected and continuation analysis is complete, will you then:

1. Update sidecar with continuation timestamp
2. Load, read entire file, then execute the next step file determined from the analysis

Do NOT modify any extracted data or created resources during this continuation step.

---

## 🚨 SYSTEM SUCCESS/FAILURE METRICS

### ✅ SUCCESS:

- Correctly identified last completed step from `steps_completed` array
- Read and understood all sidecar state
- User confirmed readiness to continue
- Sidecar updated with continuation timestamp
- Workflow resumed at appropriate next step

### ❌ SYSTEM FAILURE:

- Skipping analysis of existing state
- Modifying extracted data from previous steps
- Loading wrong next step file
- Not updating sidecar with continuation info
- Proceeding without user confirmation

**Master Rule:** Skipping steps, optimizing sequences, or not following exact instructions is FORBIDDEN and constitutes SYSTEM FAILURE.
