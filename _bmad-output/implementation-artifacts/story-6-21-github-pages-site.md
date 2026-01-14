# Story 6.21: GitHub Pages Marketing Site (Docusaurus)

## Story Info

- **Epic**: Epic 6 - Executive Resume Template & Profile System
- **Status**: review
- **Priority**: Medium
- **Estimation**: Large (5-8 story points)
- **Dependencies**: Story 6.19 (Philosophy Documentation) - content source

## User Story

As a **potential user discovering Resume as Code**,
I want **a polished marketing website that showcases the tool's capabilities**,
So that **I can understand its value, see it in action, and decide to adopt it**.

## Background

### Why a Dedicated Site?

A GitHub README is limited:
- No rich interactivity
- Limited visual design options
- Can't demonstrate the tool in action
- Doesn't convey professionalism for a "production-ready" tool

A Docusaurus site provides:
- Professional marketing presence
- Interactive demos and live examples
- Searchable documentation
- Mobile-responsive design
- Easy maintenance (markdown + React)

### Technology Choice: Docusaurus

| Feature | Benefit |
|---------|---------|
| React-based | Rich interactivity for demos |
| Markdown support | Easy content authoring |
| Built-in search | Algolia DocSearch integration |
| Versioning | Future-proof for releases |
| GitHub Pages ready | Simple deployment |
| Active community | Well-maintained, good docs |

## Acceptance Criteria

### AC1: Site Structure
**Given** the Docusaurus site is deployed
**When** a user visits the site
**Then** they see this navigation structure:
```
Home (Hero + Marketing)
├── Features
├── Philosophy
├── Demo (Interactive)
├── Docs/
│   ├── Getting Started
│   ├── Commands
│   ├── Data Model
│   ├── Configuration
│   └── API Reference
├── Examples
├── Blog (placeholder)
└── GitHub (external link)
```

### AC2: Hero Section
**Given** a user lands on the homepage
**When** the page loads
**Then** they see:
- Tagline: "Treat your career data as structured, queryable truth"
- Subheadline: Brief value proposition (2 sentences)
- Primary CTA: "Get Started" → Getting Started docs
- Secondary CTA: "View on GitHub" → Repository
- Hero visual: Animated diagram or screenshot

### AC3: Features Section
**Given** the Features section
**When** viewed
**Then** it showcases 6-8 key features with:
- Icon or illustration for each
- Feature title
- 2-3 sentence description
- Optional: "Learn more" link to relevant docs

Features to highlight:
1. **Work Unit Capture** - Structured accomplishment storage
2. **Smart Ranking** - BM25 + semantic matching for JD targeting
3. **Gap Analysis** - See what skills are covered/missing
4. **Multiple Formats** - PDF, DOCX with provenance
5. **Executive Templates** - Professional resume designs
6. **Git-Native** - Version control your career
7. **AI-Ready** - Structured data for LLM assistance
8. **Extensible** - Plugin architecture for customization

### AC4: Philosophy Section
**Given** the Philosophy page
**When** viewed
**Then** it explains:
- The "resumes as queries" mental model
- Work Units as atomic truth
- Separation of data, selection, presentation
- Embedded Excalidraw diagrams (from Story 6.19)
- Comparison: Traditional vs Resume as Code approach

### AC5: Interactive Demo
**Given** the Demo page
**When** a user interacts with it
**Then** they can:

**Demo 1: Work Unit Builder (Live)**
- Form to create a sample Work Unit
- Real-time YAML preview
- Validation feedback
- "Copy YAML" button

**Demo 2: Plan Simulator**
- Sample JD text input
- Sample Work Units (pre-loaded)
- "Run Plan" button
- Display ranked results with scores
- Show skill coverage analysis

**Demo 3: Output Preview**
- Toggle between PDF/DOCX preview
- Show how Work Units render to resume bullets
- Template selector (modern, executive, ATS-safe)

### AC6: Documentation Integration
**Given** the Docs section
**When** navigating
**Then** users find:
- Getting Started guide (from README)
- Command Reference (detailed CLI docs)
- Data Model (schemas, relationships)
- Configuration (all options documented)
- Searchable via Algolia (or local search)

### AC7: Code Examples
**Given** the Examples page
**When** viewed
**Then** it shows:
- Runnable code snippets with syntax highlighting
- Copy-to-clipboard functionality
- Multiple scenarios (incident response, greenfield, leadership)
- Expected output for each example

