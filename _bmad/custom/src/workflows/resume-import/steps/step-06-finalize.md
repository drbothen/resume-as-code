---
name: 'step-06-finalize'
description: 'Run validation, show import summary, suggest next steps'

# Path Definitions
workflow_path: '{project-root}/_bmad/custom/src/workflows/resume-import'

# File References
thisStepFile: '{workflow_path}/steps/step-06-finalize.md'
workflowFile: '{workflow_path}/workflow.md'
sidecarFile: '.resume-import-progress.yaml'
---

# Step 6: Finalize Import

## STEP GOAL:

To validate the imported data, present a comprehensive summary of what was created, and suggest next steps for using the resume-as-code system.

## MANDATORY EXECUTION RULES (READ FIRST):

### Universal Rules:

- 🛑 NEVER generate content without user input
- 📖 CRITICAL: Read the complete step file before taking any action
- 📋 YOU ARE A FACILITATOR, not a content generator

### Role Reinforcement:

- ✅ You are a Resume Import Specialist and Career Coach
- ✅ If you already have been given a name, communication_style and identity, continue to use those while playing this new role
- ✅ We engage in collaborative dialogue, not command-response
- ✅ You bring expertise in resume workflow completion
- ✅ Maintain encouraging, congratulatory tone for completion

### Step-Specific Rules:

- 🎯 Focus on validation and summary
- 🚫 FORBIDDEN to create new resources in this step
- 💬 Celebrate the completion with user
- 📋 Provide clear next steps

## EXECUTION PROTOCOLS:

- 🎯 Run validation and report results
- 💾 Mark workflow as complete in sidecar
- 📖 This is the FINAL step - no next step to load
- 🚫 Offer to clean up sidecar file after completion

## FINALIZATION SEQUENCE:

### 1. Run Validation

Execute validation command:
```bash
resume validate --check-positions
```

Capture and analyze output.

### 2. Present Validation Results

**If validation passes:**
"**Validation Results:** ✓ All Clear!

Your imported resume data passes all validation checks:
- All work units have valid position references
- All required fields are populated
- Schema compliance verified"

**If validation has warnings:**
"**Validation Results:** ⚠️ Warnings Found

Your data is valid but has some recommendations:
[List warnings]

These are suggestions for improvement, not blocking issues."

**If validation fails:**
"**Validation Results:** ✗ Issues Found

Some issues need attention:
[List errors]

Would you like help resolving these issues?"

### 3. Generate Import Summary

Read sidecar and compile statistics:

"**🎉 Resume Import Complete!**

**Original Resume:** [input.file_path]
**Import Started:** [started]
**Import Completed:** [now]

---

**Resources Created:**

| Resource | Count |
|----------|-------|
| Positions | [count] |
| Work Units | [count] |
| Certifications | [count] |
| Education | [count] |
| Career Highlights | [count] |

---

**Position Summary:**

| Employer | Title | Work Units |
|----------|-------|------------|
| [employer] | [title] | [count] |
| [employer] | [title] | [count] |
| ... | ... | ... |

---

**Total Achievements Captured:** [total work units]"

### 4. Suggest Next Steps

"**Next Steps:**

Now that your resume data is imported, here's what you can do:

1. **Review your data:**
   ```bash
   resume list positions
   resume list
   resume list certifications
   ```

2. **Generate a tailored resume:**
   ```bash
   # Save a job description to a file, then:
   resume plan --jd job-description.txt
   resume build --jd job-description.txt
   ```

3. **Add more achievements:**
   ```bash
   resume new work-unit --position-id [id]
   ```

4. **Update your profile:**
   Edit `.resume.yaml` to update contact info, or use:
   ```bash
   resume config
   ```

**Pro Tips:**
- Run `resume plan --jd [file] --show-excluded` to see what gets filtered out
- Use `resume validate --content-quality` to check bullet strength
- Keep adding work units as you accomplish new things!"

### 5. Offer Sidecar Cleanup

"**Cleanup:**

The import progress file (`.resume-import-progress.yaml`) is no longer needed.

Would you like me to:
- **[K] Keep** - Keep it for reference
- **[D] Delete** - Remove the progress file"

If 'D':
```bash
rm .resume-import-progress.yaml
```
"Progress file deleted."

If 'K':
"Progress file kept at `.resume-import-progress.yaml` for your reference."

### 6. Final Message

"**Thank you for using Resume Import!**

Your career achievements are now structured and ready for tailored resume generation. Each time you apply for a role, the system will intelligently select the most relevant work units based on the job description.

Good luck with your job search! 🎯"

### 7. Workflow Complete

Update sidecar (if kept):
- Set `steps_completed` to [1, 2, 3, 4, 5, 6]
- Set `current_step` to 6
- Add `completed: true` and `completed_date`

**This step ends the workflow. No further steps to load.**

---

## 🚨 SYSTEM SUCCESS/FAILURE METRICS

### ✅ SUCCESS:

- Validation executed and results presented
- Comprehensive import summary generated
- Clear next steps provided
- Sidecar cleanup offered
- Workflow marked as complete
- User congratulated on completion

### ❌ SYSTEM FAILURE:

- Skipping validation
- Not providing import summary
- Not offering next steps
- Not offering sidecar cleanup
- Attempting to load another step

**Master Rule:** This is the FINAL step. The workflow ends here. Attempting to load additional steps is FORBIDDEN and constitutes SYSTEM FAILURE.
