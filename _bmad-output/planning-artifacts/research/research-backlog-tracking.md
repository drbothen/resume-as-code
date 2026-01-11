# Research Backlog Tracking

**Project:** Resume as Code
**Created:** 2026-01-10
**Last Updated:** 2026-01-10
**Total Items:** 64 (46 original + 12 new + 4 content strategy + 1 AI agent + 1 embedding update)

---

## Status Legend

| Status | Meaning |
|--------|---------|
| COMPLETE | Research done, findings integrated into planning docs |
| VALIDATED | Fresh research (2026-01-10) confirms findings still current |
| UPDATE-NEEDED | Research exists but needs refresh based on validation audit |
| IN-PROGRESS | Currently being researched |
| PENDING | Not yet started |
| POST-MVP | Deferred to post-MVP phase |
| NOT-NEEDED | Determined unnecessary after review |

---

## Summary Dashboard

| Batch | Complete + Integrated | Validated | Update Needed | In-Progress | Pending | Post-MVP |
|-------|----------------------|-----------|---------------|-------------|---------|----------|
| A (1-10) | 9 | 1 | 0 | 0 | 0 | 0 |
| B (11-19) | 7 | 0 | 0 | 0 | 0 | 2 |
| C (20-23) | 4 | 1 | 0 | 0 | 0 | 0 |
| D (24-28) | 5 | 0 | 0 | 0 | 0 | 0 |
| E (29-46) | 14 | 1 | 0 | 0 | 0 | 3 |
| NEW (47-58) | 7 | 0 | 0 | 0 | 0 | 6 |
| CONTENT (59-63) | 5 | 0 | 0 | 0 | 0 | 0 |
| AI AGENT (64+) | 1 | 0 | 0 | 0 | 0 | 0 |
| **TOTAL** | **52** | **3** | **0** | **0** | **0** | **11** |

**Ready for Implementation:** 54/63 items (86%) - excludes 11 POST-MVP items
**Fully Integrated into Architecture/Epics:** 54/63 items (86%)

**ALL PENDING RESEARCH ITEMS COMPLETE!**

*Note: RB-047, RB-048, RB-050 now COMPLETE + INTEGRATED into Architecture Section 1.3.1, Section 3.2, and Epics Story 4.1.5, Story 4.2*

---

## BATCH A: Schema Design, Data Structures, Tooling (Items 1-10)

### RB-001: Work Unit Schema Design
- **Status:** COMPLETE
- **Summary:** PAR (Problem-Action-Result) structure validated as industry best practice
- **Location:** Comprehensive Research Section 1
- **Integrated Into:** Architecture Section 1.3, Epic 2
- **Notes:** Schema finalized in Architecture doc

### RB-002: Evidence and Provenance Structures
- **Status:** COMPLETE
- **Summary:** Evidence types defined (repo, metrics, docs, certs)
- **Location:** Comprehensive Research Section 2
- **Integrated Into:** Architecture (hooks), PRD FR-WU-011
- **Notes:** MVP has hooks; full implementation post-MVP

### RB-003: Skill Emergence Models
- **Status:** COMPLETE
- **Summary:** Inference vs declaration patterns researched
- **Location:** Comprehensive Research Section 3
- **Integrated Into:** Deferred to post-MVP (skill inference)
- **Notes:** Self-declared skills for MVP; inference is future feature

### RB-004: Career Graph Theory
- **Status:** POST-MVP
- **Summary:** Knowledge graph structures for career analysis
- **Location:** Comprehensive Research Section 4
- **Integrated Into:** Not in MVP scope
- **Notes:** Interesting future feature, not critical for MVP

### RB-005: YAML vs JSON vs TOML
- **Status:** COMPLETE
- **Summary:** YAML chosen (40% more readable, comments, better diffs)
- **Location:** Comprehensive Research Section 5
- **Integrated Into:** Architecture Section 1.3
- **Notes:** Decision validated and locked

### RB-006: File-per-Unit Storage Patterns
- **Status:** COMPLETE
- **Summary:** Directory structure and naming conventions defined
- **Location:** Comprehensive Research Section 6
- **Integrated Into:** Architecture Section 2.3
- **Notes:** `work-units/wu-YYYY-MM-DD-slug.yaml` pattern

### RB-007: Template-to-PDF Pipelines
- **Status:** VALIDATED (2026-01-10)
- **Summary:** WeasyPrint confirmed as best choice for static HTML→PDF
- **Location:** Comprehensive Research Section 7, Validation Audit
- **Integrated Into:** Architecture Section 1.3, Epic 5
- **Notes:** Fresh research confirms WeasyPrint still optimal

