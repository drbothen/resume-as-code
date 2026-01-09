---
title: "Comprehensive Resume-as-Code Research"
date: 2026-01-09
research_type: technical
project: resume
items_covered: 46
batches_completed: 5
status: complete
---

# Comprehensive Resume-as-Code Research

**Project:** Resume as Code
**Researcher:** Mary (Business Analyst)
**Date:** 2026-01-09
**Total Research Items:** 46
**Status:** Complete

---

## Research Backlog

### Batch A: First Principles + Morphological (Items 1-10) ✅
### Batch B: IaC + SSG Patterns (Items 11-19) ✅
### Batch C: Existing Tools (Items 20-23) ✅
### Batch D: AI Integration (Items 24-28) ✅
### Batch E: Implementation Details (Items 29-46) ✅

---

# BATCH A: Schema Design, Data Structures, and Tooling

## Executive Summary

This research establishes the foundational technical and methodological framework for Resume-as-Code systems. Key findings include the superiority of YAML for human-readable resume data storage, the Problem-Action-Result (PAR) structure as the optimal accomplishment model, and the emergence of skill inference algorithms that can extract capabilities from work descriptions rather than relying on self-declared skills.

---

## 1. Work Unit Schema Design

### Core Finding: Problem-Action-Result (PAR) Structure

The foundation of accomplishment modeling is the **PAR method**:
- **Problem**: Business context, constraints, challenges faced
- **Action**: Specific decisions, tools employed, approaches implemented
- **Result**: Quantifiable metrics—revenue, costs, time saved, efficiency improvements

### Recommended Work Unit Schema

```yaml
id: wu-unique-identifier
context:
  domain: string  # e.g., "industrial cybersecurity"
  system: string  # e.g., "MSS ingestion pipeline"
  constraints: []  # e.g., ["safety-critical", "regulated"]
problem:
  statement: string  # Business context description
  scale: string  # Size/scope of the problem
inputs:
  signals: []  # What triggered this work
actions:
  - string  # Specific actions taken
skills_demonstrated:
  - string  # Skills applied
outputs:
  artifacts: []  # What was created
outcomes:
  impact: []  # Measurable results
  metrics:
    type: string  # revenue|percentage|time|quality|throughput
    value: number
    unit: string
evidence:
  - type: string  # repo|doc|dashboard|certification
    url: string
time:
  started: date
  ended: date
```

### Measurement Framework

| Metric Type | Description | Example |
|------------|-------------|---------|
| Revenue/Profit | Direct financial impact | "$2M revenue increase" |
| Percentage | Relative improvements | "40% reduction in errors" |
| Time Savings | Efficiency gains | "20 hours/week saved" |
| Scale | Size of systems/data | "10M records processed" |
| Quality | Accuracy, satisfaction | "99.9% uptime achieved" |
| Throughput | Volume processed | "1000 requests/second" |

### JSON Resume Limitations

The standard JSON Resume schema provides limited support for work unit decomposition—highlights are simple string arrays, not structured accomplishment objects. Our Work Unit schema extends this foundation significantly.

---

## 2. Evidence and Provenance Structures

### Provenance Model (Inspired by Software Supply Chain)

Evidence types for professional accomplishments:

| Evidence Type | Description | Example |
|--------------|-------------|---------|
| Code Repository | Git URLs with commit hashes | `git://repo#commit` |
| Project Management | Task/milestone references | Jira ticket links |
| Metrics | Dashboard/report links | Grafana dashboard URL |
| Documentation | Design docs, specs | Confluence page |
| Communication | Email threads, Slack | Meeting notes |
| Certification | Badge/verification URLs | Credly badge |

### Proof-of-Work Concept

Rather than requiring third-party attestation:
- Git commit histories verify code contributions
- Metrics dashboards provide contemporaneous records
- Public projects enable direct examination
- Evidence transforms resume from unverified claims to documented facts

---

## 3. Skill Emergence Models

### Inference vs Declaration

Traditional resumes rely on self-declared skills with these problems:
- Professionals inflate proficiency levels
- Skill categories inconsistent across individuals
- Presence doesn't indicate proficiency or recency

### Skill Inference Process

1. **Input**: Structured accomplishment data (problem, actions, results)
2. **NER Analysis**: Named Entity Recognition identifies technologies, methodologies
3. **Context Analysis**: Proficiency signals extracted from language
4. **Output**: Inferred skills with proficiency levels

### Proficiency Indicators

| Signal | Interpretation |
|--------|---------------|
| "worked with" | Basic familiarity |
| "architected", "led" | Expert-level proficiency |
| Recent accomplishments | Current proficiency |
| Older accomplishments | Potentially outdated |
| Large scale | Higher proficiency |
| Mentoring others | Expert level |

### Proficiency Levels

1. **Foundational**: Basic familiarity, execution under guidance
2. **Intermediate**: Independent execution and troubleshooting
3. **Advanced**: Optimization, architecture, mentoring
4. **Strategic**: Driving adoption across organizations

---

## 4. Career Graph Theory

### Knowledge Graph Structure

Node types:
- Professionals (individuals)
- Skills
- Roles
- Companies
- Projects
- Technologies
- Certifications
- Educational institutions

Edge types:
- `possesses` (professional → skill, with proficiency)
- `works_in` (professional → role)
- `works_for` (professional → company)
- `requires` (role → skill)
- `prerequisite` (skill → skill)
- `adjacency` (skill ↔ skill)

### LinkedIn Economic Graph Example

The most comprehensive implementation:
- Career transition recommendations via skill transfer analysis
- Learning path suggestions via skill prerequisites
- Labor market trend analysis
- Talent-to-role matching via skill graph alignment

### Graph Analysis Capabilities

- **Skill adjacency**: Which skills commonly develop together
- **Career path analysis**: Common progression patterns
- **Opportunity identification**: Role matching based on adjacent skills
- **Community detection**: Clusters of related professionals/roles

---

## 5. YAML vs JSON vs TOML

### Comparison Matrix

| Aspect | YAML | JSON | TOML |
|--------|------|------|------|
| Human Readability | ⭐⭐⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐⭐ |
| Machine Parsing | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ |
| Comments Support | ✅ | ❌ | ✅ |
| Ecosystem Maturity | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ |
| Version Control Diffs | ⭐⭐⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐⭐ |

### Recommendation: YAML

**Why YAML for Resume-as-Code:**
1. Superior human readability for manual editing
2. Natural indentation-based hierarchy
3. Comment support for documentation
4. Excellent version control diffs
5. Mature parsing libraries (PyYAML, ruamel.yaml)
6. Export to JSON for API consumption when needed

---

## 6. File-per-Unit Storage Patterns

### Single File vs File-per-Unit

| Approach | Pros | Cons |
|----------|------|------|
| **Single File** | Simple versioning, atomic updates | Unwieldy at scale, coarse diffs |
| **File-per-Unit** | Granular version control, reusability | Requires manifest coordination |

### Recommended Directory Structure

```
/resume-data/
├── metadata/
│   └── profile.yaml          # Name, contact, summary
├── work/
│   ├── 2024-company-a/
│   │   ├── role.yaml         # Role metadata
│   │   ├── wu-project-1.yaml # Work unit
│   │   └── wu-project-2.yaml
│   └── 2023-company-b/
│       └── ...
├── education/
│   └── degree-1.yaml
├── skills/
│   └── taxonomy.yaml         # Skill definitions
├── evidence/
│   └── provenance.yaml       # Evidence references
└── manifest.yaml             # Ties it all together
```

### Naming Convention

Pattern: `{YEAR}-{COMPANY}-{PROJECT_SLUG}.yaml`

Examples:
- `2024-acme-ingestion-pipeline.yaml`
- `2023-startup-auth-system.yaml`

---

## 7. Template-to-PDF Pipelines

### Approach Comparison

| Tool | Type | Pros | Cons |
|------|------|------|------|
| **WeasyPrint** | Python HTML→PDF | Simple, lightweight, pure Python | Limited CSS, no JS |
| **Puppeteer** | Headless Chrome | Full CSS/JS support | Heavy, slow |
| **Prince XML** | Commercial | Best quality | Expensive |
| **ReportLab** | Python native | Precise control | Complex code |

### Recommended Pipeline

```
YAML Data → Jinja2 Template → HTML + CSS → WeasyPrint → PDF
```

**Stack:**
1. **Data**: PyYAML for loading
2. **Validation**: Pydantic for schema validation
3. **Templating**: Jinja2 for HTML generation
4. **PDF**: WeasyPrint for conversion

### Multi-Template Support

- **ATS-Optimized**: Single-column, keyword-dense
- **Modern**: Two-column, aesthetically optimized
- **Executive**: Narrative-focused, achievement-heavy
- **Technical**: Skills-matrix, project-detailed

---

## 8. Natural Language JD Parsing

### Parsing Challenges

Job descriptions vary widely:
- Explicit skill lists vs narrative descriptions
- "Required" vs "preferred" vs "nice-to-have"
- Version/recency requirements ("5+ years Python")
- Implicit requirements not explicitly stated

### Multi-Stage Parsing Approach

1. **Rule-based extraction**: Keyword dictionaries, regex patterns
2. **NER models**: Trained on job posting corpora
3. **ML classification**: Learn patterns from labeled data
4. **Domain knowledge**: Occupational taxonomies for context

### Key Entities to Extract

- Job title and level
- Required skills (with proficiency)
- Preferred skills
- Years of experience
- Educational requirements
- Location/remote status
- Salary range

---

## 9. Resume-to-JD Matching Algorithms

### Algorithm Levels

| Level | Approach | Accuracy |
|-------|----------|----------|
| **Basic** | Keyword matching | Low - misses synonyms |
| **Intermediate** | TF-IDF similarity | Medium |
| **Advanced** | Semantic embeddings | High (94.2% reported) |
| **Hybrid** | Multiple approaches combined | Highest |

### Semantic Similarity Approach

1. Transform resume and JD text into vector embeddings
2. Use transformer models (BERT, Sentence-BERT)
3. Calculate cosine similarity between vectors
4. Score ranges from 0 (no match) to 1 (perfect match)

### Multi-Dimensional Scoring

- Explicit skill matches
- Implicit skill inference
- Proficiency level alignment
- Experience level matching
- Educational requirement alignment
- Cultural fit signals

### Research Finding

Modern semantic systems achieve **94.2% accuracy** with **85% improvement** over keyword-based screening.

---

## 10. Python Resume Tooling Ecosystem

### Recommended Stack

| Category | Library | Purpose |
|----------|---------|---------|
| **YAML** | PyYAML, ruamel.yaml | Data parsing/generation |
| **Validation** | Pydantic | Schema validation, type safety |
| **Templating** | Jinja2 | HTML template rendering |
| **PDF** | WeasyPrint | HTML-to-PDF conversion |
| **NLP** | spaCy | Entity extraction, parsing |
| **ML** | Hugging Face transformers | Semantic similarity |
| **Graphs** | NetworkX | Career graph analysis |

### Existing Tools

| Tool | Description |
|------|-------------|
| **pyresparser** | Extract structured data from PDF/DOCX resumes |
| **ResumeParser** | NER-based resume parsing |
| **JSON Resume** | Standard schema with tooling ecosystem |
| **yamlresume** | YAML-based resume management |

---

## Key Sources

- JSON Resume Schema: https://docs.jsonresume.org/schema
- WeasyPrint documentation and tutorials
- spaCy NLP library: https://spacy.io
- Pydantic validation: https://docs.pydantic.dev
- Skills inference research from MIT CISR and Rolemapper

---

*Batch A Complete*

---

# BATCH B: IaC + SSG Patterns (Items 11-19)

