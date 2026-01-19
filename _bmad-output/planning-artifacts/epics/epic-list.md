# Epic List

## Epic 1: Project Foundation & Developer Experience
**User Outcome:** A working CLI tool with help, error handling, and configuration infrastructure

**FRs Covered:** FR28, FR29, FR30, FR34, FR35, FR36, FR37, FR38

This epic establishes the project foundation including pyproject.toml with full dependency spec, src/resume_as_code/ package structure, Click CLI skeleton, Rich console integration, configuration loader with hierarchy support, and AI agent compatibility features (Research-Validated 2026-01-10: semantic exit codes, JSON output with format versioning, stdout/stderr separation, CLAUDE.md context file).

---

## Epic 2: Work Unit Creation & Capture
**User Outcome:** Users can capture Work Units right after accomplishments happen (Journey 1: "The Capture")

**FRs Covered:** FR1, FR2, FR3, FR4, FR5, FR9, FR10, FR11

This epic delivers the core capture experience: creating Work Units with archetypes (incident, greenfield, leadership), the `--from memory` quick capture flag, editor integration, proper file storage with naming conventions, and rich metadata support (confidence levels, tags, evidence linking).

---

## Epic 3: Work Unit Validation & Discovery
**User Outcome:** Users can validate their Work Units and browse their collection with confidence

**FRs Covered:** FR6, FR7, FR8

This epic provides quality assurance through schema validation with actionable feedback, and discovery through the list command with filtering and JSON output support.

---

## Epic 4: Resume Planning & Explainability
**User Outcome:** Users can run `resume plan` and see exactly what will be included/excluded with reasons (Journey 2: "The Plan")

**FRs Covered:** FR12, FR13, FR14, FR15, FR16, FR17, FR18, FR19

This is the killer feature - the Terraform-style preview that no other resume tool offers. Users analyze job descriptions against their Work Units, see BM25 rankings with relevance scores, understand exclusion reasons, identify skill gaps, review proposed rewrites, and save plans for later use.

---

## Epic 5: Resume Generation & Output
**User Outcome:** Users can generate tailored PDF and DOCX resumes with full provenance

**FRs Covered:** FR20, FR21, FR22, FR23, FR24, FR25, FR26, FR27, FR31, FR32, FR33

This epic completes the workflow with the build command, PDF output via WeasyPrint, DOCX output via python-docx, manifest files for provenance tracking, configurable output directories, and template/scoring configuration options.

---

## Epic 6: Executive Resume Template & Profile System
**User Outcome:** Executive-level users get specialized templates with career highlights, board roles, and scope indicators

See: [epic-6-executive-resume-template-profile-system.md](epic-6-executive-resume-template-profile-system.md)

---

## Epic 7: Schema & Data Model Refactoring
**User Outcome:** Cleaner data models with proper separation and validation

See: [epic-7-schema-data-model-refactoring.md](epic-7-schema-data-model-refactoring.md)

---

## Epic 8: Resume Template Enhancements
**User Outcome:** Improved template rendering with grouped positions and better visual hierarchy

See: [epic-8-resume-template-enhancements.md](epic-8-resume-template-enhancements.md)

---

## Epic 9: Data Management & Migration
**User Outcome:** Safe schema upgrades with automatic migration and rollback support

See: [epic-9-data-management-migration.md](epic-9-data-management-migration.md)

---

## Epic 10: Distribution & Release Management
**User Outcome:** Simple installation via pip from PyPI

This epic enables package distribution through PyPI with `pip install resume-as-code-ng`, GitHub Actions release workflows, and trusted publisher authentication.

---

## Epic 11: Technical Debt & Platform Enhancements
**User Outcome:** Comprehensive validation, custom templates, and improved platform quality

**Tech Debt Covered:** TD-004, TD-005, TD-006, TD-007, TD-008

This epic addresses accumulated technical debt: PyPI logo display fix, directory-based sharding for data files, custom templates directory support, template authoring documentation, and comprehensive resource validation across all data types.

See: [epic-11-technical-debt-platform-enhancements.md](epic-11-technical-debt-platform-enhancements.md)

---
