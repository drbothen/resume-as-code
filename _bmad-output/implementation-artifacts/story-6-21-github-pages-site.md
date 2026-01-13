# Story 6.21: GitHub Pages Marketing Site (Docusaurus)

## Story Info

- **Epic**: Epic 6 - Executive Resume Template & Profile System
- **Status**: ready-for-dev
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
- [ ] Initialize Docusaurus in `website/` directory
- [ ] Configure `docusaurus.config.js` with project settings
- [ ] Set up custom theme colors matching project branding
- [ ] Configure sidebar navigation in `sidebars.js`
- [ ] Test local development server

### Task 2: Homepage Design
- [ ] Create hero section with tagline and CTAs
- [ ] Create hero visual (diagram or animation)
- [ ] Build feature cards component
- [ ] Add social proof section (placeholder for testimonials)
- [ ] Style with custom CSS

### Task 3: Features Page
- [ ] Design feature card component
- [ ] Write copy for 8 features
- [ ] Add icons/illustrations for each feature
- [ ] Link features to relevant documentation
- [ ] Ensure mobile responsive layout

### Task 4: Philosophy Page
- [ ] Port content from docs/philosophy.md
- [ ] Embed Excalidraw diagrams (SVG)
- [ ] Create comparison visualization (traditional vs RaC)
- [ ] Add interactive elements where appropriate
- [ ] Link to detailed documentation

### Task 5: Interactive Demo - Work Unit Builder
- [ ] Create form component for Work Unit fields
- [ ] Implement real-time YAML generation
- [ ] Add validation feedback (schema compliance)
- [ ] Implement copy-to-clipboard
- [ ] Style for desktop and mobile

### Task 6: Interactive Demo - Plan Simulator
- [ ] Create JD input textarea
- [ ] Pre-load sample Work Units
- [ ] Implement mock ranking display
- [ ] Show skill coverage visualization
- [ ] Add explanatory tooltips

### Task 7: Interactive Demo - Output Preview
- [ ] Create template selector (modern, executive, ATS)
- [ ] Build resume preview component
- [ ] Show how Work Units map to bullets
- [ ] Toggle between formats (visual only)

### Task 8: Documentation Migration
- [ ] Port Getting Started from README
- [ ] Create command reference pages
- [ ] Port data model docs from docs/
- [ ] Add configuration reference
- [ ] Set up search (local or Algolia)

### Task 9: Examples Page
- [ ] Create code example component with copy button
- [ ] Write 4-5 complete workflow examples
- [ ] Add expected output for each
- [ ] Ensure syntax highlighting works

### Task 10: GitHub Actions Deployment
- [ ] Create deployment workflow
- [ ] Configure GitHub Pages settings
- [ ] Test deployment on push
- [ ] Verify site is accessible

### Task 11: SEO & Polish
- [ ] Add meta tags and og:image
- [ ] Generate sitemap
- [ ] Configure robots.txt
- [ ] Test social sharing cards
- [ ] Cross-browser testing
- [ ] Lighthouse audit (aim for 90+ scores)

## Definition of Done

- [ ] Site deployed to GitHub Pages
- [ ] All navigation items functional
- [ ] Homepage renders with hero, features
- [ ] Philosophy page with embedded diagrams
- [ ] All 3 interactive demos functional
- [ ] Documentation searchable
- [ ] Mobile responsive (tested on phone)
- [ ] Lighthouse performance score 90+
- [ ] No console errors
- [ ] Links all work (no 404s)

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