### RB-008: Natural Language JD Parsing
- **Status:** COMPLETE
- **Summary:** Multi-stage parsing approach (rule-based + NER + ML)
- **Location:** Comprehensive Research Section 8
- **Integrated Into:** Epic 4 Story 4.1
- **Notes:** MVP uses simple keyword extraction

### RB-009: Resume-to-JD Matching Algorithms
- **Status:** COMPLETE
- **Summary:** BM25 + semantic hybrid ranking validated
- **Location:** Comprehensive Research Section 9
- **Integrated Into:** Architecture Section 1.3, Epic 4 Story 4.2
- **Notes:** 94.2% accuracy with hybrid approach

### RB-010: Python Resume Tooling Ecosystem
- **Status:** COMPLETE
- **Summary:** Stack defined (PyYAML, Pydantic, Jinja2, WeasyPrint, spaCy, sentence-transformers)
- **Location:** Comprehensive Research Section 10
- **Integrated Into:** Architecture pyproject.toml
- **Notes:** All dependencies specified with versions

---

## BATCH B: IaC + SSG Patterns (Items 11-19)

### RB-011: Terraform "Plan Before Apply" Pattern
- **Status:** COMPLETE
- **Summary:** Core differentiating feature researched
- **Location:** Comprehensive Research Section 11
- **Integrated Into:** PRD FR-PLAN-*, Epic 4
- **Notes:** This is THE killer feature

### RB-012: State and Provenance Tracking
- **Status:** COMPLETE
- **Summary:** Submission tracking schema designed
- **Location:** Comprehensive Research Section 12, Section 37
- **Integrated Into:** Architecture (hooks), deferred full impl
- **Notes:** Git-based lineage for MVP; full tracking post-MVP

### RB-013: Module and Archetype Patterns
- **Status:** COMPLETE
- **Summary:** Work unit archetypes (incident, greenfield, leadership, etc.)
- **Location:** Comprehensive Research Section 13, Section 34
- **Integrated Into:** PRD FR-WU-002/003, Epic 2 Story 2.2
- **Notes:** 6 standard archetypes defined

### RB-014: Provider Architecture
- **Status:** COMPLETE
- **Summary:** Abstract ResumeProvider pattern for multi-format output
- **Location:** Comprehensive Research Section 14
- **Integrated Into:** Architecture Section 5.3, Epic 5
- **Notes:** PDF, DOCX, ATS providers planned

### RB-015: Content/Layout Separation
- **Status:** COMPLETE
- **Summary:** SSG pattern: content in YAML, presentation in templates
- **Location:** Comprehensive Research Section 15
- **Integrated Into:** Architecture templating approach
- **Notes:** Jinja2 templating with theme switching

### RB-016: Frontmatter Standards
- **Status:** POST-MVP
- **Summary:** Resume frontmatter schema for targeting
- **Location:** Comprehensive Research Section 16
- **Integrated Into:** Not in MVP scope
- **Notes:** Nice-to-have for multi-target resumes

### RB-017: Shortcode/Component Systems
- **Status:** POST-MVP
- **Summary:** Hugo-style shortcodes for resume components
- **Location:** Comprehensive Research Section 17
- **Integrated Into:** Not in MVP scope
- **Notes:** Future feature for complex templates

### RB-018: Build Pipeline Design
- **Status:** COMPLETE
- **Summary:** Incremental builds, parallel generation, caching
- **Location:** Comprehensive Research Section 18, Section 35
- **Integrated Into:** Architecture Section 5.4
- **Notes:** Watch mode deferred to post-MVP

### RB-019: Taxonomy Systems
- **Status:** COMPLETE
- **Summary:** Skill and domain taxonomies for filtering
- **Location:** Comprehensive Research Section 19
- **Integrated Into:** PRD FR-WU-010 (tags)
- **Notes:** Basic tagging for MVP; full taxonomy post-MVP

---

## BATCH C: Existing Tools & Standards (Items 20-23)

### RB-020: JSON Resume Standard
- **Status:** COMPLETE
- **Summary:** Standard schema analyzed; limitations identified
- **Location:** Comprehensive Research Section 20
- **Integrated Into:** PRD (export target), Architecture
- **Notes:** Export to JSON Resume supported; not source format

### RB-021: ATS Parsing Behavior
- **Status:** VALIDATED (2026-01-10)
- **Summary:** 97.8% Fortune 500 ATS usage confirmed; parsing rules documented
- **Location:** Comprehensive Research Section 21, Validation Audit
- **Integrated Into:** Epic 5 Story 5.4 (ATS Provider)
- **Notes:** Fresh research confirms statistics still accurate

