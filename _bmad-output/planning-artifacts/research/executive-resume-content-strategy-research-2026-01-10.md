# Executive Resume Content Strategy Research

**Date:** 2026-01-10
**Researcher:** Mary (Business Analyst Agent)
**Research Type:** Deep Research via Perplexity
**Topics Covered:** RB-059, RB-060, RB-061, RB-062

---

## Executive Summary

This research validates and extends our Resume-as-Code architecture's approach to accomplishment framing and provides actionable guidance for executive-level resume content strategy. Key findings:

1. **PAR Framework VALIDATED** - PAR remains best practice for resume contexts; STAR better for interviews
2. **Executive Resumes Require Different Approach** - 2-3 pages, results-first (RAS formula), strategic framing
3. **Quantification is Critical** - Metrics improve recruiter engagement by 73%+
4. **Modern Best Practice: Action + Metric + Outcome** - Evolved beyond traditional frameworks

---

## RB-059: Executive Resume Templates and Best Practices

### Key Findings

#### Optimal Length for C-Level and VP-Level Resumes
- **Industry consensus: 2-3 pages** for executives with 10+ years experience
- One-page rule is **thoroughly discredited** by 2025-2026 research
- ResumeGo 2018 study: recruiters prefer 2-page resumes 2.3x more than 1-page
- Three pages acceptable when content is substantial; avoid orphaned sentences on third page

#### Section Ordering and Structure
**Recommended hierarchy:**
1. **Header** - Name (18-22pt), title, contact info, LinkedIn
2. **Executive Summary** (3-5 sentences) - Personal brand, quantified achievements
3. **Professional Experience** - Reverse chronological, 4-6 bullets per recent role
4. **Education & Certifications** - Degrees, executive education, relevant certs
5. **Optional sections** - Board memberships, professional affiliations, skills

#### Visual Design Conventions
| Element | Recommendation |
|---------|----------------|
| **Fonts** | Sans-serif (Calibri, Arial, Helvetica) or serif (Cambria, Georgia) |
| **Body size** | 10-12pt |
| **Name size** | 18-22pt |
| **Margins** | 0.5-1 inch all sides |
| **Line spacing** | 1.0-1.15 |
| **Columns** | Single column preferred for ATS; two-column acceptable but riskier |

#### Executive vs Standard Resume Differences
| Aspect | Standard Resume | Executive Resume |
|--------|-----------------|------------------|
| Length | 1-2 pages | 2-3 pages |
| Focus | Tasks/responsibilities | Strategic impact/transformation |
| Metrics | Nice to have | Essential |
| Perspective | Activity-based | Outcome-based |
| Framing | What was done | Why it mattered strategically |

### Integration Recommendations for Resume-as-Code

1. **Template System** should support executive-specific layouts
2. **Work Unit Schema** should capture scope indicators (budget, team size, revenue)
3. **Plan Preview** should flag when Work Units lack quantification
4. **ATS Provider** should use single-column layout, standard section headers

---

## RB-060: Accomplishment Framing Strategies for Senior Professionals

### Key Findings

#### Executive vs Mid-Level Language Patterns

**Mid-level accomplishment:**
> "Led a team of 12 data analysts to implement new reporting systems, improving monthly closing time by 20%"

**Executive-level accomplishment:**
> "Directed cross-functional analytics transformation program that unified reporting across 12 business units, reducing corporate-wide financial close cycle from 45 to 28 days and enabling real-time executive decision-making, resulting in $2.3M in optimized working capital allocation"

#### Executive Action Verbs (Use These)
- **Strategic verbs**: orchestrated, spearheaded, championed, transformed, repositioned, reshaped, revitalized, pioneered, catalyzed, navigated
- **Leadership verbs**: cultivated, mentored, mobilized, aligned, unified
- **Influence verbs**: persuaded, convinced, articulated, championed, mobilized

**Avoid these weak verbs:**
- managed, handled, was responsible for, helped, worked on

#### Quantifying Leadership Impact

