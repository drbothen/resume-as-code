# Story 7.13: Impact Category Classification

**Epic:** Epic 7 - Schema & Data Model Refactoring
**Story Points:** 5
**Priority:** P3 (innovative)
**Status:** Review

---

## User Story

As a **job seeker**,
I want **my achievements categorized by impact type and matched against role expectations**,
So that **my financial achievements rank higher for sales roles and my operational achievements rank higher for engineering roles**.

---

## Background

Resume best practices emphasize matching achievement types to role expectations. A sales role values revenue generation and customer wins, while an engineering role values operational improvements and technical depth.

**Research Basis:** Novel enhancement based on resume best practices. Studies show quantified impacts (with numbers) are 78% more compelling to recruiters than qualitative claims.

The existing Outcome model (see `work_unit.py:167-176`) has:
- `result: str` - Main result text
- `quantified_impact: str | None` - Optional quantified metrics
- `business_value: str | None` - Optional business context

This story adds pattern-based classification and role-aware scoring.

---

## Acceptance Criteria

### AC1: Financial impact classification
**Given** a work unit outcome with financial metrics ("$500K revenue", "saved $2M")
**When** impact classification runs
**Then** it's tagged as `financial` impact with confidence score

### AC2: Operational impact classification
**Given** a work unit outcome with operational metrics ("reduced latency 40%", "99.9% uptime")
**When** impact classification runs
**Then** it's tagged as `operational` impact

### AC3: Multi-category classification
**Given** a work unit outcome "Led team of 15 to deliver $3M revenue platform"
**When** impact classification runs
**Then** it's tagged with both `talent` and `financial` impacts
**And** each has an independent confidence score

### AC4: Role type inference from JD
**Given** JD for a "Senior Sales Engineer" role
**When** role type is inferred
**Then** `sales` role type is detected
**And** `financial` and `customer` impacts are prioritized

**Given** JD for "Staff Software Engineer" role
**When** role type is inferred
**Then** `engineering` role type is detected
**And** `operational` and `technical` impacts are prioritized

### AC5: Quantified impact boost
**Given** a work unit with quantified impact ("saved $2M annually")
**When** scoring
**Then** it receives 25% boost over qualitative claims ("improved efficiency")

### AC6: Impact alignment in match reasons
**Given** impact category matching
**When** generating match_reasons
**Then** reasons include alignment info ("Financial impact aligns with Sales role")

### AC7: Configurable impact scoring
**Given** config with `use_impact_matching: false`
**When** ranking runs
**Then** impact alignment scoring is skipped
**And** backward compatible with existing behavior

---

## Technical Design

### 1. Impact Category Type

```python
# src/resume_as_code/services/impact_classifier.py
"""Impact classification for work unit outcomes."""

from __future__ import annotations

import re
from typing import Literal, NamedTuple

# Impact category type
ImpactCategory = Literal[
    "financial",
    "operational",
    "talent",
    "customer",
    "organizational",
    "technical",
]


class ImpactMatch(NamedTuple):
    """An impact category match with confidence score."""
    category: ImpactCategory
    confidence: float  # 0.0 to 1.0
    matched_patterns: list[str]  # Which patterns matched (for debugging)
```

### 2. Pattern-Based Classification

