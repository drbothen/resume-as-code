# Resume as Code Documentation

> Your career data as structured, queryable truth.

This documentation explains the philosophy, data model, and workflow behind Resume as Code — a CLI tool that treats resume generation as a code problem rather than a document editing problem.

---

## Quick Start

If you're new to Resume as Code, start here:

1. **[Philosophy](./philosophy.md)** — Understand *why* this approach works
2. **[Data Model](./data-model.md)** — Learn the building blocks
3. **[Workflow](./workflow.md)** — Master the Capture → Plan → Build pipeline

For installation and CLI commands, see the [main README](../README.md).

---

## Documentation Index

| Document | Description |
|----------|-------------|
| [Philosophy](./philosophy.md) | The "Resume as Code" mental model |
| [Data Model](./data-model.md) | Work Units, Positions, Certifications, Education, Publications, Board Roles |
| [Workflow](./workflow.md) | The four-stage pipeline: Capture → Validate → Plan → Build |
| [Import Workflows](./import-workflows.md) | Migrate existing resumes and thought leadership content |

---

## Diagrams

Visual guides to key concepts. SVG files are exported from Excalidraw source files in the same directory.

| Diagram | Description |
|---------|-------------|
| [Data Model](./diagrams/data-model.svg) | Entity relationships and schema structure |
| [Workflow Pipeline](./diagrams/workflow-pipeline.svg) | The Capture → Validate → Plan → Build pipeline |
| [Philosophy Concept](./diagrams/philosophy-concept.svg) | Traditional vs Resume as Code comparison |

> **Editing diagrams**: See the [Diagram Management Guide](./diagrams/README.md) for instructions on editing and exporting diagrams.

---

## Key Concepts at a Glance

### Resumes as Queries

Instead of editing a document for each job application, you:
1. **Capture** accomplishments as structured Work Units
2. **Query** your capability graph using a job description
3. **Generate** a tailored resume from the best matches

### The Atomic Unit: Work Unit

A Work Unit is a single, documented accomplishment containing:
- **Problem** — The challenge you faced
- **Actions** — What you did
- **Result** — The quantified outcome

### Git-Native Benefits

- Version control for your career data
- Branch for different career directions
- Diff to see what changed over time
- Never lose an accomplishment

---

*For the CLI reference and command documentation, see the [main README](../README.md).*