**Five dimensions of executive quantification:**
1. **Financial**: Revenue, cost savings, profit margin, ROI
2. **Operational**: Cycle time, productivity, error rates, quality
3. **Talent**: Team growth, retention, promotion rates, engagement scores
4. **Customer/Market**: Acquisition, retention, NPS, market share
5. **Organizational**: Process improvements, capability building

**Example transformation:**
- Before: "Improved operational efficiency"
- After: "Implemented advanced planning and scheduling system reducing production cycle time by 22% while increasing equipment utilization by 18%, generating $3.2M in annual cost savings"

#### Presenting Soft Accomplishments

Cultural transformation example:
> "Led comprehensive organizational culture transformation emphasizing psychological safety and continuous learning; established new values-based performance management system; implemented peer recognition program; achieved 22% improvement in internal survey measures of 'feel valued and respected at work'; established mentorship program pairing senior leaders with underrepresented employees, resulting in 16 mentoring relationships and 5 protege advancements to leadership positions"

### Common Executive Resume Mistakes

1. **Vague branding** - "Results-oriented leader" tells nothing
2. **Responsibility focus** - Listing duties instead of achievements
3. **Uncontextualized metrics** - "25% improvement" without baseline
4. **Overstating personal contribution** - Taking credit for team/org efforts
5. **Ignoring soft accomplishments** - Only financial/operational metrics

### Integration Recommendations for Resume-as-Code

1. **Work Unit Schema** should require:
   - Baseline metrics (before state)
   - Outcome metrics (after state)
   - Scope indicators (team size, budget, revenue influenced)
   - Impact category (financial, operational, talent, customer, organizational)

2. **Validation Rules** should flag:
   - Missing quantification
   - Weak action verbs
   - Missing baseline context

3. **Archetype Templates** should include:
   - Executive transformation archetype
   - Cultural leadership archetype
   - Strategic repositioning archetype

---

## RB-061: PAR/CAR/STAR Framework Validation

### Key Findings

#### Framework Comparison

| Framework | Components | Best For | Recruiter Preference |
|-----------|------------|----------|---------------------|
| **PAR** | Problem-Action-Result | Resume bullets, phone screens, technical interviews | High for resumes |
| **CAR** | Challenge-Action-Result | Mid-senior roles, versatile contexts | Growing preference |
| **STAR** | Situation-Task-Action-Result | Behavioral interviews, complex situations | Strong for interviews |

#### Framework Selection by Context

| Context | Recommended Framework |
|---------|----------------------|
| Resume bullet points | PAR or CAR |
| Phone screening | PAR |
| Behavioral interview | STAR |
| Panel interview (rapid-fire) | PAR |
| Executive interview | STAR, SOAR, or RAS |
| Technical interview | PAR |

#### PAR Framework Validation
- **VALIDATED** as best practice for resume contexts
- Three-component structure aligns with recruiter attention spans (6-15 seconds)
- Eliminates rambling that can occur with STAR
- Directly addresses: "What was the issue, what did you do, what changed?"

#### Modern Evolution: RAS Formula (Results-Action-Situation)
For executive resumes, **lead with results**:
> "Decreased run rate by $50M annually through process standardization, headcount reductions, and labor arbitrage"

This inverts traditional frameworks to put impact first.

#### 2025-2026 Best Practice: Action + Metric + Outcome
Modern accomplishment structure:
```
[Strong Action Verb] + [Specific Task/Project] + [Quantified Metric], resulting in [Clear Outcome]
```

Example:
> "Implemented enterprise CRM system serving 2,400 users, reducing sales cycle from 45 to 28 days and increasing win rate by 23%"

#### No Framework is Obsolete
- All three frameworks remain valid
- **Key insight**: Execution quality matters more than framework choice
- Modern approach: Framework flexibility - adapt to context

### Integration Recommendations for Resume-as-Code

1. **Architecture Validation**: PAR framework in our schema is VALIDATED
2. **Enhance Work Unit Schema** to support:
   - Problem/Challenge statement
   - Action description (with strong verb guidance)
   - Result (quantified with baseline)