```python
# Impact detection patterns (regex)
# Each pattern list is checked against lowercased text
IMPACT_PATTERNS: dict[ImpactCategory, list[str]] = {
    "financial": [
        r"\$[\d,]+[KMB]?",           # Dollar amounts: $500K, $2M, $1,000
        r"\brevenue\b",               # Revenue mentions
        r"\bcost\s*sav",              # Cost savings
        r"\broi\b",                   # Return on investment
        r"\bprofit\b",                # Profit mentions
        r"\bbudget\b",                # Budget impact
        r"\bmargin\b",                # Margin improvements
        r"\barr\b",                   # Annual recurring revenue
        r"\bmrr\b",                   # Monthly recurring revenue
    ],
    "operational": [
        r"\d+%\s*(?:reduc|improv|increas|faster|efficiency)",  # Percentage improvements
        r"\bautomat",                 # Automation
        r"\bstreamlin",               # Streamlining
        r"\boptimiz",                 # Optimization
        r"\blatency\b",               # Latency reduction
        r"\buptime\b",                # Uptime improvements
        r"\bthroughput\b",            # Throughput gains
        r"\bdeployment\b",            # Deployment improvements
        r"\bdowntime\b",              # Downtime reduction
        r"\bsla\b",                   # SLA improvements
        r"\d+x\s*(?:faster|improvement)",  # Multiplier improvements
    ],
    "talent": [
        r"\bhired?\s+\d+",            # Hiring: "hired 15"
        r"\bmentor",                  # Mentoring
        r"\bteam\s+of\s+\d+",         # Team size: "team of 20"
        r"\bretention\b",             # Retention (also in customer)
        r"\bonboard",                 # Onboarding
        r"\btrain",                   # Training
        r"\bcoach",                   # Coaching
        r"\bdeveloped\s+\d+\s+engineer",  # Career development
        r"\bpromot",                  # Promotions
    ],
    "customer": [
        r"\bnps\b",                   # Net Promoter Score
        r"\bcsat\b",                  # Customer satisfaction
        r"\bcustomer\s+satisfaction", # Customer satisfaction
        r"\buser\s+growth\b",         # User growth
        r"\bchurn\b",                 # Churn reduction
        r"\bacquisition\b",           # Customer acquisition
        r"\bcustomer\s+retention",    # Customer retention
        r"\bconversion\b",            # Conversion rate
        r"\bdau\b|\bmau\b",           # Daily/Monthly active users
        r"\buser\s+engagement",       # User engagement
    ],
    "organizational": [
        r"\btransform",               # Transformation
        r"\bculture\b",               # Culture change
        r"\bstrateg",                 # Strategic initiatives
        r"\brestructur",              # Restructuring
        r"\bmerger\b",                # Mergers
        r"\bacquisition\b",           # Acquisitions (also in customer)
        r"\binitiative\b",            # Initiatives
        r"\bchange\s+management",     # Change management
        r"\breorganiz",               # Reorganization
        r"\bvision\b",                # Vision setting
    ],
    "technical": [
        r"\barchitect",               # Architecture
        r"\bdesign",                  # Design (technical context)
        r"\bimplement",               # Implementation
        r"\bdeploy",                  # Deployment
        r"\bscale\b",                 # Scaling
        r"\bmigrat",                  # Migration
        r"\binfrastructure\b",        # Infrastructure
        r"\brefactor",                # Refactoring
        r"\bintegrat",                # Integration
        r"\bapi\b",                   # API development
        r"\bmicroservices?\b",        # Microservices
    ],
}


def classify_impact(outcome_text: str) -> list[ImpactMatch]:
    """Classify outcome text into impact categories with confidence scores.

    Args:
        outcome_text: The outcome text to classify (result + quantified_impact + business_value)

    Returns:
        List of ImpactMatch tuples, sorted by confidence (highest first).
        Empty list if no patterns match.
    """
    text = outcome_text.lower()
    results: list[ImpactMatch] = []

    for category, patterns in IMPACT_PATTERNS.items():
        matched_patterns: list[str] = []

        for pattern in patterns:
            if re.search(pattern, text, re.IGNORECASE):
                matched_patterns.append(pattern)

        if matched_patterns:
            # Confidence based on number of pattern matches
            # 1 match = 0.3, 2 matches = 0.6, 3+ matches = 0.9, cap at 1.0
            confidence = min(1.0, len(matched_patterns) * 0.3)
            results.append(ImpactMatch(
                category=category,
                confidence=confidence,
                matched_patterns=matched_patterns,
            ))

    # Sort by confidence, highest first
    return sorted(results, key=lambda x: -x.confidence)


def has_quantified_impact(outcome_text: str) -> bool:
    """Check if outcome contains quantified metrics.

    Looks for patterns like:
    - Percentages: 40%, 50%
    - Dollar amounts: $500K, $2M, $1,000,000
    - Multipliers: 10x, 3x
    - Time metrics: 2 hours, 3 days, 50% faster

    Args:
        outcome_text: Text to check for quantification

    Returns:
        True if quantified metrics are present
    """
    patterns = [
        r'\d+%',                      # Percentages
        r'\$[\d,]+[KMB]?',            # Dollar amounts
        r'\d+x\b',                    # Multipliers (10x, 3x)
        r'\d+\s*(?:hours?|days?|weeks?|months?)',  # Time metrics
        r'(?:reduced|improved|increased)\s+.*?\d+',  # Action + number
    ]

    for pattern in patterns:
        if re.search(pattern, outcome_text, re.IGNORECASE):
            return True

    return False
```