### RB-022: Existing Resume-as-Code Tools
- **Status:** COMPLETE
- **Summary:** Competitive analysis (JSON Resume, Reactive Resume, YAMLResume, etc.)
- **Location:** Comprehensive Research Section 22
- **Integrated Into:** Product Brief differentiation
- **Notes:** Market gaps identified; our differentiators clear

### RB-023: LinkedIn Data Export
- **Status:** COMPLETE
- **Summary:** Export process, limitations, conversion tools
- **Location:** Comprehensive Research Section 23, Section 42
- **Integrated Into:** Post-MVP (LinkedIn import)
- **Notes:** Implementation code provided but deferred

---

## BATCH D: AI Integration (Items 24-28)

### RB-024: Work Unit Capture Flow UX
- **Status:** COMPLETE
- **Summary:** Three-phase conversational capture approach
- **Location:** Comprehensive Research Section 24, Section 30
- **Integrated Into:** PRD FR-WU-001 (progressive disclosure)
- **Notes:** CLI prompts follow this pattern

### RB-025: Explainable AI for Resume Selection
- **Status:** COMPLETE
- **Summary:** Feature importance, counterfactual, example-based explanations
- **Location:** Comprehensive Research Section 25
- **Integrated Into:** PRD FR-PLAN-004, Epic 4 Story 4.3
- **Notes:** `match_reasons` in plan output

### RB-026: Style Profile Translation
- **Status:** COMPLETE
- **Summary:** Audience-specific language (executive, technical, ATS)
- **Location:** Comprehensive Research Section 26
- **Integrated Into:** LLM hooks (post-MVP full impl)
- **Notes:** Manual variant selection for MVP

### RB-027: Embedding Models for Skill Matching
- **Status:** COMPLETE
- **Summary:** Embedding model recommendation updated to multilingual-e5-large-instruct (primary) with all-MiniLM-L6-v2 as fallback
- **Location:** Comprehensive Research Section 27, hybrid-search-implementation-research-2026-01-10.md (RB-048)
- **Integrated Into:** Architecture Section 1.3, Section 1.3.1 (Model Specifications)
- **Notes:** Fresh research (2026-01-10) confirms multilingual-e5-large-instruct as best choice for resume-JD matching. Architecture fully updated with model specs, instruction prefixes, and fallback strategy.
- **Key Findings:**
  - Primary: multilingual-e5-large-instruct (1024-dim, 560M params, ~1.1GB VRAM)
  - Fallback: all-MiniLM-L6-v2 (384-dim, 22M params, ~200MB) for resource-constrained
  - Instruction prefixes critical: "passage:" for JDs, "query:" for Work Units
  - ~10-15% improvement over MiniLM on retrieval benchmarks

### RB-028: MCP Server Design Patterns
- **Status:** COMPLETE
- **Summary:** Tool design for composable resume AI integration
- **Location:** Comprehensive Research Section 28
- **Integrated Into:** Architecture (future LLM integration)
- **Notes:** Architecture ready for MCP; implementation deferred

---

## BATCH E: Implementation Details (Items 29-46)

### RB-029: Work Unit Schema Finalization
- **Status:** COMPLETE
- **Summary:** JSON Schema validation, versioning strategy
- **Location:** Comprehensive Research Section 29
- **Integrated Into:** Architecture schemas/, Epic 2 Story 2.1
- **Notes:** Schema version embedded in documents

### RB-030: Draft Work Unit Capture Flow
- **Status:** COMPLETE
- **Summary:** Progressive disclosure CLI patterns
- **Location:** Comprehensive Research Section 30
- **Integrated Into:** Epic 2 Story 2.3
- **Notes:** State persistence for resumable capture

### RB-031: Rank Work Units Algorithm
- **Status:** VALIDATED (2026-01-10)
- **Summary:** BM25 + RRF fusion confirmed as best practice
- **Location:** Comprehensive Research Section 31, Validation Audit
- **Integrated Into:** Epic 4 Story 4.2 (UPDATED with RRF)
- **Notes:** Architecture updated with RRF fusion method

### RB-032: Resume Plan Output Format
- **Status:** COMPLETE
- **Summary:** Terraform-style diff output with ANSI colors
- **Location:** Comprehensive Research Section 32
- **Integrated Into:** PRD FR-PLAN-005, Epic 4 Story 4.3
- **Notes:** Rich library for terminal formatting

### RB-033: PDF Output Provider
- **Status:** COMPLETE
- **Summary:** WeasyPrint pipeline with print CSS
- **Location:** Comprehensive Research Section 33
- **Integrated Into:** Epic 5 Story 5.2
- **Notes:** Font embedding patterns documented

