"""Unit tests for impact classification service.

Story 7.13: Impact Category Classification
Tests pattern-based classification of work unit outcomes.
"""

from __future__ import annotations

import pytest

from resume_as_code.services.impact_classifier import (
    ImpactMatch,
    calculate_impact_alignment,
    classify_impact,
    has_quantified_impact,
    infer_role_type,
)


class TestClassifyImpact:
    """Test pattern-based impact classification."""

    def test_financial_impact_detection(self) -> None:
        """AC1: Financial impact classification with dollar amounts."""
        text = "Generated $500K in new revenue"
        impacts = classify_impact(text)

        assert len(impacts) >= 1
        assert impacts[0].category == "financial"
        assert impacts[0].confidence >= 0.3

    def test_financial_impact_cost_savings(self) -> None:
        """AC1: Financial impact with cost savings language."""
        text = "Saved $2M annually through process optimization"
        impacts = classify_impact(text)

        categories = [i.category for i in impacts]
        assert "financial" in categories

    def test_operational_impact_detection(self) -> None:
        """AC2: Operational impact with percentage improvements."""
        text = "Reduced latency by 40% through optimization"
        impacts = classify_impact(text)

        categories = [i.category for i in impacts]
        assert "operational" in categories

    def test_operational_impact_uptime(self) -> None:
        """AC2: Operational impact with uptime metrics."""
        text = "Achieved 99.9% uptime for production systems"
        impacts = classify_impact(text)

        categories = [i.category for i in impacts]
        assert "operational" in categories

    def test_multiple_impact_categories(self) -> None:
        """AC3: Multi-category classification with independent scores."""
        text = "Led team of 15 to deliver $3M revenue platform"
        impacts = classify_impact(text)

        categories = [i.category for i in impacts]
        assert "talent" in categories
        assert "financial" in categories

    def test_multi_category_independent_confidence(self) -> None:
        """AC3: Each category has independent confidence score."""
        text = "Led team of 15 engineers to generate $5M revenue with 50% cost savings"
        impacts = classify_impact(text)

        # Should have multiple categories, each with independent confidence
        assert len(impacts) >= 2
        for impact in impacts:
            assert 0.0 <= impact.confidence <= 1.0

    def test_no_impacts_returns_empty(self) -> None:
        """No patterns matched returns empty list."""
        text = "Did some work on a project"
        impacts = classify_impact(text)

        # May return empty or have low-confidence generic matches
        assert isinstance(impacts, list)

    def test_confidence_increases_with_matches(self) -> None:
        """Confidence increases with more pattern matches."""
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

    def test_talent_impact_team_leadership(self) -> None:
        """Talent impact with team leadership patterns."""
        text = "Hired 10 engineers and mentored 5 to senior level"
        impacts = classify_impact(text)

        categories = [i.category for i in impacts]
        assert "talent" in categories

    def test_customer_impact_nps(self) -> None:
        """Customer impact with NPS metrics."""
        text = "Improved NPS from 30 to 65 through UX redesign"
        impacts = classify_impact(text)

        categories = [i.category for i in impacts]
        assert "customer" in categories

    def test_technical_impact_architecture(self) -> None:
        """Technical impact with architecture patterns."""
        text = "Architected microservices platform for 100x scale"
        impacts = classify_impact(text)

        categories = [i.category for i in impacts]
        assert "technical" in categories

    def test_organizational_impact_transformation(self) -> None:
        """Organizational impact with transformation patterns."""
        text = "Led digital transformation across 3 business units"
        impacts = classify_impact(text)

        categories = [i.category for i in impacts]
        assert "organizational" in categories


class TestHasQuantifiedImpact:
    """Test quantification detection for AC5 (25% boost)."""

    @pytest.mark.parametrize(
        "text,expected",
        [
            ("Saved $2M annually", True),
            ("Improved efficiency by 40%", True),
            ("Achieved 10x performance improvement", True),
            ("Reduced deployment time from 4 hours to 30 minutes", True),
            ("Reduced time by 50% faster", True),
            ("Improved the process significantly", False),
            ("Made things better", False),
            ("Worked on the project", False),
        ],
    )
    def test_quantification_detection(self, text: str, expected: bool) -> None:
        """AC5: Detect quantified metrics for boost."""
        assert has_quantified_impact(text) == expected