## Executive Summary

This research explores how proven architectural patterns from Infrastructure-as-Code (Terraform) and Static Site Generators (Hugo, Jekyll) can be applied to Resume-as-Code systems. Key findings include the power of the "plan-before-apply" workflow for resume preview, state management for submission provenance, module systems for experience archetypes, and provider abstraction for multi-format output.

---

## 11. Terraform "Plan Before Apply" Pattern

### Core Workflow

Terraform's three-step workflow:
1. **Write**: Author configurations describing desired state
2. **Plan**: Preview what changes will be made
3. **Apply**: Execute the changes

### Resume Application: `resume plan`

```bash
$ resume plan --jd senior-backend.txt --template modern

Resume Plan for: Senior Backend Engineer @ TechCorp
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

CONTENT SELECTION:
  + Include: Cloud Migration Project (95% relevance)
  + Include: API Gateway Architecture (92% relevance)
  + Include: Performance Optimization (88% relevance)
  ~ Partial: Database Scaling (65% - include metrics only)
  - Exclude: Frontend Dashboard (23% relevance)

SKILL EMPHASIS:
  ↑ Kubernetes, Go, PostgreSQL (high match)
  → Python, AWS (moderate match)
  ↓ React, TypeScript (low relevance)

REWRITING:
  • "Led team" → "Architected and led" (stronger action verb)
  • Adding quantified metrics to 2 achievements

Plan: 4 work units, 12 skills, 1 page PDF
Apply this plan? [y/n/edit]
```

### Key Benefits

- **Human judgment inserted** before final commitment
- **Speculative plans** for different targets without commitment
- **Team review** - mentors can review plans before submission
- **`--auto-approve`** for automated pipelines (with safeguards)

---

## 12. State and Provenance Tracking

### Terraform State Concepts

- **State file**: JSON record of managed resources
- **Remote backends**: Secure, versioned storage (S3, Azure, GCS)
- **State locking**: Prevent concurrent corruption
- **State migration**: Move between backends

### Resume Provenance Schema

```yaml
# submissions.yaml - Resume submission provenance
submissions:
  - id: sub-2026-01-09-techcorp
    timestamp: 2026-01-09T14:30:00Z
    target:
      company: TechCorp
      position: Senior Backend Engineer
      job_id: JOB-12345
    resume:
      version: v2.3.1
      commit: abc123def
      template: modern-technical
      format: pdf
    content:
      work_units_included:
        - wu-2024-cloud-migration
        - wu-2024-api-gateway
        - wu-2023-perf-optimization
      skills_emphasized:
        - kubernetes
        - golang
        - postgresql
    outcome:
      status: phone_screen  # submitted|rejected|phone_screen|onsite|offer
      last_updated: 2026-01-15
```

### Provenance Capabilities

| Capability | Description |
|------------|-------------|
| **Audit Trail** | What was sent, when, to whom |
| **Version Rollback** | Restore previous configurations |
| **Pattern Analysis** | Which versions got responses |
| **Duplicate Prevention** | Avoid re-applying to same company |

---

## 13. Module and Archetype Patterns

### Terraform Module Concept

- Self-contained, reusable resource packages
- Input variables for customization
- Output values for integration
- Version constraints for stability

### Work Unit Archetypes

```yaml
# archetypes/incident-response.yaml
archetype: incident-response
description: "Crisis management and incident resolution"
required_fields:
  - incident_type      # security|outage|data_loss|compliance
  - severity           # P1|P2|P3
  - team_size
  - resolution_time
  - business_impact_prevented
optional_fields:
  - root_cause
  - preventive_measures
  - lessons_learned
template: |
  Led {{severity}} {{incident_type}} response with {{team_size}}-person team.
  Resolved in {{resolution_time}}, preventing {{business_impact_prevented}}.
  {{#if root_cause}}Root cause: {{root_cause}}{{/if}}
```

### Standard Archetypes

| Archetype | Use Case |
|-----------|----------|
| **incident-response** | Crisis management, outages, security incidents |
| **greenfield-project** | Building from scratch, new systems |
| **system-scaling** | Performance, growth, optimization |
| **leadership** | Team building, mentoring, process improvement |
| **migration** | Cloud migrations, technology upgrades |
| **integration** | API development, third-party integrations |

### Benefits

- **Faster capture**: Fill structured templates vs free-form
- **Consistency**: Standardized narrative structure
- **Upgradability**: Improve archetype, all instances benefit
- **Guidance**: Clear prompts for what to include

---

## 14. Provider Architecture

### Terraform Provider Model

- Providers abstract platform-specific logic
- Common interface for Terraform core
- Handles authentication, API calls, state
- New providers added without core changes

### Resume Output Providers

```python
# Abstract provider interface
class ResumeProvider:
    def render(self, resume_data: ResumeData, config: ProviderConfig) -> bytes:
        raise NotImplementedError

    def validate(self, resume_data: ResumeData) -> list[ValidationError]:
        raise NotImplementedError

# Concrete implementations
class PDFProvider(ResumeProvider):
    """Modern, visually appealing PDF for human review"""

class ATSProvider(ResumeProvider):
    """Single-column, keyword-optimized for ATS parsing"""

class DOCXProvider(ResumeProvider):
    """Editable Word format for recruiters"""

class HTMLProvider(ResumeProvider):
    """Responsive web version for portfolios"""

class JSONResumeProvider(ResumeProvider):
    """JSON Resume format for interoperability"""
```

### Provider Characteristics

| Provider | Optimization | Use Case |
|----------|--------------|----------|
| **PDF Modern** | Visual appeal, typography | Direct recruiter submission |
| **PDF ATS** | Simple layout, keywords | Applicant tracking systems |
| **DOCX** | Editability | Recruiter modifications |
| **HTML** | Responsiveness | Portfolio websites |
| **JSON Resume** | Interoperability | Platform integrations |

---

## 15. Content/Layout Separation (SSG Pattern)

### Core Principle

Content (what you say) is completely independent of presentation (how it looks).

### Hugo/Jekyll Model

```
Content (Markdown)  →  Template (HTML/CSS)  →  Output
     ↓                       ↓
  Unchanged              Swappable
```

### Resume Application

```yaml
# content/work-units/cloud-migration.yaml (CONTENT)
id: wu-2024-cloud-migration
problem: Legacy on-prem infrastructure causing scaling issues
actions:
  - Designed multi-region AWS architecture
  - Led 6-person migration team
  - Implemented IaC with Terraform
results:
  - 40% cost reduction
  - 99.99% uptime achieved
  - 3x scaling capacity
```

```html
<!-- templates/modern/work-unit.html (PRESENTATION) -->
<div class="achievement">
  <h3>{{ title }}</h3>
  <p class="context">{{ problem }}</p>
  <ul class="actions">
    {% for action in actions %}
    <li>{{ action }}</li>
    {% endfor %}
  </ul>
  <div class="metrics">
    {% for result in results %}
    <span class="metric">{{ result }}</span>
    {% endfor %}
  </div>
</div>
```

### Benefits

- **Theme switching** without content changes
- **Audience adaptation** - same content, different emphasis
- **Format-free storage** - content renders to any format
- **A/B testing** - test different presentations

---

## 16. Frontmatter Standards

### SSG Frontmatter Pattern

```yaml
---
title: "Page Title"
date: 2026-01-09
tags: [python, backend]
draft: false
custom_field: "anything"
---

Content goes here...
```

### Resume Frontmatter Schema

```yaml
---
# Reserved fields (standard semantics)
title: "Software Engineer Resume"
version: "2.3.1"
generated: 2026-01-09
template: modern-technical
target:
  company: TechCorp
  position: Senior Backend Engineer
  jd_file: jobs/techcorp-backend.txt

# Content selection
include:
  work_units: [wu-2024-*, wu-2023-cloud-*]
  skills: [backend, cloud, databases]
exclude:
  work_units: [wu-*-frontend-*]

# Presentation directives
emphasis:
  skills: [kubernetes, golang]
  achievements: [cost-reduction, scaling]
tone: technical  # technical|business|leadership

# Freeform/custom fields
recruiter_notes: "Referred by Jane Smith"
salary_target: 180000
---
```

### Field Categories

| Category | Examples |
|----------|----------|
| **Reserved** | title, version, generated, template |
| **Target** | company, position, jd_file |
| **Selection** | include, exclude, filter |
| **Presentation** | emphasis, tone, format |
| **Custom** | Any additional metadata |

---

## 17. Shortcode/Component Systems

### Hugo Shortcode Syntax

```markdown
{{< youtube id="abc123" >}}
{{< figure src="image.png" caption="My caption" >}}
{{< highlight python >}}
def hello():
    print("Hello")
{{< /highlight >}}
```

### Resume Semantic Components

```markdown
## Professional Experience

{{< work_unit id="wu-2024-cloud-migration" highlight="metrics" >}}

{{< skills_matrix categories="backend,cloud,databases" >}}

{{< impact_block
    metric="40%"
    description="cost reduction"
    context="through cloud optimization"
>}}

{{< timeline
    items="wu-2024-*"
    style="compact"
>}}

{{< certification
    name="AWS Solutions Architect"
    date="2024-03"
    badge_url="https://..."
>}}
```

### Component Library

| Component | Purpose |
|-----------|---------|
| `work_unit` | Render a work unit with options |
| `skills_matrix` | Grid of skills by category |
| `impact_block` | Highlighted achievement metric |
| `timeline` | Chronological visualization |
| `certification` | Credential with badge |
| `project_card` | Project summary block |
| `quote` | Testimonial or endorsement |

---

## 18. Build Pipeline Design

### SSG Build Pipeline

```
Source Files → Parse → Transform → Template → Output
     ↓           ↓         ↓          ↓         ↓
  Monitor    Validate   Process    Render    Write
```

### Resume Build Pipeline

```bash
$ resume build --watch

[14:30:01] Starting build...
[14:30:01] Loading configuration: resume.yaml
[14:30:01] Validating schema... ✓
[14:30:01] Loading 12 work units... ✓
[14:30:01] Processing templates... ✓
[14:30:02] Generating PDF (modern)... ✓
[14:30:02] Generating PDF (ats)... ✓
[14:30:02] Build complete: 2 files, 1.2s

[14:30:02] Watching for changes...

[14:32:15] Changed: work/wu-2024-cloud-migration.yaml
[14:32:15] Rebuilding affected outputs...
[14:32:15] Regenerated: resume-modern.pdf
[14:32:15] Regenerated: resume-ats.pdf
[14:32:16] Build complete: 0.4s (incremental)
```

### Pipeline Features

| Feature | Description |
|---------|-------------|
| **Watch Mode** | Monitor files, auto-rebuild on change |
| **Incremental Builds** | Only rebuild affected outputs |
| **Live Preview** | Browser auto-refresh on change |
| **Dependency Tracking** | Know what affects what |
| **Validation** | Schema, spelling, URL checking |
| **Parallel Generation** | Multiple formats simultaneously |

---

## 19. Taxonomy Systems

### Hugo Taxonomy Model

```yaml
# config.yaml
taxonomies:
  tag: tags
  category: categories
  skill: skills
  domain: domains
```

### Resume Taxonomy Structure

```yaml
# taxonomies/skills.yaml
skills:
  programming:
    - python
    - golang
    - typescript
  cloud:
    - aws
    - gcp
    - kubernetes
  databases:
    - postgresql
    - mongodb
    - redis
  practices:
    - ci-cd
    - infrastructure-as-code
    - observability

# taxonomies/domains.yaml
domains:
  - cybersecurity
  - fintech
  - healthcare
  - e-commerce

# taxonomies/impact-types.yaml
impact_types:
  - cost-reduction
  - revenue-growth
  - efficiency
  - reliability
  - security
```