### RB-034: Work Unit Archetypes
- **Status:** COMPLETE
- **Summary:** 6 archetype templates (incident, greenfield, leadership, migration, integration, scaling)
- **Location:** Comprehensive Research Section 34
- **Integrated Into:** Epic 2 Story 2.2
- **Notes:** CLI `resume new --archetype` command

### RB-035: Resume Build Pipeline
- **Status:** COMPLETE
- **Summary:** Incremental builds, caching, parallel generation
- **Location:** Comprehensive Research Section 35
- **Integrated Into:** Architecture Section 5.4
- **Notes:** BuildCache class pattern provided

### RB-036: ATS-Safe Provider
- **Status:** COMPLETE
- **Summary:** Single-column, keyword-optimized template
- **Location:** Comprehensive Research Section 36
- **Integrated Into:** Epic 5 Story 5.4
- **Notes:** ATS-safe HTML template provided

### RB-037: Submission Provenance Schema
- **Status:** COMPLETE
- **Summary:** Lightweight tracking without CRM
- **Location:** Comprehensive Research Section 37
- **Integrated Into:** Architecture (hooks), post-MVP full impl
- **Notes:** Git-based lineage for MVP

### RB-038: Archetype Scaffolding CLI
- **Status:** COMPLETE
- **Summary:** `resume new` command implementation
- **Location:** Comprehensive Research Section 38
- **Integrated Into:** Epic 2 Story 2.2
- **Notes:** Interactive capture with archetype selection

### RB-039: Validate Work Unit Linting
- **Status:** COMPLETE
- **Summary:** JSON Schema + custom rules (quality, taxonomy)
- **Location:** Comprehensive Research Section 39
- **Integrated Into:** Epic 3 Story 3.1
- **Notes:** WorkUnitValidator class pattern

### RB-040: DOCX Output Provider
- **Status:** COMPLETE
- **Summary:** python-docx/docxtpl template-based generation
- **Location:** Comprehensive Research Section 40
- **Integrated Into:** Epic 5 Story 5.3
- **Notes:** RichText formatting for action verbs

### RB-041: JSON Resume Export
- **Status:** POST-MVP
- **Summary:** Lossy projection to JSON Resume format
- **Location:** Comprehensive Research Section 41
- **Integrated Into:** Not in MVP scope
- **Notes:** Code provided; implement when needed

### RB-042: LinkedIn Import
- **Status:** POST-MVP
- **Summary:** CSV parsing with confidence tracking
- **Location:** Comprehensive Research Section 42
- **Integrated Into:** Not in MVP scope
- **Notes:** Low-confidence import with manual enrichment

### RB-043: Semantic Search with Embeddings
- **Status:** COMPLETE
- **Summary:** Embedding-based work unit search
- **Location:** Comprehensive Research Section 43
- **Integrated Into:** Epic 4 (semantic ranking)
- **Notes:** Update to use multilingual-e5-large-instruct

### RB-044: Gap Analysis
- **Status:** POST-MVP
- **Summary:** Skill gap detection against target role
- **Location:** Comprehensive Research Section 44
- **Integrated Into:** Not in MVP scope
- **Notes:** Nice-to-have feature; code provided

### RB-045: Watch Mode for Live Preview
- **Status:** POST-MVP
- **Summary:** File watching with debounce, auto-rebuild
- **Location:** Comprehensive Research Section 45
- **Integrated Into:** Not in MVP scope
- **Notes:** watchdog library pattern provided

### RB-046: HTML Portfolio Provider
- **Status:** POST-MVP
- **Summary:** Static portfolio site generation
- **Location:** Comprehensive Research Section 46
- **Integrated Into:** Not in MVP scope
- **Notes:** Responsive HTML with dark mode support

---

## NEW ITEMS: Identified from Validation Audit (Items 47-58)

### RB-047: Reciprocal Rank Fusion (RRF) Implementation Details
- **Status:** COMPLETE + INTEGRATED
- **Priority:** HIGH
- **Summary:** RRF formula: 1/(k+rank), k=60 standard, deterministic tie-breaking
- **Location:** hybrid-search-implementation-research-2026-01-10.md
- **Integrated Into:**
  - Architecture Section 1.3 (RRF Parameter k=60 in Technical Constraints table)
  - Architecture Section 1.3.1 (Hybrid Search Implementation - full RRF details)
  - Epics Story 4.2 (BM25 Ranking Engine acceptance criteria with RRF fusion)
- **Key Findings:**
  - Core formula: RRF_Score(d) = Σ (1 / (k + rank_i(d)))
  - k=60 provides robust balance without tuning
  - Retrieve top_k*2 from each method before fusion
  - Deterministic tie-breaking via secondary doc_id sort
  - ~2-5ms fusion overhead for 100-document lists

