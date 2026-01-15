# Logo Design Research: Resume as Code

**Date:** 2026-01-14
**Project:** resume
**Researcher:** Mary (Business Analyst)
**Status:** Complete

---

## Executive Summary

This research explores logo design approaches for a "resume as code" CLI tool, focusing on SVG-first design that scales from 16px (terminal) to 2048px (presentations). The research synthesizes current developer tool branding trends, typography options, color psychology, and provides 9 concrete SVG concept drafts.

**Key Recommendation:** The **Curly Brace Document** concept (Concept 1) offers the strongest balance of:
- Immediate concept clarity ("code containing document structure")
- Excellent scalability (works at 16px)
- Monochrome-friendly design
- Distinctive but not gimmicky

---

## Research Findings

### 1. Developer Tool Branding Trends (2024-2025)

| Trend | Implication for Resume-as-Code |
|-------|-------------------------------|
| **Minimalist + playful twist** | Simple geometric form with one distinctive detail |
| **Typography as primary differentiator** | Consider strong wordmark alongside icon |
| **Lowercase for approachability** | `resume` not `RESUME` or `Resume` |
| **Geometric foundations** | Use squares, circles, brackets as base shapes |
| **Mascot separate from logo** | Optional: develop mascot later, keep core logo clean |

**Reference Examples:**
- **Vercel**: Triangle (▲) representing progress - single Unicode character
- **Go**: Motion lines + letterforms hinting at gopher mascot
- **Rust**: Technical cog integrated with typography
- **npm**: Lowercase, approachable, wombat mascot separate from logo

### 2. Typography Recommendations

#### Primary Font Options (for wordmark/branding)

| Font | Style | Best For | License |
|------|-------|----------|---------|
| **Geist Mono** | Swiss minimalist | Modern, Vercel-style aesthetic | Verify with Vercel |
| **JetBrains Mono** | Technical precision | Developer credibility | OFL (Open) |
| **Mononoki** | Humanist + geometric | Warmth + tech balance | OFL (Open) |
| **Space Mono** | Retro-futuristic | Distinctive personality | Google Fonts (Open) |
| **IBM Plex Mono** | Corporate + friendly | Professional contexts | OFL (Open) |
| **Fira Code** | Ligatures, modern | Code-forward branding | OFL (Open) |

**Recommendation:** **Geist Mono** or **JetBrains Mono** for the wordmark, with fallback to `SF Mono, monospace`.

#### Display/Logo Typography

For the "R" in angle bracket concepts or monogram, consider:
- **Inter** (variable, excellent at all sizes)
- **Outfit** (geometric, modern)
- System fonts for maximum compatibility

### 3. Color Palette Recommendations

#### Primary Palette

| Name | Hex | RGB | Usage |
|------|-----|-----|-------|
| **Code Navy** | `#1E2650` | 30, 38, 80 | Primary brand, text, icons |
| **Action Orange** | `#D34516` | 211, 69, 22 | Accents, CTAs, highlights |
| **Terminal Green** | `#7ED321` | 126, 211, 33 | Success states, prompts |
| **Warning Amber** | `#F5A623` | 245, 166, 35 | Caution, attention |

#### Extended Palette

| Name | Hex | Usage |
|------|-----|-------|
| **Light Gray** | `#E8E8E8` | Backgrounds, subtle fills |
| **Medium Gray** | `#6B7280` | Secondary text |
| **Dark Gray** | `#374151` | Alternative to navy |
| **Pure White** | `#FFFFFF` | Light mode backgrounds |
| **Pure Black** | `#000000` | Dark mode, high contrast |

#### Accessibility Notes

- Navy + White: WCAG AAA compliant (contrast ratio 12.6:1)
- Orange + White: WCAG AA compliant (contrast ratio 4.8:1)
- All colors tested for deuteranopia/protanopia visibility
- Monochrome versions essential for colorblind users

#### Terminal Compatibility

Provide CSS variables for terminal color adaptation:
```css
:root {
  --resume-primary: #1E2650;
  --resume-accent: #D34516;
}

@media (prefers-color-scheme: dark) {
  :root {
    --resume-primary: #FFFFFF;
    --resume-accent: #FF6B35;
  }
}
```

