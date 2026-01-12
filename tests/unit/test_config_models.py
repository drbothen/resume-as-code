"""Tests for configuration Pydantic models."""

from __future__ import annotations

from pathlib import Path

import pytest

from resume_as_code.models.config import (
    ConfigSource,
    ResumeConfig,
    ScoringWeights,
    SkillsConfig,
)


class TestScoringWeights:
    """Test ScoringWeights model."""

    def test_default_values(self) -> None:
        """ScoringWeights should have sensible defaults."""
        weights = ScoringWeights()
        assert weights.title_weight == 1.0
        assert weights.skills_weight == 1.0
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
        """Default scoring weights should be ScoringWeights defaults."""
        config = ResumeConfig()
        assert config.scoring_weights.title_weight == 1.0
        assert config.scoring_weights.skills_weight == 1.0
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
