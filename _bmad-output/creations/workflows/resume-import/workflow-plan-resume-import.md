---
stepsCompleted: [1, 2, 3, 4, 6, 7, 8]
---

# Workflow Creation Plan: resume-import

## Initial Project Context

- **Module:** bmm
- **Target Location:** _bmad/custom/src/workflows/resume-import/
- **Created:** 2026-01-17

## Workflow Overview

**Purpose:** Parse existing resume documents (DOCX, PDF) and transform them into structured resume-as-code data with proper PAR (Problem-Action-Result) formatting.

**Problem Solved:** Users with existing resumes want to migrate to resume-as-code without manually recreating all their positions, work units, certifications, and education entries.

**Target Users:** Resume-as-code users migrating existing resumes

## Key Features (from user requirements)

1. **Resume Parsing** - Extract structured data from resume documents
2. **Position Extraction** - Identify employers, titles, dates
3. **Bullet Reframing** - Transform vague bullets into PAR format
4. **Elicitation Support** - Ask clarifying questions to improve content
5. **Confirmation Before Creation** - User approval before CLI commands
6. **CLI Integration** - Use `resume new position`, `resume new work-unit`, etc.

## Initial Workflow Concept

```
┌─────────────────────────────────────────────────────────────────┐
│                      resume-import workflow                     │
├─────────────────────────────────────────────────────────────────┤
│  Step 1: Load Resume                                            │
│  ├─ Accept file path (DOCX, PDF)                                │
│  └─ Parse and extract raw text                                  │
├─────────────────────────────────────────────────────────────────┤
│  Step 2: Extract Structure                                      │
│  ├─ Identify positions (employer, title, dates)                 │
│  ├─ Identify certifications                                     │
│  ├─ Identify education                                          │
│  └─ Identify bullet points per position                         │
├─────────────────────────────────────────────────────────────────┤
│  Step 3: Elicit & Reframe                                       │
│  ├─ For each bullet, ask clarifying questions                   │
│  ├─ Transform to PAR format                                     │
│  ├─ Suggest skills and tags                                     │
│  └─ User confirms or edits each work unit                       │
├─────────────────────────────────────────────────────────────────┤
│  Step 4: Create Resources                                       │
│  ├─ Show commands to be executed                                │
│  ├─ User confirms batch or individual creation                  │
│  └─ Execute resume CLI commands                                 │
├─────────────────────────────────────────────────────────────────┤
│  Step 5: Summary & Review                                       │
│  ├─ Show created resources                                      │
│  └─ Suggest next steps (validate, plan, build)                  │
└─────────────────────────────────────────────────────────────────┘
```

## Notes

- Workflow should handle incomplete or vague resume bullets gracefully
- Elicitation is key - many resume bullets lack quantified impact
- Should support batch processing with individual confirmation

---

## Detailed Requirements (Step 2)

### 1. Workflow Type Classification

**Hybrid: Action + Interactive Workflow**
- Action component: Executes CLI commands (`resume new position`, `resume new work-unit`, etc.)
- Interactive component: Guides user through elicitation and confirmation at each step

### 2. Workflow Flow Pattern

**Iterative with Phases**
```
Phase 1: Load & Parse
Phase 2: Extract & Review Structure
Phase 3: Elicit & Reframe (iterative per position)
Phase 4: Create Resources (with confirmation)
Phase 5: Summary & Next Steps
```

### 3. User Interaction Style

- **Highly Collaborative**: User involved at every major decision point
- **Confirmation Required**: No CLI commands executed without explicit approval
- **Elicitation Focus**: Smart questioning to improve weak bullets
- **Adaptive**: Skip elicitation for bullets that are already strong (have metrics, clear outcomes)

### 4. Instruction Style

**Intent-Based** with some prescriptive elements:
- Intent-based for elicitation conversations (natural, adaptive)
- Prescriptive for CLI command generation (exact format required)

### 5. Input Requirements

| Input | Required | Description |
|-------|----------|-------------|
| Resume file path | Yes | DOCX or PDF file |
| Target project directory | Yes | Where `.resume.yaml` exists |

**Supported Formats:**
- Primary: DOCX (most common)
- Secondary: PDF (may have parsing limitations)
- Future: Plain text, LinkedIn exports

### 6. Output Specifications

**Primary Outputs:**
- Created positions in `positions.yaml`
- Created work unit files in `work-units/` directory
- Created certifications in `.resume.yaml`
- Created education entries in `.resume.yaml`

**Intermediate Outputs:**
- Extracted structure summary (for user review)
- PAR-formatted bullets (before CLI execution)
- Command preview (before execution)

### 7. Success Criteria

