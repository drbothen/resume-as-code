"""Tests for SkillCurator service."""

from __future__ import annotations

import pytest

from resume_as_code.models.skill_entry import SkillEntry
from resume_as_code.services.skill_curator import CurationResult, SkillCurator
from resume_as_code.services.skill_registry import SkillRegistry


class TestSkillCuratorDeduplication:
    """Tests for case-insensitive deduplication (AC #1)."""

    def test_deduplication_case_insensitive(self) -> None:
        """Should deduplicate skills case-insensitively."""
        curator = SkillCurator()
        result = curator.curate({"AWS", "aws", "Aws"})

        assert len(result.included) == 1
        assert result.included[0] in ["AWS", "aws", "Aws"]

    def test_prefers_title_case_over_lowercase(self) -> None:
        """Should prefer title case when deduplicating."""
        curator = SkillCurator()
        result = curator.curate({"python", "Python"})

        assert result.included[0] == "Python"

    def test_prefers_title_case_over_uppercase(self) -> None:
        """Should prefer title case over all uppercase."""
        curator = SkillCurator()
        result = curator.curate({"PYTHON", "Python"})

        assert result.included[0] == "Python"

    def test_prefers_uppercase_over_lowercase(self) -> None:
        """Should prefer uppercase over lowercase when no title case."""
        curator = SkillCurator()
        result = curator.curate({"aws", "AWS"})

        # AWS is uppercase, should be preferred over lowercase aws
        assert result.included[0] == "AWS"

    def test_deduplication_with_mixed_cases(self) -> None:
        """Should deduplicate ['AWS', 'aws', 'Python', 'python', 'Terraform']."""
        curator = SkillCurator()
        result = curator.curate({"AWS", "aws", "Python", "python", "Terraform"})

        assert len(result.included) == 3
        # Check each skill appears exactly once
        lower_included = [s.lower() for s in result.included]
        assert lower_included.count("aws") == 1
        assert lower_included.count("python") == 1
        assert lower_included.count("terraform") == 1

    def test_deduplication_hyphen_vs_space(self) -> None:
        """Should deduplicate hyphenated tags with spaced skills.

        Tags like 'business-development' should dedupe with skills like
        'Business Development' since they represent the same skill.
        """
        curator = SkillCurator()
        result = curator.curate({"business-development", "Business Development"})

        assert len(result.included) == 1
        # Should prefer title case spaced version
        assert result.included[0] == "Business Development"

    def test_deduplication_hyphen_multiple_words(self) -> None:
        """Should dedupe multi-hyphen tags with multi-word skills."""
        curator = SkillCurator()
        result = curator.curate({"machine-learning-ops", "Machine Learning Ops"})

        assert len(result.included) == 1
        assert result.included[0] == "Machine Learning Ops"

    def test_hyphenated_acronyms_uppercased(self) -> None:
        """Short words (<=3 chars) in hyphenated strings should be uppercased."""
        curator = SkillCurator()
        result = curator.curate({"ci-cd"})

        assert len(result.included) == 1
        assert result.included[0] == "CI CD"

    def test_hyphenated_mixed_acronym_and_word(self) -> None:
        """Hyphenated strings with mixed acronyms and words."""
        curator = SkillCurator()
        result = curator.curate({"aws-lambda", "api-gateway", "ot-security"})

        assert len(result.included) == 3
        assert "AWS Lambda" in result.included
        assert "API Gateway" in result.included
        assert "OT Security" in result.included

    def test_non_hyphenated_acronyms_preserved(self) -> None:
        """Non-hyphenated acronyms should pass through unchanged."""
        curator = SkillCurator()
        result = curator.curate({"AWS", "API", "CI/CD"})

        assert "AWS" in result.included
        assert "API" in result.included
        assert "CI/CD" in result.included

    def test_lowercase_words_title_cased(self) -> None:
        """All-lowercase words longer than 3 chars should be title-cased."""
        curator = SkillCurator()
        result = curator.curate({"compliance", "consulting", "python"})

        assert "Compliance" in result.included
        assert "Consulting" in result.included
        assert "Python" in result.included

    def test_short_lowercase_words_unchanged(self) -> None:
        """Short lowercase words (<=3 chars) should pass through unchanged (likely acronyms)."""
        curator = SkillCurator()
        result = curator.curate({"aws", "k8s", "sql"})

        # Short lowercase words pass through unchanged
        # (deduplication would prefer uppercase versions if both exist)
        assert "aws" in result.included
        assert "k8s" in result.included
        assert "sql" in result.included


