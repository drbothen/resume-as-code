# Resume-as-Code Research Backlog

**Generated:** 2026-01-09
**Source:** Brainstorming Session Extraction
**Total Items:** 46
**Status:** Pending Research

---

## Category 1: First Principles (4 items)

| # | Topic | Research Question | Status |
|---|-------|-------------------|--------|
| 1 | Work Unit Schema Design | What fields are essential for a "documented instance of applied capability"? How do other systems model work/accomplishments? | pending |
| 2 | Evidence/Proof Structures | How can work be linked to verifiable artifacts (repos, docs, metrics)? What provenance standards exist? | pending |
| 3 | Skill Emergence Models | How can skills/seniority be inferred from aggregated work units rather than declared? | pending |
| 4 | Career Graph Theory | What graph structures best represent careers? How do knowledge graphs model professional experience? | pending |

## Category 2: Morphological Analysis (6 items)

| # | Topic | Research Question | Status |
|---|-------|-------------------|--------|
| 5 | YAML vs Alternatives | Why YAML over JSON/TOML for resume data? What are parsing/validation tradeoffs? | pending |
| 6 | File-per-Unit Storage | What naming conventions work best? How do other "content as files" systems handle this? | pending |
| 7 | Jinja2 + HTML/CSS to PDF | What's the best pipeline for template-to-PDF? WeasyPrint, Puppeteer, others? | pending |
| 8 | Natural Language Query | How can JD text be parsed into queryable requirements? What NLP approaches work? | pending |
| 9 | JD Matching/Scoring | What algorithms score resume content against job descriptions? Semantic similarity approaches? | pending |
| 10 | Python Tooling Ecosystem | What Python libraries exist for resume generation, PDF creation, YAML handling? | pending |

## Category 3: IaC Patterns (4 items)

| # | Topic | Research Question | Status |
|---|-------|-------------------|--------|
| 11 | Plan Before Apply Pattern | How does Terraform's plan/apply translate to resume generation? What should `resume plan` output? | pending |
| 12 | State/Provenance Tracking | How can submission history be tracked without becoming a CRM? What's the minimal schema? | pending |
| 13 | Module/Archetype Patterns | How do Terraform modules work? How can Work Unit archetypes accelerate capture? | pending |
| 14 | Provider Architecture | How do Terraform providers abstract outputs? How to design PDF/DOCX/ATS providers? | pending |

## Category 4: SSG Patterns (5 items)

| # | Topic | Research Question | Status |
|---|-------|-------------------|--------|
| 15 | Content/Layout Separation | How do Hugo/Jekyll separate content from themes? Best practices for resume theming? | pending |
| 16 | Frontmatter Standards | What reserved vs freeform keys pattern works best? How do SSGs handle this? | pending |
| 17 | Shortcode/Component Systems | How can semantic components (`{{ impact_block }}`) work at render time? | pending |
| 18 | Build Pipeline Design | How do SSG build pipelines work? What can `resume build --watch` learn from them? | pending |
| 19 | Taxonomy Systems | How do SSGs handle many-to-many tagging? Best practices for skill/domain taxonomies? | pending |

## Category 5: Existing Tools (4 items)

| # | Topic | Research Question | Status |
|---|-------|-------------------|--------|
| 20 | JSON Resume Standard | What does the JSON Resume schema cover? What are its limitations? How to export to it? | pending |
| 21 | ATS Parsing Behavior | How do major ATS systems (Workday, Greenhouse, Lever, Taleo) parse resumes? What breaks them? | pending |
| 22 | Existing Resume-as-Code Tools | What tools exist? (reactive-resume, jsonresume-theme-*, others) What gaps remain? | pending |
| 23 | LinkedIn Data Export | What data can be exported? What format? How do tools like LinkedIn2Resume work? | pending |

## Category 6: AI Integration (5 items)

| # | Topic | Research Question | Status |
|---|-------|-------------------|--------|
| 24 | Capture Flow UX | How should "raw input → Work Unit YAML" work? What prompting/extraction approaches? | pending |
| 25 | Explainable AI Selection | How can AI ranking be made transparent? What explanation formats build trust? | pending |
| 26 | Style Profile Translation | How do different audiences (exec, hiring manager, ATS) need different language? | pending |
| 27 | Embedding Models for Skills | Which embedding models work best for skill/experience matching? OpenAI, Cohere, open-source? | pending |
| 28 | MCP Server Design Patterns | What are best practices for MCP server tool design? How granular should tools be? | pending |

## Category 7: Implementation Backlog (18 items)

| # | Topic | Research Question | Status |
|---|-------|-------------------|--------|
| 29 | Work Unit Schema Finalization | What's the complete, validated schema? | pending |
| 30 | Draft Work Unit Capture | Best UX for capturing work units from raw input? | pending |
| 31 | Rank Work Units Algorithm | Scoring algorithm design and implementation? | pending |
| 32 | Resume Plan Output Format | What should the plan preview look like? | pending |
| 33 | PDF Output Provider | Library selection and template design? | pending |
| 34 | Work Unit Archetypes | What archetypes cover most work types? (incident, greenfield, scaling, leadership) | pending |
| 35 | Resume Build Pipeline | End-to-end implementation architecture? | pending |
| 36 | ATS-Safe Provider | Constraints and formatting rules? | pending |
| 37 | Submission Provenance Schema | Minimal tracking schema? | pending |
| 38 | Archetype Scaffolding | `resume new` command design? | pending |
| 39 | Validate Work Unit Linting | What validation rules? Schema + semantic checks? | pending |
| 40 | DOCX Output Provider | Library selection (python-docx, pandoc, etc.)? | pending |
| 41 | JSON Resume Export | Mapping Work Units → JSON Resume schema? | pending |
| 42 | LinkedIn Import | Parsing and confidence scoring approach? | pending |
| 43 | Semantic Search | Vector DB and embedding pipeline design? | pending |
| 44 | Gap Analysis | Competency model structure and comparison logic? | pending |
| 45 | Watch Mode | Live preview implementation? | pending |
| 46 | HTML Portfolio Provider | Static site generation for portfolio? | pending |

---

## Research Execution Plan

**Approach:** Batch by category, deep research each batch, save incrementally

| Batch | Category | Items | Focus |
|-------|----------|-------|-------|
| A | First Principles + Morphological | 1-10 | Schema, data structures, tooling |
| B | IaC + SSG Patterns | 11-19 | Architecture patterns, pipeline design |
| C | Existing Tools | 20-23 | Competitive landscape, standards |
| D | AI Integration | 24-28 | ML/AI approaches, MCP design |
| E | Implementation | 29-46 | Technical implementation details |

---

*This backlog extracted from brainstorming session 2026-01-09*