### Taxonomy-Driven Generation

```yaml
# Generate resume filtered by taxonomy
target:
  position: "Cloud Security Engineer"

filters:
  domains: [cybersecurity, cloud]
  skills: [aws, kubernetes, security]
  impact_types: [security, reliability]

# System automatically selects work units
# tagged with matching taxonomies
```

### Benefits

- **Dynamic filtering**: Generate targeted resumes automatically
- **Many-to-many**: Work units can have multiple tags
- **Skill relationships**: Parent/child, adjacency
- **Analytics**: Which skills appear in which contexts

---

## Key Sources (Batch B)

- Terraform Core Workflow: https://developer.hashicorp.com/terraform/intro/core-workflow
- Terraform State Management: https://spacelift.io/blog/terraform-state
- Terraform Modules: https://scalr.com/learning-center/mastering-terraform-modules
- Hugo vs Jekyll: https://gethugothemes.com/hugo-vs-jekyll
- Hugo Shortcodes: https://gohugo.io/content-management/shortcodes/
- Hugo Taxonomies: https://gohugo.io/content-management/taxonomies/
- Resume-as-Code implementations: Paul Fioravanti, Alex Watt

---

*Batch B Complete*

---

# BATCH C: Existing Tools & Standards (Items 20-23)

## Executive Summary

This research examines the existing ecosystem of resume tools, standards, and platforms. Key findings include JSON Resume as the leading standardization effort (though with limitations), the critical importance of ATS optimization (97.8% of Fortune 500 use ATS), and the fragmented but growing landscape of resume-as-code tools.

---

## 20. JSON Resume Standard

### Schema Overview

JSON Resume is a community-driven open-source standard for machine-readable resume data.

**Core Sections:**

| Section | Key Fields |
|---------|------------|
| `basics` | name, label, email, phone, url, summary, location, profiles |
| `work` | company, position, url, startDate, endDate, summary, highlights |
| `education` | institution, url, area, studyType, startDate, endDate, score, courses |
| `skills` | name, level, keywords |
| `projects` | name, description, highlights, keywords, startDate, endDate, url |
| `certificates` | name, date, issuer, url |
| `publications` | name, publisher, releaseDate, url, summary |
| `languages` | language, fluency |
| `interests` | name, keywords |
| `awards` | title, date, awarder, summary |
| `volunteer` | organization, position, url, startDate, endDate, summary, highlights |

### Ecosystem Scale

- **400+ themes** available via npm registry
- **Official CLI** for validation and export
- **Online editors**: jsonresume.io, resumake.io
- **Registry hosting**: registry.jsonresume.org/username

### JSON Resume Limitations

| Limitation | Impact |
|------------|--------|
| No structured accomplishment model | Highlights are flat string arrays |
| Limited evidence support | No fields for repos, metrics, artifacts |
| No skill proficiency inference | Skills are self-declared only |
| No temporal complexity | Overlapping roles problematic |
| No relationships | Can't link skills to projects |
| Limited multimedia | Only basic image URL |

### Work Unit → JSON Resume Export

```yaml
# Work Unit (our richer format)
id: wu-2024-cloud-migration
problem: Legacy infrastructure causing scaling issues
actions:
  - Designed multi-region AWS architecture
  - Led 6-person migration team
results:
  - cost_reduction: 40%
  - uptime: 99.99%
skills: [aws, terraform, kubernetes]
evidence:
  - repo: github.com/company/migration
  - dashboard: grafana.company.com/metrics
```

```json
// Exported to JSON Resume (lossy projection)
{
  "work": [{
    "company": "Company Name",
    "position": "Cloud Architect",
    "highlights": [
      "Designed multi-region AWS architecture, achieving 40% cost reduction",
      "Led 6-person migration team to 99.99% uptime"
    ]
  }]
}
```

**Note:** Export to JSON Resume is intentionally lossy - it's a compatibility target, not the source of truth.

---

## 21. ATS Parsing Behavior

### ATS Market Reality

- **97.8%** of Fortune 500 companies use ATS
- **99.7%** of recruiters use keyword filters
- **88%** of employers say ATS filters out qualified candidates

### Major ATS Systems

| System | Market | Parsing Quality |
|--------|--------|-----------------|
| Workday | Enterprise | High (native HRIS integration) |
| Greenhouse | Mid-large | High (AI-driven parsing) |
| Lever | Startups/Mid | Good (ATS + CRM combo) |
| iCIMS | Enterprise | Good |
| Taleo (Oracle) | Enterprise | Legacy, improving |
| SmartRecruiters | Enterprise | Good (scale-optimized) |
| BambooHR | SMB | Good |

### What Breaks ATS Parsing

| Issue | Why It Breaks | Solution |
|-------|---------------|----------|
| Multi-column layouts | Parser reads left-to-right | Single column |
| Tables | Cell boundaries confuse parser | Plain text lists |
| Text boxes | Content may be skipped | Body text only |
| Headers/footers | Often ignored entirely | Critical info in body |
| Graphics/images | Cannot be parsed | Remove or supplement with text |
| Non-standard bullets | Not recognized | Use standard • or - |
| Creative headers | "My Journey" not recognized | Use "Work Experience" |
| Fancy fonts | May not render | Arial, Calibri, Georgia |
| Inconsistent dates | Misinterpretation | Use MM/YYYY consistently |

### ATS-Safe Format Specifications

```
Font: Arial, Calibri, Georgia, Helvetica (10-12pt body, 14-16pt headers)
Margins: 1 inch all sides
Format: .docx or .pdf (prefer .docx for maximum compatibility)
Layout: Single column, chronological
Sections: Work Experience, Education, Skills (standard labels)
Dates: MM/YYYY – MM/YYYY or Month YYYY – Month YYYY
Bullets: Standard black dots (•)
```

### Keyword Optimization Strategy

**What recruiters filter by:**
- Skills: 76.4%
- Education: 59.7%
- Job Titles: 55.3%
- Certifications: 50.6%
- Years of Experience: 44%

**Keyword Rules:**
1. Use exact phrasing from job description
2. Include both acronyms AND full terms ("ERP" and "Enterprise Resource Planning")
3. Integrate keywords into achievement statements, not keyword dumps
4. Match required skills explicitly

**Example - Context Integration:**
```
❌ Bad: "Skills: social media, marketing, Facebook, Instagram"

✅ Good: "Developed comprehensive social media marketing strategies
         across Facebook, Instagram, and LinkedIn, increasing brand
         engagement by 45% and generating 200+ qualified leads per quarter"
```

---

## 22. Existing Resume-as-Code Tools

### Tool Landscape

| Tool | Format | Output | Key Feature |
|------|--------|--------|-------------|
| **JSON Resume** | JSON | PDF, HTML, MD | Standard schema, 400+ themes |
| **Reactive Resume** | Web UI | PDF, JSON | Privacy-focused, self-hostable |
| **YAMLResume** | YAML | PDF (LaTeX) | Human-readable, watch mode |
| **Resume-as-Code (PyPI)** | YAML | Word, MD, LaTeX | Jinja templating, Google Drive |
| **RenderCV** | JSON Resume | PDF (LaTeX) | Pixel-perfect rendering |
| **Resumake** | Web UI | JSON, PDF | Easy online editor |
| **LaTeX templates** | LaTeX | PDF | Professional typography |
| **HTML templates** | HTML/CSS | Web, PDF | Portfolio integration |

### Reactive Resume Features

- Free, open-source, self-hostable
- Zero tracking/advertising
- Real-time editing with live preview
- Drag-and-drop customization
- OpenAI integration for writing enhancement
- Share personalized links
- Download tracking
- Multi-language support
- Dark mode

### YAMLResume Approach

```yaml
# resume.yaml - Human-readable format
basics:
  name: Joshua Magady
  label: Security Architect

work:
  - company: TechCorp
    position: Senior Engineer
    startDate: 2022-01
    highlights:
      - Led cloud migration achieving 40% cost reduction
```

```bash
# Build with watch mode
$ yamlresume build --watch --output resume.pdf
```

### Market Gaps Identified

| Gap | Description |
|-----|-------------|
| **Unified workflow** | No tool combines data management + ATS optimization + multi-format export |
| **Role-specific variants** | Limited support for auto-generating targeted versions |
| **Emerging elements** | No structured fields for OSS contributions, deployed projects |
| **A/B testing** | No resume effectiveness analytics |
| **JD analysis** | Limited intelligent keyword extraction from job descriptions |
| **Portfolio integration** | Resume and portfolio often separate systems |

---

## 23. LinkedIn Data Export

### Export Process

1. Navigate to Settings → Data Privacy → "Get a copy of your data"
2. Select data categories (Connections, Profile, etc.)
3. Click "Request Archive"
4. Wait for email (minutes for contacts, up to 72 hours for full profile)
5. Download zip file

### Exported Data Fields

**Basic Export:**
- Profile URL
- Name, job title
- Current company, description
- Location
- Connection count
- Experience duration

**Complete Export:**
- All basic fields plus:
- Company details (size, industry, specialties)
- Profile picture
- Full work history
- Education details
- Skills and endorsements
- Recommendations (limited)
- Activity data

### LinkedIn → JSON Resume Tools

| Tool | Method | Features |
|------|--------|----------|
| **linkedin-to-jsonresume** | Browser extension/bookmarklet | Direct profile scraping, multiple schema versions |
| **jmperezperez converter** | Web app | Process data export zip file |

### Conversion Workflow

```bash
# Using linkedin-to-jsonresume extension
1. Install browser extension
2. Navigate to LinkedIn profile
3. Click extension icon
4. Download JSON Resume file

# Using web converter
1. Request LinkedIn data export
2. Wait for email (up to 72 hours)
3. Upload zip to jmperezperez.com/linkedin-to-json-resume/
4. Download converted JSON Resume
```

### LinkedIn Export Limitations

| Limitation | Impact |
|------------|--------|
| 72-hour delay | Friction in quick conversion workflows |
| No recommendations text | Lose social proof |
| No endorsement counts | Lose skill validation signals |
| No activity/posts | Lose thought leadership evidence |
| No media attachments | Lose portfolio samples |
| API restrictions | Direct API access no longer available |

### Privacy Considerations

- GDPR requires explicit consent for data processing
- Scraping may violate LinkedIn ToS
- Data protection needed for extracted information
- Must provide transparent privacy notices
- Support data subject rights (access, deletion)

---

## Competitive Analysis Summary

### Strengths of Existing Tools

- JSON Resume provides solid standardization foundation
- Multiple export formats widely supported
- Open-source options available (Reactive Resume, YAMLResume)
- Theme ecosystems enable customization
- LinkedIn integration paths exist

### Weaknesses / Opportunities

- **Fragmentation**: Tools specialized, not integrated
- **ATS intelligence**: Limited automatic optimization
- **Work Unit atomicity**: No tool models accomplishments as first-class entities
- **Evidence linking**: No provenance/proof support
- **Skill inference**: All rely on self-declaration
- **`resume plan`**: No preview-before-apply pattern exists
- **Submission tracking**: No provenance across applications

---

## Key Sources (Batch C)

- JSON Resume Schema: https://docs.jsonresume.org/schema
- Jobscan ATS research: https://www.jobscan.co
- Reactive Resume: https://rxresu.me
- YAMLResume: https://github.com/yamlresume/yamlresume
- LinkedIn-to-JSON Resume: https://github.com/joshuatz/linkedin-to-jsonresume
- ATS parsing research from MokaHR, Textkernel, industry surveys

---

*Batch C Complete*

---

# BATCH D: AI Integration (Items 24-28)

## Executive Summary