### AC8: Mobile Responsive
**Given** a user visits on mobile
**When** browsing the site
**Then**:
- Navigation collapses to hamburger menu
- Content is readable without horizontal scroll
- Interactive demos work on touch devices
- Images scale appropriately

### AC9: GitHub Pages Deployment
**Given** the site is ready
**When** deployed
**Then**:
- Accessible at `https://[username].github.io/resume-as-code/`
- Automated deployment via GitHub Actions
- Build passes on PR (preview deployments optional)

### AC10: SEO & Meta
**Given** the site is indexed
**When** searched
**Then**:
- Proper meta tags (title, description, og:image)
- Sitemap generated
- robots.txt configured
- Social sharing cards work

## Technical Notes

### Project Structure

```
website/                         # Docusaurus project root
├── docusaurus.config.js         # Main configuration
├── sidebars.js                  # Documentation sidebar
├── package.json
├── src/
│   ├── components/
│   │   ├── HomepageFeatures/    # Feature cards
│   │   ├── WorkUnitBuilder/     # Interactive demo
│   │   ├── PlanSimulator/       # Ranking demo
│   │   └── OutputPreview/       # Resume preview
│   ├── css/
│   │   └── custom.css           # Theme customization
│   └── pages/
│       ├── index.js             # Homepage
│       ├── demo.js              # Interactive demo page
│       └── examples.js          # Code examples
├── docs/
│   ├── getting-started.md
│   ├── commands/
│   │   ├── new.md
│   │   ├── validate.md
│   │   ├── plan.md
│   │   └── build.md
│   ├── data-model/
│   │   ├── work-unit.md
│   │   ├── position.md
│   │   └── config.md
│   └── configuration.md
├── blog/                        # Placeholder for future posts
└── static/
    ├── img/
    │   ├── logo.svg
    │   ├── hero-diagram.svg
    │   └── screenshots/
    └── diagrams/                # Excalidraw exports
```

### Docusaurus Setup

```bash
# Initialize Docusaurus
npx create-docusaurus@latest website classic

# Key dependencies
npm install @docusaurus/preset-classic
npm install prism-react-renderer  # Syntax highlighting
npm install @monaco-editor/react  # Code editor for demos
```

### docusaurus.config.js Key Settings

```javascript
module.exports = {
  title: 'Resume as Code',
  tagline: 'Treat your career data as structured, queryable truth',
  url: 'https://[username].github.io',
  baseUrl: '/resume-as-code/',
  organizationName: '[username]',
  projectName: 'resume-as-code',

  themeConfig: {
    navbar: {
      title: 'Resume as Code',
      logo: { src: 'img/logo.svg' },
      items: [
        { to: '/docs/getting-started', label: 'Docs' },
        { to: '/demo', label: 'Demo' },
        { to: '/examples', label: 'Examples' },
        { href: 'https://github.com/...', label: 'GitHub' },
      ],
    },
    footer: {
      style: 'dark',
      links: [/* ... */],
    },
    // Algolia search (optional, can use local)
    algolia: {
      appId: '...',
      apiKey: '...',
      indexName: 'resume-as-code',
    },
  },
};
```

### Interactive Demo Components

**WorkUnitBuilder.jsx**
```jsx
import React, { useState } from 'react';
import { dump } from 'js-yaml';
import CodeBlock from '@theme/CodeBlock';

export default function WorkUnitBuilder() {
  const [formData, setFormData] = useState({
    title: '',
    problem: '',
    actions: [''],
    outcome: '',
  });

  const yaml = dump({
    schema_version: '1.0.0',
    id: `wu-${new Date().toISOString().slice(0,10)}-example`,
    ...formData,
  });

  return (
    <div className="demo-container">
      <div className="form-section">
        {/* Form inputs */}
      </div>
      <div className="preview-section">
        <CodeBlock language="yaml">{yaml}</CodeBlock>
        <button onClick={() => navigator.clipboard.writeText(yaml)}>
          Copy YAML
        </button>
      </div>
    </div>
  );
}
```

### GitHub Actions Deployment

```yaml
# .github/workflows/deploy-docs.yml
name: Deploy to GitHub Pages

on:
  push:
    branches: [main]
    paths:
      - 'website/**'

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: 20
      - name: Install dependencies
        run: cd website && npm ci
      - name: Build
        run: cd website && npm run build
      - name: Deploy
        uses: peaceiris/actions-gh-pages@v3
        with:
          github_token: ${{ secrets.GITHUB_TOKEN }}
          publish_dir: ./website/build
```

