---
name: 'step-01-init'
description: 'Initialize the resume import workflow by loading and parsing the resume file'

# Path Definitions
workflow_path: '{project-root}/_bmad/custom/src/workflows/resume-import'

# File References
thisStepFile: '{workflow_path}/steps/step-01-init.md'
nextStepFile: '{workflow_path}/steps/step-02-review.md'
continueFile: '{workflow_path}/steps/step-01b-continue.md'
workflowFile: '{workflow_path}/workflow.md'
sidecarTemplate: '{workflow_path}/templates/sidecar-template.yaml'

# Sidecar file location (in target project)
sidecarFile: '.resume-import-progress.yaml'
---

# Step 1: Workflow Initialization

## STEP GOAL:

To initialize the resume import workflow by accepting a resume file path, detecting the format, parsing the content, and extracting structured data (positions, certifications, education, bullets).

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

- 🎯 Focus ONLY on loading and parsing the resume
- 🚫 FORBIDDEN to start reframing bullets in this step
- 💬 Handle parsing errors gracefully with helpful suggestions
- 🚪 DETECT existing sidecar and route to continuation if found

## EXECUTION PROTOCOLS:

- 🎯 Show analysis before taking any action
- 💾 Create sidecar file with extracted data
- 📖 Auto-proceed to step 2 after successful extraction
- 🚫 FORBIDDEN to skip extraction validation

## CONTEXT BOUNDARIES:

- Variables from workflow.md are available in memory
- Check for existing sidecar file for continuation
- Input: resume file path from user
- Output: populated sidecar file with extracted structure

## INITIALIZATION SEQUENCE:

### 1. Check for Existing Workflow

First, check if a sidecar file already exists:

- Look for file at `{sidecarFile}` in current directory
- If exists and has `steps_completed` with values, route to step-01b-continue.md
- If not exists or empty, this is a fresh workflow

### 2. Handle Continuation (If Sidecar Exists)

If the sidecar exists and has progress:

- **STOP here** and load `{continueFile}` immediately
- Do not proceed with any initialization tasks
- Let step-01b handle the continuation logic

### 3. Fresh Workflow Setup (If No Sidecar)

If no sidecar exists or sidecar is empty:

#### A. Welcome Message

"Welcome to the Resume Import workflow! I'll help you transform your existing resume into structured resume-as-code data.

I can parse resumes in the following formats:
- **DOCX** - Microsoft Word documents
- **PDF** - PDF files
- **TXT** - Plain text files
- **MD** - Markdown files
- **LinkedIn Export** - CSV files from LinkedIn data export

Please provide the path to your resume file."

#### B. Accept File Path

Wait for user to provide the file path.

Validate the file:
- Check file exists
- Detect format from extension
- Confirm format is supported

#### C. Parse Resume Content

Based on file type, parse the content:

**For DOCX/PDF/TXT/MD:**
- Read the file content
- Extract text preserving structure where possible

**For LinkedIn Export:**
- Look for `Positions.csv`, `Certifications.csv`, `Education.csv`, `Skills.csv`
- Parse each CSV file for structured data

#### D. Extract Structure

From the parsed content, identify and extract:

**Positions:**
- Employer name
- Job title
- Start date (YYYY-MM format)
- End date (YYYY-MM or null for current)
- Bullet points under each position

**Certifications:**
- Certification name
- Issuing organization
- Date obtained
- Expiration date (if any)

**Education:**
- Degree/credential
- Institution
- Graduation year
- Honors (if any)

### 4. Create Sidecar File

Copy template from `{sidecarTemplate}` and populate with:

```yaml
workflow: resume-import
started: [current ISO date]
last_updated: [current ISO date]
current_step: 1
steps_completed: [1]

input:
  file_path: [user provided path]
  file_type: [detected type]
  parse_date: [current ISO date]

extracted:
  positions: [extracted positions array]
  certifications: [extracted certifications array]
  education: [extracted education array]

created:
  positions: []
  work_units: []
  certifications: []
  education: []

processing:
  current_position_index: 0
  current_bullet_index: 0
  position_work_units: []

research_context:
  industry: null
  role_expectations: null
  metric_benchmarks: null
  terminology: []
```

### 5. Show Extraction Summary

Present a summary of what was extracted:

"I've parsed your resume and found:

**Positions:** [count] employment entries
**Certifications:** [count] certifications
**Education:** [count] education entries
**Total Bullets:** [count] bullet points to transform

Proceeding to review the extracted structure..."

### 6. Present MENU OPTIONS

Display: **Proceeding to structure review...**

#### EXECUTION RULES:

- This is an initialization step with auto-proceed
- After successful extraction, proceed directly to next step

#### Menu Handling Logic:

- After sidecar creation and summary display, immediately load, read entire file, then execute `{nextStepFile}` to begin structure review

---

## 🚨 SYSTEM SUCCESS/FAILURE METRICS

### ✅ SUCCESS:

- Resume file successfully parsed
- Structure extracted (positions, certs, education, bullets)
- Sidecar file created with extracted data
- Summary shown to user
- Ready to proceed to step 2
- OR existing workflow properly routed to step-01b-continue.md

### ❌ SYSTEM FAILURE:

- Proceeding without valid file path
- Not detecting file format correctly
- Creating sidecar without extracted data
- Skipping extraction summary
- Not routing to step-01b-continue.md when sidecar exists

**Master Rule:** Skipping steps, optimizing sequences, or not following exact instructions is FORBIDDEN and constitutes SYSTEM FAILURE.

## CRITICAL STEP COMPLETION NOTE

ONLY WHEN initialization is complete and sidecar is created (OR continuation is properly routed), will you then immediately load, read entire file, then execute `{nextStepFile}` to begin structure review.
