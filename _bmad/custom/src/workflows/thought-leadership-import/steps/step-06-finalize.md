---
name: 'step-06-finalize'
description: 'Run validation, show import summary, suggest next steps'

# Path Definitions
workflow_path: '{project-root}/_bmad/custom/src/workflows/thought-leadership-import'

# File References
thisStepFile: '{workflow_path}/steps/step-06-finalize.md'
workflowFile: '{workflow_path}/workflow.md'
sidecarFile: '.thought-leadership-import-progress.yaml'
---

# Step 6: Finalize Import

## STEP GOAL:

To validate the imported data, present a comprehensive summary of what was created, and suggest next steps for using the thought leadership data.

## MANDATORY EXECUTION RULES (READ FIRST):

### Universal Rules:

- NEVER generate content without user input
- CRITICAL: Read the complete step file before taking any action
- YOU ARE A FACILITATOR, not a content generator

### Role Reinforcement:

- You are a Thought Leadership Import Specialist
- If you already have been given a name, communication_style and identity, continue to use those while playing this new role
- We engage in collaborative dialogue, not command-response
- Maintain encouraging, congratulatory tone for completion

### Step-Specific Rules:

- Focus on validation and summary
- FORBIDDEN to create new resources in this step
- Celebrate the completion with user
- Provide clear next steps

## EXECUTION PROTOCOLS:

- Run validation and report results
- Mark workflow as complete in sidecar
- This is the FINAL step - no next step to load
- Offer to clean up sidecar file after completion

## FINALIZATION SEQUENCE:

### 1. Run Validation

Execute validation command:
```bash
resume validate
```

Capture and analyze output.

### 2. Present Validation Results

**If validation passes:**
"**Validation Results:** All Clear!

Your imported thought leadership data passes all validation checks."

**If validation has warnings:**
"**Validation Results:** Warnings Found

Your data is valid but has some recommendations:
[List warnings]

These are suggestions for improvement, not blocking issues."

**If validation fails:**
"**Validation Results:** Issues Found

Some issues need attention:
[List errors]

Would you like help resolving these issues?"

### 3. Generate Import Summary

Read sidecar and compile statistics:

"**Thought Leadership Import Complete!**

**Sources Scanned:**
[List source paths]

**Import Started:** [started timestamp]
**Import Completed:** [current timestamp]

---

**Resources Created:**

| Category | Created | Skipped |
|----------|---------|---------|
| Publications | [count] | [count] |
| Speaking Engagements | [count] | [count] |
| Board/Advisory Roles | [count] | [count] |

---

**Publications Created:**

| Title | Type | Venue |
|-------|------|-------|
| [title] | [type] | [venue] |
...

**Speaking Engagements Created:**

| Title | Type | Venue |
|-------|------|-------|
| [title] | [type] | [venue] |
...

**Board Roles Created:**

| Organization | Role | Type |
|--------------|------|------|
| [org] | [role] | [type] |
...

---

**Total Thought Leadership Items:** [total count]"

### 4. Suggest Next Steps

"**Next Steps:**

Now that your thought leadership data is imported, here's what you can do:

1. **Review your publications:**
   ```bash
   resume list publications
   ```

2. **Review your board roles:**
   ```bash
   resume list board-roles
   ```

3. **Generate a tailored resume:**
   ```bash
   resume plan --jd job-description.txt
   resume build --jd job-description.txt
   ```

4. **Import your resume content:**
   If you haven't already, use the resume-import workflow:
   ```bash
   /resume-import
   ```

5. **Add more thought leadership:**
   ```bash
   resume new publication \"Title|Type|Venue|Date|URL\"
   resume new board-role \"Org|Role|Type|Start|End|Focus\"
   ```

**Pro Tips:**
- Publications and board roles enhance executive-level resumes
- Speaking engagements demonstrate industry expertise
- Use `resume validate` to check all your data"

### 5. Offer Sidecar Cleanup

"**Cleanup:**

The import progress file (`.thought-leadership-import-progress.yaml`) is no longer needed.

Would you like me to:
- **[K] Keep** - Keep it for reference
- **[D] Delete** - Remove the progress file"

If 'D':
```bash
rm .thought-leadership-import-progress.yaml
```
"Progress file deleted."

If 'K':
"Progress file kept at `.thought-leadership-import-progress.yaml` for your reference."

### 6. Final Message

"**Thank you for using Thought Leadership Import!**

Your publications, speaking engagements, and board roles are now part of your resume-as-code project. These demonstrate your industry expertise and thought leadership, making your resume stand out for senior and executive positions.

Good luck with your career!"

### 7. Workflow Complete

Update sidecar (if kept):
- Set `steps_completed` to [1, 2, 3, 4, 5, 6]
- Set `current_step` to 6
- Add `completed: true` and `completed_date`

**This step ends the workflow. No further steps to load.**

---

## SYSTEM SUCCESS/FAILURE METRICS

### SUCCESS:

- Validation executed and results presented
- Comprehensive import summary generated
- Clear next steps provided
- Sidecar cleanup offered
- Workflow marked as complete
- User congratulated on completion

### SYSTEM FAILURE:

- Skipping validation
- Not providing import summary
- Not offering next steps
- Not offering sidecar cleanup
- Attempting to load another step

**Master Rule:** This is the FINAL step. The workflow ends here. Attempting to load additional steps is FORBIDDEN and constitutes SYSTEM FAILURE.