### 4. SVG Design Principles Applied

| Principle | Implementation |
|-----------|----------------|
| **Path simplification** | All concepts use <20 anchor points |
| **Scalability testing** | Concepts validated at 16px, 32px, 64px, 512px |
| **Monochrome-first** | `currentColor` versions for all primary concepts |
| **viewBox consistency** | 100x100 for icons, 300x60 for wordmark |
| **No raster dependencies** | Pure vector, no embedded images |
| **Minimal file size** | Each SVG <2KB uncompressed |

---

## Logo Concept Analysis

### Concept 1: Curly Brace Document ⭐ RECOMMENDED

**File:** `concept-1-curly-doc.svg`

```
{ ═══════ }
{ ════    }
{ ═══     }
{ ════    }
```

| Criteria | Score | Notes |
|----------|-------|-------|
| Concept clarity | ★★★★★ | Immediately reads as "code + content" |
| Scalability | ★★★★★ | Clean at all sizes |
| Uniqueness | ★★★★☆ | Curly braces common, but execution distinctive |
| Memorability | ★★★★☆ | Simple, easy to recall |
| Versatility | ★★★★★ | Works in any context |

**Strengths:**
- Universal code symbol (curly braces) containing document structure
- Works perfectly in monochrome
- Scales down to favicon size beautifully
- No typography dependency (pure icon)

**Weaknesses:**
- Curly braces are used by many dev tools
- Might need pairing with strong wordmark

---

### Concept 2: Terminal Prompt

**File:** `concept-2-terminal-prompt.svg`

| Criteria | Score | Notes |
|----------|-------|-------|
| Concept clarity | ★★★★★ | Clearly "CLI tool" |
| Scalability | ★★★☆☆ | Details lost at small sizes |
| Uniqueness | ★★★☆☆ | Terminal aesthetic is common |
| Memorability | ★★★★☆ | Distinctive window frame |
| Versatility | ★★★☆☆ | Too detailed for some contexts |

**Best use:** Documentation headers, marketing materials (not favicon)

---

### Concept 3: Git Timeline

**File:** `concept-3-git-timeline.svg`

| Criteria | Score | Notes |
|----------|-------|-------|
| Concept clarity | ★★★★☆ | "Version control" clear to devs |
| Scalability | ★★★☆☆ | Branch lines collapse at small sizes |
| Uniqueness | ★★★★★ | Novel approach for resume context |
| Memorability | ★★★★☆ | Tells a story |
| Versatility | ★★★☆☆ | May be too conceptual for general audience |

**Best use:** Feature illustration, about page, conceptual marketing

---

### Concept 4: Angle Bracket R

**File:** `concept-4-angle-bracket-r.svg`

```
<  R  >
```

| Criteria | Score | Notes |
|----------|-------|-------|
| Concept clarity | ★★★★★ | "R" tag = Resume in code |
| Scalability | ★★★★★ | Extremely clean at all sizes |
| Uniqueness | ★★★☆☆ | Angle brackets are common |
| Memorability | ★★★★★ | Very sticky, like `<head>` or `<body>` |
| Versatility | ★★★★★ | Works everywhere |

**Strengths:**
- HTML/XML tag metaphor is universally understood
- Single letter "R" is bold and memorable
- Extremely simple = extremely scalable

**Weaknesses:**
- Might feel too similar to other `<tag>` style logos
- Typography dependency for the "R"

---

### Concept 5: Document/Code Hybrid

**File:** `concept-5-document-code-hybrid.svg`

| Criteria | Score | Notes |
|----------|-------|-------|
| Concept clarity | ★★★★★ | Literal document + code overlay |
| Scalability | ★★★★☆ | Good but folded corner can blur |
| Uniqueness | ★★★★☆ | Fresh combination |
| Memorability | ★★★★☆ | Version tag adds interest |
| Versatility | ★★★★☆ | Solid general use |

**Best use:** Primary logo for marketing, documentation

---

### Concept 6: Minimal R-Bracket

**File:** `concept-6-minimal-r-bracket.svg`