class TestSkillCuratorEmptyStrings:
    """Tests for empty/whitespace string handling."""

    def test_empty_strings_filtered(self) -> None:
        """Empty strings should not appear in results."""
        curator = SkillCurator(max_count=15)
        result = curator.curate({"", "Python", "Java"})

        assert "" not in result.included
        assert len(result.included) == 2

    def test_whitespace_only_strings_filtered(self) -> None:
        """Whitespace-only strings should not appear in results."""
        curator = SkillCurator(max_count=15)
        result = curator.curate({"  ", "\t", "\n", "Python"})

        assert "  " not in result.included
        assert "\t" not in result.included
        assert "\n" not in result.included
        assert len(result.included) == 1
        assert result.included[0] == "Python"

    def test_empty_and_valid_mixed(self) -> None:
        """Should handle mix of empty, whitespace, and valid skills."""
        curator = SkillCurator(max_count=15)
        result = curator.curate({"", "  ", "Python", "Java", "\t"})

        assert len(result.included) == 2
        assert "Python" in result.included
        assert "Java" in result.included


class TestSkillCuratorMaxLimit:
    """Tests for max_display limiting (AC #2, #5)."""

    def test_max_display_limit(self) -> None:
        """Should limit to max_count skills."""
        curator = SkillCurator(max_count=3)
        result = curator.curate({"A", "B", "C", "D", "E"})

        assert len(result.included) == 3
        assert len(result.excluded) == 2

    def test_default_max_display_is_15(self) -> None:
        """Default max_count should be 15."""
        curator = SkillCurator()
        skills = {f"Skill{i}" for i in range(20)}
        result = curator.curate(skills)

        assert len(result.included) == 15
        assert len(result.excluded) == 5

    def test_excluded_skills_have_exceeded_reason(self) -> None:
        """Excluded skills due to limit should have 'exceeded_max_display' reason."""
        curator = SkillCurator(max_count=2)
        result = curator.curate({"A", "B", "C", "D"})

        exceeded_skills = [e for e in result.excluded if e[1] == "exceeded_max_display"]
        assert len(exceeded_skills) == 2


class TestSkillCuratorJDPrioritization:
    """Tests for JD keyword prioritization (AC #3)."""

    def test_jd_keyword_prioritization(self) -> None:
        """Should prioritize JD-matching skills."""
        curator = SkillCurator(max_count=3)
        result = curator.curate(
            {"Python", "Java", "Ruby", "Go"},
            jd_keywords={"python", "go"},
        )

        # Python and Go should be in top positions (JD matches)
        top_two_lower = [s.lower() for s in result.included[:2]]
        assert "python" in top_two_lower
        assert "go" in top_two_lower

    def test_jd_skills_ordered_by_relevance_not_alphabetically(self) -> None:
        """Skills should be ordered by JD relevance, not alphabetically."""
        curator = SkillCurator(max_count=4)
        result = curator.curate(
            {"Alpha", "Beta", "Gamma", "Delta"},
            jd_keywords={"gamma", "beta"},
        )

        # JD-matching skills should come first, regardless of alphabetical order
        jd_matching = result.included[:2]
        jd_matching_lower = [s.lower() for s in jd_matching]
        assert "gamma" in jd_matching_lower or "beta" in jd_matching_lower

    def test_skills_without_jd_keywords(self) -> None:
        """Should still work without JD keywords."""
        curator = SkillCurator()
        result = curator.curate({"Python", "Java", "Go"})

        assert len(result.included) == 3


class TestSkillCuratorExcludeList:
    """Tests for exclude list filtering (AC #4)."""

    def test_exclude_list(self) -> None:
        """Should exclude configured skills."""
        curator = SkillCurator(exclude=["PHP", "jQuery"])
        result = curator.curate({"Python", "PHP", "JavaScript", "jQuery"})

        assert "PHP" not in result.included
        assert "jQuery" not in result.included
        assert "Python" in result.included
        assert "JavaScript" in result.included

    def test_exclude_list_case_insensitive(self) -> None:
        """Exclude list should be case-insensitive."""
        curator = SkillCurator(exclude=["php", "jquery"])
        result = curator.curate({"Python", "PHP", "JavaScript", "jQuery"})

        assert "PHP" not in result.included
        assert "jQuery" not in result.included

    def test_excluded_skills_have_config_exclude_reason(self) -> None:
        """Excluded skills from config should have 'config_exclude' reason."""
        curator = SkillCurator(exclude=["PHP", "jQuery"])
        result = curator.curate({"Python", "PHP", "JavaScript", "jQuery"})

        config_excluded = [e for e in result.excluded if e[1] == "config_exclude"]
        assert len(config_excluded) == 2

    def test_exclude_list_never_appears(self) -> None:
        """Excluded skills should never appear regardless of JD relevance."""
        curator = SkillCurator(exclude=["PHP"])
        result = curator.curate(
            {"Python", "PHP"},
            jd_keywords={"php"},  # PHP mentioned in JD
        )

        # PHP should still be excluded even though it's in JD
        assert "PHP" not in result.included