This research examines AI and machine learning integration for Resume-as-Code systems. Key findings include the effectiveness of conversational UX for work unit capture, the importance of explainable AI for building trust in content selection, practical approaches to style transfer for different audiences, embedding model comparisons for semantic matching, and MCP server design patterns for composable resume tools.

---

## 24. Work Unit Capture Flow UX

### The Challenge

Converting unstructured work narratives ("I led a project that improved our deployment process") into structured Work Unit YAML requires guided extraction without disrupting natural conversation.

### Three-Phase Conversational Approach

**Phase 1: Context Establishment**
```
"Tell me about your role at that company. What was your typical week like?"
"What were you most proud of during that period?"
```
- Open-ended questions build shared understanding
- Avoids premature requests for metrics

**Phase 2: Accomplishment Identification**
```
"What changed as a result of your work?"
"What problem did you solve, and how?"
```
- Temporal framing helps users recognize impact
- Targets specific challenges and solutions

**Phase 3: Metric Extraction**
```
"How many users/systems/dollars were affected?"
"What was the before and after?"
```
- Quantification comes last, with context
- Specific prompts for scale, impact, scope

### Prompting Strategies

**Multi-Stage Extraction:**
1. **Classification prompt**: Determine work unit type (IC accomplishment, leadership, project delivery)
2. **Domain-specific extraction**: Different prompts for different types
3. **Quantification prompt**: Specific metric extraction

**Few-Shot Examples:**
```
Example input: "I led a team of five engineers through a major
               database migration that reduced query latency by 60%"

Extracted Work Unit:
- project_scope: "Database migration"
- team_size: 5
- role: "Technical lead"
- outcome: "60% reduction in query latency"
- skills: ["database", "leadership", "migration"]
```

### Feedback Patterns

| Pattern | Purpose |
|---------|---------|
| **Immediate confirmation** | "I understand you improved deployment, reducing time from 2h to 15min..." |
| **Progressive complexity** | Start with context, surface metrics last |
| **Contextual clarification** | "Performance of what? Improved by how much?" |
| **Validation checkpoints** | Incremental schema validation without disruption |

### Error Recovery

```
❌ "Missing required field: measurable_outcome"

✅ "To make your accomplishment clear to hiring managers, we need
   at least one concrete metric. For example, 'reduced load times
   by 40%' or 'expanded customer base by 15%'."
```

---

## 25. Explainable AI for Resume Selection

### Why Explainability Matters

- Users deserve to understand why experiences were included/excluded
- Builds trust in automated recommendations
- Supports improvement through actionable feedback

### Explainability Techniques

**Feature Importance Analysis:**
```
Your accomplishment ranked highly because:
- Technical stack relevance: 35%
- Quantified business impact: 30%
- Scope and scale: 20%
- Recency: 15%

Suggestion: Emphasize specific ML techniques to strengthen further.
```

**Counterfactual Explanations:**
```
"Your customer support improvement would rank higher if it included
a quantified metric—e.g., 'reduced resolution time by 25%' or
'improved satisfaction from 7.2 to 8.1.'"
```

**Example-Based Explanations:**
```
"We included your 'payment system rebuild' rather than 'support
team reorganization' because payment system demonstrates more
directly relevant technical expertise to this software role."
```

### Explanation Output Format

```yaml
selection_explanation:
  work_unit: wu-2024-cloud-migration
  decision: included
  rank: 2
  relevance_score: 0.87
  factors:
    - factor: skill_match
      weight: 0.35
      detail: "Strong match: AWS, Kubernetes, Terraform"
    - factor: impact_metrics
      weight: 0.30
      detail: "40% cost reduction, 99.99% uptime"
    - factor: scope
      weight: 0.20
      detail: "Led 6-person team, enterprise scale"
  counterfactual: null  # Already included
  suggestions:
    - "Consider adding specific architectural decisions"
```

### Trust-Building Practices

- Log all decision factors for audit trails
- Provide different explanation depths for different users
- Enable "why not?" queries for excluded items
- Show confidence levels, not just decisions

---

## 26. Style Profile Translation

### Audience-Specific Language Needs

| Audience | Style Emphasis |
|----------|----------------|
| **Executives** | Business impact, strategic significance, ROI |
| **Technical Hiring Managers** | Technical depth, architecture, trade-offs |
| **ATS Systems** | Keywords, explicit skills, parseable structure |
| **Recruiters** | Leadership, career progression, accomplishments |
| **HR/Compliance** | Dates, titles, formal credentials |

### Style Dimensions

1. **Formality**: "architected enterprise-scale infrastructure" ↔ "built cool systems"
2. **Technical Depth**: Business impact focus ↔ Technical specifics
3. **Scope Perspective**: Individual contributor ↔ Organizational leader

### Multi-Stage Style Transfer

```
Stage 1: Core accomplishment extraction (invariant facts)
Stage 2: Technical depth adjustment
Stage 3: Scope perspective adjustment
Stage 4: Formality/register adjustment
```

### Style Transfer Examples

**Original (Technical):**
```
Implemented Apache Kafka-based event streaming with 99.95% uptime
SLA using Kubernetes orchestration and custom Go consumers.
```

**Executive Style:**
```
Delivered real-time data platform achieving 99.95% reliability,
enabling $2M annual revenue through improved customer insights.
```

**ATS Style:**
```
Event Streaming Platform | Apache Kafka, Kubernetes, Go
- Designed and implemented distributed event streaming architecture
- Achieved 99.95% uptime SLA through Kubernetes orchestration
- Technologies: Kafka, Kubernetes, Go, distributed systems
```

### Meaning Preservation Techniques

1. **Invariant marking**: Core facts (metrics, scope) cannot change
2. **Contrastive verification**: Compare original vs transformed
3. **Exemplar grounding**: Match patterns from real resume examples

---

## 27. Embedding Models for Skill Matching

### Model Comparison

| Model | Dimensions | Accuracy | Cost | Best For |
|-------|------------|----------|------|----------|
| **OpenAI text-embedding-3-large** | 3,072 | 77.5% | High | Maximum accuracy |
| **OpenAI text-embedding-3-small** | 1,536 | 75.2% | Medium | Balance |
| **Mistral mistral-embed** | 768 | 77.8% | Medium | Best accuracy/size ratio |
| **Cohere embed-v3** | 1,024 | 76.1% | Medium | Good multilingual |
| **all-MiniLM-L6-v2** (open) | 384 | 72.4% | Free | Budget/privacy |
| **BGE-large-en-v1.5** (open) | 1,024 | 75.9% | Free | Open-source quality |

### Key Findings

- **Mistral-embed** achieves highest accuracy (77.8%) with 4x less storage than OpenAI large
- **768-1024 dimensions** optimal for resume matching (curse of dimensionality at higher)
- **Open-source models** viable for privacy-sensitive deployments
- **Multilingual**: Boomerang and Cohere outperform OpenAI on cross-language

### Implementation Architecture

```python
# Multi-embedding approach for better matching
embeddings = {
    "experience": embed(normalized_experience_text),
    "skills": embed(skill_keywords_text),
    "education": embed(education_text),
    "summary": embed(professional_summary)
}

# Weighted matching
match_score = (
    0.70 * cosine_sim(embeddings["experience"], job_experience_embed) +
    0.15 * cosine_sim(embeddings["skills"], job_skills_embed) +
    0.10 * cosine_sim(embeddings["education"], job_education_embed) +
    0.05 * cosine_sim(embeddings["summary"], job_summary_embed)
)
```

### Similarity Metrics

| Metric | Use Case | Notes |
|--------|----------|-------|
| **Cosine Similarity** | Default choice | Scale-invariant, works with normalized vectors |
| **Inner Product** | Some OpenAI models | When trained with contrastive learning |
| **Euclidean Distance** | Avoid | Poor in high dimensions |

### Hybrid Scoring

```python
final_score = (
    0.70 * semantic_similarity +  # Embedding-based
    0.30 * keyword_match_score    # Explicit skill matching
)
```

Hybrid approach catches cases where embeddings miss explicit keyword requirements.

---

## 28. MCP Server Design Patterns

### MCP Fundamentals

Model Context Protocol enables modular AI tools that LLMs can call:
- **Resources**: File-like data (resume content, job descriptions)
- **Tools**: Callable functions (rank, generate, extract)
- **Prompts**: Pre-written templates

### Resume MCP Tool Design

```python
# Core tools for resume MCP server
tools = [
    {
        "name": "list_work_units",
        "description": "Retrieve stored work units with optional filters",
        "parameters": {
            "filters": {
                "skills": ["python", "aws"],
                "date_range": {"after": "2023-01"},
                "tags": ["leadership"]
            }
        }
    },
    {
        "name": "rank_work_units",
        "description": "Rank work units by relevance to job description",
        "parameters": {
            "job_description": "string or resource_id",
            "top_k": 5,
            "weights": {"skills": 0.4, "impact": 0.3, "recency": 0.3}
        }
    },
    {
        "name": "generate_resume",
        "description": "Generate resume in specified format for audience",
        "parameters": {
            "work_unit_ids": ["wu-1", "wu-2"],
            "template": "modern-technical",
            "audience": "technical_hiring_manager",
            "format": "pdf"
        }
    },
    {
        "name": "extract_work_unit",
        "description": "Parse conversational input into structured work unit",
        "parameters": {
            "raw_text": "string",
            "context": "optional previous conversation"
        }
    },
    {
        "name": "explain_selection",
        "description": "Explain why work units were selected/excluded",
        "parameters": {
            "work_unit_ids": ["wu-1", "wu-2"],
            "job_description_id": "jd-123",
            "explanation_type": "feature_importance|counterfactual|example"
        }
    }
]
```

### Tool Granularity Guidelines

| Granularity | Example | Problem |
|-------------|---------|---------|
| **Too fine** | `set_work_unit_title`, `set_work_unit_skills` | Too many calls needed |
| **Too coarse** | `manage_everything` | No composability |
| **Just right** | `rank_work_units`, `generate_resume` | Maps to user intent |

**Principle**: One tool = one coherent user request

### Composable Tool Chains

```
User: "Create a resume for this software engineering job"

Agent workflow:
1. extract_job_requirements(job_description)
2. rank_work_units(requirements, top_k=5)
3. generate_resume(ranked_units, template="ats-safe")
4. explain_selection(ranked_units, job_description)
```

### Security Considerations

- **Role-based access**: Job seekers edit own data, recruiters read-only
- **Data redaction**: Sensitive info (salary) redacted by default
- **Audit logging**: All tool calls logged with context
- **Input validation**: Prevent prompt injection in raw text

### State Management Pattern

```yaml
# Resources manage state, tools stay stateless
resources:
  - id: current_job_description
    type: job_description
    data: {...}
  - id: selected_work_units
    type: work_unit_selection
    data: [wu-1, wu-2, wu-3]
  - id: candidate_profile
    type: profile
    data: {...}

# Tools reference resources, don't store state
tool_call:
  name: generate_resume
  params:
    work_units: "@selected_work_units"
    target_job: "@current_job_description"
```

---

## AI Integration Architecture Summary