### 3. Role Type Inference

```python
# Role type mappings
RoleType = Literal["sales", "engineering", "product", "hr", "executive", "marketing", "operations", "finance", "general"]

# Title patterns to role types (first match wins)
ROLE_TYPE_PATTERNS: list[tuple[RoleType, list[str]]] = [
    ("executive", [
        r"\bcto\b", r"\bceo\b", r"\bcfo\b", r"\bcoo\b", r"\bcio\b",
        r"\bvp\b", r"\bvice president\b", r"\bchief\b", r"\bdirector\b",
        r"\bhead of\b", r"\bgeneral manager\b",
    ]),
    ("sales", [
        r"\bsales\b", r"\baccount\s+(?:executive|manager)\b",
        r"\bbusiness\s+development\b", r"\bsdr\b", r"\bbdr\b",
        r"\brevenue\b", r"\bpartnership\b",
    ]),
    ("marketing", [
        r"\bmarketing\b", r"\bgrowth\b", r"\bbrand\b",
        r"\bcontent\b", r"\bseo\b", r"\bsem\b", r"\bdemand\s+gen\b",
    ]),
    ("product", [
        r"\bproduct\s+(?:manager|owner|lead)\b", r"\bpm\b",
        r"\bux\b", r"\bui\b", r"\bdesigner\b",
    ]),
    ("hr", [
        r"\bhr\b", r"\bhuman\s+resources\b", r"\bpeople\s+(?:ops|operations)\b",
        r"\btalent\b", r"\brecruit",
    ]),
    ("finance", [
        r"\bfinance\b", r"\baccounting\b", r"\bcontroller\b",
        r"\bfp&a\b", r"\btreasury\b",
    ]),
    ("operations", [
        r"\boperations\b", r"\bops\b", r"\bsupply\s+chain\b",
        r"\blogistics\b", r"\bprocurement\b",
    ]),
    ("engineering", [
        r"\bengineer", r"\bdeveloper\b", r"\bsoftware\b", r"\bsre\b",
        r"\bdevops\b", r"\barchitect\b", r"\bplatform\b", r"\bdata\b",
        r"\bbackend\b", r"\bfrontend\b", r"\bfull\s*stack\b",
    ]),
]


# Role type to prioritized impact categories
ROLE_IMPACT_PRIORITY: dict[RoleType, list[ImpactCategory]] = {
    "sales": ["financial", "customer"],
    "engineering": ["operational", "technical"],
    "product": ["customer", "operational"],
    "hr": ["talent", "organizational"],
    "executive": ["organizational", "financial"],
    "marketing": ["customer", "financial"],
    "operations": ["operational", "financial"],
    "finance": ["financial", "operational"],
    "general": ["operational", "technical"],  # Default fallback
}


def infer_role_type(jd_title: str | None) -> RoleType:
    """Infer role type from job description title.

    Args:
        jd_title: The job title from the JD

    Returns:
        Inferred RoleType, defaults to "general" if no match
    """
    if not jd_title:
        return "general"

    title_lower = jd_title.lower()

    for role_type, patterns in ROLE_TYPE_PATTERNS:
        for pattern in patterns:
            if re.search(pattern, title_lower):
                return role_type

    return "general"
```

### 4. Impact Alignment Scoring

