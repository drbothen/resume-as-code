---
name: 'step-01-init'
description: 'Initialize workflow, scan sources, detect content types'

# Path Definitions
workflow_path: '{project-root}/_bmad/custom/src/workflows/thought-leadership-import'

# File References
thisStepFile: '{workflow_path}/steps/step-01-init.md'
nextStepFile: '{workflow_path}/steps/step-02-review.md'
workflowFile: '{workflow_path}/workflow.md'
sidecarFile: '.thought-leadership-import-progress.yaml'
---

# Step 1: Initialize and Scan Sources

## STEP GOAL:

To identify the source(s) of thought leadership content, scan for publications, speaking engagements, and board roles, and prepare the data for user review.

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
- You bring expertise in content organization and metadata extraction
- Maintain helpful, detail-oriented tone throughout

### Step-Specific Rules:

- Focus on discovering and cataloging content
- FORBIDDEN to create any resources in this step
- Ask clarifying questions about source locations
- Support multiple source types

## EXECUTION PROTOCOLS:

- Scan all provided sources thoroughly
- Extract metadata from frontmatter and filenames
- Categorize content by type (publication, speaking, board role)
- Create sidecar file with discovered items

## INITIALIZATION SEQUENCE:

### 1. Welcome and Source Discovery

Present welcome message:

"**Welcome to Thought Leadership Import!**

I'll help you import your publications, speaking engagements, and board roles into your resume-as-code project.

**What sources would you like to import from?**

Common sources include:
- **Git repo with articles** - Directory containing markdown files with your published content
- **Speaking/events list** - CSV, YAML, or text file listing your talks and presentations
- **Board roles document** - File listing your advisory and board positions

Please provide the path(s) to your source(s). You can provide multiple paths separated by commas.

Example: `~/repos/my-blog, ~/documents/speaking-history.csv`"

Wait for user input.

### 2. Validate Source Paths

For each provided path:
- Check if path exists
- Determine source type (directory, file, git repo)
- Identify file types present

If path doesn't exist:
"I couldn't find `[path]`. Please check the path and try again."

### 3. Scan Sources

For each valid source:

**If directory/git repo:**
- List all `.md` files
- For each markdown file:
  - Read frontmatter (YAML between `---` markers)
  - Extract: title, date, type, tags, venue, url
  - If no frontmatter, try to extract from filename pattern: `YYYY-MM-DD-title-slug.md`
  - Categorize as publication (article/whitepaper) based on content

**If CSV file:**
- Read header row to identify columns
- Map columns to fields (title, type, date, venue, url)
- Extract each row as a potential item

**If YAML/JSON file:**
- Parse structured data
- Extract items with their metadata

**If plain text:**
- Parse line by line
- Look for patterns: "Title - Venue - Date"

### 4. Categorize Discovered Items

Group items into categories:

**Publications:**
- Articles (blog posts, online articles)
- Whitepapers (technical documents)
- Books (full books or chapters)

**Speaking Engagements:**
- Conference talks
- Webinars
- Podcasts

**Board/Advisory Roles:**
- Director positions
- Advisory board
- Committee memberships

### 5. Create Sidecar File

Create `.thought-leadership-import-progress.yaml`:

```yaml
workflow: thought-leadership-import
started: [current timestamp]
last_updated: [current timestamp]
current_step: 1
steps_completed: []

sources:
  - path: [source path]
    type: [directory|file|git]
    files_found: [count]

discovered:
  publications:
    - title: "[title]"
      type: "[article|whitepaper|book]"
      date: "[date or null]"
      venue: "[venue or null]"
      url: "[url or null]"
      source_file: "[original file path]"
      status: pending

  speaking:
    - title: "[title]"
      type: "[conference|webinar|podcast]"
      date: "[date or null]"
      venue: "[venue or null]"
      url: "[url or null]"
      source_file: "[original file path]"
      status: pending

  board_roles:
    - organization: "[org name]"
      role: "[role title]"
      type: "[director|advisory|committee]"
      start_date: "[date or null]"
      end_date: "[date or null]"
      focus: "[focus area or null]"
      status: pending

created:
  publications: []
  speaking: []
  board_roles: []
```

### 6. Present Discovery Summary

"**Discovery Complete!**

**Sources Scanned:**
- [source 1]: [file count] files
- [source 2]: [file count] files

**Items Found:**

| Category | Count | With Complete Metadata |
|----------|-------|------------------------|
| Publications | [count] | [count with date+title] |
| Speaking Engagements | [count] | [count with date+title+venue] |
| Board/Advisory Roles | [count] | [count with org+role] |

**Total items to import:** [total count]

Some items may need additional information (dates, venues, URLs) which we'll gather in the next steps."

### 7. Present MENU OPTIONS

Display: **Source Scan Complete - Select an Option:** [C] Continue to Review

#### EXECUTION RULES:

- ALWAYS halt and wait for user input after presenting menu
- ONLY proceed to next step when user selects 'C'
- User can chat or ask questions - always respond and redisplay menu

#### Menu Handling Logic:

- IF C: Update sidecar `steps_completed` to [1], then load, read entire file, then execute {nextStepFile}
- IF user asks questions: Respond helpfully, then redisplay menu

## CRITICAL STEP COMPLETION NOTE

ONLY WHEN C is selected will you update sidecar and load {nextStepFile} to begin reviewing discovered items.

---

## SYSTEM SUCCESS/FAILURE METRICS

### SUCCESS:

- All provided source paths validated
- Sources scanned for content
- Items categorized by type
- Sidecar file created with discovered items
- Summary presented to user

### SYSTEM FAILURE:

- Skipping source validation
- Not scanning all files in directories
- Creating resources before review step
- Not creating sidecar file
- Proceeding without user confirmation

**Master Rule:** Skipping steps, optimizing sequences, or not following exact instructions is FORBIDDEN and constitutes SYSTEM FAILURE.