```
┌─────────────────────────────────────────────────────────────┐
│                    USER CONVERSATION                        │
│  "I led a team that rebuilt our deployment pipeline..."     │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│              CONVERSATIONAL CAPTURE (Item 24)               │
│  Multi-phase extraction: Context → Accomplishment → Metrics │
│  Few-shot prompting, progressive complexity                 │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                 STRUCTURED WORK UNIT YAML                   │
│  Normalized, schema-validated, evidence-linked              │
└─────────────────────────────────────────────────────────────┘
                              │
         ┌────────────────────┼────────────────────┐
         ▼                    ▼                    ▼
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│ SEMANTIC MATCH  │  │ EXPLAINABLE     │  │ STYLE TRANSFER  │
│ (Item 27)       │  │ RANKING (25)    │  │ (Item 26)       │
│ Embeddings +    │  │ Feature import, │  │ Executive/Tech/ │
│ Similarity      │  │ Counterfactuals │  │ ATS adaptation  │
└─────────────────┘  └─────────────────┘  └─────────────────┘
         │                    │                    │
         └────────────────────┼────────────────────┘
                              ▼
┌─────────────────────────────────────────────────────────────┐
│              MCP SERVER TOOLS (Item 28)                     │
│  list_work_units | rank_work_units | generate_resume        │
│  extract_work_unit | explain_selection                      │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    GENERATED RESUME                         │
│  PDF/DOCX/HTML with full explainability and provenance      │
└─────────────────────────────────────────────────────────────┘
```

---

## Key Sources (Batch D)

- YAMLResume architecture: https://github.com/yamlresume/yamlresume
- Conversational form design: Sendbird AI tutorials
- Explainable AI: christophm.github.io/interpretable-ml-book/
- Embedding benchmarks: Vectara, AIMutiple research
- MCP documentation: modelcontextprotocol.io
- Prompting strategies: promptingguide.ai

---

*Batch D Complete - Continuing to Batch E...*

---

# BATCH E: Implementation Details (Items 29-46)

## Executive Summary

This final batch covers the practical implementation details for building a Resume-as-Code CLI system. The research synthesizes thirteen critical technical domains: YAML schema versioning and validation, progressive disclosure CLI patterns, BM25/TF-IDF ranking algorithms, terraform-style plan output, PDF generation pipelines, DOCX template systems, Hugo-style archetypes, incremental build systems, provenance tracking, validation tooling, import mechanisms, file watching, and HTML portfolio generation.

---

## 29. Work Unit Schema Finalization

### Schema Versioning Strategy

**Embed version directly in documents:**
```yaml
schema_version: "1.0"
id: wu-2024-03-15-pipeline
# ... rest of work unit
```

**Key Principles:**
- Schema version tracks structural changes, independent of application version
- Read-time transformation: handle multiple versions during migration periods
- Backward compatibility: maintain handlers for old formats during reads

**Migration Pattern:**
```python
def load_work_unit(path):
    data = yaml.load(path)
    version = data.get('schema_version', '1.0')

    if version == '1.0':
        data = migrate_v1_to_v2(data)

    return validate_and_return(data)
```

### JSON Schema for YAML Validation

**Best Practice:** Define schema in JSON Schema format, store data in YAML.

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://resume-as-code/work-unit.schema.json",
  "type": "object",
  "required": ["id", "context", "problem", "actions", "outputs"],
  "properties": {
    "schema_version": {"type": "string", "pattern": "^\\d+\\.\\d+$"},
    "id": {"type": "string", "pattern": "^wu-\\d{4}-\\d{2}-\\d{2}-"},
    "context": {
      "type": "object",
      "properties": {
        "domain": {"type": "string"},
        "system": {"type": "string"},
        "constraints": {"type": "array", "items": {"type": "string"}}
      }
    },
    "skills_demonstrated": {
      "type": "array",
      "items": {"type": "string"},
      "minItems": 1
    }
  }
}
```

**Validation Tooling:** Python `jsonschema` library provides comprehensive validation with detailed error paths.

---

## 30. Draft Work Unit Capture Flow

### Progressive Disclosure Principles

Progressive disclosure reduces cognitive load by revealing information step-by-step:

**Stage 1 - Essential Context:**
```
What did you work on? (system/project name)
> MSS ingestion pipeline

What was the problem or opportunity?
> Client telemetry ingestion was inconsistent and brittle
```

**Stage 2 - Actions Taken:**
```
What actions did you take? (one per line, blank to finish)
> Designed vector-based ingestion pipeline
> Implemented schema normalization
> Introduced IaC-based deployment
>
```

**Stage 3 - Results/Impact:**
```
What were the measurable outcomes?
> 40% reduction in ingestion failures, faster client onboarding
```

**Stage 4 - Conditional Details:**
```
Any skills you want to highlight? [auto-suggested: systems architecture, data engineering]
Any evidence to link? (repos, docs, etc.)
```

### State Persistence for Resumable Capture

```python
class CaptureState:
    def __init__(self, state_file="~/.resume-as-code/capture_state.json"):
        self.state_file = Path(state_file).expanduser()
        self.state = self._load() or {"step": 1, "data": {}}

    def _load(self):
        if self.state_file.exists():
            return json.loads(self.state_file.read_text())
        return None

    def save(self):
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        self.state_file.write_text(json.dumps(self.state))

    def clear(self):
        self.state_file.unlink(missing_ok=True)
```

**Draft vs Complete States:**
- Draft submissions retained for 15 minutes (configurable)
- Complete submissions trigger validation and storage
- Abandoned drafts can be recovered within retention window

---

## 31. Rank Work Units Algorithm

### BM25 Implementation

**Core Formula:**
```
Score(q,d) = Σ IDF(t) × [f(t,d) × (k1 + 1)] / [f(t,d) + k1 × (1 - b + b × |d|/avgdl)]
```

**Parameters:**
- `k1 = 1.2` - term saturation (higher = more weight to repeated terms)
- `b = 0.75` - length normalization (0 = no normalization, 1 = full)

**Python Implementation:**
```python
import math
from collections import Counter

class BM25Ranker:
    def __init__(self, work_units, k1=1.2, b=0.75):
        self.k1 = k1
        self.b = b
        self.work_units = work_units
        self.avgdl = sum(len(wu.tokens) for wu in work_units) / len(work_units)
        self.doc_freqs = self._compute_doc_freqs()
        self.N = len(work_units)

    def _compute_doc_freqs(self):
        df = Counter()
        for wu in self.work_units:
            df.update(set(wu.tokens))
        return df

    def idf(self, term):
        n = self.doc_freqs.get(term, 0)
        return math.log((self.N - n + 0.5) / (n + 0.5) + 1)

    def score(self, work_unit, query_terms):
        score = 0.0
        doc_len = len(work_unit.tokens)
        term_freqs = Counter(work_unit.tokens)

        for term in query_terms:
            tf = term_freqs.get(term, 0)
            idf = self.idf(term)
            numerator = tf * (self.k1 + 1)
            denominator = tf + self.k1 * (1 - self.b + self.b * doc_len / self.avgdl)
            score += idf * (numerator / denominator)

        return score
```

### Multi-Dimensional Scoring

Combine BM25 with semantic similarity:

```python
def combined_score(work_unit, jd, weights):
    scores = {
        'keyword': bm25_ranker.score(work_unit, jd.tokens),
        'semantic': embedding_similarity(work_unit.embedding, jd.embedding),
        'recency': recency_score(work_unit.time.ended),
        'impact': impact_score(work_unit.outcomes)
    }

    # Normalize to percentiles within corpus
    normalized = {k: percentile_rank(v, all_scores[k]) for k, v in scores.items()}

    # Weighted combination
    return sum(normalized[k] * weights[k] for k in weights)
```

**Explainability Output:**
```yaml
ranking_explanation:
  work_unit: wu-2024-03-15-pipeline
  final_score: 0.87
  components:
    keyword_match:
      score: 0.82
      matched_terms:
        - "data pipeline": {tf: 3, idf: 2.1, contribution: 0.31}
        - "infrastructure": {tf: 2, idf: 1.8, contribution: 0.22}
    semantic_similarity: 0.91
    recency_boost: 0.15
    impact_signals: ["quantified outcome", "production system"]
```

---

## 32. Resume Plan Output Format

### Terraform-Style Plan Design

```
$ resume plan --jd senior-data-engineer.txt

Resume Plan: senior-data-engineer
═══════════════════════════════════════════════════════════════════

📋 Work Units to Include (8 selected, 12 available)
───────────────────────────────────────────────────────────────────

+ wu-2024-03-15-pipeline     [INCLUDE]  Score: 0.92
  │ "MSS ingestion pipeline redesign"
  │ Match: data pipeline (0.31), infrastructure (0.22), IaC (0.18)
  │ Impact: 40% reduction in failures (quantified)

+ wu-2023-11-20-alerting     [INCLUDE]  Score: 0.87
  │ "Real-time alert correlation system"
  │ Match: streaming (0.28), data engineering (0.24)

~ wu-2023-06-10-dashboard    [REWRITE]  Score: 0.78
  │ "Executive metrics dashboard"
  │ Suggestion: Emphasize data modeling over visualization
  │ Original: "Built dashboard for executive team"
  │ Proposed: "Designed data models powering executive KPI tracking"

- wu-2022-09-05-support      [EXCLUDE]  Score: 0.34
  │ "Customer support automation"
  │ Reason: Low relevance to data engineering role

───────────────────────────────────────────────────────────────────
📊 Skills Coverage
───────────────────────────────────────────────────────────────────

  Required by JD          Your Coverage
  ─────────────────────   ─────────────────────
  Python                  ████████████████████ 95% (8 work units)
  SQL                     ████████████████░░░░ 80% (6 work units)
  Airflow                 ████████░░░░░░░░░░░░ 40% (2 work units)
  Spark                   ░░░░░░░░░░░░░░░░░░░░  0% ⚠️ GAP

───────────────────────────────────────────────────────────────────
⚠️  Warnings
───────────────────────────────────────────────────────────────────

• Missing skill: Spark (mentioned 3x in JD, no matching work units)
• Consider: Add spark-related experience or acknowledge gap in cover letter

───────────────────────────────────────────────────────────────────
Plan: 8 to include, 1 to rewrite, 3 to exclude

Run `resume apply` to generate artifacts
Run `resume plan --verbose` for detailed scoring breakdown
```

### ANSI Color Formatting

```python
class Colors:
    GREEN = '\033[32;1m'   # Bold green - additions/includes
    RED = '\033[31;1m'     # Bold red - exclusions
    YELLOW = '\033[33;1m'  # Bold yellow - warnings
    CYAN = '\033[36;1m'    # Bold cyan - modifications
    DIM = '\033[2m'        # Dim - context/explanations
    RESET = '\033[0m'

def format_inclusion(work_unit, score):
    return f"{Colors.GREEN}+ {work_unit.id:<28}{Colors.RESET} [INCLUDE]  Score: {score:.2f}"

def format_exclusion(work_unit, score, reason):
    return f"{Colors.RED}- {work_unit.id:<28}{Colors.RESET} [EXCLUDE]  Score: {score:.2f}\n" \
           f"  {Colors.DIM}│ Reason: {reason}{Colors.RESET}"
```

---

## 33. PDF Output Provider

### WeasyPrint Pipeline

**Architecture:**
```
YAML Data → Jinja2 Template → HTML+CSS → WeasyPrint → PDF
```

**Implementation:**
```python
from weasyprint import HTML, CSS
from jinja2 import Environment, FileSystemLoader

def generate_pdf(resume_data, template_name, output_path):
    # Load template
    env = Environment(loader=FileSystemLoader('templates'))
    template = env.get_template(f'{template_name}.html')

    # Render HTML
    html_content = template.render(**resume_data)

    # Generate PDF with print CSS
    html = HTML(string=html_content, base_url='templates/')
    css = CSS(filename='templates/print.css')

    html.write_pdf(output_path, stylesheets=[css])
```

### Print CSS Best Practices

```css
@page {
    size: letter;
    margin: 0.5in 0.75in;

    @bottom-center {
        content: counter(page) " of " counter(pages);
        font-size: 9pt;
        color: #666;
    }
}