### RB-048: multilingual-e5-large-instruct Model Evaluation
- **Status:** COMPLETE + INTEGRATED
- **Priority:** HIGH
- **Summary:** 1024-dim embeddings, instruction-tuned, "query:"/"passage:" prefixes critical
- **Location:** hybrid-search-implementation-research-2026-01-10.md
- **Integrated Into:**
  - Architecture Section 1.3 (Embeddings technology choices with model specs)
  - Architecture Section 1.3.1 (Model Specifications table, Instruction Prefixes table)
  - Epics Story 4.1.5 (NEW: Embedding Service & Cache with model selection)
  - Epics Story 4.2 (Embedding prefixes in technical notes)
- **Key Findings:**
  - 560M parameters, 1024-dimensional output
  - ~1.1GB VRAM (float16), 30-50ms per query on GPU
  - Use "passage:" prefix for job descriptions (indexed)
  - Use "query:" prefix for resumes (search queries)
  - ~66.9 NDCG@10 on MTEB retrieval, +10-15% vs MiniLM
  - Fallback: all-MiniLM-L6-v2 for resource-constrained

### RB-049: Field-Specific Embeddings Strategy
- **Status:** COMPLETE
- **Priority:** MEDIUM
- **Summary:** Multi-field embeddings achieve ~95% accuracy vs 60-70% for single-vector; 70/20/5/5 weighting recommended
- **Location:** schema-and-embeddings-research-2026-01-10.md
- **Integrated Into:**
  - Architecture Section 1.3.1 (Field-specific embedding strategy)
  - Epics Story 4.1.5 (multi-field embedding acceptance criteria)
- **Key Findings:**
  - Single-vector: 60-70% accuracy; Multi-field: ~95% accuracy
  - Weighting: 70% experience, 20% education, 5% skills, 5% languages
  - ColBERT/ColBERTv2 for token-level granularity
  - MUVERA technique for efficient multi-vector search
  - Instruction prefixes critical for e5-instruct models

### RB-050: Embedding Cache Invalidation Strategy
- **Status:** COMPLETE + INTEGRATED
- **Priority:** MEDIUM
- **Summary:** Cache keys must include model hash; SQLite + pickle + gzip for CLI tools
- **Location:** hybrid-search-implementation-research-2026-01-10.md
- **Integrated Into:**
  - Architecture Section 1.3 (Embedding Cache technology choice)
  - Architecture Section 1.3.1 (Cache Key Design formula)
  - Architecture Section 3.2 (Data Architecture - cache schema, directory structure, invalidation strategy)
  - Epics Story 4.1.5 (NEW: Embedding Service & Cache with full cache implementation)
- **Key Findings:**
  - Cache key = hash(model_id + model_version + model_hash + text_hash)
  - Compute model hash once at init, not per-operation
  - Directory structure: .resume-cache/{model_id}/{version_hash}/
  - SQLite for index, pickle + gzip for embedding storage
  - Clear stale cache on model version mismatch
  - Migration: parallel caching during transition, then cleanup

### RB-051: ATS Keyword Density Optimization
- **Status:** COMPLETE
- **Priority:** LOW
- **Summary:** Optimal 2-3% keyword density; 60-80% keyword coverage; placement strategy validated
- **Location:** ats-keyword-and-resume-length-research-2026-01-10.md
- **Integrated Into:**
  - Architecture Section 1.4 (ATS optimization guidelines)
  - Epics Story 5.4 (ATS-safe template with keyword guidance)
  - Epics Story 4.3 (Plan output keyword analysis)
- **Key Findings:**
  - Optimal density: 2-3% of total word count
  - Target 60-80% JD keyword coverage
  - Modern ATS uses NLP + exact match (both matter)
  - Recruiter thresholds: 65-80% depending on role volume
  - Keyword stuffing now triggers LOWER scores
  - Placement priority: Summary > Skills > Experience > Education

### RB-052: Resume Length Best Practices by Career Stage
- **Status:** COMPLETE
- **Priority:** LOW
- **Summary:** Two-page resumes achieve 35% higher interview rates; one-page rule obsolete for 5+ year experience
- **Location:** ats-keyword-and-resume-length-research-2026-01-10.md
- **Integrated Into:**
  - Architecture Section 1.4 (content density guidelines)
  - Epics Story 5.1 (template length variants)
  - Epics Story 4.3 (Plan output word count analysis)
- **Key Findings:**
  - 2-page resumes: 3.45% interview rate vs 2.5% for 1-page (35% improvement)
  - Entry-level (0-5 yrs): 1 page optimal
  - Mid-career (5-15 yrs): 2 pages optimal
  - Executive (15+ yrs): 2-3 pages
  - Optimal word count: 475-600 (1 page), 800-1,200 (2 pages)
  - 4-6 bullets per role, 100-160 chars per bullet
  - Federal policy (Sept 2025): strict 2-page max

