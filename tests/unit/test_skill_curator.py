"""Tests for SkillCurator service."""

from __future__ import annotations

from resume_as_code.services.skill_curator import CurationResult, SkillCurator


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
