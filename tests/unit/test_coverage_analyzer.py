"""Tests for coverage analyzer service."""

from __future__ import annotations

import pytest


@pytest.fixture
def sample_work_units_for_coverage() -> list[dict]:
    """Sample Work Units with various skills for coverage testing."""
    return [
        {
            "id": "wu-2026-01-10-python-api",
            "title": "Built Python REST API",
            "problem": {"statement": "Needed scalable API"},
            "actions": ["Designed API with FastAPI"],
            "outcome": {"result": "Handles 10K requests"},
            "tags": ["python", "api", "fastapi"],
            "skills_demonstrated": ["python", "api-design"],
        },
        {
            "id": "wu-2025-06-15-java-migration",
            "title": "Java Service Migration",
            "problem": {"statement": "Legacy Java issues"},
            "actions": ["Upgraded to Java 17"],
            "outcome": {"result": "30% memory reduction"},
            "tags": ["java", "spring"],
            "skills_demonstrated": ["java"],
        },
        {
            "id": "wu-2024-03-20-kubernetes",
            "title": "Kubernetes Deployment",
            "problem": {"statement": "Manual deployments"},
            "actions": ["Set up K8s cluster"],
            "outcome": {"result": "80% faster deployments"},
            "tags": ["kubernetes", "devops"],
            "skills_demonstrated": ["kubernetes", "devops"],
        },
    ]


class TestCoverageLevel:
    """Tests for CoverageLevel enum."""

    def test_coverage_level_values(self):
        """CoverageLevel has strong, weak, and gap values."""
        from resume_as_code.services.coverage_analyzer import CoverageLevel

        assert CoverageLevel.STRONG.value == "strong"
        assert CoverageLevel.WEAK.value == "weak"
        assert CoverageLevel.GAP.value == "gap"


class TestSkillCoverage:
    """Tests for SkillCoverage dataclass."""

    def test_skill_coverage_symbol_strong(self):
        """AC2: Strong coverage shows ✓ symbol."""
        from resume_as_code.services.coverage_analyzer import (
            CoverageLevel,
            SkillCoverage,
        )

        coverage = SkillCoverage(
            skill="python",
            level=CoverageLevel.STRONG,
            matching_work_units=["wu-2026-01-10-python-api"],
        )
        assert coverage.symbol == "✓"

    def test_skill_coverage_symbol_weak(self):
        """AC3: Weak coverage shows △ symbol."""
        from resume_as_code.services.coverage_analyzer import (
            CoverageLevel,
            SkillCoverage,
        )

        coverage = SkillCoverage(
            skill="fastapi",
            level=CoverageLevel.WEAK,
            matching_work_units=["wu-2026-01-10-python-api"],
        )
        assert coverage.symbol == "△"

    def test_skill_coverage_symbol_gap(self):
        """AC4: Gap coverage shows ✗ symbol."""
        from resume_as_code.services.coverage_analyzer import (
            CoverageLevel,
            SkillCoverage,
        )

        coverage = SkillCoverage(
            skill="rust",
            level=CoverageLevel.GAP,
            matching_work_units=[],
        )
        assert coverage.symbol == "✗"

    def test_skill_coverage_color_mapping(self):
        """Colors mapped correctly: strong=green, weak=yellow, gap=red."""
        from resume_as_code.services.coverage_analyzer import (
            CoverageLevel,
            SkillCoverage,
        )

        strong = SkillCoverage("python", CoverageLevel.STRONG, ["wu-1"])
        weak = SkillCoverage("api", CoverageLevel.WEAK, ["wu-1"])
        gap = SkillCoverage("rust", CoverageLevel.GAP, [])

        assert strong.color == "green"
        assert weak.color == "yellow"
        assert gap.color == "red"