| Criterion | Measure |
|-----------|---------|
| Complete extraction | All positions, certs, education identified |
| Quality transformation | Bullets converted to PAR format with metrics where possible |
| User satisfaction | User confirms each work unit before creation |
| CLI success | All commands execute without error |
| Project valid | `resume validate` passes after import |

### 8. Design Decisions

- **Elicitation depth**: Elicit only for weak bullets (no metrics, vague outcomes)
- **Batch vs Individual**: Create positions first (batch), then work units per position (individual confirmation)
- **Partial imports**: Yes, allow users to skip sections
- **Error handling**: Continue on individual failures, report at end

---

## Tools Configuration (Step 3)

### Supported Input Formats

| Format | Parsing Approach |
|--------|------------------|
| **DOCX** | python-docx library |
| **PDF** | PyPDF2 or pdfplumber |
| **Plain Text (.txt)** | Direct file read |
| **Markdown (.md)** | Direct file read with structure preservation |
| **LinkedIn Export** | Parse CSV files from LinkedIn data export ZIP |

### Core BMAD Tools

| Tool | Included | Integration Points |
|------|----------|-------------------|
| **Party-Mode** | No | Not needed - single-user workflow |
| **Advanced Elicitation** | **Yes** | Step 3 (Elicit & Reframe) - improve weak bullets |
| **Brainstorming** | No | Elicitation covers requirements |

### LLM Features

| Feature | Included | Use Cases |
|---------|----------|-----------|
| **Web-Browsing / Perplexity** | **Yes** | Research industry context, terminology, metric benchmarks for PAR reframing |
| **File I/O** | **Yes** | Read all resume formats, write work unit files |
| **Sub-Agents** | No | Sequential processing sufficient |
| **Sub-Processes** | No | Sequential processing sufficient |

### Web Research Integration

**Integration Point:** Step 3 (Elicit & Reframe)

**Research triggers:**
- Before reframing each position's bullets, research role/industry context
- When user provides target job title or company, research specific expectations
- When quantifying impact, research industry benchmarks for comparison

**Use Cases:**
1. Industry terminology - Current buzzwords and jargon for target roles
2. Metric benchmarks - What "good" looks like for specific achievements
3. Action verb trends - Which verbs resonate for specific roles
4. Role expectations - What hiring managers look for in positions
5. Company research - Align language to target company values (optional)

### Memory Systems

| System | Included | Purpose |
|--------|----------|---------|
| **Sidecar File** | **Yes** | Save import progress for large resumes or interrupted sessions |

### External Integrations

None required - resume CLI via Bash provides all needed functionality.

### Installation Requirements

- **No additional installations required** - all tools are built-in or use standard Python libraries
- Resume parsing libraries (python-docx, PyPDF2) are recommendations for the workflow user's environment

---

## Workflow Structure Design (Step 6)

### Step Overview

| Step | Name | Purpose | User Input |
|------|------|---------|------------|
| 1 | Init | Load resume, parse, extract structure | File path only |
| 1b | Continue | Resume from sidecar if interrupted | Confirm resume |
| 2 | Review Structure | Confirm/edit extracted data | Medium |
| 3 | Create Positions | Batch create positions via CLI | Confirm batch |
| 4 | Process Bullets | Elicit, research, reframe, create work units | **High** (iterative) |
| 5 | Supporting Data | Create certs, education, highlights | Confirm each |
| 6 | Finalize | Validate, summarize, suggest next steps | None |

### Continuation Support

**Enabled:** Yes - uses sidecar file for progress tracking

**Sidecar tracks:**
- Current step
- Positions created (IDs)
- Work units created (IDs)
- Positions pending processing
- Original extracted data

### Step Flow Diagram

```
┌──────────────┐
│  Step 1      │
│  Init        │──────────┐
└──────┬───────┘          │
       │                  │ (sidecar exists)
       │ (new)            ▼
       │           ┌──────────────┐
       │           │  Step 1b     │
       │           │  Continue    │
       │           └──────┬───────┘
       │                  │
       ▼                  ▼
┌──────────────┐
│  Step 2      │
│  Review      │
└──────┬───────┘
       │
       ▼
┌──────────────┐
│  Step 3      │
│  Positions   │
└──────┬───────┘
       │
       ▼
┌──────────────┐
│  Step 4      │◄────┐
│  Bullets     │     │ (loop per position)
└──────┬───────┘─────┘
       │
       ▼
┌──────────────┐
│  Step 5      │
│  Supporting  │
└──────┬───────┘
       │
       ▼
┌──────────────┐
│  Step 6      │
│  Finalize    │
└──────────────┘
```

### Interaction Patterns by Step

**Step 1 - Init:**
- Auto-proceed after successful parse
- No menu (initialization step)

**Step 1b - Continue:**
- Menu: [C] Continue to next step