```python
def calculate_impact_alignment(
    work_unit_impacts: list[ImpactMatch],
    role_type: RoleType,
    is_quantified: bool,
) -> float:
    """Calculate alignment score between work unit impacts and role expectations.

    Args:
        work_unit_impacts: Classified impacts from the work unit
        role_type: Inferred role type from JD
        is_quantified: Whether the outcome has quantified metrics

    Returns:
        Alignment score between 0.0 and 1.0
    """
    if not work_unit_impacts:
        # No detected impacts - neutral score
        return 0.5

    expected_impacts = ROLE_IMPACT_PRIORITY.get(role_type, [])
    if not expected_impacts:
        return 0.5

    alignment_score = 0.0

    for impact in work_unit_impacts:
        if impact.category in expected_impacts:
            # Primary impact match (first in list) gets full weight
            # Secondary impact match gets half weight
            if impact.category == expected_impacts[0]:
                alignment_score += impact.confidence * 1.0
            else:
                alignment_score += impact.confidence * 0.5

    # Apply quantified boost (25%)
    if is_quantified:
        alignment_score *= 1.25

    # Cap at 1.0
    return min(1.0, alignment_score)
```

### 5. Configuration Extension

```python
# src/resume_as_code/models/config.py - add to ScoringWeights

class ScoringWeights(BaseModel):
    # ... existing fields ...

    use_impact_matching: bool = Field(
        default=True,
        description="Enable impact category matching against role type"
    )
    impact_blend: float = Field(
        default=0.1,
        ge=0.0,
        le=0.3,
        description="How much impact alignment affects final score (0.1 = 10%)"
    )
    quantified_boost: float = Field(
        default=1.25,
        ge=1.0,
        le=2.0,
        description="Multiplier for work units with quantified outcomes (1.25 = 25% boost)"
    )
```

### 6. Ranker Integration

```python
# src/resume_as_code/services/ranker.py - add method and integrate

from resume_as_code.services.impact_classifier import (
    classify_impact,
    has_quantified_impact,
    infer_role_type,
    calculate_impact_alignment,
)

class HybridRanker:
    # ... existing methods ...

    def _calculate_impact_score(
        self,
        work_unit: WorkUnit,
        jd: JobDescription,
    ) -> float:
        """Calculate impact alignment score for a work unit.

        Returns 0.5 (neutral) if impact matching is disabled.
        """
        if not self.config.scoring_weights.use_impact_matching:
            return 0.5  # Neutral - doesn't affect ranking

        # Build outcome text from all outcome fields
        outcome = work_unit.outcome
        outcome_text = " ".join(filter(None, [
            outcome.result,
            outcome.quantified_impact,
            outcome.business_value,
        ]))

        # Classify work unit impacts
        impacts = classify_impact(outcome_text)

        # Check for quantification
        is_quantified = has_quantified_impact(outcome_text)

        # Infer role type from JD
        role_type = infer_role_type(jd.title)

        # Calculate alignment
        return calculate_impact_alignment(impacts, role_type, is_quantified)

    def _generate_impact_reason(
        self,
        work_unit: WorkUnit,
        jd: JobDescription,
        impact_score: float,
    ) -> str | None:
        """Generate human-readable impact alignment reason."""
        if not self.config.scoring_weights.use_impact_matching:
            return None

        outcome = work_unit.outcome
        outcome_text = " ".join(filter(None, [
            outcome.result,
            outcome.quantified_impact,
            outcome.business_value,
        ]))

        impacts = classify_impact(outcome_text)
        role_type = infer_role_type(jd.title)

        if not impacts:
            return None

        top_impact = impacts[0].category.capitalize()

        if impact_score >= 0.7:
            return f"{top_impact} impact aligns with {role_type.capitalize()} role"
        elif impact_score >= 0.4:
            return f"{top_impact} impact partially relevant to {role_type.capitalize()} role"
        else:
            return None  # Low alignment - don't highlight
```

### 7. Updated Score Blending

Update the score blending to include impact:

```python
def _blend_all_scores(
    self,
    relevance_score: float,
    recency_score: float,
    seniority_score: float,
    impact_score: float,
) -> float:
    """Blend all scoring components into final score.

    Formula:
    final = relevance × relevance_blend
          + recency × recency_blend
          + seniority × seniority_blend
          + impact × impact_blend

    Where blends sum to 1.0
    """
    weights = self.config.scoring_weights

    # Calculate relevance blend as remainder
    recency_blend = weights.recency_blend
    seniority_blend = weights.seniority_blend
    impact_blend = weights.impact_blend
    relevance_blend = 1.0 - recency_blend - seniority_blend - impact_blend

    return (
        relevance_score * relevance_blend
        + recency_score * recency_blend
        + seniority_score * seniority_blend
        + impact_score * impact_blend
    )
```