class TestSkillCuratorPrioritize:
    """Tests for prioritize list."""

    def test_prioritize_list(self) -> None:
        """Should put prioritized skills first."""
        curator = SkillCurator(prioritize=["Kubernetes"])
        result = curator.curate({"Python", "Java", "Kubernetes", "Docker"})

        assert result.included[0] == "Kubernetes"

    def test_prioritize_multiple_skills(self) -> None:
        """Multiple prioritized skills should all come first."""
        curator = SkillCurator(prioritize=["Kubernetes", "Docker"])
        result = curator.curate({"Python", "Java", "Kubernetes", "Docker", "Go"})

        # Both Kubernetes and Docker should be in top 2
        top_two = result.included[:2]
        assert "Kubernetes" in top_two
        assert "Docker" in top_two

    def test_prioritize_over_jd_keywords(self) -> None:
        """Prioritized skills should rank above JD keywords."""
        curator = SkillCurator(prioritize=["Terraform"])
        result = curator.curate(
            {"Python", "Terraform", "Go"},
            jd_keywords={"python", "go"},
        )

        # Terraform should be first even though Python and Go are in JD
        assert result.included[0] == "Terraform"


class TestSkillCuratorStats:
    """Tests for curation statistics."""

    def test_stats_tracking(self) -> None:
        """Should track curation statistics."""
        curator = SkillCurator(max_count=2, exclude=["PHP"])
        result = curator.curate({"Python", "python", "PHP", "Java", "Go"})

        assert result.stats["total_raw"] == 5
        assert result.stats["after_dedup"] == 4  # Python deduped
        assert result.stats["after_filter"] == 3  # PHP excluded
        assert result.stats["included"] == 2  # max_count
        assert result.stats["excluded"] == 2  # 1 PHP + 1 exceeded limit


class TestCurationResult:
    """Tests for CurationResult dataclass."""

    def test_curation_result_structure(self) -> None:
        """CurationResult should have correct structure."""
        result = CurationResult(
            included=["Python", "Java"],
            excluded=[("PHP", "config_exclude")],
            stats={"total_raw": 3},
        )

        assert result.included == ["Python", "Java"]
        assert result.excluded == [("PHP", "config_exclude")]
        assert result.stats == {"total_raw": 3}


@pytest.fixture
def skill_registry() -> SkillRegistry:
    """Create a test skill registry."""
    entries = [
        SkillEntry(canonical="Kubernetes", aliases=["k8s", "kube"]),
        SkillEntry(canonical="TypeScript", aliases=["ts"]),
        SkillEntry(canonical="Python", aliases=["py", "python3"]),
        SkillEntry(
            canonical="Amazon Web Services",
            aliases=["aws", "amazon aws"],
            category="cloud",
        ),
        SkillEntry(canonical="JavaScript", aliases=["js", "ecmascript"]),
    ]
    return SkillRegistry(entries)