### RB-053: Jina-v2-base as Alternative Embedding Model
- **Status:** POST-MVP
- **Priority:** LOW
- **Summary:** Evaluate Jina embeddings as alternative to e5
- **Rationale:** ACL-2025 research uses Jina for resume matching
- **Action Needed:** Comparative benchmark if e5 doesn't meet requirements
- **Target:** Post-MVP optimization

### RB-054: Cross-Encoder Re-ranking
- **Status:** POST-MVP
- **Priority:** MEDIUM
- **Summary:** Add cross-encoder as final re-ranking step
- **Rationale:** 2025 best practices suggest cross-encoder on top-K
- **Action Needed:** Research cross-encoder models for resume domain
- **Target:** Post-MVP enhancement

### RB-055: Cover Letter Generation Integration
- **Status:** POST-MVP
- **Priority:** LOW
- **Summary:** Research cover letter generation tied to resume
- **Rationale:** Natural extension of resume generation
- **Action Needed:** Research LLM prompting strategies
- **Target:** Future feature

### RB-056: Resume Analytics Dashboard
- **Status:** POST-MVP
- **Priority:** LOW
- **Summary:** Track which resume versions got responses
- **Rationale:** Mentioned in research but not detailed
- **Action Needed:** Research analytics patterns
- **Target:** Future feature

### RB-057: Multi-Language Resume Support
- **Status:** POST-MVP
- **Priority:** LOW
- **Summary:** Internationalization for resume content
- **Rationale:** e5 model supports multilingual
- **Action Needed:** Research i18n patterns for resumes
- **Target:** Future feature

### RB-058: PDF Accessibility Compliance (WCAG)
- **Status:** POST-MVP
- **Priority:** MEDIUM
- **Summary:** Ensure PDF output meets accessibility standards
- **Rationale:** HTML accessibility mentioned but not PDF
- **Action Needed:** Research PDF/UA compliance with WeasyPrint
- **Target:** Post-MVP compliance

### RB-059: Executive Resume Templates and Best Practices
- **Status:** COMPLETE + INTEGRATED
- **Priority:** HIGH
- **Summary:** 2-3 pages optimal for executives; single-column for ATS; results-first formatting
- **Location:** executive-resume-content-strategy-research-2026-01-10.md
- **Integrated Into:**
  - Architecture Section 1.4 (Content Strategy Standards)
  - Architecture templates/ (executive.html, ats-executive.html)
  - Epics Story 5.1 (executive template acceptance criteria)
- **Key Findings:**
  - 2-3 page standard (one-page rule discredited)
  - Sans-serif fonts (10-12pt body, 18-22pt name)
  - Executive summary essential (3-5 sentences, quantified)
  - Single-column for ATS compatibility

### RB-060: Accomplishment Framing Strategies for Senior Professionals
- **Status:** COMPLETE + INTEGRATED
- **Priority:** HIGH
- **Summary:** Executive framing requires strategic impact language, 5 quantification dimensions
- **Location:** executive-resume-content-strategy-research-2026-01-10.md
- **Integrated Into:**
  - Architecture Section 1.4 (5 quantification dimensions, action verb standards)
  - Architecture Work Unit Schema Extensions (scope, impact_category, metrics, framing)
  - Epics Story 2.1 (executive-level schema fields acceptance criteria)
  - Epics Story 3.2 (content quality validation with weak verb detection)
- **Key Findings:**
  - Use strategic verbs (orchestrated, spearheaded, championed, transformed)
  - Five impact dimensions: financial, operational, talent, customer, organizational
  - Always include baseline context for metrics
  - Soft accomplishments matter - quantify via proxy metrics

### RB-061: PAR/CAR/STAR Framework Validation
- **Status:** VALIDATED + INTEGRATED
- **Priority:** HIGH
- **Summary:** PAR framework CONFIRMED as best practice for resume contexts
- **Location:** executive-resume-content-strategy-research-2026-01-10.md
- **Integrated Into:**
  - Architecture Section 1.4 (PAR primary, RAS for executives, STAR for interviews)
  - Epics Technology Stack line (Content Strategy reference)
- **Key Findings:**
  - PAR best for resumes and phone screens
  - STAR best for behavioral interviews
  - CAR is versatile middle ground
  - Modern evolution: RAS (Results-Action-Situation) for executives
  - No framework obsolete; execution quality > framework choice