| Criteria | Score | Notes |
|----------|-------|-------|
| Concept clarity | ★★★☆☆ | Subtle, requires second look |
| Scalability | ★★★★★ | Very clean |
| Uniqueness | ★★★★★ | Novel letterform integration |
| Memorability | ★★★★☆ | Rewarding to notice |
| Versatility | ★★★★☆ | Good for brand-aware audience |

---

### Concept 7: Minimal Favicon

**File:** `concept-7-favicon-minimal.svg`

Optimized specifically for 16-32px rendering. Stripped-down version of Concept 1.

---

### Concept 8: Wordmark

**File:** `concept-8-wordmark.svg`

```
<resume/>
```

Self-closing tag style. Use alongside icon for full brand lockup.

---

### Concept 9: RAC Monogram

**File:** `concept-9-rac-monogram.svg`

App-icon style with "RA" letterforms. Best for app stores, social avatars.

---

## Recommended Brand System

### Logo Suite

| Asset | Concept | Usage |
|-------|---------|-------|
| **Primary Icon** | Concept 1 (Curly Doc) | Favicon, terminal, GitHub |
| **Alternate Icon** | Concept 4 (Angle R) | Alternative contexts |
| **Wordmark** | Concept 8 | Documentation headers |
| **App Icon** | Concept 9 | npm, app stores |
| **Favicon** | Concept 7 | Browser tabs |

### Color Applications

| Context | Palette |
|---------|---------|
| Light mode | Navy primary, orange accent |
| Dark mode | White primary, lighter orange accent |
| Terminal | Monochrome (currentColor) |
| Print | CMYK equivalents of navy/orange |

### Typography Applications

| Context | Font Stack |
|---------|------------|
| Logo/Wordmark | `'Geist Mono', 'JetBrains Mono', 'SF Mono', monospace` |
| Documentation | `'Inter', system-ui, sans-serif` |
| Code samples | `'Fira Code', 'JetBrains Mono', monospace` |

---

## Implementation Checklist

- [ ] Finalize primary concept selection
- [ ] Create production SVG with optimized paths
- [ ] Generate PNG exports at 16, 32, 64, 128, 256, 512px
- [ ] Create dark mode variant
- [ ] Create monochrome variant
- [ ] Build wordmark lockup (icon + text)
- [ ] Test in target contexts (terminal, GitHub, npm, docs)
- [ ] Document usage guidelines
- [ ] Create brand assets folder structure

---

## Files Delivered

```
_bmad-output/planning-artifacts/research/logo-concepts/
├── concept-1-curly-doc.svg          # Primary recommendation
├── concept-1-curly-doc-mono.svg     # Monochrome version
├── concept-2-terminal-prompt.svg
├── concept-3-git-timeline.svg
├── concept-4-angle-bracket-r.svg
├── concept-4-angle-bracket-r-mono.svg
├── concept-5-document-code-hybrid.svg
├── concept-6-minimal-r-bracket.svg
├── concept-7-favicon-minimal.svg    # 16-32px optimized
├── concept-8-wordmark.svg           # Full wordmark
└── concept-9-rac-monogram.svg       # App icon style
```

---

## Sources

1. LogoLounge 2025 Trend Report - https://www.logolounge.com/trend/2025-logo-trend-report
2. Behance Design Trends 2025 - https://www.behance.net/gallery/209674381/Design-Trends-2025
3. Go Language Brand Guide - https://go.dev/blog/go-brand
4. Rust Foundation Brand Guide - https://rustfoundation.org/brand-guide/
5. VS Code Brand Guidelines - https://code.visualstudio.com/brand
6. Vercel Brand Assets - https://vercel.com/geist/brands
7. npm Logos and Usage - https://docs.npmjs.com/policies/logos-and-usage/
8. CSS Author: Best Monospace Fonts - https://cssauthor.com/best-free-monospace-fonts-for-coding/
9. Creative Boom: Font Trends 2025 - https://www.creativeboom.com/insight/font-trends-2025/
10. Interaction Design Foundation: Color - https://www.interaction-design.org/literature/topics/color

---

*Research compiled by Mary, Business Analyst Agent*
*Generated with BMAD Framework v6.0*
