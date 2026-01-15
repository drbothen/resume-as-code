# Epic 6 Dependencies Updated

```
Story 6.1 (Profile) ─────────────────────────────────────────────┐
Story 6.2 (Certifications) ──────────────────────────────────────┤
Story 6.3 (Skills Curation) ─────────────────────────────────────┤
Story 6.6 (Education) ───────────────────────────────────────────┼──► Story 6.4 (Executive Template)
Story 6.7 (Positions) ───────────────────────────────────────────┤          │
Story 6.13 (Career Highlights) ──────────────────────────────────┤          │
Story 6.14 (Board Roles) ────────────────────────────────────────┤          ▼
Story 6.15 (Publications) ───────────────────────────────────────┤   Story 6.17 (CTO Template)
Story 6.16 (Enhanced Scope) ─────────────────────────────────────┘
                                                                           │
Story 6.2 (Certifications) ──────────────────────────────────────┐         │
Story 6.6 (Education) ───────────────────────────────────────────┼──► Story 6.18 (Enhanced Plan)
Story 6.7 (Positions) ───────────────────────────────────────────┘

Story 6.19 (Philosophy Documentation) ──► Independent (can start anytime)
```

---

## Story 6.19: Resume as Code Philosophy Documentation

As a **potential user or contributor discovering this project**,
I want **comprehensive documentation explaining the Resume as Code philosophy**,
So that **I understand the "why" behind the approach and can effectively use or contribute to the tool**.

**Acceptance Criteria:**

**Given** the project repository
**When** documentation is complete
**Then** a `docs/` folder exists with:
```
docs/
├── README.md                    # Index/navigation
├── philosophy.md                # Core philosophy explanation
├── data-model.md                # Work Units, Positions, etc.
├── workflow.md                  # Capture → Plan → Build flow
└── diagrams/
    ├── data-model.excalidraw    # Entity relationships
    ├── workflow-pipeline.excalidraw  # 4-stage pipeline
    └── philosophy-concept.excalidraw # Traditional vs RaC comparison
```

**Given** a user reads `docs/philosophy.md`
**When** they finish reading
**Then** they understand:
- The "resumes as queries against capability graph" mental model
- Why Work Units are the atomic unit (not jobs, not bullet points)
- The PAR framework (Problem-Action-Result)
- Git-native benefits (versioning, branching, collaboration)
- Separation of data, selection, and presentation

**Given** the data model diagram (Excalidraw)
**When** viewed
**Then** it shows:
- Work Unit, Position, Certification, Education entities
- Relationships with cardinality (Work Units → Position is many-to-one)
- Config aggregation (Profile, Skills, etc.)

**Given** the workflow pipeline diagram (Excalidraw)
**When** viewed
**Then** it shows:
- Four stages: Capture → Validate → Plan → Build
- Command names, inputs, outputs at each stage
- Data flow arrows with labels

**Given** the philosophy concept diagram (Excalidraw)
**When** viewed
**Then** it contrasts:
- Traditional approach (document-centric, multiple resume files)
- Resume as Code approach (data-centric, queries against capability graph)

**Technical Notes:**
- Use BMAD Excalidraw workflows for diagram creation
- Export both `.excalidraw` (editable) and `.svg` (embeddable)
- Keep documentation evergreen — avoid version-specific details
- Cross-link all documents from index
- Update main README.md with link to docs folder

---

## Story 6.20: Comprehensive README Update

As a **developer discovering the Resume as Code repository**,
I want **a comprehensive README that explains what the tool does and how to use it**,
So that **I can quickly understand the value proposition and get started**.

**Dependencies:** Story 6.19 (Philosophy Documentation) - for docs/ folder links

**Acceptance Criteria:**

**Given** the updated README.md
**When** viewed on GitHub
**Then** it includes these sections:
1. Title with tagline + philosophy teaser
2. Key Features list (8-10 features)
3. Quick Start guide (install → create → validate → plan → build)
4. Command Reference (all commands with flags and examples)
5. Examples section (practical workflows)
6. Configuration section (hierarchy, .resume.yaml example)
7. Documentation link (→ docs/)
8. Contributing section (dev setup, code quality, git flow)
9. License

**Given** a new user follows the Quick Start
**When** they complete it
**Then** they have:
- Installed the tool
- Created their first Work Unit
- Run validation
- Generated a resume from a sample JD

**Given** the Command Reference section
**When** viewed
**Then** it documents all commands:
- `resume new work-unit` - Create Work Units
- `resume validate` - Schema validation
- `resume list` - List Work Units
- `resume plan --jd FILE` - Preview selection
- `resume build --jd FILE` - Generate resume
- `resume config` - Configuration management
- `resume cache clear` - Cache management

**Technical Notes:**
- Keep README under 500 lines — link to docs/ for details
- All code examples must be copy-pasteable and tested
- Use tables for flag documentation
- Add badges (Python version, license) for visual appeal

---

## Story 6.21: GitHub Pages Marketing Site (Docusaurus)

As a **potential user discovering Resume as Code**,
I want **a polished marketing website that showcases the tool's capabilities**,
So that **I can understand its value, see it in action, and decide to adopt it**.

**Dependencies:** Story 6.19 (Philosophy Documentation) - content and diagrams source

**Acceptance Criteria:**

**Given** the Docusaurus site is deployed
**When** a user visits the site
**Then** they see:
- **Hero Section**: Tagline, value proposition, CTAs (Get Started, GitHub)
- **Features**: 8 key features with icons and descriptions
- **Philosophy**: "Resumes as queries" explanation with embedded diagrams
- **Interactive Demos**: Work Unit Builder, Plan Simulator, Output Preview
- **Documentation**: Searchable docs (Getting Started, Commands, Data Model)
- **Examples**: Runnable code snippets with expected output

**Given** the Demo page
**When** a user interacts with it
**Then** they can:
- Build a sample Work Unit with real-time YAML preview
- Run a mock plan against sample JD and Work Units
- Preview how Work Units render to resume bullets
- Copy generated YAML to clipboard

**Given** the site is deployed
**When** accessed
**Then**:
- Available at `https://[username].github.io/resume-as-code/`
- Mobile responsive (hamburger nav, touch-friendly)
- Lighthouse score 90+ (performance, accessibility)
- Automated deployment via GitHub Actions

**Technical Notes:**
- Use Docusaurus classic template
- Interactive demos built with React components
- Monaco editor for code input/preview
- Port existing docs/ content to Docusaurus format
- Local search (or Algolia if available)
- GitHub Actions workflow for automated deployment

**Site Structure:**
```
Home (Hero + Marketing)
├── Features
├── Philosophy (with Excalidraw diagrams)
├── Demo (3 interactive demos)
├── Docs/
│   ├── Getting Started
│   ├── Commands
│   ├── Data Model
│   └── Configuration
├── Examples
└── GitHub (external)
```


---