### RB-062: Resume Trends 2025-2026
- **Status:** COMPLETE + INTEGRATED
- **Priority:** HIGH
- **Summary:** AI-era requires quality over keywords; skills-based hiring dominant
- **Location:** executive-resume-content-strategy-research-2026-01-10.md
- **Integrated Into:**
  - Architecture Section 1.4 (ATS optimization notes)
  - Epics Story 5.1 (ATS-safe template requirements)
- **Key Findings:**
  - ATS now 94-97% parsing accuracy
  - AI evaluates writing quality, not just keywords
  - Results-first orientation (lead with metrics)
  - 90% recruiters seek explicit skill evidence
  - LinkedIn-resume consistency critical

### RB-063: Work Unit Schema Validation & Best Practices 2025-2026
- **Status:** COMPLETE
- **Priority:** HIGH
- **Summary:** JSON Resume limitations identified; O*NET integration recommended; Pydantic v2 validation patterns; JSON Schema 2020-12 preferred
- **Location:** schema-and-embeddings-research-2026-01-10.md
- **Integrated Into:**
  - Architecture Section 1.3 (schema validation technology choices)
  - Architecture Work Unit Schema (PAR structure, evidence types, confidence fields)
  - Epics Story 2.1 (schema validation acceptance criteria)
- **Key Findings:**
  - JSON Resume lacks PAR structure, quantification, evidence linking
  - O*NET SOC codes provide standardized competency framework
  - Pydantic v2: field_validator, model_validator, discriminated unions
  - JSON Schema 2020-12 preferred over draft-07
  - Schema versioning: semantic versioning with backward compatibility
  - Confidence fields for partially recalled accomplishments

---

## AI AGENT INTEGRATION (Items 64+)

### RB-064: Claude Code CLI Friendliness & AI Agent Integration Patterns
- **Status:** COMPLETE + INTEGRATED ✅
- **Priority:** HIGH
- **Summary:** Comprehensive CLI design patterns for AI agent consumption
- **Location:** claude-code-cli-friendliness-research-2026-01-10.md
- **Integrated Into:** (2026-01-10)
  - Architecture Section 3.3 (CLI Interface Design) - AI Agent Compatibility table, Semantic Exit Codes
  - Architecture Section 4.4 (Format Patterns) - JSON output with format_version, Stdout/Stderr Separation, Enhanced Error Objects
  - Epics Story 1.2 (Rich Console & Output Formatting) - --quiet flag, stderr separation
  - Epics Story 1.4 (Error Handling & Exit Codes) - Semantic exit codes 0-5, StructuredError with recoverable
  - Epics Story 1.5 (AI Agent Context Documentation) - NEW STORY for CLAUDE.md file
- **Key Findings:**
  1. **JSON output essential:** Every command must support `--json` for structured output
  2. **Semantic exit codes:** 0=success, 1=user error, 2=config error, 3=validation, 4=not found, 5=system error
  3. **Non-interactive by default:** All input via flags/env vars; no prompts
  4. **Stdout/stderr separation:** Results to stdout, progress/errors to stderr
  5. **Complete --help:** Agents should be able to use commands from help alone
  6. **Structured errors:** Include code, message, path, suggestion, recoverable fields
  7. **Dry-run support:** `--dry-run` flag for safe preview of operations
  8. **CLAUDE.md file:** Project context file for Claude Code integration
  9. **Format versioning:** Include `format_version` in JSON output for schema evolution
  10. **MCP consideration:** Design with Model Context Protocol compatibility for future

---

## Priority Queue for Remaining Research

### Immediate (Before Implementation Starts)
~~1. **RB-047**: RRF Implementation Details~~ - COMPLETE
~~2. **RB-048**: e5-large-instruct Model Evaluation~~ - COMPLETE
~~3. **RB-050**: Embedding Cache Invalidation Strategy~~ - COMPLETE
~~4. **RB-063**: Work Unit Schema Validation~~ - COMPLETE
~~5. **RB-049**: Field-Specific Embeddings Strategy~~ - COMPLETE

### During Implementation (Remaining)
~~1. **RB-051**: ATS Keyword Density Optimization~~ - COMPLETE
~~2. **RB-052**: Resume Length Best Practices~~ - COMPLETE

**ALL PENDING RESEARCH COMPLETE!** Ready for implementation.

### Recently Completed (2026-01-10)
- **RB-047**: RRF Implementation Details - COMPLETE
- **RB-048**: e5-large-instruct Model Evaluation - COMPLETE
- **RB-049**: Field-Specific Embeddings Strategy - COMPLETE
- **RB-050**: Embedding Cache Invalidation - COMPLETE
- **RB-051**: ATS Keyword Density Optimization - COMPLETE
- **RB-052**: Resume Length Best Practices - COMPLETE
- **RB-059**: Executive Resume Templates - COMPLETE + INTEGRATED
- **RB-060**: Accomplishment Framing Strategies - COMPLETE + INTEGRATED
- **RB-061**: PAR/CAR/STAR Framework - VALIDATED + INTEGRATED
- **RB-062**: Resume Trends 2025-2026 - COMPLETE + INTEGRATED
- **RB-063**: Work Unit Schema Validation - COMPLETE

