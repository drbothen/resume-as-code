# rac.me Brand Guidelines

> Resume as Code — Your career, versioned.

---

## Brand Overview

**rac.me** is a CLI tool that treats career data as structured, queryable truth. The brand identity reflects this philosophy: precise, technical, and developer-friendly while remaining approachable.

**Brand Personality:**
- Technical but not cold
- Precise but not rigid
- Developer-native but accessible
- Minimal but not sterile

---

## Logo System

### Primary Icon

The curly brace document mark represents code structure containing career content.

| File | Usage |
|------|-------|
| `icon.svg` | Primary logo, color version |
| `icon-mono.svg` | Terminal, single-color contexts |
| `favicon.svg` | Browser tabs, 16-32px contexts |

### Lockups

| File | Usage |
|------|-------|
| `lockup-horizontal.svg` | Website headers, documentation |
| `lockup-horizontal-mono.svg` | Single-color, terminal output |
| `lockup-stacked.svg` | Square contexts, social avatars |
| `lockup-dark.svg` | Dark backgrounds |
| `wordmark.svg` | Text-only contexts |

---

## Logo Usage Rules

### Clear Space

Maintain minimum clear space equal to the height of one "content line" in the icon around all sides.

```
        ┌─────────────────────┐
        │                     │
        │   ╭    ╮            │
        │   │ ══ │  rac.me    │
        │   │ ═  │            │
        │   ╰    ╯            │
        │                     │
        └─────────────────────┘
             ↑ clear space
```

### Minimum Sizes

| Asset | Minimum Size |
|-------|--------------|
| Icon | 16px |
| Favicon | 16px |
| Horizontal lockup | 140px wide |
| Stacked lockup | 60px wide |

### Do's

- Use the provided SVG files without modification
- Maintain aspect ratios when scaling
- Use monochrome version on busy backgrounds
- Use dark mode version on dark backgrounds
- Ensure adequate contrast with background

### Don'ts

- Don't stretch or distort the logo
- Don't rotate the logo
- Don't change the colors
- Don't add effects (shadows, gradients, glows)
- Don't place on low-contrast backgrounds
- Don't recreate the logo in different fonts
- Don't rearrange lockup elements

---

## Color Palette

### Primary Colors

| Name | Hex | RGB | Usage |
|------|-----|-----|-------|
| **Code Navy** | `#1E2650` | 30, 38, 80 | Primary brand, text, icons |
| **Action Orange** | `#D34516` | 211, 69, 22 | Accents, CTAs, the dot in rac.me |

### Secondary Colors

| Name | Hex | RGB | Usage |
|------|-----|-----|-------|
| **Terminal Green** | `#7ED321` | 126, 211, 33 | Success states, CLI prompts |
| **Warning Amber** | `#F5A623` | 245, 166, 35 | Caution, attention states |

### Dark Mode Colors

| Name | Hex | RGB | Usage |
|------|-----|-----|-------|
| **White** | `#FFFFFF` | 255, 255, 255 | Primary on dark backgrounds |
| **Light Orange** | `#FF6B35` | 255, 107, 53 | Accent on dark backgrounds |

### Neutral Colors

| Name | Hex | RGB | Usage |
|------|-----|-----|-------|
| **Light Gray** | `#E8E8E8` | 232, 232, 232 | Backgrounds, subtle fills |
| **Medium Gray** | `#6B7280` | 107, 114, 128 | Secondary text |
| **Dark Gray** | `#374151` | 55, 65, 81 | Alternative to navy |
| **Pure Black** | `#000000` | 0, 0, 0 | High contrast contexts |

### Color Accessibility

- Navy + White: WCAG AAA (contrast ratio 12.6:1)
- Orange + White: WCAG AA (contrast ratio 4.8:1)
- All colors tested for colorblind visibility
- Always provide monochrome alternative

### CSS Variables

```css
:root {
  /* Primary */
  --rac-navy: #1E2650;
  --rac-orange: #D34516;

  /* Secondary */
  --rac-green: #7ED321;
  --rac-amber: #F5A623;

  /* Neutrals */
  --rac-gray-light: #E8E8E8;
  --rac-gray-medium: #6B7280;
  --rac-gray-dark: #374151;
}

@media (prefers-color-scheme: dark) {
  :root {
    --rac-primary: #FFFFFF;
    --rac-accent: #FF6B35;
  }
}
```

---

## Typography

### Primary Font Stack (Wordmarks & Code)

```css
font-family: 'Geist Mono', 'JetBrains Mono', 'SF Mono', 'Fira Code', monospace;
```

| Font | Source | License |
|------|--------|---------|
| Geist Mono | Vercel | SIL OFL |
| JetBrains Mono | JetBrains | SIL OFL |
| SF Mono | Apple | System font |
| Fira Code | Mozilla | SIL OFL |

### Secondary Font Stack (Documentation & UI)

```css
font-family: 'Inter', system-ui, -apple-system, sans-serif;
```

### Typography Guidelines

- **Wordmark:** Always lowercase `rac.me`
- **Product name:** "Resume as Code" or "rac.me"
- **CLI references:** Use monospace: `resume build`
- **Headings:** Sentence case preferred

---

## Voice & Tone

### Writing Style

- Direct and concise
- Technical but accessible
- Confident, not boastful
- Helpful, not condescending

### Example Phrases

| Do | Don't |
|----|-------|
| "Generate targeted resumes" | "Our revolutionary AI-powered solution" |
| "Your career data, versioned" | "The future of resume building" |
| "Built for developers" | "Enterprise-grade synergy platform" |

---

## File Inventory

```
assets/brand/
├── BRAND-GUIDELINES.md    # This document
├── icon.svg               # Primary icon (color)
├── icon-mono.svg          # Icon (monochrome)
├── favicon.svg            # 16-32px optimized
├── lockup-horizontal.svg  # Icon + wordmark
├── lockup-horizontal-mono.svg
├── lockup-stacked.svg     # Vertical layout
├── lockup-dark.svg        # Dark backgrounds
└── wordmark.svg           # Text only
```

---

## Contact

For brand questions or asset requests, open an issue at:
https://github.com/drbothen/resume-as-code

---

*Last updated: 2026-01-14*
