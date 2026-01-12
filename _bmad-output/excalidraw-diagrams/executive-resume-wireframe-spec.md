# Executive Resume Wireframe Specification

**Created:** 2026-01-12
**Author:** Joshua Magady
**File:** `executive-resume-wireframe.excalidraw`

---

## Overview

This wireframe represents a single-column executive resume layout optimized for senior technical professionals. The design follows research-validated best practices for ATS compatibility and recruiter readability.

---

## Layout Specifications

### Page Dimensions

| Property | Value |
|----------|-------|
| Width | 800px (represents 8.5") |
| Height | 1040px (represents 11") |
| Aspect Ratio | Letter (US standard) |
| Margins | 1 inch equivalent (40px) |

### Visual Hierarchy Distribution

| Zone | Percentage | Content |
|------|------------|---------|
| Header | 20% | Name, title, contact |
| Body | 70% | Summary, skills, experience |
| Footer | 10% | Education, certifications |

---

## Section Specifications

### 1. Header Section

**Purpose:** Establish identity and professional brand instantly

| Element | Typography | Color | Position |
|---------|------------|-------|----------|
| Name | 22pt bold | #424242 | Centered |
| Professional Title | 14pt regular | #2c3e50 | Centered, below name |
| Contact Line | 10pt regular | #666666 | Centered, pipe separators |
| Bottom Border | 3px solid | #2c3e50 | Full width |

**Contact Line Format:**
```
Location  |  email@example.com  |  555-123-4567  |  LinkedIn
```

### 2. Executive Summary Section

**Purpose:** 3-5 sentence value proposition

| Property | Value |
|----------|-------|
| Header | "EXECUTIVE SUMMARY" 14pt uppercase |
| Header Color | #2c3e50 |
| Divider | 1px #dddddd |
| Content Box | Light gray background (#fafafa) |
| Text Size | 11pt |
| Alignment | Left-justified |

### 3. Core Competencies Section

**Purpose:** Scannable skills for keyword matching

| Property | Value |
|----------|-------|
| Header | "CORE COMPETENCIES" 14pt uppercase |
| Layout | Horizontal flex wrap |
| Tag Style | Pill/badge (rounded rectangle) |
| Tag Background | #f0f4f8 |
| Tag Border | #d0d8e0 |
| Tag Text | 10pt #424242 |
| Tag Spacing | 10px gap |
| Recommended Count | 8-12 skills |

### 4. Professional Experience Section

**Purpose:** Demonstrate impact with quantified achievements

#### Position Entry Structure:

```
┌─────────────────────────────────────────────────────────┐
│ Company Name (13pt bold)              Dates (11pt gray) │
│ Title, Location (11pt italic)                           │
│ ┌─────────────────────────────────────────────────┐     │
│ │ Team: X | Budget: $XM | Scope: Geographic      │     │ ← SCOPE INDICATORS
│ └─────────────────────────────────────────────────┘     │
│ • Achievement bullet with metrics (11pt)                │
│ • Achievement bullet with metrics                       │
│ • Achievement bullet with metrics                       │
│ • Achievement bullet with metrics                       │
└─────────────────────────────────────────────────────────┘
```

#### Scope Indicators (Key Executive Feature)

| Metric Type | Format Example |
|-------------|----------------|
| Team Size | "Led team of 15" or "Managed 15 direct reports" |
| Budget | "$2M budget" or "$2M P&L responsibility" |
| Revenue | "$10M revenue impact" |
| Geographic | "Global", "Multi-region", "APAC/EMEA/Americas" |
| Organizational | "Cross-functional", "Enterprise-wide" |

**Styling:**
- Background: #f0f4f8
- Border: #d0d8e0
- Text: #2c3e50 (accent color)
- Format: Pipe-separated values

### 5. Education Section

**Purpose:** Credential verification (minimal for senior roles)

| Property | Value |
|----------|-------|
| Header | "EDUCATION" 14pt uppercase |
| Entry Format | Degree, Institution, Year - Honors |
| Text Size | 11pt |
| Position | After Experience (industry standard for 10+ years) |

### 6. Certifications Section

**Purpose:** Technical credibility and current knowledge

| Property | Value |
|----------|-------|
| Header | "CERTIFICATIONS" 14pt uppercase |
| Entry Format | Certification Name, Issuer, Year |
| Text Size | 11pt |
| List Style | Simple list, no bullets |

---

## Color Palette

### Primary Colors (Classic Wireframe Theme)

| Role | Color | Hex | Usage |
|------|-------|-----|-------|
| Background | White | #ffffff | Page background |
| Container | Light Gray | #f5f5f5 | Section backgrounds |
| Border | Gray | #9e9e9e | Page border, dividers |
| Text | Dark Gray | #424242 | Body text |

### Accent Colors (Executive Theme)

| Role | Color | Hex | Usage |
|------|-------|-----|-------|
| Accent | Dark Blue-Gray | #2c3e50 | Headers, borders, links |
| Secondary Text | Medium Gray | #666666 | Dates, meta info |
| Scope Values | Dark Green | #1a5f2a | Metrics, achievements |
| Tag Background | Light Blue-Gray | #f0f4f8 | Skill tags, scope box |

---

## Typography Scale

| Element | Size | Weight | Style |
|---------|------|--------|-------|
| Name | 22pt | Bold | Normal |
| Professional Title | 14pt | Regular | Normal |
| Section Headers | 14pt | Bold | Uppercase |
| Company/Position | 13pt | Bold | Normal |
| Body Text | 11pt | Regular | Normal |
| Contact/Dates | 10-11pt | Regular | Normal/Italic |
| Skill Tags | 10pt | Regular | Normal |

---

## Spacing Standards

| Element | Spacing |
|---------|---------|
| Page Margins | 40px (1 inch equivalent) |
| Section Gap | 20-30px |
| Position Gap | 16-20px |
| Line Height | 1.4-1.5 |
| Bullet Spacing | 4-6px |
| Tag Gap | 10px |

---

## Responsive Considerations

### Multi-Page Handling

For resumes exceeding one page:

1. **Page 2+ Header:** Name only, 10pt, top margin
2. **Page Breaks:** Between sections, never mid-position
3. **Recommended Length:** 2-3 pages for executive level

### Print Optimization

- All colors print cleanly in grayscale
- Minimum text size: 10pt
- High contrast ratios (WCAG AAA)

---

## ATS Compatibility Features

| Feature | Implementation |
|---------|---------------|
| Layout | Single-column (no tables/columns) |
| Fonts | System fonts (Calibri, Arial) |
| Headers | Clear section demarcation |
| Text | Selectable, not images |
| Format | Semantic HTML structure |

---

## Design Variations

### Available Templates

1. **Executive (This Spec)** - Sans-serif, modern, tech-focused
2. **Executive-Classic** - Serif, traditional, finance/law-focused
3. **Modern** - Lighter styling, startup-friendly
4. **ATS-Safe** - Minimal styling, maximum compatibility

---

## Implementation Notes

### For CSS (WeasyPrint)

```css
@page { size: letter; margin: 1in; }
body { font-family: 'Calibri', Arial, sans-serif; font-size: 10.5pt; }
h2 { font-size: 12pt; text-transform: uppercase; border-bottom: 1px solid #ddd; }
.scope-line { background: #f0f4f8; color: #2c3e50; }
```

### For python-docx (Word)

```python
section.left_margin = Inches(1)
run.font.name = 'Arial'
run.font.size = Pt(10.5)
run.font.color.rgb = RGBColor(0x42, 0x42, 0x42)
```

---

## References

- [CSS Styling Research](../planning-artifacts/research/technical-executive-resume-css-styling-research-2026-01-12.md)
- [Story 6.4: Executive Resume Template](../implementation-artifacts/6-4-executive-resume-template.md)
- Wireframe File: `executive-resume-wireframe.excalidraw`