**Step 2 - Review:**
- Menu: [A] Advanced Elicitation [P] Party Mode [C] Continue

**Step 3 - Create Positions:**
- Menu: [C] Continue (after confirmation)

**Step 4 - Process Bullets (Iterative):**
- Per-position loop with research + elicitation
- Menu: [S] Skip position [N] Next position [F] Finish all

**Step 5 - Supporting Data:**
- Menu: [C] Continue (after confirmation)

**Step 6 - Finalize:**
- No menu (final step)
- Presents summary and ends workflow

### File Structure

```
_bmad/custom/src/workflows/resume-import/
├── workflow.md
├── steps/
│   ├── step-01-init.md
│   ├── step-01b-continue.md
│   ├── step-02-review.md
│   ├── step-03-positions.md
│   ├── step-04-bullets.md
│   ├── step-05-supporting.md
│   └── step-06-finalize.md
└── templates/
    └── sidecar-template.yaml
```

### AI Role Definition

| Aspect | Value |
|--------|-------|
| **Role** | Resume Import Specialist & Career Coach |
| **Expertise** | Resume writing, PAR formatting, industry terminology |
| **Tone** | Collaborative, encouraging, detail-oriented |
| **Style** | Intent-based for elicitation, prescriptive for CLI commands |

### Error Handling

| Scenario | Handling |
|----------|----------|
| Parse failure | Show error, suggest alternative format |
| CLI command failure | Log error, continue with next item, report at end |
| Invalid position reference | Skip work unit, warn user |
| User cancels mid-workflow | Save progress to sidecar |

### Success Criteria

- All extracted positions created in `positions.yaml`
- All bullets transformed to PAR format work units
- All certifications and education entries created
- `resume validate` passes without errors
- User satisfied with reframed content

---

## Build Summary (Step 7)

### Files Created

| File | Path | Purpose |
|------|------|---------|
| `workflow.md` | `_bmad/custom/src/workflows/resume-import/workflow.md` | Main workflow configuration |
| `step-01-init.md` | `_bmad/custom/src/workflows/resume-import/steps/step-01-init.md` | Initialize, parse resume |
| `step-01b-continue.md` | `_bmad/custom/src/workflows/resume-import/steps/step-01b-continue.md` | Resume from sidecar |
| `step-02-review.md` | `_bmad/custom/src/workflows/resume-import/steps/step-02-review.md` | Review extracted structure |
| `step-03-positions.md` | `_bmad/custom/src/workflows/resume-import/steps/step-03-positions.md` | Create positions via CLI |
| `step-04-bullets.md` | `_bmad/custom/src/workflows/resume-import/steps/step-04-bullets.md` | Elicit, research, reframe (iterative) |
| `step-05-supporting.md` | `_bmad/custom/src/workflows/resume-import/steps/step-05-supporting.md` | Create certs, education, highlights |
| `step-06-finalize.md` | `_bmad/custom/src/workflows/resume-import/steps/step-06-finalize.md` | Validate and summarize |
| `sidecar-template.yaml` | `_bmad/custom/src/workflows/resume-import/templates/sidecar-template.yaml` | Progress tracking template |

### Build Statistics

- **Total files created:** 9
- **Step files:** 7 (including continuation step)
- **Template files:** 1
- **Configuration files:** 1

### Installation Required

To make this workflow available, add it to the BMAD skills list or invoke directly:

```bash
# Direct invocation (after installation)
/resume-import

# Or load workflow.md directly
```

### Testing Recommendations

1. **Test with sample resume:**
   - Use a simple DOCX or TXT resume
   - Verify parsing extracts positions correctly
   - Test elicitation flow with weak bullets

2. **Test continuation:**
   - Start workflow, stop mid-process
   - Resume and verify state is preserved

3. **Test error handling:**
   - Provide invalid file path
   - Test with resume missing sections

### Next Steps

- ✅ **Skill Registration Complete** - Added to `_bmad/_config/workflow-manifest.csv`
- Test with real resume documents
- Consider adding more input format parsers

---

## Skill Registration (Step 8)

### Registration Details

| Field | Value |
|-------|-------|
| **Skill ID** | `bmad:custom:workflows:resume-import` |
| **Manifest File** | `_bmad/_config/workflow-manifest.csv` |
| **Module** | custom |

### Invocation Methods

```bash
# Slash command
/resume-import

# Or ask Claude directly
"Run the resume-import workflow"
```

### How It Works

1. Claude Code reads `_bmad/_config/workflow-manifest.csv` at startup
2. Each row defines a workflow with name, description, module, and path
3. Workflows become available as skills with pattern: `bmad:<module>:workflows:<name>`
4. The Skill tool loads and executes the workflow.md file when invoked