class TestCoverageReport:
    """Tests for CoverageReport dataclass."""

    def test_coverage_report_counts(self):
        """CoverageReport correctly counts strong, weak, and gap items."""
        from resume_as_code.services.coverage_analyzer import (
            CoverageLevel,
            CoverageReport,
            SkillCoverage,
        )

        items = [
            SkillCoverage("python", CoverageLevel.STRONG, ["wu-1"]),
            SkillCoverage("java", CoverageLevel.STRONG, ["wu-2"]),
            SkillCoverage("api", CoverageLevel.WEAK, ["wu-1"]),
            SkillCoverage("rust", CoverageLevel.GAP, []),
            SkillCoverage("go", CoverageLevel.GAP, []),
        ]
        report = CoverageReport(items=items)

        assert report.strong_count == 2
        assert report.weak_count == 1
        assert report.gap_count == 2

    def test_coverage_percentage_all_strong(self):
        """100% coverage when all skills are strongly covered."""
        from resume_as_code.services.coverage_analyzer import (
            CoverageLevel,
            CoverageReport,
            SkillCoverage,
        )

        items = [
            SkillCoverage("python", CoverageLevel.STRONG, ["wu-1"]),
            SkillCoverage("java", CoverageLevel.STRONG, ["wu-2"]),
        ]
        report = CoverageReport(items=items)

        assert report.coverage_percentage == 100.0

    def test_coverage_percentage_mixed(self):
        """Weak skills count as 0.5 coverage."""
        from resume_as_code.services.coverage_analyzer import (
            CoverageLevel,
            CoverageReport,
            SkillCoverage,
        )

        # 1 strong (1.0) + 1 weak (0.5) + 1 gap (0) = 1.5 / 3 = 50%
        items = [
            SkillCoverage("python", CoverageLevel.STRONG, ["wu-1"]),
            SkillCoverage("api", CoverageLevel.WEAK, ["wu-1"]),
            SkillCoverage("rust", CoverageLevel.GAP, []),
        ]
        report = CoverageReport(items=items)

        assert report.coverage_percentage == 50.0

    def test_coverage_percentage_empty(self):
        """Empty report returns 100% (no requirements = fully covered)."""
        from resume_as_code.services.coverage_analyzer import CoverageReport

        report = CoverageReport(items=[])
        assert report.coverage_percentage == 100.0