class TestSkillCuratorWithRegistry:
    """Tests for SkillCurator integration with SkillRegistry (Story 7.4)."""

    def test_curator_normalizes_alias_to_canonical(self, skill_registry: SkillRegistry) -> None:
        """Alias should normalize to canonical name (AC #1, #3)."""
        curator = SkillCurator(registry=skill_registry)
        result = curator.curate({"k8s", "py"})

        assert "Kubernetes" in result.included
        assert "Python" in result.included
        assert "k8s" not in result.included
        assert "py" not in result.included

    def test_curator_normalizes_multiple_aliases_to_same_canonical(
        self, skill_registry: SkillRegistry
    ) -> None:
        """Multiple aliases for same skill should dedupe to one canonical name (AC #5)."""
        curator = SkillCurator(registry=skill_registry)
        result = curator.curate({"k8s", "kube", "Kubernetes"})

        assert result.included.count("Kubernetes") == 1
        assert len(result.included) == 1

    def test_curator_passthrough_unknown_skill(self, skill_registry: SkillRegistry) -> None:
        """Unknown skill passes through unchanged (AC #4)."""
        curator = SkillCurator(registry=skill_registry)
        result = curator.curate({"CustomFramework", "k8s"})

        assert "CustomFramework" in result.included
        assert "Kubernetes" in result.included

    def test_curator_jd_matches_via_alias_expansion(self, skill_registry: SkillRegistry) -> None:
        """JD keyword matches via alias expansion (AC #6)."""
        curator = SkillCurator(registry=skill_registry, max_count=3)
        # JD has "Kubernetes", work unit has "k8s" - should match and be prioritized
        result = curator.curate(
            {"k8s", "Ruby", "Java"},
            jd_keywords={"Kubernetes"},
        )

        # k8s should be normalized to Kubernetes and ranked high due to JD match
        assert result.included[0] == "Kubernetes"

    def test_curator_jd_alias_in_keywords_matches_canonical(
        self, skill_registry: SkillRegistry
    ) -> None:
        """JD keyword as alias matches canonical skill in work units."""
        curator = SkillCurator(registry=skill_registry, max_count=3)
        # JD has "ts" (alias), work unit has "TypeScript" - should match
        result = curator.curate(
            {"TypeScript", "Java", "Go"},
            jd_keywords={"ts"},
        )

        # TypeScript should be ranked high because "ts" expands to match it
        assert result.included[0] == "TypeScript"

    def test_curator_without_registry_no_normalization(self) -> None:
        """Without registry, skills pass through as-is."""
        curator = SkillCurator()  # No registry
        result = curator.curate({"k8s", "py"})

        # Without registry, aliases are not normalized
        assert "k8s" in result.included
        assert "py" in result.included
        assert "Kubernetes" not in result.included

    def test_curator_registry_with_exclude_list(self, skill_registry: SkillRegistry) -> None:
        """Exclude list works with registry normalization."""
        curator = SkillCurator(registry=skill_registry, exclude=["Kubernetes"])
        result = curator.curate({"k8s", "Python"})

        # k8s normalizes to Kubernetes, which is excluded
        assert "Kubernetes" not in result.included
        assert "k8s" not in result.included
        assert "Python" in result.included

    def test_curator_registry_with_prioritize_list(self, skill_registry: SkillRegistry) -> None:
        """Prioritize list works with registry normalization."""
        curator = SkillCurator(registry=skill_registry, prioritize=["Kubernetes"])
        result = curator.curate({"k8s", "Python", "Java"})

        # k8s normalizes to Kubernetes which is prioritized
        assert result.included[0] == "Kubernetes"


class TestSkillCuratorONetLookup:
    """Test O*NET discovery during curation (Story 7.17)."""

    def test_curator_lookup_and_cache_for_unknown_skill(self) -> None:
        """Unknown skills trigger O*NET lookup_and_cache (AC #4)."""
        from unittest.mock import MagicMock

        # Create registry with mock that tracks calls
        registry = SkillRegistry([])
        registry.lookup_and_cache = MagicMock(return_value=None)
        # Set _onet_service to non-None so has_onet_service returns True
        registry._onet_service = MagicMock()

        curator = SkillCurator(registry=registry)
        curator.curate({"NewUnknownSkill"})

        # Should have called lookup_and_cache for unknown skill
        registry.lookup_and_cache.assert_called_with("NewUnknownSkill")

    def test_curator_uses_discovered_canonical(self) -> None:
        """Discovered skill uses O*NET canonical name (AC #4)."""
        from unittest.mock import MagicMock

        # Create registry with mock that returns discovered entry
        registry = SkillRegistry([])
        discovered_entry = SkillEntry(canonical="Computer Programming", aliases=["programming"])
        registry.lookup_and_cache = MagicMock(return_value=discovered_entry)
        # Set _onet_service to non-None so has_onet_service returns True
        registry._onet_service = MagicMock()

        curator = SkillCurator(registry=registry)
        result = curator.curate({"programming"})

        # Should use canonical name from O*NET
        assert "Computer Programming" in result.included
        assert "programming" not in result.included

    def test_curator_no_lookup_for_known_skills(self) -> None:
        """Known skills don't trigger O*NET lookup."""
        from unittest.mock import MagicMock

        entries = [SkillEntry(canonical="Python", aliases=["py"])]
        registry = SkillRegistry(entries)
        registry.lookup_and_cache = MagicMock(return_value=None)

        curator = SkillCurator(registry=registry)
        curator.curate({"py"})  # Known alias

        # Should NOT call lookup_and_cache - skill is known
        registry.lookup_and_cache.assert_not_called()

    def test_curator_passthrough_when_lookup_returns_none(self) -> None:
        """Unknown skill passes through when O*NET returns nothing."""
        from unittest.mock import MagicMock

        registry = SkillRegistry([])
        registry.lookup_and_cache = MagicMock(return_value=None)
        # Set _onet_service to non-None so has_onet_service returns True
        registry._onet_service = MagicMock()

        curator = SkillCurator(registry=registry)
        result = curator.curate({"ObscureSkillXYZ"})

        # Original skill should pass through
        assert "ObscureSkillXYZ" in result.included
