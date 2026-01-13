# Story 6.20: Comprehensive README Update

## Story Info

- **Epic**: Epic 6 - Executive Resume Template & Profile System
- **Status**: ready-for-dev
- **Priority**: Medium
- **Estimation**: Small (2 story points)
- **Dependencies**: Story 6.19 (Philosophy Documentation) - for docs/ folder link

## User Story

As a **developer discovering the Resume as Code repository**,
I want **a comprehensive README that explains what the tool does and how to use it**,
So that **I can quickly understand the value proposition and get started**.

## Background

The current README is minimal (46 lines) with only basic installation and usage commands. It doesn't explain:
- What problem Resume as Code solves
- The philosophy behind the approach
- Key features and capabilities
- Complete command reference
- Practical examples
- How to contribute

A comprehensive README is essential for:
1. **First impressions** — README is the landing page for the project
2. **Adoption** — Users need to understand value before investing time
3. **Self-service** — Reduce questions by documenting common workflows
4. **Contribution** — Clear guidelines encourage community involvement

## Acceptance Criteria

### AC1: README Structure
**Given** the updated README.md
**When** viewed on GitHub
**Then** it includes these sections in order:
1. Title with tagline
2. Philosophy teaser (2-3 sentences)
3. Key Features list
4. Quick Start guide
5. Command Reference (all commands)
6. Examples section
7. Configuration section
8. Documentation link (→ docs/)
9. Contributing section
10. License

### AC2: Philosophy Teaser
**Given** a user reads the README intro
**When** they finish the first section
**Then** they understand:
- Resume as Code treats career data as structured, queryable truth
- Work Units are the atomic unit of accomplishment
- Resumes are generated queries, not edited documents
- Link to `docs/philosophy.md` for deep dive

### AC3: Key Features List
**Given** the Features section
**When** viewed
**Then** it highlights:
- Work Unit capture with archetypes
- Schema validation with actionable feedback
- Hybrid ranking (BM25 + semantic) for JD matching
- Skill coverage and gap analysis
- Multiple output formats (PDF, DOCX)
- Executive resume templates
- Position/certification/education management
- Full provenance via manifest

### AC4: Quick Start Guide
**Given** a new user follows the Quick Start
**When** they complete it
**Then** they have:
1. Installed the tool
2. Created their first Work Unit
3. Run validation
4. Generated a resume from a sample JD

```bash
# Install
uv sync --all-extras

# Create your first Work Unit
uv run resume new work-unit --archetype greenfield

# Validate
uv run resume validate

# Plan (preview selection)
uv run resume plan --jd examples/jd/senior-engineer.txt

# Build resume
uv run resume build --jd examples/jd/senior-engineer.txt
```

### AC5: Command Reference
**Given** the Command Reference section
**When** viewed
**Then** it documents all commands:

| Command | Description |
|---------|-------------|
| `resume new work-unit` | Create a new Work Unit |
| `resume validate` | Validate Work Units against schema |
| `resume list` | List all Work Units |
| `resume plan --jd FILE` | Preview resume selection for JD |
| `resume build --jd FILE` | Generate resume files |
| `resume config` | View/set configuration |
| `resume cache clear` | Clear embedding cache |

Each command includes:
- Purpose (one line)
- Common flags
- Example usage

### AC6: Examples Section
**Given** the Examples section
**When** viewed
**Then** it shows practical workflows:
- Creating Work Units for different scenarios (incident, project, leadership)
- Running targeted resume generation
- Using JSON output for scripting
- Configuring profile and certifications

### AC7: Configuration Section
**Given** the Configuration section
**When** viewed
**Then** it explains:
- Configuration hierarchy (CLI > env > project > user > defaults)
- `.resume.yaml` structure with example
- Key configuration options (profile, certifications, skills)
- Link to `docs/data-model.md` for schema details

### AC8: Documentation Link
**Given** the README
**When** a user wants more detail
**Then** there's a clear link to `docs/` folder with:
- Philosophy deep dive
- Data model reference
- Workflow documentation
- Architecture diagrams