## Tasks

### Task 1: Docusaurus Project Setup
- [x] Initialize Docusaurus in `website/` directory
- [x] Configure `docusaurus.config.ts` with project settings
- [x] Set up custom theme colors matching project branding
- [x] Configure sidebar navigation in `sidebars.ts`
- [x] Test local development server

### Task 2: Homepage Design
- [x] Create hero section with tagline and CTAs
- [x] Create hero visual (code example demo)
- [x] Build feature cards component
- [x] Add "How it Works" section
- [x] Style with custom CSS

### Task 3: Features Page
- [x] Design feature card component
- [x] Write copy for 8 features
- [x] Add emoji icons for each feature
- [x] Link features to relevant documentation
- [x] Ensure mobile responsive layout

### Task 4: Philosophy Page
- [x] Port content from docs/philosophy.md
- [x] Create "Problem vs Solution" visualization
- [x] Explain PAR framework and resumes as queries
- [x] List benefits of the approach
- [x] Link to detailed documentation

### Task 5: Interactive Demo - Work Unit Builder
- [x] Create form component for Work Unit fields
- [x] Implement real-time YAML generation
- [x] Add validation feedback (visual indicators)
- [x] Implement copy-to-clipboard
- [x] Style for desktop and mobile

### Task 6: Interactive Demo - Plan Simulator
- [x] Create JD input textarea
- [x] Pre-load sample Work Units
- [x] Implement mock BM25 ranking display
- [x] Show skill coverage visualization
- [x] Add result status indicators

### Task 7: Interactive Demo - Output Preview
- [x] Create template selector (modern, executive, ATS)
- [x] Build resume preview component
- [x] Show how Work Units map to bullets
- [x] Toggle between formats (visual only)

### Task 8: Documentation Migration
- [x] Port Getting Started from README
- [x] Create command reference pages (new, list, show, remove, validate, plan, build, config)
- [x] Port data model docs (work-unit, position, certification, education, profile)
- [x] Add configuration reference
- [x] Configure sidebar navigation

### Task 9: Examples Page
- [x] Create expandable example component
- [x] Write 5 complete workflow examples
- [x] Add expected output for each
- [x] Ensure syntax highlighting works

### Task 10: GitHub Actions Deployment
- [x] Create deployment workflow (.github/workflows/deploy-docs.yml)
- [x] Configure for GitHub Pages (actions/upload-pages-artifact, actions/deploy-pages)
- [x] Trigger on push to main (website/** paths)
- [x] Support workflow_dispatch for manual runs

### Task 11: SEO & Polish
- [x] Add meta tags (keywords, author, Twitter, OG)
- [x] Generate sitemap
- [x] Configure robots.txt
- [x] Configure social sharing cards
- [x] Remove template blog posts
- [ ] Cross-browser testing (manual step)
- [ ] Lighthouse audit (manual step)

## Definition of Done

- [ ] Site deployed to GitHub Pages (ready - awaiting push to main)
- [x] All navigation items functional
- [x] Homepage renders with hero, features
- [x] Philosophy page with core concepts explained
- [x] All 3 interactive demos functional
- [x] Documentation sidebar configured with all sections
- [x] Mobile responsive CSS (via CSS grid)
- [ ] Lighthouse performance score 90+ (manual validation)
- [x] Build passes with no errors
- [x] Links all work (no 404s)

## Design Guidelines

### Color Palette
```css
--primary: #2563eb;      /* Blue - trust, professionalism */
--secondary: #10b981;    /* Green - success, growth */
--accent: #8b5cf6;       /* Purple - creativity, innovation */
--dark: #1e293b;         /* Dark slate - text */
--light: #f8fafc;        /* Light background */
```

### Typography
- Headings: Inter or system-ui
- Body: Same, optimized for readability
- Code: JetBrains Mono or Fira Code

### Visual Style
- Clean, modern, minimal
- Generous whitespace
- Subtle shadows and borders
- Professional but approachable
- Developer-focused aesthetic

## Notes

- This is a larger story - consider breaking into multiple PRs
- Interactive demos can be simplified for MVP (static mockups first)
- Algolia search requires application - can use local search initially
- Consider hosting screenshots/videos on CDN for performance
- Blog section is placeholder - can be populated post-launch
