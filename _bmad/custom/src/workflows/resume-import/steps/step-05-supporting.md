---
name: 'step-05-supporting'
description: 'Create certifications, education entries, and optional career highlights'

# Path Definitions
workflow_path: '{project-root}/_bmad/custom/src/workflows/resume-import'

# File References
thisStepFile: '{workflow_path}/steps/step-05-supporting.md'
nextStepFile: '{workflow_path}/steps/step-06-finalize.md'
workflowFile: '{workflow_path}/workflow.md'
sidecarFile: '.resume-import-progress.yaml'
---

# Step 5: Supporting Data Creation

## STEP GOAL:

To create certifications, education entries, and optionally suggest career highlights from the imported work units.

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
- ✅ You bring expertise in resume completeness
- ✅ Maintain encouraging, detail-oriented tone throughout

### Step-Specific Rules:

- 🎯 Focus on certifications, education, and highlights
- 🚫 FORBIDDEN to execute commands without user confirmation
- 💬 Allow user to skip any category
- 📋 Track created resources in sidecar

## EXECUTION PROTOCOLS:

- 🎯 Process each category with user confirmation
- 💾 Update sidecar with created resources
- 📖 Update sidecar `steps_completed` to include 5 before loading next step
- 🚫 Categories marked as skipped in step 2 should be skipped here

## CONTEXT BOUNDARIES:

- Certifications and education confirmed in step 2
- User may have skipped categories
- Career highlights are optional suggestions
- All commands need user approval

## SUPPORTING DATA SEQUENCE:

### 1. Load Sidecar Data

Read the sidecar file and load:
- `extracted.certifications` - Confirmed certifications
- `extracted.education` - Confirmed education
- `created.work_units` - For highlight suggestions

### 2. Create Certifications

If certifications were not skipped and exist:

"**Creating Certifications:**"

For each certification, generate command:
```bash
resume new certification "[name]|[issuer]|[date]|[expires]"
```

Present commands:
"I'll create the following certifications:

```bash
resume new certification \"[name]|[issuer]|[date]|[expires]\"
resume new certification \"[name]|[issuer]|[date]|[expires]\"
```

Type 'GO' to create all, or 'SKIP' to skip certifications."

Upon 'GO':
- Execute each command
- Capture results
- Update sidecar `created.certifications`

If certifications were skipped:
"Certifications were skipped during review. Moving on..."

### 3. Create Education

If education was not skipped and exists:

"**Creating Education Entries:**"

For each education entry, generate command:
```bash
resume new education "[degree]|[institution]|[year]|[honors]"
```

Present commands:
"I'll create the following education entries:

```bash
resume new education \"[degree]|[institution]|[year]|[honors]\"
resume new education \"[degree]|[institution]|[year]|[honors]\"
```

Type 'GO' to create all, or 'SKIP' to skip education."

Upon 'GO':
- Execute each command
- Capture results
- Update sidecar `created.education`

If education was skipped:
"Education was skipped during review. Moving on..."

### 4. Suggest Career Highlights (Optional)

Analyze created work units to identify top achievements:

"**Career Highlights (Optional):**

Based on your imported work units, here are some standout achievements that could work as career highlights:

1. \"[Achievement from most impactful work unit]\"
2. \"[Achievement with largest metrics]\"
3. \"[Leadership or strategic achievement]\"

Career highlights appear in executive resume formats. Would you like to:
- Type 'ADD' to add these as career highlights
- Type 'EDIT' to modify them first
- Type 'SKIP' to skip career highlights for now"

If 'ADD':
For each highlight:
```bash
resume new highlight --text "[highlight text]"
```

If 'EDIT':
Allow user to modify, then create.

If 'SKIP':
Continue without creating highlights.

### 5. Show Creation Summary

"**Supporting Data Created:**

**Certifications:**
[✓ or SKIPPED] [list of created certifications]

**Education:**
[✓ or SKIPPED] [list of created education entries]

**Career Highlights:**
[✓ or SKIPPED] [list of created highlights]"

### 6. Update Sidecar

Update sidecar file:
- Set `steps_completed` to include 5
- Set `current_step` to 5
- Update `created` section with all created resources

### 7. Present MENU OPTIONS

Display: **Supporting Data Complete - Select an Option:** [C] Continue to Finalize

#### EXECUTION RULES:

- ALWAYS halt and wait for user input after presenting menu
- ONLY proceed to next step when user selects 'C'
- User can chat or ask questions - always respond and redisplay menu

#### Menu Handling Logic:

- IF C: Update sidecar `steps_completed` to [1, 2, 3, 4, 5], then load, read entire file, then execute {nextStepFile}
- IF Any other comments or queries: help user respond then redisplay menu

## CRITICAL STEP COMPLETION NOTE

ONLY WHEN C is selected and all supporting data is created (or explicitly skipped), will you then load, read entire file, then execute {nextStepFile} to finalize the import.

---

## 🚨 SYSTEM SUCCESS/FAILURE METRICS

### ✅ SUCCESS:

- Certifications created (or properly skipped)
- Education created (or properly skipped)
- Career highlights offered and handled
- All resources tracked in sidecar
- Sidecar updated with step 5 completion

### ❌ SYSTEM FAILURE:

- Executing commands without user approval
- Not respecting skip decisions from step 2
- Not offering career highlights option
- Not updating sidecar with created resources

**Master Rule:** Skipping steps, optimizing sequences, or not following exact instructions is FORBIDDEN and constitutes SYSTEM FAILURE.