3. **Add guidance system** suggesting:
   - Framework selection based on output format
   - Action verb alternatives
   - Quantification prompts

---

## RB-062: Resume Trends 2025-2026

### Key Findings

#### AI-Era Resume Writing
- ATS systems now achieve 94-97% parsing accuracy
- AI evaluates writing quality, strategic coherence, clarity
- Keyword-stuffing less effective; quality communication matters more
- Personal branding and distinctive positioning increasingly important

#### Emerging Competency Requirements
1. **Digital transformation experience** - Expected for most senior roles
2. **AI fluency** - Understanding AI implications for business
3. **Soft skills resurgence** - Transparent communication, trust-building
4. **Resilience/crisis navigation** - Demonstrated ability to lead through uncertainty
5. **DEI/ESG leadership** - Increasingly expected differentiators

#### Format Evolution
- **Results-first orientation** - Lead with metrics, not context
- **Skills-based hiring** - 90% of recruiters seek skill evidence
- **LinkedIn alignment** - Resume and LinkedIn must be consistent
- **Minimalist design** - Clean layouts outperform decorative designs

#### ATS Optimization Best Practices
- Use standard section headers: "Professional Summary", "Work Experience", "Skills"
- Consistent date formatting throughout
- Keywords from job descriptions naturally incorporated
- Single-column layouts for maximum compatibility

### Integration Recommendations for Resume-as-Code

1. **ATS Provider** implementation priorities:
   - Standard section headers
   - Consistent formatting
   - Natural keyword integration from JD analysis

2. **Plan Command** should:
   - Surface keyword coverage analysis
   - Show skill alignment with target JD
   - Highlight differentiation opportunities

3. **Future considerations**:
   - LinkedIn export consistency checking
   - AI-readability scoring
   - Personal brand coherence analysis

---

## Consolidated Recommendations

### Schema Enhancements (Epic 2)

Add to Work Unit schema:
```yaml
work_unit:
  # Existing fields...

  # NEW: Executive-level fields
  scope:
    budget_managed: "$X"
    team_size: N
    revenue_influenced: "$X"
    geographic_reach: "N regions/countries"

  impact_category:
    - financial
    - operational
    - talent
    - customer
    - organizational

  metrics:
    baseline: "description of before state"
    outcome: "quantified result"
    percentage_change: N%

  framing:
    action_verb: "spearheaded"  # Strong verb from approved list
    strategic_context: "why this mattered"
```

### Validation Rules (Epic 3)

Add quality checks:
1. Weak verb detection (managed, helped, worked on)
2. Missing quantification warning
3. Missing baseline context warning
4. Scope indicator completeness check
5. Action verb diversity check (avoid repetition)

### Template Enhancements (Epic 5)

Executive template requirements:
- 2-3 page layouts
- Results-first bullet formatting
- Scope indicators display
- Professional summary section
- Single-column ATS-safe variant

### Plan Command Enhancements (Epic 4)

Add to plan output:
- Keyword coverage analysis vs JD
- Quantification completeness score
- Action verb strength analysis
- Suggested improvements for weak Work Units

---

## Research Sources Summary

### RB-059 Sources
- Executive Career Brand guidance
- Briefcase Coach research
- Page Executive recommendations
- Career Steering 2026 trends
- LinkedIn recruiter research

### RB-060 Sources
- Career Impressions executive resume analysis
- Page Executive leadership CV guidance
- AIHR cultural transformation research
- Indeed.com leadership skills research
- Yale OCS accomplishment writing guides

### RB-061 Sources
- MIT CAPD PAR method documentation
- Resume.com STAR method guidance
- Recruiting firm comparative studies
- HR association framework recommendations
- Interview Guys framework comparisons

### RB-062 Sources
- Resume Builder 2025-2026 trends
- JobScan ATS research
- NACE recruiter surveys
- Job market evolution studies
- AI recruiting impact research

---

*Research completed by Mary (Business Analyst Agent) on 2026-01-10*