### Post-MVP Backlog
- RB-053: Jina-v2-base Alternative
- RB-054: Cross-Encoder Re-ranking
- RB-055: Cover Letter Generation
- RB-056: Resume Analytics Dashboard
- RB-057: Multi-Language Support
- RB-058: PDF Accessibility

---

## Research Completion Tracking

| Milestone | Items | Complete | Percentage |
|-----------|-------|----------|------------|
| MVP Ready | 52 | 52 | 100% |
| Total Backlog | 63 | 52 | 83% |
| Post-MVP Deferred | 11 | 0 | N/A |

**Status:** ALL MVP RESEARCH COMPLETE! ✅

**Next Action:** Begin Epic 1 implementation (Project Foundation & Developer Experience).

**Recent Progress (2026-01-10):**

**Hybrid Search Implementation Research (RB-047, RB-048, RB-050):**
- Completed deep research on RRF fusion, e5-large-instruct model, and cache invalidation
- Created hybrid-search-implementation-research-2026-01-10.md with detailed findings
- **INTEGRATED** all hybrid search findings into planning artifacts:
  - Architecture Section 1.3: Added RRF parameter k=60, Embedding Cache technology
  - Architecture Section 1.3.1: NEW section "Hybrid Search Implementation" with RRF formula, model specs, instruction prefixes, cache key design
  - Architecture Section 3.2: Updated cache format (SQLite + pickle + gzip), added cache schema and invalidation strategy
  - Epics Story 4.1.5: NEW story "Embedding Service & Cache" with full implementation guidance
  - Epics Story 4.2: Added RRF fusion acceptance criteria, embedding prefix requirements, detailed technical notes

**Content Strategy Research (RB-059 through RB-062):**
- Completed executive resume content strategy research
- PAR framework VALIDATED as best practice for resume contexts
- Created executive-resume-content-strategy-research-2026-01-10.md with detailed findings
- **INTEGRATED** all content strategy findings into planning artifacts:
  - Architecture Section 1.4: Content Strategy Standards (new section)
  - Architecture Work Unit Schema Extensions (scope, impact_category, metrics, framing)
  - Architecture templates/ (added executive.html, ats-executive.html)
  - Architecture archetypes/ (added transformation.yaml, cultural.yaml, strategic.yaml)
  - Epics Story 2.1: Added executive-level schema acceptance criteria
  - Epics Story 2.2: Added executive archetype acceptance criteria
  - Epics Story 3.2: Added content quality validation (weak verb detection)
  - Epics Story 5.1: Added executive template acceptance criteria

**Schema & Embeddings Research (RB-063, RB-049):**
- Completed deep research on Work Unit schema validation and field-specific embeddings
- Created schema-and-embeddings-research-2026-01-10.md with detailed findings
- **Key Findings:**
  - RB-063: JSON Resume limitations require custom extensions; O*NET integration recommended; Pydantic v2 validation patterns; JSON Schema 2020-12 preferred
  - RB-049: Multi-field embeddings achieve ~95% accuracy vs 60-70% for single-vector; 70/20/5/5 weighting (experience/education/skills/languages)

**ATS & Resume Length Research (RB-051, RB-052):**
- Completed deep research on ATS keyword optimization and resume length best practices
- Created ats-keyword-and-resume-length-research-2026-01-10.md with detailed findings
- **Key Findings:**
  - RB-051: Optimal keyword density 2-3%; target 60-80% JD keyword coverage; placement strategy (Summary > Skills > Experience)
  - RB-052: Two-page resumes achieve 35% higher interview rates; optimal word count 475-600 (1pg) or 800-1,200 (2pg); 4-6 bullets/role
- **INTEGRATED:** Architecture Section 1.4 (ATS Keyword Optimization, Content Density Guidelines); Epics Story 3.2 (content density validation); Epics Story 4.3 (keyword analysis in plan output)

**Embedding Model Update (RB-027):**
- Updated status from UPDATE-NEEDED to COMPLETE
- Architecture already reflects new model recommendation (multilingual-e5-large-instruct as primary)
- No additional changes required

**ALL RESEARCH COMPLETE AND INTEGRATED!** Ready to begin Epic 1 implementation.

---

*Last Updated: 2026-01-10*