/* Prevent awkward page breaks */
.work-unit {
    page-break-inside: avoid;
}

.section-header {
    page-break-after: avoid;
}

/* Print-specific styles */
@media print {
    a { text-decoration: none; color: inherit; }
    .no-print { display: none; }
}
```

### Font Embedding

```python
from weasyprint import HTML
from weasyprint.text.fonts import FontConfiguration

font_config = FontConfiguration()
css = CSS(string='''
    @font-face {
        font-family: 'Resume Font';
        src: url('fonts/Inter-Regular.woff2') format('woff2');
    }
    body { font-family: 'Resume Font', sans-serif; }
''', font_config=font_config)

html.write_pdf(output_path, stylesheets=[css], font_config=font_config)
```

---

## 34. Work Unit Archetypes

### Archetype Templates

**Incident Response Archetype:**
```yaml
# archetypes/incident.yaml
_archetype: incident
_description: "Security incident or production issue response"

context:
  domain: ""  # e.g., "cybersecurity", "production operations"
  system: ""
  constraints:
    - time-critical
    - high-stakes

problem:
  statement: ""
  severity: ""  # critical/high/medium
  blast_radius: ""  # users/systems affected

inputs:
  signals:
    - alert notification
    - # add indicators of compromise or symptoms

actions:
  - "Triaged initial report"
  - "Contained affected systems"
  - "Identified root cause"
  - "Remediated vulnerability"
  - "Documented lessons learned"

outputs:
  artifacts:
    - incident report
    - post-mortem document
    - remediation playbook

outcomes:
  impact:
    - "Mean time to resolution: X hours"
    - "Systems restored to normal operation"
```

**Greenfield Project Archetype:**
```yaml
# archetypes/greenfield.yaml
_archetype: greenfield
_description: "New system or feature built from scratch"

context:
  domain: ""
  system: ""
  constraints: []

problem:
  statement: ""
  business_driver: ""

inputs:
  signals:
    - stakeholder requirements
    - # add research/analysis inputs

actions:
  - "Gathered and analyzed requirements"
  - "Designed system architecture"
  - "Implemented core functionality"
  - "Deployed to production"

skills_demonstrated: []

outputs:
  artifacts:
    - design document
    - deployed system
    - documentation

outcomes:
  impact: []
```

### Scaffolding CLI

```python
@click.command()
@click.argument('archetype')
@click.option('--id', default=None, help='Work unit ID (auto-generated if not provided)')
def new(archetype, id):
    """Create a new work unit from an archetype."""
    archetype_path = Path(f'archetypes/{archetype}.yaml')

    if not archetype_path.exists():
        available = [p.stem for p in Path('archetypes').glob('*.yaml')]
        click.echo(f"Unknown archetype '{archetype}'. Available: {', '.join(available)}")
        return

    template = yaml.safe_load(archetype_path.read_text())

    # Generate ID if not provided
    if id is None:
        id = f"wu-{date.today().isoformat()}-{archetype}-{uuid4().hex[:6]}"

    template['id'] = id
    template.pop('_archetype', None)
    template.pop('_description', None)

    output_path = Path(f'work-units/{id}.yaml')
    output_path.write_text(yaml.dump(template, default_flow_style=False))

    click.echo(f"Created: {output_path}")
```

---

## 35. Resume Build Pipeline

### Incremental Build Architecture

```python
from pathlib import Path
import hashlib
import json

class BuildCache:
    def __init__(self, cache_dir='.resume-cache'):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        self.manifest_path = self.cache_dir / 'manifest.json'
        self.manifest = self._load_manifest()

    def _load_manifest(self):
        if self.manifest_path.exists():
            return json.loads(self.manifest_path.read_text())
        return {}

    def _hash_file(self, path):
        return hashlib.sha256(Path(path).read_bytes()).hexdigest()

    def is_stale(self, input_paths, output_path):
        """Check if output needs rebuilding based on input changes."""
        output_key = str(output_path)

        if output_key not in self.manifest:
            return True

        cached = self.manifest[output_key]

        # Check if output exists
        if not Path(output_path).exists():
            return True

        # Check if any input changed
        for input_path in input_paths:
            current_hash = self._hash_file(input_path)
            if cached.get('inputs', {}).get(str(input_path)) != current_hash:
                return True

        return False

    def record_build(self, input_paths, output_path):
        """Record successful build for future cache checks."""
        self.manifest[str(output_path)] = {
            'inputs': {str(p): self._hash_file(p) for p in input_paths},
            'built_at': datetime.now().isoformat()
        }
        self.manifest_path.write_text(json.dumps(self.manifest, indent=2))
```

### Parallel Generation

```python
from concurrent.futures import ThreadPoolExecutor

def build_all(jd_path, formats=['pdf', 'docx', 'html']):
    # Sequential: load and rank (shared dependency)
    work_units = load_work_units()
    jd = load_jd(jd_path)
    selected = rank_and_select(work_units, jd)

    # Parallel: generate each format independently
    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = {
            executor.submit(generate_pdf, selected, jd): 'pdf',
            executor.submit(generate_docx, selected, jd): 'docx',
            executor.submit(generate_html, selected, jd): 'html',
        }

        for future in as_completed(futures):
            format_name = futures[future]
            try:
                output_path = future.result()
                click.echo(f"Generated: {output_path}")
            except Exception as e:
                click.echo(f"Failed to generate {format_name}: {e}", err=True)
