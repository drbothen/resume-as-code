"""Tests for configuration Pydantic models."""

from __future__ import annotations

from pathlib import Path

import pytest

from resume_as_code.models.config import (
    ConfigSource,
    CurationConfig,
    DocxConfig,
    ONetConfig,
    ResumeConfig,
    ScoringWeights,
    SkillsConfig,
)


class TestScoringWeights:
    """Test ScoringWeights model."""

    def test_default_values(self) -> None:
        """ScoringWeights should have sensible defaults (field-weighted per HBR 2023)."""
        weights = ScoringWeights()
        assert weights.title_weight == 2.0
        assert weights.skills_weight == 1.5
        assert weights.experience_weight == 1.0

    def test_custom_values(self) -> None:
        """ScoringWeights should accept custom values."""
        weights = ScoringWeights(title_weight=2.0, skills_weight=3.0, experience_weight=1.5)
        assert weights.title_weight == 2.0
        assert weights.skills_weight == 3.0
        assert weights.experience_weight == 1.5

    def test_weight_minimum_bound(self) -> None:
        """Weights should have minimum value of 0."""
        with pytest.raises(ValueError):
            ScoringWeights(title_weight=-1.0)

    def test_weight_maximum_bound(self) -> None:
        """Weights should have maximum value of 10."""
        with pytest.raises(ValueError):
            ScoringWeights(skills_weight=11.0)


class TestResumeConfig:
    """Test ResumeConfig model."""

    def test_default_output_dir(self) -> None:
        """Default output_dir should be ./dist."""
        config = ResumeConfig()
        assert config.output_dir == Path("./dist")

    def test_default_format(self) -> None:
        """Default format should be 'both'."""
        config = ResumeConfig()
        assert config.default_format == "both"

    def test_default_template(self) -> None:
        """Default template should be 'modern'."""
        config = ResumeConfig()
        assert config.default_template == "modern"

    def test_default_work_units_dir(self) -> None:
        """Default work_units_dir should be ./work-units."""
        config = ResumeConfig()
        assert config.work_units_dir == Path("./work-units")

    def test_default_scoring_weights(self) -> None:
        """Default scoring weights should be ScoringWeights defaults (field-weighted)."""
        config = ResumeConfig()
        assert config.scoring_weights.title_weight == 2.0
        assert config.scoring_weights.skills_weight == 1.5
        assert config.scoring_weights.experience_weight == 1.0

    def test_default_top_k(self) -> None:
        """Default top_k should be 8."""
        config = ResumeConfig()
        assert config.default_top_k == 8

    def test_default_editor_is_none(self) -> None:
        """Default editor should be None (falls back to $EDITOR)."""
        config = ResumeConfig()
        assert config.editor is None

    def test_custom_values(self) -> None:
        """ResumeConfig should accept custom values."""
        config = ResumeConfig(
            output_dir=Path("./custom"),
            default_format="pdf",
            default_template="ats-safe",
            default_top_k=10,
        )
        assert config.output_dir == Path("./custom")
        assert config.default_format == "pdf"
        assert config.default_template == "ats-safe"
        assert config.default_top_k == 10

    def test_path_expansion_string(self) -> None:
        """String paths should be converted to Path objects."""
        config = ResumeConfig(output_dir="./custom-dir")
        assert isinstance(config.output_dir, Path)
        assert config.output_dir == Path("./custom-dir")

    def test_path_expansion_tilde(self) -> None:
        """Tilde in paths should be expanded."""
        config = ResumeConfig(output_dir="~/custom-dir")
        assert config.output_dir.is_absolute()
        assert "~" not in str(config.output_dir)

    def test_format_enum_validation(self) -> None:
        """default_format should only accept valid values."""
        for valid_format in ["pdf", "docx", "both"]:
            config = ResumeConfig(default_format=valid_format)
            assert config.default_format == valid_format

        with pytest.raises(ValueError):
            ResumeConfig(default_format="invalid")

    def test_top_k_minimum_bound(self) -> None:
        """default_top_k should have minimum value of 1."""
        with pytest.raises(ValueError):
            ResumeConfig(default_top_k=0)

    def test_top_k_maximum_bound(self) -> None:
        """default_top_k should have maximum value of 50."""
        with pytest.raises(ValueError):
            ResumeConfig(default_top_k=51)