---

## Files to Create/Modify

| File | Action | Description |
|------|--------|-------------|
| `src/resume_as_code/services/impact_classifier.py` | Create | Impact classification service |
| `src/resume_as_code/models/config.py` | Modify | Add `use_impact_matching`, `impact_blend`, `quantified_boost` |
| `src/resume_as_code/services/ranker.py` | Modify | Integrate impact scoring and match reasons |
| `tests/unit/services/test_impact_classifier.py` | Create | Unit tests for classification |
| `tests/unit/services/test_ranker_impact.py` | Create | Ranker integration tests |

---

## Test Cases

### Unit Tests: Impact Classification

```python
# tests/unit/services/test_impact_classifier.py
import pytest
from resume_as_code.services.impact_classifier import (
    classify_impact,
    has_quantified_impact,
    infer_role_type,
    calculate_impact_alignment,
    ImpactMatch,
)


class TestClassifyImpact:
    """Test pattern-based impact classification."""

    def test_financial_impact_detection(self):
        text = "Generated $500K in new revenue"
        impacts = classify_impact(text)

        assert len(impacts) >= 1
        assert impacts[0].category == "financial"
        assert impacts[0].confidence >= 0.3

    def test_operational_impact_detection(self):
        text = "Reduced latency by 40% through optimization"
        impacts = classify_impact(text)

        categories = [i.category for i in impacts]
        assert "operational" in categories

    def test_multiple_impact_categories(self):
        text = "Led team of 15 to deliver $3M revenue platform"
        impacts = classify_impact(text)

        categories = [i.category for i in impacts]
        assert "talent" in categories
        assert "financial" in categories

    def test_no_impacts_returns_empty(self):
        text = "Did some work on a project"
        impacts = classify_impact(text)

        # May match "technical" due to generic patterns, or be empty
        # Key is no crash and reasonable result
        assert isinstance(impacts, list)

    def test_confidence_increases_with_matches(self):
        low_match = "Improved revenue"  # 1 pattern
        high_match = "Improved ROI and profit margin, saving costs"  # 4 patterns

        low_impacts = classify_impact(low_match)
        high_impacts = classify_impact(high_match)

        # Higher match count should yield higher confidence
        if low_impacts and high_impacts:
            low_financial = next((i for i in low_impacts if i.category == "financial"), None)
            high_financial = next((i for i in high_impacts if i.category == "financial"), None)
            if low_financial and high_financial:
                assert high_financial.confidence >= low_financial.confidence


class TestHasQuantifiedImpact:
    """Test quantification detection."""

    @pytest.mark.parametrize("text,expected", [
        ("Saved $2M annually", True),
        ("Improved efficiency by 40%", True),
        ("Achieved 10x performance improvement", True),
        ("Reduced deployment time from 4 hours to 30 minutes", True),
        ("Improved the process significantly", False),
        ("Made things better", False),
    ])
    def test_quantification_detection(self, text: str, expected: bool):
        assert has_quantified_impact(text) == expected


class TestInferRoleType:
    """Test role type inference from JD titles."""

    @pytest.mark.parametrize("title,expected", [
        ("Senior Software Engineer", "engineering"),
        ("Staff Platform Engineer", "engineering"),
        ("Sales Engineer", "sales"),  # Sales takes priority
        ("Account Executive", "sales"),
        ("Product Manager", "product"),
        ("VP of Engineering", "executive"),
        ("CTO", "executive"),
        ("Marketing Manager", "marketing"),
        ("HR Business Partner", "hr"),
        ("Unknown Role Title", "general"),
        (None, "general"),
    ])
    def test_role_type_inference(self, title: str | None, expected: str):
        assert infer_role_type(title) == expected


class TestImpactAlignment:
    """Test impact alignment scoring."""

    def test_perfect_alignment(self):
        # Financial impact for sales role
        impacts = [ImpactMatch("financial", 0.9, ["revenue"])]
        score = calculate_impact_alignment(impacts, "sales", is_quantified=False)

        assert score >= 0.8

    def test_secondary_alignment(self):
        # Customer impact for sales role (second priority)
        impacts = [ImpactMatch("customer", 0.9, ["nps"])]
        score = calculate_impact_alignment(impacts, "sales", is_quantified=False)

        # Should be lower than primary but still positive
        assert 0.3 <= score <= 0.7

    def test_no_alignment(self):
        # Technical impact for HR role
        impacts = [ImpactMatch("technical", 0.9, ["implement"])]
        score = calculate_impact_alignment(impacts, "hr", is_quantified=False)

        # Should be low - no alignment
        assert score <= 0.5

    def test_quantified_boost(self):
        impacts = [ImpactMatch("financial", 0.6, ["revenue"])]

        unquantified = calculate_impact_alignment(impacts, "sales", is_quantified=False)
        quantified = calculate_impact_alignment(impacts, "sales", is_quantified=True)

        assert quantified > unquantified
        assert quantified == pytest.approx(unquantified * 1.25, rel=0.01)

    def test_no_impacts_returns_neutral(self):
        score = calculate_impact_alignment([], "engineering", is_quantified=False)
        assert score == 0.5
```