```

---

## 36. ATS-Safe Provider

### ATS Optimization Constraints

**Key ATS Behaviors:**
- Single-column layouts parse most reliably
- Tables, columns, and text boxes often break parsing
- Standard section headers improve field mapping
- Keyword density matters for ranking

**ATS-Safe Template:**
```html
<!-- ats-safe.html -->
<html>
<head>
    <style>
        body {
            font-family: Arial, sans-serif;  /* System fonts only */
            font-size: 11pt;
            line-height: 1.4;
            max-width: 7.5in;
            margin: 0 auto;
        }
        h1 { font-size: 16pt; margin-bottom: 4pt; }
        h2 { font-size: 12pt; border-bottom: 1pt solid #000; }
        .contact { font-size: 10pt; }
        ul { margin: 6pt 0; padding-left: 18pt; }
    </style>
</head>
<body>
    <h1>{{ name }}</h1>
    <p class="contact">{{ email }} | {{ phone }} | {{ location }}</p>

    <h2>Professional Summary</h2>
    <p>{{ summary }}</p>

    <h2>Skills</h2>
    <p>{{ skills | join(', ') }}</p>

    <h2>Professional Experience</h2>
    {% for job in experience %}
    <p><strong>{{ job.title }}</strong> | {{ job.company }} | {{ job.dates }}</p>
    <ul>
        {% for bullet in job.bullets %}
        <li>{{ bullet }}</li>
        {% endfor %}
    </ul>
    {% endfor %}

    <h2>Education</h2>
    {% for edu in education %}
    <p><strong>{{ edu.degree }}</strong> | {{ edu.school }} | {{ edu.year }}</p>
    {% endfor %}
</body>
</html>
```

### Keyword Optimization

```python
def optimize_for_ats(work_units, jd):
    """Ensure JD keywords appear in resume output."""
    jd_keywords = extract_keywords(jd)
    resume_keywords = set()

    for wu in work_units:
        resume_keywords.update(extract_keywords(wu))

    missing = jd_keywords - resume_keywords

    if missing:
        return {
            'status': 'warning',
            'missing_keywords': list(missing),
            'suggestion': 'Consider incorporating these terms where authentic'
        }

    return {'status': 'ok', 'keyword_coverage': len(jd_keywords & resume_keywords) / len(jd_keywords)}
```

---

## 37. Submission Provenance Schema

### Lightweight Tracking Without CRM

```yaml
# submissions/2024-03-15-acme-sre.yaml
id: sub-2024-03-15-acme
submitted_at: 2024-03-15T10:30:00Z
target:
  company: Acme Corp
  role: Senior SRE
  job_id: "JD-12345"  # optional
  source: linkedin  # where you found it

artifacts:
  resume:
    path: generated/acme-sre-resume.pdf
    sha256: "abc123..."
    work_units_included:
      - wu-2024-03-15-pipeline
      - wu-2023-11-20-alerting
      - wu-2023-06-10-dashboard
  cover_letter:
    path: generated/acme-sre-cover.pdf
    sha256: "def456..."

plan_snapshot:
  jd_hash: "789xyz..."
  scoring_weights:
    keyword: 0.4
    semantic: 0.4
    recency: 0.2

status: submitted  # submitted | interviewing | rejected | offer
notes: |
  Applied through company portal. Referral from Jane Doe.

timeline:
  - date: 2024-03-15
    event: submitted
  - date: 2024-03-22
    event: recruiter_screen
    notes: "30 min call, discussed team structure"
```

### Git-Based Lineage

```bash
# Every resume generation auto-commits
git add work-units/ generated/ submissions/
git commit -m "Generated resume for Acme Corp SRE position

Work units: wu-2024-03-15-pipeline, wu-2023-11-20-alerting
JD hash: 789xyz
Template: modern-tech"
```

**Query examples:**
```bash
# When did I add Python skill?
git log --all -p -- 'work-units/*.yaml' | grep -B5 "Python"

# What resume did I send to Acme?
git log --oneline -- 'submissions/*acme*'

# Compare current skills to 6 months ago
git diff HEAD~100 -- 'work-units/' | grep skills_demonstrated
```

---

## 38. Archetype Scaffolding CLI

### Full CLI Implementation

```python
import click
from pathlib import Path
from datetime import date
import yaml

@click.group()
def cli():
    """Resume-as-Code CLI"""
    pass

@cli.command()
@click.argument('archetype', required=False)
@click.option('--list', 'list_archetypes', is_flag=True, help='List available archetypes')
def new(archetype, list_archetypes):
    """Create a new work unit from an archetype."""
    archetypes_dir = Path('archetypes')

    if list_archetypes or archetype is None:
        click.echo("Available archetypes:")
        for path in sorted(archetypes_dir.glob('*.yaml')):
            meta = yaml.safe_load(path.read_text())
            desc = meta.get('_description', 'No description')
            click.echo(f"  {path.stem:<20} {desc}")
        return

    archetype_path = archetypes_dir / f'{archetype}.yaml'
    if not archetype_path.exists():
        click.echo(f"Unknown archetype: {archetype}", err=True)
        raise SystemExit(1)

    # Interactive capture
    click.echo(f"\nCreating new {archetype} work unit\n")

    template = yaml.safe_load(archetype_path.read_text())

    # Generate ID
    short_desc = click.prompt("Brief description (for filename)", type=str)
    slug = short_desc.lower().replace(' ', '-')[:30]
    work_unit_id = f"wu-{date.today().isoformat()}-{slug}"

    template['id'] = work_unit_id
    template.pop('_archetype', None)
    template.pop('_description', None)

    output_path = Path(f'work-units/{work_unit_id}.yaml')
    output_path.parent.mkdir(exist_ok=True)
    output_path.write_text(yaml.dump(template, default_flow_style=False, sort_keys=False))

    click.echo(f"\nCreated: {output_path}")
    click.echo(f"Edit this file to fill in your work unit details.")

if __name__ == '__main__':
    cli()
```

---

## 39. Validate Work Unit Linting

### Schema + Custom Rules

```python
import jsonschema
from pathlib import Path
import yaml

class WorkUnitValidator:
    def __init__(self, schema_path='schemas/work-unit.schema.json'):
        self.schema = json.loads(Path(schema_path).read_text())
        self.custom_rules = [
            self.check_id_format,
            self.check_date_consistency,
            self.check_outcome_quality,
            self.check_skill_taxonomy,
        ]

    def validate(self, work_unit_path):
        data = yaml.safe_load(Path(work_unit_path).read_text())
        errors = []
        warnings = []

        # JSON Schema validation
        validator = jsonschema.Draft202012Validator(self.schema)
        for error in validator.iter_errors(data):
            errors.append({
                'type': 'schema',
                'path': '/'.join(str(p) for p in error.path),
                'message': error.message
            })

        # Custom rule validation
        for rule in self.custom_rules:
            rule_errors, rule_warnings = rule(data)
            errors.extend(rule_errors)
            warnings.extend(rule_warnings)

        return {'valid': len(errors) == 0, 'errors': errors, 'warnings': warnings}

    def check_outcome_quality(self, data):
        """Warn if outcomes lack quantification."""
        errors, warnings = [], []

        outcomes = data.get('outcomes', {}).get('impact', [])
        quantified = sum(1 for o in outcomes if any(c.isdigit() for c in o))

        if outcomes and quantified == 0:
            warnings.append({
                'type': 'quality',
                'path': 'outcomes/impact',
                'message': 'No quantified outcomes. Consider adding metrics (%, time saved, etc.)'
            })

        return errors, warnings

    def check_skill_taxonomy(self, data):
        """Validate skills against known taxonomy."""
        errors, warnings = [], []
        known_skills = self.load_skill_taxonomy()

        for skill in data.get('skills_demonstrated', []):
            if skill.lower() not in known_skills:
                warnings.append({
                    'type': 'taxonomy',
                    'path': 'skills_demonstrated',
                    'message': f"Unknown skill '{skill}'. Consider using standard name or adding to taxonomy."
                })

        return errors, warnings
```

### CLI Integration

```python
@cli.command()
@click.argument('paths', nargs=-1, type=click.Path(exists=True))
@click.option('--fix', is_flag=True, help='Auto-fix simple issues')
def validate(paths, fix):
    """Validate work unit files."""
    if not paths:
        paths = list(Path('work-units').glob('*.yaml'))

    validator = WorkUnitValidator()
    all_valid = True

    for path in paths:
        result = validator.validate(path)

        if result['errors']:
            all_valid = False
            click.echo(f"\n{Colors.RED}✗ {path}{Colors.RESET}")
            for err in result['errors']:
                click.echo(f"  ERROR [{err['path']}]: {err['message']}")

        if result['warnings']:
            click.echo(f"\n{Colors.YELLOW}⚠ {path}{Colors.RESET}")
            for warn in result['warnings']:
                click.echo(f"  WARN [{warn['path']}]: {warn['message']}")

        if result['valid'] and not result['warnings']:
            click.echo(f"{Colors.GREEN}✓ {path}{Colors.RESET}")

    raise SystemExit(0 if all_valid else 1)
```

---

## 40. DOCX Output Provider

### Template-Based Generation

```python
from docxtpl import DocxTemplate, RichText

def generate_docx(resume_data, template_path, output_path):
    doc = DocxTemplate(template_path)

    # Prepare context with rich text formatting
    context = {
        'name': resume_data['name'],
        'title': resume_data['title'],
        'contact': f"{resume_data['email']} | {resume_data['phone']}",
        'summary': resume_data.get('summary', ''),
        'experience': [],
        'skills': ', '.join(resume_data.get('skills', [])),
    }

    # Format experience entries
    for job in resume_data.get('experience', []):
        bullets = []
        for bullet in job.get('bullets', []):
            rt = RichText()
            # Bold action verbs
            if ' ' in bullet:
                verb, rest = bullet.split(' ', 1)
                rt.add(verb, bold=True)
                rt.add(' ' + rest)
            else:
                rt.add(bullet)
            bullets.append(rt)

        context['experience'].append({
            'title': job['title'],
            'company': job['company'],
            'dates': f"{job['start']} - {job.get('end', 'Present')}",
            'bullets': bullets
        })

    doc.render(context)
    doc.save(output_path)

    return output_path
```

### Word Template Design

In the Word template file (`templates/resume.docx`):

```
{{ name }}
{{ title }}
{{ contact }}

PROFESSIONAL SUMMARY
{{ summary }}

SKILLS
{{ skills }}

PROFESSIONAL EXPERIENCE
{%tr for job in experience %}
{{ job.title }} | {{ job.company }} | {{ job.dates }}
{%tr for bullet in job.bullets %}
• {{ bullet }}
{%tr endfor %}
{%tr endfor %}
```

---

## 41. JSON Resume Export

### Lossy Projection

```python
def export_json_resume(work_units, metadata):
    """Export to JSON Resume format (lossy - loses causality, constraints, evidence)."""

    # Group work units by employer
    by_employer = defaultdict(list)
    for wu in work_units:
        employer = wu.get('context', {}).get('employer', 'Independent')
        by_employer[employer].append(wu)

    json_resume = {
        "basics": {
            "name": metadata['name'],
            "label": metadata.get('title', ''),
            "email": metadata.get('email', ''),
            "phone": metadata.get('phone', ''),
            "summary": metadata.get('summary', ''),
        },
        "work": [],
        "skills": [],
    }

    # Convert work units to work entries
    for employer, units in by_employer.items():
        # Find date range
        start_dates = [wu['time']['started'] for wu in units if wu.get('time', {}).get('started')]
        end_dates = [wu['time']['ended'] for wu in units if wu.get('time', {}).get('ended')]

        highlights = []
        for wu in units:
            # Flatten to bullet points (loses structure)
            problem = wu.get('problem', {}).get('statement', '')
            outcomes = wu.get('outcomes', {}).get('impact', [])
            if problem and outcomes:
                highlights.append(f"{problem} - {outcomes[0]}")

        json_resume['work'].append({
            "company": employer,
            "position": units[0].get('context', {}).get('role', 'Contributor'),
            "startDate": min(start_dates) if start_dates else '',
            "endDate": max(end_dates) if end_dates else '',
            "highlights": highlights
        })

    # Aggregate skills
    all_skills = set()
    for wu in work_units:
        all_skills.update(wu.get('skills_demonstrated', []))

    # Group by category (simplified)
    json_resume['skills'] = [
        {"name": "Technical Skills", "keywords": list(all_skills)}
    ]

    return json_resume
```

---

## 42. LinkedIn Import

### Parsing LinkedIn Export

```python
import csv
from pathlib import Path
from datetime import datetime

def import_linkedin_positions(csv_path):
    """Import from LinkedIn data export (Settings > Get a copy of your data)."""

    positions = []
    confidence_notes = []

    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            position = {
                'context': {
                    'employer': row.get('Company Name', ''),
                    'role': row.get('Title', ''),
                    'domain': '',  # Not available - LOW CONFIDENCE
                },
                'time': {
                    'started': parse_linkedin_date(row.get('Started On', '')),
                    'ended': parse_linkedin_date(row.get('Finished On', '')) or None,
                },
                'problem': {
                    'statement': '',  # Not available - needs manual entry
                },
                'actions': [],  # Not available - needs manual entry
                'outputs': {'artifacts': []},
                'outcomes': {'impact': []},  # Not available - needs manual entry
                'skills_demonstrated': [],
                '_import_metadata': {
                    'source': 'linkedin',
                    'imported_at': datetime.now().isoformat(),
                    'confidence': 'low',
                    'missing_fields': ['domain', 'problem', 'actions', 'outcomes', 'skills'],
                }
            }

            # Add description if available
            if row.get('Description'):
                position['_raw_description'] = row['Description']
                position['_import_metadata']['has_description'] = True

            positions.append(position)

    return {
        'positions': positions,
        'import_summary': {
            'total': len(positions),
            'needs_enrichment': len(positions),  # All need manual work
            'confidence': 'low',
            'recommendation': 'Review each position and add problem/action/outcome details'
        }
    }

def parse_linkedin_date(date_str):
    """Parse LinkedIn date format (e.g., 'Jan 2020')."""
    if not date_str:
        return None
    try:
        return datetime.strptime(date_str, '%b %Y').strftime('%Y-%m')
    except ValueError:
        return date_str
```

---

## 43. Semantic Search with Embeddings

### Embedding-Based Search

```python
from sentence_transformers import SentenceTransformer
import numpy as np
from pathlib import Path
import pickle

class SemanticSearch:
    def __init__(self, model_name='all-MiniLM-L6-v2'):
        self.model = SentenceTransformer(model_name)
        self.index_path = Path('.resume-cache/embeddings.pkl')
        self.embeddings = {}
        self._load_index()

    def _load_index(self):
        if self.index_path.exists():
            self.embeddings = pickle.loads(self.index_path.read_bytes())

    def _save_index(self):
        self.index_path.parent.mkdir(exist_ok=True)
        self.index_path.write_bytes(pickle.dumps(self.embeddings))

    def index_work_unit(self, work_unit):
        """Create embedding for a work unit."""
        # Concatenate searchable text
        text_parts = [
            work_unit.get('problem', {}).get('statement', ''),
            ' '.join(work_unit.get('actions', [])),
            ' '.join(work_unit.get('outcomes', {}).get('impact', [])),
            ' '.join(work_unit.get('skills_demonstrated', [])),
        ]
        text = ' '.join(filter(None, text_parts))

        embedding = self.model.encode(text)
        self.embeddings[work_unit['id']] = {
            'embedding': embedding,
            'text': text
        }
        self._save_index()

    def search(self, query, top_k=5):
        """Find work units most similar to query."""
        query_embedding = self.model.encode(query)

        results = []
        for wu_id, data in self.embeddings.items():
            similarity = np.dot(query_embedding, data['embedding']) / (
                np.linalg.norm(query_embedding) * np.linalg.norm(data['embedding'])
            )
            results.append((wu_id, similarity))

        results.sort(key=lambda x: x[1], reverse=True)
        return results[:top_k]
```

---

## 44. Gap Analysis

### Skill Gap Detection

```python
def analyze_gaps(work_units, target_role_requirements):
    """Identify skill gaps between current work units and target role."""

    # Extract demonstrated skills
    demonstrated = set()
    skill_evidence = defaultdict(list)

    for wu in work_units:
        for skill in wu.get('skills_demonstrated', []):
            demonstrated.add(skill.lower())
            skill_evidence[skill.lower()].append({
                'work_unit': wu['id'],
                'context': wu.get('context', {}).get('system', ''),
                'recency': wu.get('time', {}).get('ended', '')
            })

    # Compare to requirements
    required = set(s.lower() for s in target_role_requirements.get('required_skills', []))
    preferred = set(s.lower() for s in target_role_requirements.get('preferred_skills', []))

    analysis = {
        'coverage': {
            'required': {
                'met': list(required & demonstrated),
                'missing': list(required - demonstrated),
                'coverage_pct': len(required & demonstrated) / len(required) * 100 if required else 100
            },
            'preferred': {
                'met': list(preferred & demonstrated),
                'missing': list(preferred - demonstrated),
                'coverage_pct': len(preferred & demonstrated) / len(preferred) * 100 if preferred else 100
            }
        },
        'evidence': {skill: skill_evidence[skill] for skill in demonstrated},
        'recommendations': []
    }

    # Generate recommendations
    for skill in analysis['coverage']['required']['missing']:
        analysis['recommendations'].append({
            'priority': 'high',
            'skill': skill,
            'suggestion': f"Critical gap: '{skill}' is required but not demonstrated in any work unit"
        })

    for skill in analysis['coverage']['preferred']['missing']:
        analysis['recommendations'].append({
            'priority': 'medium',
            'skill': skill,
            'suggestion': f"Nice-to-have: '{skill}' would strengthen your application"
        })

    return analysis
```

---

## 45. Watch Mode for Live Preview

### File Watching Implementation

```python
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import threading
import time
import webbrowser

class ResumeWatcher(FileSystemEventHandler):
    def __init__(self, rebuild_callback, debounce_seconds=1.0):
        self.rebuild_callback = rebuild_callback
        self.debounce_seconds = debounce_seconds
        self.timer = None
        self.lock = threading.Lock()

    def on_modified(self, event):
        if event.is_directory:
            return

        # Only watch relevant files
        if not event.src_path.endswith(('.yaml', '.yml', '.html', '.css')):
            return

        with self.lock:
            if self.timer:
                self.timer.cancel()
            self.timer = threading.Timer(
                self.debounce_seconds,
                self._trigger_rebuild,
                args=[event.src_path]
            )
            self.timer.start()

    def _trigger_rebuild(self, changed_path):
        click.echo(f"\n{Colors.CYAN}Changed: {changed_path}{Colors.RESET}")
        try:
            self.rebuild_callback()
            click.echo(f"{Colors.GREEN}Rebuilt successfully{Colors.RESET}")
        except Exception as e:
            click.echo(f"{Colors.RED}Build failed: {e}{Colors.RESET}")

@cli.command()
@click.option('--jd', required=True, type=click.Path(exists=True))
@click.option('--format', 'output_format', default='html', type=click.Choice(['html', 'pdf']))
@click.option('--open/--no-open', default=True, help='Open in browser')
def watch(jd, output_format, open):
    """Watch for changes and rebuild automatically."""

    output_path = Path(f'generated/preview.{output_format}')

    def rebuild():
        work_units = load_work_units()
        jd_data = load_jd(jd)
        selected = rank_and_select(work_units, jd_data)

        if output_format == 'html':
            generate_html(selected, jd_data, output_path)
        else:
            generate_pdf(selected, jd_data, output_path)

    # Initial build
    rebuild()

    if open and output_format == 'html':
        webbrowser.open(f'file://{output_path.absolute()}')

    # Set up watcher
    handler = ResumeWatcher(rebuild)
    observer = Observer()
    observer.schedule(handler, 'work-units/', recursive=True)
    observer.schedule(handler, 'templates/', recursive=True)
    observer.start()

    click.echo(f"\nWatching for changes... (Ctrl+C to stop)")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
```

---

## 46. HTML Portfolio Provider

### Static Portfolio Generation

```html
<!-- templates/portfolio.html -->
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ name }} - Portfolio</title>
    <meta name="description" content="{{ summary | truncate(160) }}">

    <!-- Open Graph -->
    <meta property="og:title" content="{{ name }} - {{ title }}">
    <meta property="og:description" content="{{ summary | truncate(200) }}">
    <meta property="og:type" content="profile">

    <style>
        :root {
            --primary: #2563eb;
            --text: #1f2937;
            --muted: #6b7280;
            --bg: #ffffff;
            --card-bg: #f9fafb;
        }

        @media (prefers-color-scheme: dark) {
            :root {
                --primary: #60a5fa;
                --text: #f9fafb;
                --muted: #9ca3af;
                --bg: #111827;
                --card-bg: #1f2937;
            }
        }

        * { box-sizing: border-box; }

        body {
            font-family: system-ui, -apple-system, sans-serif;
            line-height: 1.6;
            color: var(--text);
            background: var(--bg);
            max-width: 800px;
            margin: 0 auto;
            padding: 2rem;
        }

        .work-unit {
            background: var(--card-bg);
            border-radius: 8px;
            padding: 1.5rem;
            margin: 1rem 0;
        }

        .skills {
            display: flex;
            flex-wrap: wrap;
            gap: 0.5rem;
        }

        .skill-tag {
            background: var(--primary);
            color: white;
            padding: 0.25rem 0.75rem;
            border-radius: 999px;
            font-size: 0.875rem;
        }

        @media print {
            body { max-width: 100%; }
            .work-unit { break-inside: avoid; }
        }
    </style>