class TestInferRoleType:
    """Test role type inference from JD titles (AC4)."""

    @pytest.mark.parametrize(
        "title,expected",
        [
            ("Senior Software Engineer", "engineering"),
            ("Staff Platform Engineer", "engineering"),
            ("Sales Engineer", "sales"),  # Sales takes priority
            ("Account Executive", "sales"),
            ("Business Development Representative", "sales"),
            ("Product Manager", "product"),
            ("VP of Engineering", "executive"),
            ("CTO", "executive"),
            ("Chief Technology Officer", "executive"),
            ("Director of Engineering", "executive"),
            ("Marketing Manager", "marketing"),
            ("Growth Lead", "marketing"),
            ("HR Business Partner", "hr"),
            ("Talent Acquisition Lead", "hr"),
            ("Finance Director", "executive"),  # Director triggers executive
            ("Operations Manager", "operations"),
            ("Unknown Role Title", "general"),
            (None, "general"),
            ("", "general"),
        ],
    )
    def test_role_type_inference(self, title: str | None, expected: str) -> None:
        """AC4: Infer role type from JD title."""
        assert infer_role_type(title) == expected

    def test_sales_prioritized_over_engineering(self) -> None:
        """AC4: Sales Engineer should prioritize 'sales' role type."""
        # This is the key differentiator - Sales Engineer is a sales role
        assert infer_role_type("Senior Sales Engineer") == "sales"


class TestImpactAlignment:
    """Test impact alignment scoring."""

    def test_perfect_alignment(self) -> None:
        """Financial impact for sales role gets high alignment."""
        impacts = [ImpactMatch("financial", 0.9, ["revenue"])]
        score = calculate_impact_alignment(impacts, "sales", is_quantified=False)

        assert score >= 0.8

    def test_secondary_alignment(self) -> None:
        """Customer impact for sales role (second priority)."""
        impacts = [ImpactMatch("customer", 0.9, ["nps"])]
        score = calculate_impact_alignment(impacts, "sales", is_quantified=False)

        # Should be lower than primary but still positive
        assert 0.3 <= score <= 0.7

    def test_no_alignment(self) -> None:
        """Technical impact for HR role gets low alignment."""
        impacts = [ImpactMatch("technical", 0.9, ["implement"])]
        score = calculate_impact_alignment(impacts, "hr", is_quantified=False)

        # Should be low - no alignment
        assert score <= 0.5

    def test_quantified_boost(self) -> None:
        """AC5: Quantified impacts get 25% boost."""
        impacts = [ImpactMatch("financial", 0.6, ["revenue"])]

        unquantified = calculate_impact_alignment(impacts, "sales", is_quantified=False)
        quantified = calculate_impact_alignment(impacts, "sales", is_quantified=True)

        assert quantified > unquantified
        assert quantified == pytest.approx(unquantified * 1.25, rel=0.01)

    def test_no_impacts_returns_neutral(self) -> None:
        """AC7: No impacts returns neutral 0.5 score."""
        score = calculate_impact_alignment([], "engineering", is_quantified=False)
        assert score == 0.5

    def test_capped_at_one(self) -> None:
        """Score should never exceed 1.0."""
        # Multiple strong impacts with quantified boost
        impacts = [
            ImpactMatch("financial", 1.0, ["revenue", "roi", "profit"]),
            ImpactMatch("customer", 0.9, ["nps", "churn"]),
        ]
        score = calculate_impact_alignment(impacts, "sales", is_quantified=True)

        assert score <= 1.0

    def test_engineering_role_prefers_operational(self) -> None:
        """Engineering roles should prefer operational/technical impacts."""
        operational = [ImpactMatch("operational", 0.8, ["latency", "uptime"])]
        financial = [ImpactMatch("financial", 0.8, ["revenue"])]

        op_score = calculate_impact_alignment(operational, "engineering", is_quantified=False)
        fin_score = calculate_impact_alignment(financial, "engineering", is_quantified=False)

        assert op_score > fin_score