### AC9: Contributing Section
**Given** the Contributing section
**When** a potential contributor reads it
**Then** they understand:
- How to set up development environment
- Code quality requirements (ruff, mypy, pytest)
- Git flow branching strategy
- Commit message format (conventional commits)
- Link to CONTRIBUTING.md (if exists) or inline guidelines

### AC10: Visual Appeal
**Given** the README renders on GitHub
**When** viewed
**Then** it includes:
- Badges (optional: build status, version, license)
- Clear section headers
- Code blocks with syntax highlighting
- Tables for structured information
- Appropriate use of bold/italic for emphasis

## Technical Notes

### README Structure Template

```markdown
# Resume as Code

> Treat your career data as structured, queryable truth.

CLI tool for git-native resume generation from structured Work Units.

## The Philosophy

[2-3 sentence teaser linking to docs/philosophy.md]

## Features

- [Feature list with brief descriptions]

## Quick Start

[Step-by-step getting started]

## Command Reference

### `resume new work-unit`
[Description, flags, example]

### `resume validate`
[...]

## Examples

### Creating a Work Unit
[Code example]

### Generating a Targeted Resume
[Code example]

## Configuration

### Project Configuration (`.resume.yaml`)
[Example with comments]

### Configuration Hierarchy
[Explanation]

## Documentation

For detailed documentation, see the [docs/](docs/) folder:
- [Philosophy](docs/philosophy.md)
- [Data Model](docs/data-model.md)
- [Workflow](docs/workflow.md)

## Development

[Dev setup, testing, code quality]

## Contributing

[Guidelines or link to CONTRIBUTING.md]

## License

MIT License - see [LICENSE](LICENSE)
```

### Badges (Optional)

```markdown
![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)
![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)
```

### Keep README Maintainable

- Don't duplicate detailed documentation (link to docs/ instead)
- Focus on "getting started" rather than comprehensive reference
- Update command reference when CLI changes
- Keep examples simple and copy-pasteable

## Tasks

### Task 1: Write Philosophy Teaser
- [ ] Write 2-3 sentence intro explaining the core concept
- [ ] Include the key insight: "resumes as queries"
- [ ] Add link to `docs/philosophy.md`

### Task 2: Write Features Section
- [ ] List 8-10 key features with one-line descriptions
- [ ] Order by user value (most important first)
- [ ] Use consistent formatting (emoji optional)

### Task 3: Write Quick Start Guide
- [ ] Document installation (uv sync, platform requirements)
- [ ] Show first Work Unit creation
- [ ] Show validation
- [ ] Show plan and build commands
- [ ] Ensure all commands are copy-pasteable

### Task 4: Write Command Reference
- [ ] Document all CLI commands
- [ ] Include purpose, common flags, example for each
- [ ] Use tables for flag documentation
- [ ] Keep examples concise

### Task 5: Write Examples Section
- [ ] Add 3-4 practical workflow examples
- [ ] Include different archetypes (incident, greenfield, leadership)
- [ ] Show JSON output usage
- [ ] Show configuration examples

### Task 6: Write Configuration Section
- [ ] Explain configuration hierarchy
- [ ] Show annotated `.resume.yaml` example
- [ ] Document key options (profile, certifications, skills)
- [ ] Link to docs/data-model.md

### Task 7: Write Documentation Links
- [ ] Add Documentation section
- [ ] Link to all docs/ files
- [ ] Brief description of each document

### Task 8: Write Contributing Section
- [ ] Document dev environment setup
- [ ] List code quality requirements
- [ ] Explain Git flow and commit format
- [ ] Keep concise (link to CONTRIBUTING.md if detailed)

### Task 9: Final Polish
- [ ] Add badges (optional)
- [ ] Review section ordering
- [ ] Check all code blocks render correctly
- [ ] Verify all links work
- [ ] Spell check

## Definition of Done

- [ ] All sections from AC1 are present
- [ ] Quick Start guide is tested and works
- [ ] All command examples are accurate
- [ ] Links to docs/ folder work (requires 6.19)
- [ ] README renders correctly on GitHub
- [ ] No broken links
- [ ] Spell-checked

## Notes

- This story depends on Story 6.19 completing first (for docs/ links)
- Keep README under 500 lines — link to docs/ for details
- Test Quick Start commands before finalizing
- Consider adding a "Why Resume as Code?" comparison section (optional)