</head>
<body>
    <header>
        <h1>{{ name }}</h1>
        <p class="title">{{ title }}</p>
        <p class="contact">{{ email }} {% if website %}| <a href="{{ website }}">{{ website }}</a>{% endif %}</p>
    </header>

    <section id="summary">
        <h2>About</h2>
        <p>{{ summary }}</p>
    </section>

    <section id="skills">
        <h2>Skills</h2>
        <div class="skills">
            {% for skill in skills %}
            <span class="skill-tag">{{ skill }}</span>
            {% endfor %}
        </div>
    </section>

    <section id="work">
        <h2>Selected Work</h2>
        {% for wu in work_units %}
        <article class="work-unit">
            <h3>{{ wu.context.system }}</h3>
            <p class="problem">{{ wu.problem.statement }}</p>
            <ul class="outcomes">
                {% for outcome in wu.outcomes.impact %}
                <li>{{ outcome }}</li>
                {% endfor %}
            </ul>
            <div class="skills">
                {% for skill in wu.skills_demonstrated %}
                <span class="skill-tag">{{ skill }}</span>
                {% endfor %}
            </div>
        </article>
        {% endfor %}
    </section>

    <footer>
        <p>Generated with Resume-as-Code</p>
    </footer>
</body>
</html>
```

### Accessibility Compliance

```python
def validate_accessibility(html_path):
    """Basic WCAG checks for generated HTML."""
    from bs4 import BeautifulSoup

    soup = BeautifulSoup(Path(html_path).read_text(), 'html.parser')
    issues = []

    # Check images have alt text
    for img in soup.find_all('img'):
        if not img.get('alt'):
            issues.append(f"Image missing alt text: {img.get('src', 'unknown')}")

    # Check heading hierarchy
    headings = soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
    prev_level = 0
    for h in headings:
        level = int(h.name[1])
        if level > prev_level + 1:
            issues.append(f"Heading jump from h{prev_level} to {h.name}: '{h.text[:30]}'")
        prev_level = level

    # Check for lang attribute
    html_tag = soup.find('html')
    if not html_tag or not html_tag.get('lang'):
        issues.append("Missing lang attribute on <html>")

    # Check color contrast (simplified)
    # Full implementation would use actual color contrast calculations

    return {
        'valid': len(issues) == 0,
        'issues': issues,
        'checks_performed': ['alt_text', 'heading_hierarchy', 'lang_attribute']
    }
```

---

## Implementation Synthesis

### Complete CLI Architecture

```
resume-as-code/
├── work-units/               # YAML work unit files
│   └── wu-2024-03-15-*.yaml
├── archetypes/               # Templates for new work units
│   ├── incident.yaml
│   ├── greenfield.yaml
│   └── leadership.yaml
├── templates/                # Output templates
│   ├── modern.html
│   ├── ats-safe.html
│   ├── resume.docx
│   └── portfolio.html
├── schemas/                  # Validation schemas
│   └── work-unit.schema.json
├── generated/                # Output artifacts
├── submissions/              # Provenance tracking
├── .resume-cache/            # Build cache + embeddings
└── resume.py                 # CLI entry point
```

### Recommended Implementation Order

1. **Foundation (Week 1-2)**
   - Work Unit YAML schema with JSON Schema validation
   - Basic CLI with `new`, `validate`, `list` commands
   - File-based storage with ID generation

2. **Core Generation (Week 3-4)**
   - BM25 ranking implementation
   - `plan` command with terraform-style output
   - WeasyPrint PDF generation
   - Basic HTML template

3. **Polish & Features (Week 5-6)**
   - DOCX generation with python-docx
   - Watch mode for live preview
   - ATS-safe template variant
   - Submission provenance tracking

4. **Advanced (Future)**
   - Semantic search with embeddings
   - LinkedIn import
   - Gap analysis
   - Portfolio site generation

---

## Key Sources (Batch E)

- Schema versioning: docs.suews.io, milvus.io
- JSON Schema: json-schema.org/learn/getting-started-step-by-step
- Progressive disclosure: dev.to/lollypopdesign, justinmind.com
- BM25: geeksforgeeks.org, kmwllc.com
- Terraform plan: atmos.tools/cli/commands
- ANSI colors: codequoi.com
- WeasyPrint vs Puppeteer: stackshare.io, nutrient.io
- python-docx: docxtpl.readthedocs.io
- Watchdog: pypi.org/project/watchdog
- Data lineage: atlan.com, secoda.co
- JSON validation: python-jsonschema.readthedocs.io
- Accessibility: WCAG guidelines

---

*Batch E Complete - All research batches finished.*

---

# FINAL RESEARCH SYNTHESIS

## Executive Summary

This comprehensive research document covers 46 research items across 5 batches, providing the technical foundation for building a Resume-as-Code system. The research validates the brainstorming session's core thesis: **traditional resume tools help you sound impressive; this system helps you prove value—then decide how to present it.**

## Key Architectural Decisions Validated

| Decision | Research Finding | Confidence |
|----------|------------------|------------|
| **YAML over JSON** | YAML 40% more readable, supports comments, better for human editing | High |
| **Work Unit as Core Atom** | PAR (Problem-Action-Result) structure proven in industry | High |
| **BM25 + Semantic Hybrid Ranking** | Combines keyword precision with conceptual matching | High |
| **WeasyPrint for PDF** | Pure Python, no browser overhead, good CSS support | High |
| **Terraform-style `plan` Command** | Unique differentiator, no existing tool offers this | High |
| **MCP Server Architecture** | Composable, well-documented protocol for AI tool integration | High |

## Critical Implementation Insights

### Schema Design
- Embed `schema_version` in documents for migration support
- Use JSON Schema for validation, YAML for storage
- Include `_import_metadata` for confidence tracking on imported data

### Ranking Algorithm
- BM25 with k1=1.2, b=0.75 as baseline parameters
- Combine with semantic embeddings (all-MiniLM-L6-v2 recommended for speed)
- Always provide explainability output showing why selections were made

### PDF Generation Pipeline
```
YAML → Jinja2 Template → HTML+CSS → WeasyPrint → PDF
```

### ATS Optimization
- 97.8% of Fortune 500 use ATS systems
- Single-column layouts parse most reliably
- Standard section headers improve field mapping
- Keyword optimization is critical for ranking

## Recommended MVP Scope

**Phase 1 - Foundation:**
1. Work Unit YAML schema with JSON Schema validation
2. Basic CLI (`new`, `validate`, `list` commands)
3. File-per-unit storage with naming convention

**Phase 2 - Core:**
4. BM25 ranking implementation
5. `plan` command with terraform-style output
6. WeasyPrint PDF generation
7. Basic HTML template

**Phase 3 - Polish:**
8. DOCX generation with python-docx
9. Watch mode for live preview
10. ATS-safe template variant
11. Submission provenance tracking

## Differentiation from Existing Tools

| Feature | JSON Resume | Reactive Resume | Resume-as-Code |
|---------|-------------|-----------------|----------------|
| **Core Atom** | Job | Job | Work Unit |
| **Selection Logic** | None | Manual | AI-powered with explanation |
| **Plan Preview** | None | None | Terraform-style diff |
| **Provenance** | None | None | Git-based lineage |
| **Tailoring** | Manual | Manual | JD-driven ranking |

## Risk Mitigation

| Risk | Mitigation |
|------|------------|
| Capture friction | Progressive disclosure, archetypes, draft persistence |
| AI "hallucination" | Explanations as first-class output, manifest for every generation |
| ATS parsing failures | Dedicated ATS-safe provider, keyword coverage warnings |
| Scope creep | Clear MVP boundaries, "future" designations |

---

## Research Complete

**Total Items Researched:** 46
**Research Depth:** Comprehensive with source citations
**Ready for:** Product Brief and PRD development

---

*Research conducted using Perplexity Deep Research*
*Generated: 2026-01-09*