class TestAnalyzeCoverage:
    """Tests for analyze_coverage function."""

    def test_strong_match_in_tags(self, sample_work_units_for_coverage: list[dict]):
        """AC2: Skill in Work Unit tags = strong match."""
        from resume_as_code.services.coverage_analyzer import (
            CoverageLevel,
            analyze_coverage,
        )

        jd_skills = ["python"]  # In tags of wu-2026-01-10-python-api
        report = analyze_coverage(jd_skills, sample_work_units_for_coverage)

        assert len(report.items) == 1
        assert report.items[0].skill == "python"
        assert report.items[0].level == CoverageLevel.STRONG
        assert "wu-2026-01-10-python-api" in report.items[0].matching_work_units

    def test_strong_match_in_skills_demonstrated(self, sample_work_units_for_coverage: list[dict]):
        """AC2: Skill in skills_demonstrated = strong match."""
        from resume_as_code.services.coverage_analyzer import (
            CoverageLevel,
            analyze_coverage,
        )

        jd_skills = ["api-design"]  # In skills_demonstrated
        report = analyze_coverage(jd_skills, sample_work_units_for_coverage)

        assert len(report.items) == 1
        assert report.items[0].level == CoverageLevel.STRONG

    def test_weak_match_in_text(self, sample_work_units_for_coverage: list[dict]):
        """AC3: Skill mentioned in text but not tags/skills = weak match."""
        from resume_as_code.services.coverage_analyzer import (
            CoverageLevel,
            analyze_coverage,
        )

        jd_skills = ["REST"]  # In title "Built Python REST API" but not tags
        report = analyze_coverage(jd_skills, sample_work_units_for_coverage)

        assert len(report.items) == 1
        assert report.items[0].level == CoverageLevel.WEAK
        assert "wu-2026-01-10-python-api" in report.items[0].matching_work_units

    def test_gap_no_match(self, sample_work_units_for_coverage: list[dict]):
        """AC4: Skill not found anywhere = gap."""
        from resume_as_code.services.coverage_analyzer import (
            CoverageLevel,
            analyze_coverage,
        )

        jd_skills = ["rust"]  # Not in any Work Unit
        report = analyze_coverage(jd_skills, sample_work_units_for_coverage)

        assert len(report.items) == 1
        assert report.items[0].skill == "rust"
        assert report.items[0].level == CoverageLevel.GAP
        assert report.items[0].matching_work_units == []

    def test_multiple_skills_mixed_coverage(self, sample_work_units_for_coverage: list[dict]):
        """AC1: Multiple skills with different coverage levels."""
        from resume_as_code.services.coverage_analyzer import (
            CoverageLevel,
            analyze_coverage,
        )

        jd_skills = ["python", "kubernetes", "REST", "rust", "go"]
        report = analyze_coverage(jd_skills, sample_work_units_for_coverage)

        assert len(report.items) == 5

        # Map skills to coverage levels
        coverage_map = {item.skill: item.level for item in report.items}

        assert coverage_map["python"] == CoverageLevel.STRONG  # In tags
        assert coverage_map["kubernetes"] == CoverageLevel.STRONG  # In tags
        assert coverage_map["REST"] == CoverageLevel.WEAK  # In text only
        assert coverage_map["rust"] == CoverageLevel.GAP  # Not found
        assert coverage_map["go"] == CoverageLevel.GAP  # Not found

    def test_case_insensitive_matching(self, sample_work_units_for_coverage: list[dict]):
        """Skill matching is case-insensitive."""
        from resume_as_code.services.coverage_analyzer import (
            CoverageLevel,
            analyze_coverage,
        )

        jd_skills = ["PYTHON", "Python", "python"]
        report = analyze_coverage(jd_skills, sample_work_units_for_coverage)

        # All variations should match
        for item in report.items:
            assert item.level == CoverageLevel.STRONG

    def test_empty_skills_returns_empty_report(self, sample_work_units_for_coverage: list[dict]):
        """Empty JD skills returns empty report."""
        from resume_as_code.services.coverage_analyzer import analyze_coverage

        report = analyze_coverage([], sample_work_units_for_coverage)
        assert report.items == []

    def test_empty_work_units_all_gaps(self):
        """No Work Units = all skills are gaps."""
        from resume_as_code.services.coverage_analyzer import (
            CoverageLevel,
            analyze_coverage,
        )

        jd_skills = ["python", "java"]
        report = analyze_coverage(jd_skills, [])

        assert len(report.items) == 2
        assert all(item.level == CoverageLevel.GAP for item in report.items)

    def test_multiple_work_units_match_same_skill(self, sample_work_units_for_coverage: list[dict]):
        """AC2: Multiple Work Units matching same skill are all listed."""
        from resume_as_code.services.coverage_analyzer import analyze_coverage

        jd_skills = ["devops"]  # In wu-kubernetes
        report = analyze_coverage(jd_skills, sample_work_units_for_coverage)

        assert len(report.items) == 1
        # Should include the kubernetes work unit that has devops tag
        assert "wu-2024-03-20-kubernetes" in report.items[0].matching_work_units

    def test_dict_format_skills_demonstrated(self):
        """Skills in dict format {"name": "skill"} are matched correctly."""
        from resume_as_code.services.coverage_analyzer import (
            CoverageLevel,
            analyze_coverage,
        )

        # Work Unit with dict-format skills_demonstrated
        work_units = [
            {
                "id": "wu-dict-skills",
                "title": "Project with dict skills",
                "problem": {"statement": "Test problem"},
                "actions": ["Did something"],
                "outcome": {"result": "Success"},
                "tags": [],
                "skills_demonstrated": [
                    {"name": "python", "level": "expert"},
                    {"name": "docker", "level": "intermediate"},
                ],
            }
        ]

        jd_skills = ["python", "docker", "rust"]
        report = analyze_coverage(jd_skills, work_units)

        # Map results for easier assertion
        coverage_map = {item.skill: item for item in report.items}

        # python and docker should be strong matches (in skills_demonstrated)
        assert coverage_map["python"].level == CoverageLevel.STRONG
        assert coverage_map["docker"].level == CoverageLevel.STRONG
        # rust should be a gap
        assert coverage_map["rust"].level == CoverageLevel.GAP


class TestCoverageReportSerialization:
    """Tests for coverage report JSON serialization."""

    def test_coverage_report_to_dict(self):
        """CoverageReport can be serialized to dict for JSON output."""
        from resume_as_code.services.coverage_analyzer import (
            CoverageLevel,
            CoverageReport,
            SkillCoverage,
        )

        items = [
            SkillCoverage("python", CoverageLevel.STRONG, ["wu-1", "wu-2"]),
            SkillCoverage("rust", CoverageLevel.GAP, []),
        ]
        report = CoverageReport(items=items)

        data = report.to_dict()

        assert "items" in data
        assert "coverage_percentage" in data
        assert "strong_count" in data
        assert "weak_count" in data
        assert "gap_count" in data
        assert data["strong_count"] == 1
        assert data["gap_count"] == 1

    def test_skill_coverage_to_dict(self):
        """SkillCoverage can be serialized to dict."""
        from resume_as_code.services.coverage_analyzer import (
            CoverageLevel,
            SkillCoverage,
        )

        coverage = SkillCoverage("python", CoverageLevel.STRONG, ["wu-1"])
        data = coverage.to_dict()

        assert data["skill"] == "python"
        assert data["level"] == "strong"
        assert data["symbol"] == "✓"
        assert data["matching_work_units"] == ["wu-1"]