class TestConfigSource:
    """Test ConfigSource model."""

    def test_config_source_with_default(self) -> None:
        """ConfigSource should track default source."""
        source = ConfigSource(value="./dist", source="default")
        assert source.value == "./dist"
        assert source.source == "default"
        assert source.path is None

    def test_config_source_with_file_path(self) -> None:
        """ConfigSource should track file path for file-based sources."""
        source = ConfigSource(
            value="./custom",
            source="project",
            path="/path/to/.resume.yaml",
        )
        assert source.source == "project"
        assert source.path == "/path/to/.resume.yaml"

    def test_config_source_valid_sources(self) -> None:
        """ConfigSource should only accept valid source values."""
        for valid_source in ["default", "user", "project", "env", "cli"]:
            source = ConfigSource(value="test", source=valid_source)
            assert source.source == valid_source

    def test_config_source_invalid_source(self) -> None:
        """ConfigSource should reject invalid source values."""
        with pytest.raises(ValueError):
            ConfigSource(value="test", source="invalid")

    def test_config_source_various_value_types(self) -> None:
        """ConfigSource should accept various value types."""
        # String
        source = ConfigSource(value="string", source="default")
        assert source.value == "string"

        # Int
        source = ConfigSource(value=42, source="default")
        assert source.value == 42

        # Float
        source = ConfigSource(value=3.14, source="default")
        assert source.value == 3.14

        # Bool
        source = ConfigSource(value=True, source="default")
        assert source.value is True

        # Dict
        source = ConfigSource(value={"key": "val"}, source="default")
        assert source.value == {"key": "val"}

        # List
        source = ConfigSource(value=[1, 2, 3], source="default")
        assert source.value == [1, 2, 3]

        # None
        source = ConfigSource(value=None, source="default")
        assert source.value is None


class TestSkillsConfig:
    """Test SkillsConfig model for skills curation settings."""

    def test_default_max_display(self) -> None:
        """Default max_display should be 15."""
        config = SkillsConfig()
        assert config.max_display == 15

    def test_default_exclude_is_empty_list(self) -> None:
        """Default exclude list should be empty."""
        config = SkillsConfig()
        assert config.exclude == []

    def test_default_prioritize_is_empty_list(self) -> None:
        """Default prioritize list should be empty."""
        config = SkillsConfig()
        assert config.prioritize == []

    def test_custom_max_display(self) -> None:
        """SkillsConfig should accept custom max_display."""
        config = SkillsConfig(max_display=12)
        assert config.max_display == 12

    def test_custom_exclude_list(self) -> None:
        """SkillsConfig should accept custom exclude list."""
        config = SkillsConfig(exclude=["PHP", "jQuery"])
        assert config.exclude == ["PHP", "jQuery"]

    def test_custom_prioritize_list(self) -> None:
        """SkillsConfig should accept custom prioritize list."""
        config = SkillsConfig(prioritize=["Python", "Kubernetes"])
        assert config.prioritize == ["Python", "Kubernetes"]

    def test_max_display_minimum_bound(self) -> None:
        """max_display should have minimum value of 1."""
        with pytest.raises(ValueError):
            SkillsConfig(max_display=0)

    def test_max_display_maximum_bound(self) -> None:
        """max_display should have maximum value of 50."""
        with pytest.raises(ValueError):
            SkillsConfig(max_display=51)

    def test_full_configuration(self) -> None:
        """SkillsConfig should accept all fields together."""
        config = SkillsConfig(
            max_display=10,
            exclude=["PHP", "Visual Basic"],
            prioritize=["Python", "AWS"],
        )
        assert config.max_display == 10
        assert config.exclude == ["PHP", "Visual Basic"]
        assert config.prioritize == ["Python", "AWS"]