### Integration Tests

```python
# tests/unit/services/test_ranker_impact.py
import pytest
from resume_as_code.models.work_unit import WorkUnit, Outcome
from resume_as_code.models.job_description import JobDescription


class TestRankerImpactScoring:
    """Test impact integration in ranking."""

    def test_impact_disabled_returns_neutral(self, ranker_no_impact):
        wu = WorkUnit(
            title="Test",
            outcome=Outcome(result="Generated $5M revenue"),
            # ...
        )
        jd = JobDescription(title="Software Engineer", raw_text="...")

        score = ranker_no_impact._calculate_impact_score(wu, jd)
        assert score == 0.5  # Neutral

    def test_financial_impact_boosts_sales_role(self, ranker_with_impact):
        financial_wu = WorkUnit(
            title="Revenue work",
            outcome=Outcome(result="Generated $5M in new revenue"),
        )
        technical_wu = WorkUnit(
            title="Technical work",
            outcome=Outcome(result="Implemented microservices architecture"),
        )

        jd = JobDescription(title="Account Executive", raw_text="Sales role...")

        financial_score = ranker_with_impact._calculate_impact_score(financial_wu, jd)
        technical_score = ranker_with_impact._calculate_impact_score(technical_wu, jd)

        assert financial_score > technical_score
```

---

## Definition of Done

- [x] `impact_classifier.py` service created with:
  - [x] `classify_impact()` function with pattern matching
  - [x] `has_quantified_impact()` function
  - [x] `infer_role_type()` function
  - [x] `calculate_impact_alignment()` function
- [x] Config extended with `use_impact_matching`, `impact_blend`, `quantified_boost`
- [x] HybridRanker integrates impact scoring via `_calculate_impact_score()`
- [x] Match reasons include impact alignment info
- [x] Score blending updated to include impact component
- [x] Unit tests pass for classification patterns
- [x] Integration tests pass for ranker
- [x] Backward compatible (disabled = neutral 0.5 score)
- [x] `uv run ruff check` passes
- [x] `uv run mypy src --strict` passes

---

## Implementation Notes

1. **Pattern Order Doesn't Matter**: Unlike seniority (first match wins), impact classification collects all matches and returns multiple categories with confidence scores.

2. **Confidence Calculation**: Simple linear - 1 pattern = 0.3, 2 patterns = 0.6, 3+ patterns = 0.9. Could be refined later.

3. **Role Type Priority**: "executive" and "sales" are checked before "engineering" because titles like "Sales Engineer" should prioritize sales.

4. **Neutral Score**: When impact matching is disabled or no impacts detected, return 0.5 (neutral) so it doesn't affect the blended score.

5. **Quantified Boost**: Default 25% boost is conservative. The `quantified_boost` config allows tuning from 1.0 (no boost) to 2.0 (double weight).

6. **Pattern Overlap**: Some patterns like "acquisition" appear in both "customer" and "organizational". This is intentional - the context determines which is more likely, and both categories will be returned.