class TestResumeConfigSkills:
    """Test skills field in ResumeConfig."""

    def test_default_skills_config(self) -> None:
        """ResumeConfig should have default SkillsConfig."""
        config = ResumeConfig()
        assert config.skills.max_display == 15
        assert config.skills.exclude == []
        assert config.skills.prioritize == []

    def test_custom_skills_config(self) -> None:
        """ResumeConfig should accept custom skills configuration."""
        config = ResumeConfig(
            skills=SkillsConfig(
                max_display=12,
                exclude=["PHP"],
                prioritize=["Python"],
            )
        )
        assert config.skills.max_display == 12
        assert config.skills.exclude == ["PHP"]
        assert config.skills.prioritize == ["Python"]


class TestONetConfig:
    """Test ONetConfig model for O*NET API v2.0 integration."""

    def test_default_enabled_is_true(self) -> None:
        """Default enabled should be True."""
        config = ONetConfig()
        assert config.enabled is True

    def test_default_api_key_is_none(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Default api_key should be None when env var not set."""
        monkeypatch.delenv("ONET_API_KEY", raising=False)
        config = ONetConfig()
        assert config.api_key is None

    def test_default_cache_ttl_24_hours(self) -> None:
        """Default cache_ttl should be 86400 seconds (24 hours)."""
        config = ONetConfig()
        assert config.cache_ttl == 86400

    def test_default_timeout_10_seconds(self) -> None:
        """Default timeout should be 10.0 seconds."""
        config = ONetConfig()
        assert config.timeout == 10.0

    def test_default_retry_delay_200ms(self) -> None:
        """Default retry_delay_ms should be 200 (O*NET minimum)."""
        config = ONetConfig()
        assert config.retry_delay_ms == 200

    def test_custom_api_key(self) -> None:
        """ONetConfig should accept custom api_key."""
        config = ONetConfig(api_key="test-key-123")
        assert config.api_key == "test-key-123"

    def test_custom_cache_ttl(self) -> None:
        """ONetConfig should accept custom cache_ttl."""
        config = ONetConfig(cache_ttl=7200)  # 2 hours
        assert config.cache_ttl == 7200

    def test_cache_ttl_minimum_bound(self) -> None:
        """cache_ttl should have minimum value of 3600 (1 hour)."""
        with pytest.raises(ValueError):
            ONetConfig(cache_ttl=1800)  # 30 minutes - too low

    def test_timeout_minimum_bound(self) -> None:
        """timeout should have minimum value of 1.0."""
        with pytest.raises(ValueError):
            ONetConfig(timeout=0.5)

    def test_timeout_maximum_bound(self) -> None:
        """timeout should have maximum value of 60.0."""
        with pytest.raises(ValueError):
            ONetConfig(timeout=120.0)

    def test_retry_delay_minimum_bound(self) -> None:
        """retry_delay_ms should have minimum value of 200 (O*NET requirement)."""
        with pytest.raises(ValueError):
            ONetConfig(retry_delay_ms=100)

    def test_is_configured_with_api_key(self) -> None:
        """is_configured should return True when enabled and api_key set."""
        config = ONetConfig(enabled=True, api_key="test-key")
        assert config.is_configured is True

    def test_is_configured_without_api_key(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """is_configured should return False when api_key is None."""
        monkeypatch.delenv("ONET_API_KEY", raising=False)
        config = ONetConfig(enabled=True, api_key=None)
        assert config.is_configured is False

    def test_is_configured_when_disabled(self) -> None:
        """is_configured should return False when disabled."""
        config = ONetConfig(enabled=False, api_key="test-key")
        assert config.is_configured is False

    def test_api_key_from_environment(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """api_key should be resolved from ONET_API_KEY environment variable."""
        monkeypatch.setenv("ONET_API_KEY", "env-api-key")
        config = ONetConfig()
        assert config.api_key == "env-api-key"

    def test_config_api_key_overrides_env(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Explicit api_key should override environment variable."""
        monkeypatch.setenv("ONET_API_KEY", "env-api-key")
        config = ONetConfig(api_key="explicit-key")
        assert config.api_key == "explicit-key"

    def test_disabled_config(self) -> None:
        """ONetConfig should accept disabled state."""
        config = ONetConfig(enabled=False)
        assert config.enabled is False
        assert config.is_configured is False


class TestResumeConfigONet:
    """Test onet field in ResumeConfig."""

    def test_default_onet_is_none(self) -> None:
        """ResumeConfig should have onet as None by default."""
        config = ResumeConfig()
        assert config.onet is None

    def test_custom_onet_config(self) -> None:
        """ResumeConfig should accept custom onet configuration."""
        config = ResumeConfig(
            onet=ONetConfig(
                enabled=True,
                api_key="test-key",
                cache_ttl=7200,
            )
        )
        assert config.onet is not None
        assert config.onet.api_key == "test-key"
        assert config.onet.cache_ttl == 7200


class TestCurationConfig:
    """Test CurationConfig model (Story 7.14 + 7.18 action scoring)."""

    def test_default_action_scoring_enabled(self) -> None:
        """Default action_scoring_enabled should be True."""
        config = CurationConfig()
        assert config.action_scoring_enabled is True

    def test_default_min_action_relevance_score(self) -> None:
        """Default min_action_relevance_score should be 0.25."""
        config = CurationConfig()
        assert config.min_action_relevance_score == 0.25

    def test_custom_action_scoring_enabled_false(self) -> None:
        """CurationConfig should accept action_scoring_enabled=False."""
        config = CurationConfig(action_scoring_enabled=False)
        assert config.action_scoring_enabled is False

    def test_custom_min_action_relevance_score(self) -> None:
        """CurationConfig should accept custom min_action_relevance_score."""
        config = CurationConfig(min_action_relevance_score=0.5)
        assert config.min_action_relevance_score == 0.5

    def test_min_action_relevance_score_minimum_bound(self) -> None:
        """min_action_relevance_score should have minimum value of 0.0."""
        config = CurationConfig(min_action_relevance_score=0.0)
        assert config.min_action_relevance_score == 0.0

        with pytest.raises(ValueError):
            CurationConfig(min_action_relevance_score=-0.1)

    def test_min_action_relevance_score_maximum_bound(self) -> None:
        """min_action_relevance_score should have maximum value of 1.0."""
        config = CurationConfig(min_action_relevance_score=1.0)
        assert config.min_action_relevance_score == 1.0

        with pytest.raises(ValueError):
            CurationConfig(min_action_relevance_score=1.1)

    def test_existing_min_relevance_score(self) -> None:
        """Existing min_relevance_score should still work."""
        config = CurationConfig(min_relevance_score=0.5)
        assert config.min_relevance_score == 0.5

    def test_full_action_scoring_config(self) -> None:
        """CurationConfig should accept all action scoring fields together."""
        config = CurationConfig(
            action_scoring_enabled=True,
            min_action_relevance_score=0.3,
            min_relevance_score=0.4,
        )
        assert config.action_scoring_enabled is True
        assert config.min_action_relevance_score == 0.3
        assert config.min_relevance_score == 0.4


class TestResumeConfigCuration:
    """Test curation field in ResumeConfig."""

    def test_default_curation_config(self) -> None:
        """ResumeConfig should have default CurationConfig."""
        config = ResumeConfig()
        assert config.curation.action_scoring_enabled is True
        assert config.curation.min_action_relevance_score == 0.25

    def test_custom_curation_config(self) -> None:
        """ResumeConfig should accept custom curation configuration."""
        config = ResumeConfig(
            curation=CurationConfig(
                action_scoring_enabled=False,
                min_action_relevance_score=0.5,
            )
        )
        assert config.curation.action_scoring_enabled is False
        assert config.curation.min_action_relevance_score == 0.5


class TestResumeConfigEmploymentContinuity:
    """Test employment_continuity field in ResumeConfig (Story 7.20)."""

    def test_default_employment_continuity_is_minimum_bullet(self) -> None:
        """Default employment_continuity should be 'minimum_bullet'."""
        config = ResumeConfig()
        assert config.employment_continuity == "minimum_bullet"

    def test_employment_continuity_minimum_bullet(self) -> None:
        """ResumeConfig should accept 'minimum_bullet' mode."""
        config = ResumeConfig(employment_continuity="minimum_bullet")
        assert config.employment_continuity == "minimum_bullet"

    def test_employment_continuity_allow_gaps(self) -> None:
        """ResumeConfig should accept 'allow_gaps' mode."""
        config = ResumeConfig(employment_continuity="allow_gaps")
        assert config.employment_continuity == "allow_gaps"

    def test_employment_continuity_invalid_mode_rejected(self) -> None:
        """Invalid employment_continuity mode should raise ValueError."""
        import pytest

        with pytest.raises(ValueError):
            ResumeConfig(employment_continuity="invalid_mode")

    def test_employment_continuity_mode_type_exported(self) -> None:
        """EmploymentContinuityMode type should be importable."""
        from resume_as_code.models.config import EmploymentContinuityMode

        # Type checking - ensure it's a Literal type with correct values
        assert EmploymentContinuityMode is not None


class TestResumeConfigTailoredNotice:
    """Test tailored_notice fields in ResumeConfig (Story 7.19)."""

    def test_tailored_notice_defaults_false(self) -> None:
        """Tailored notice should be opt-in (default False)."""
        config = ResumeConfig()
        assert config.tailored_notice is False

    def test_tailored_notice_text_defaults_none(self) -> None:
        """Tailored notice text should default to None."""
        config = ResumeConfig()
        assert config.tailored_notice_text is None

    def test_tailored_notice_enabled(self) -> None:
        """ResumeConfig should accept tailored_notice=True."""
        config = ResumeConfig(tailored_notice=True)
        assert config.tailored_notice is True

    def test_tailored_notice_custom_text(self) -> None:
        """ResumeConfig should accept custom tailored_notice_text."""
        custom_text = "Custom footer message for recruiters."
        config = ResumeConfig(
            tailored_notice=True,
            tailored_notice_text=custom_text,
        )
        assert config.tailored_notice is True
        assert config.tailored_notice_text == custom_text

    def test_tailored_notice_text_without_enabled(self) -> None:
        """Custom text can be set even if tailored_notice is False."""
        config = ResumeConfig(
            tailored_notice=False,
            tailored_notice_text="Text but not shown",
        )
        assert config.tailored_notice is False
        assert config.tailored_notice_text == "Text but not shown"

    def test_default_tailored_notice_constant_exists(self) -> None:
        """DEFAULT_TAILORED_NOTICE constant should exist."""
        from resume_as_code.models.config import DEFAULT_TAILORED_NOTICE

        assert DEFAULT_TAILORED_NOTICE is not None
        assert "relevant" in DEFAULT_TAILORED_NOTICE.lower()
        assert "request" in DEFAULT_TAILORED_NOTICE.lower()


class TestDataPaths:
    """Test DataPaths model for custom data file paths (Story 9.2 + 11.2)."""

    def test_default_all_none(self) -> None:
        """DataPaths should have all fields as None by default."""
        from resume_as_code.models.config import DataPaths

        paths = DataPaths()
        assert paths.profile is None
        assert paths.certifications is None
        assert paths.education is None
        assert paths.highlights is None
        assert paths.publications is None
        assert paths.board_roles is None

    def test_custom_file_paths(self) -> None:
        """DataPaths should accept custom file paths."""
        from resume_as_code.models.config import DataPaths

        paths = DataPaths(
            certifications="./data/certs.yaml",
            education="./data/edu.yaml",
        )
        assert paths.certifications == "./data/certs.yaml"
        assert paths.education == "./data/edu.yaml"

    # Story 11.2: Directory mode fields
    def test_directory_mode_fields_exist(self) -> None:
        """DataPaths should have *_dir fields for directory mode (TD-005)."""
        from resume_as_code.models.config import DataPaths

        paths = DataPaths()
        assert paths.certifications_dir is None
        assert paths.education_dir is None
        assert paths.highlights_dir is None
        assert paths.publications_dir is None
        assert paths.board_roles_dir is None

    def test_custom_directory_paths(self) -> None:
        """DataPaths should accept custom directory paths."""
        from resume_as_code.models.config import DataPaths

        paths = DataPaths(
            certifications_dir="./certifications/",
            publications_dir="./publications/",
        )
        assert paths.certifications_dir == "./certifications/"
        assert paths.publications_dir == "./publications/"

    def test_dual_config_validation_certifications(self) -> None:
        """DataPaths should reject both certifications and certifications_dir."""
        from resume_as_code.models.config import DataPaths

        with pytest.raises(ValueError, match="Cannot specify both"):
            DataPaths(
                certifications="./certifications.yaml",
                certifications_dir="./certifications/",
            )

    def test_dual_config_validation_education(self) -> None:
        """DataPaths should reject both education and education_dir."""
        from resume_as_code.models.config import DataPaths

        with pytest.raises(ValueError, match="Cannot specify both"):
            DataPaths(
                education="./education.yaml",
                education_dir="./education/",
            )

    def test_dual_config_validation_publications(self) -> None:
        """DataPaths should reject both publications and publications_dir."""
        from resume_as_code.models.config import DataPaths

        with pytest.raises(ValueError, match="Cannot specify both"):
            DataPaths(
                publications="./publications.yaml",
                publications_dir="./publications/",
            )

    def test_dual_config_validation_board_roles(self) -> None:
        """DataPaths should reject both board_roles and board_roles_dir."""
        from resume_as_code.models.config import DataPaths

        with pytest.raises(ValueError, match="Cannot specify both"):
            DataPaths(
                board_roles="./board-roles.yaml",
                board_roles_dir="./board-roles/",
            )

    def test_dual_config_validation_highlights(self) -> None:
        """DataPaths should reject both highlights and highlights_dir."""
        from resume_as_code.models.config import DataPaths

        with pytest.raises(ValueError, match="Cannot specify both"):
            DataPaths(
                highlights="./highlights.yaml",
                highlights_dir="./highlights/",
            )

    def test_mixed_file_and_directory_allowed(self) -> None:
        """DataPaths should allow file mode for some and dir mode for others."""
        from resume_as_code.models.config import DataPaths

        paths = DataPaths(
            certifications="./certifications.yaml",  # File mode
            publications_dir="./publications/",  # Directory mode
        )
        assert paths.certifications == "./certifications.yaml"
        assert paths.certifications_dir is None
        assert paths.publications is None
        assert paths.publications_dir == "./publications/"


class TestTemplateOptions:
    """Test TemplateOptions model for template rendering configuration (Story 8.1)."""

    def test_default_group_employer_positions_is_true(self) -> None:
        """Default group_employer_positions should be True."""
        from resume_as_code.models.config import TemplateOptions

        options = TemplateOptions()
        assert options.group_employer_positions is True

    def test_group_employer_positions_can_be_disabled(self) -> None:
        """TemplateOptions should accept group_employer_positions=False."""
        from resume_as_code.models.config import TemplateOptions

        options = TemplateOptions(group_employer_positions=False)
        assert options.group_employer_positions is False

    def test_group_employer_positions_explicit_true(self) -> None:
        """TemplateOptions should accept explicit group_employer_positions=True."""
        from resume_as_code.models.config import TemplateOptions

        options = TemplateOptions(group_employer_positions=True)
        assert options.group_employer_positions is True


class TestResumeConfigTemplateOptions:
    """Test template_options field in ResumeConfig (Story 8.1)."""

    def test_default_template_options(self) -> None:
        """ResumeConfig should have default TemplateOptions."""
        config = ResumeConfig()
        assert config.template_options is not None
        assert config.template_options.group_employer_positions is True

    def test_custom_template_options(self) -> None:
        """ResumeConfig should accept custom template_options configuration."""
        from resume_as_code.models.config import TemplateOptions

        config = ResumeConfig(template_options=TemplateOptions(group_employer_positions=False))
        assert config.template_options.group_employer_positions is False

    def test_template_options_from_dict(self) -> None:
        """ResumeConfig should accept template_options as dict (YAML parsing)."""
        config = ResumeConfig(template_options={"group_employer_positions": False})
        assert config.template_options.group_employer_positions is False


class TestResumeConfigTemplatesDir:
    """Test templates_dir field in ResumeConfig (Story 11.3)."""

    def test_default_templates_dir_is_none(self) -> None:
        """Default templates_dir should be None (use package default)."""
        config = ResumeConfig()
        assert config.templates_dir is None

    def test_custom_templates_dir_string(self) -> None:
        """ResumeConfig should accept string path for templates_dir."""
        config = ResumeConfig(templates_dir="./my-templates")
        assert config.templates_dir == Path("./my-templates")

    def test_custom_templates_dir_path(self) -> None:
        """ResumeConfig should accept Path object for templates_dir."""
        config = ResumeConfig(templates_dir=Path("./custom-templates"))
        assert config.templates_dir == Path("./custom-templates")

    def test_templates_dir_tilde_expansion(self) -> None:
        """Tilde in templates_dir should be expanded."""
        config = ResumeConfig(templates_dir="~/templates")
        assert config.templates_dir is not None
        assert config.templates_dir.is_absolute()
        assert "~" not in str(config.templates_dir)


class TestResumeConfigHistoryYears:
    """Test history_years field in ResumeConfig (Story 13.2)."""

    def test_default_history_years_is_none(self) -> None:
        """Default history_years should be None (unlimited)."""
        config = ResumeConfig()
        assert config.history_years is None

    def test_custom_history_years(self) -> None:
        """ResumeConfig should accept custom history_years."""
        config = ResumeConfig(history_years=10)
        assert config.history_years == 10

    def test_history_years_minimum_bound(self) -> None:
        """history_years should have minimum value of 1."""
        with pytest.raises(ValueError):
            ResumeConfig(history_years=0)

    def test_history_years_maximum_bound(self) -> None:
        """history_years should have maximum value of 50."""
        with pytest.raises(ValueError):
            ResumeConfig(history_years=51)

    def test_history_years_valid_boundary_values(self) -> None:
        """history_years should accept boundary values 1 and 50."""
        config_min = ResumeConfig(history_years=1)
        assert config_min.history_years == 1

        config_max = ResumeConfig(history_years=50)
        assert config_max.history_years == 50

    def test_history_years_common_values(self) -> None:
        """history_years should accept common values (5, 10, 15, 20)."""
        for years in [5, 10, 15, 20]:
            config = ResumeConfig(history_years=years)
            assert config.history_years == years


class TestDocxConfig:
    """Test DocxConfig model for DOCX-specific configuration (Story 13.1)."""

    def test_default_template_is_none(self) -> None:
        """Default template should be None (falls back to default_template)."""
        config = DocxConfig()
        assert config.template is None

    def test_custom_template(self) -> None:
        """DocxConfig should accept custom template name."""
        config = DocxConfig(template="branded")
        assert config.template == "branded"

    def test_template_without_extension(self) -> None:
        """Template name should be stored without .docx extension."""
        config = DocxConfig(template="executive")
        assert config.template == "executive"
        assert ".docx" not in config.template

    def test_various_template_names(self) -> None:
        """DocxConfig should accept various valid template names."""
        for template_name in ["modern", "executive", "ats-safe", "branded", "minimal"]:
            config = DocxConfig(template=template_name)
            assert config.template == template_name


class TestResumeConfigDocx:
    """Test docx field in ResumeConfig (Story 13.1)."""

    def test_default_docx_is_none(self) -> None:
        """ResumeConfig should have docx as None by default."""
        config = ResumeConfig()
        assert config.docx is None

    def test_custom_docx_config(self) -> None:
        """ResumeConfig should accept custom docx configuration."""
        config = ResumeConfig(docx=DocxConfig(template="branded"))
        assert config.docx is not None
        assert config.docx.template == "branded"

    def test_docx_config_from_dict(self) -> None:
        """ResumeConfig should accept docx as dict (YAML parsing)."""
        config = ResumeConfig(docx={"template": "executive"})
        assert config.docx is not None
        assert config.docx.template == "executive"
