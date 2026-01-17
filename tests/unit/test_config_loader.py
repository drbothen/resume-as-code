"""Tests for configuration loading."""

from __future__ import annotations

from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest

from resume_as_code.config import (
    ENV_PREFIX,
    PROJECT_CONFIG_NAME,
    USER_CONFIG_PATH,
    _serialize_value,
    get_config,
    get_config_sources,
    load_env_config,
    load_project_config,
    load_user_config,
    load_yaml_file,
    merge_configs,
    reset_config,
)
from resume_as_code.models.config import ResumeConfig, ScoringWeights


class TestConstants:
    """Test module constants."""

    def test_user_config_path_in_config_dir(self) -> None:
        """User config should be in ~/.config/resume-as-code."""
        assert "resume-as-code" in str(USER_CONFIG_PATH)
        assert USER_CONFIG_PATH.name == "config.yaml"

    def test_project_config_name(self) -> None:
        """Project config should be .resume.yaml."""
        assert PROJECT_CONFIG_NAME == ".resume.yaml"

    def test_env_prefix(self) -> None:
        """Environment variable prefix should be RESUME_."""
        assert ENV_PREFIX == "RESUME_"


class TestLoadYamlFile:
    """Test YAML file loading."""

    def test_load_nonexistent_file_returns_empty_dict(self, tmp_path: Path) -> None:
        """Loading a non-existent file should return empty dict."""
        result = load_yaml_file(tmp_path / "nonexistent.yaml")
        assert result == {}

    def test_load_empty_file_returns_empty_dict(self, tmp_path: Path) -> None:
        """Loading an empty file should return empty dict."""
        config_file = tmp_path / "empty.yaml"
        config_file.write_text("")
        result = load_yaml_file(config_file)
        assert result == {}

    def test_load_valid_yaml(self, tmp_path: Path) -> None:
        """Loading valid YAML should return dict."""
        config_file = tmp_path / "config.yaml"
        config_file.write_text("output_dir: ./custom\ndefault_format: pdf\n")
        result = load_yaml_file(config_file)
        assert result == {"output_dir": "./custom", "default_format": "pdf"}

    def test_load_malformed_yaml_raises_error(self, tmp_path: Path) -> None:
        """Loading malformed YAML should raise ConfigError with helpful message."""
        from resume_as_code.config import ConfigError

        config_file = tmp_path / "malformed.yaml"
        config_file.write_text("output_dir: [\ninvalid yaml syntax")
        with pytest.raises(ConfigError) as exc_info:
            load_yaml_file(config_file)
        assert "malformed.yaml" in str(exc_info.value)
        assert "YAML" in str(exc_info.value) or "syntax" in str(exc_info.value).lower()


class TestLoadUserConfig:
    """Test user config loading."""

    def test_load_user_config_returns_empty_when_no_file(self) -> None:
        """Loading user config should return empty dict when file doesn't exist."""
        with patch.object(Path, "exists", return_value=False):
            config, path = load_user_config()
            assert config == {}
            assert path is None

    def test_load_user_config_returns_config_and_path(self, tmp_path: Path) -> None:
        """Loading user config should return config dict and path."""
        config_file = tmp_path / "config.yaml"
        config_file.write_text("output_dir: ./user-dist\n")

        with patch(
            "resume_as_code.config.USER_CONFIG_PATH",
            config_file,
        ):
            config, path = load_user_config()
            assert config == {"output_dir": "./user-dist"}
            assert path == config_file


class TestLoadProjectConfig:
    """Test project config loading."""

    def test_load_project_config_returns_empty_when_no_file(self, tmp_path: Path) -> None:
        """Loading project config should return empty dict when file doesn't exist."""
        with patch("resume_as_code.config.Path") as mock_path:
            mock_cwd = tmp_path
            mock_path.cwd.return_value = mock_cwd
            # The project file doesn't exist
            config, path = load_project_config()
            assert config == {}
            assert path is None

    def test_load_project_config_returns_config_and_path(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Loading project config should return config dict and path."""
        project_file = tmp_path / ".resume.yaml"
        project_file.write_text("output_dir: ./project-dist\n")

        monkeypatch.chdir(tmp_path)
        config, path = load_project_config()
        assert config == {"output_dir": "./project-dist"}
        assert path == project_file

    def test_load_project_config_with_explicit_path(self, tmp_path: Path) -> None:
        """Loading project config with explicit path should use that path."""
        custom_file = tmp_path / "custom.yaml"
        custom_file.write_text("output_dir: ./custom-dist\n")

        config, path = load_project_config(config_path=custom_file)
        assert config == {"output_dir": "./custom-dist"}
        assert path == custom_file

    def test_load_project_config_explicit_path_overrides_cwd(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Explicit path should be used even when .resume.yaml exists in cwd."""
        # Create default config in cwd
        default_file = tmp_path / ".resume.yaml"
        default_file.write_text("output_dir: ./default-dist\n")

        # Create custom config
        custom_file = tmp_path / "custom.yaml"
        custom_file.write_text("output_dir: ./custom-dist\n")

        monkeypatch.chdir(tmp_path)

        config, path = load_project_config(config_path=custom_file)
        assert config == {"output_dir": "./custom-dist"}
        assert path == custom_file


class TestLoadEnvConfig:
    """Test environment variable config loading."""

    def test_load_env_config_with_no_vars(self) -> None:
        """Loading env config with no RESUME_ vars should return empty dict."""
        with patch.dict("os.environ", {}, clear=True):
            config = load_env_config()
            assert config == {}

    def test_load_env_config_with_prefixed_vars(self) -> None:
        """Environment variables with RESUME_ prefix should be loaded."""
        with patch.dict(
            "os.environ",
            {"RESUME_OUTPUT_DIR": "./env-dist", "OTHER_VAR": "ignored"},
            clear=True,
        ):
            config = load_env_config()
            assert config == {"output_dir": "./env-dist"}
            assert "other_var" not in config

    def test_load_env_config_converts_key_to_lowercase(self) -> None:
        """Environment variable keys should be converted to lowercase."""
        with patch.dict(
            "os.environ",
            {"RESUME_DEFAULT_FORMAT": "pdf"},
            clear=True,
        ):
            config = load_env_config()
            assert "default_format" in config
            assert config["default_format"] == "pdf"


class TestMergeConfigs:
    """Test configuration merging."""

    def test_merge_with_only_defaults(self) -> None:
        """Merging with only defaults should return defaults."""
        defaults = {"output_dir": "./dist"}
        result = merge_configs(defaults, {}, {}, {}, None)
        assert result == {"output_dir": "./dist"}

    def test_user_overrides_defaults(self) -> None:
        """User config should override defaults."""
        defaults = {"output_dir": "./dist"}
        user = {"output_dir": "./user"}
        result = merge_configs(defaults, user, {}, {}, None)
        assert result["output_dir"] == "./user"

    def test_project_overrides_user(self) -> None:
        """Project config should override user config."""
        defaults = {"output_dir": "./dist"}
        user = {"output_dir": "./user"}
        project = {"output_dir": "./project"}
        result = merge_configs(defaults, user, project, {}, None)
        assert result["output_dir"] == "./project"

    def test_env_overrides_project(self) -> None:
        """Environment config should override project config."""
        defaults = {"output_dir": "./dist"}
        project = {"output_dir": "./project"}
        env = {"output_dir": "./env"}
        result = merge_configs(defaults, {}, project, env, None)
        assert result["output_dir"] == "./env"

    def test_cli_overrides_all(self) -> None:
        """CLI config should override all other sources."""
        defaults = {"output_dir": "./dist"}
        user = {"output_dir": "./user"}
        project = {"output_dir": "./project"}
        env = {"output_dir": "./env"}
        cli = {"output_dir": "./cli"}
        result = merge_configs(defaults, user, project, env, cli)
        assert result["output_dir"] == "./cli"

    def test_cli_none_values_ignored(self) -> None:
        """None values from CLI should not override."""
        defaults = {"output_dir": "./dist"}
        project = {"output_dir": "./project"}
        cli: dict[str, Any] = {"output_dir": None}
        result = merge_configs(defaults, {}, project, {}, cli)
        assert result["output_dir"] == "./project"

    def test_merge_preserves_non_overridden_keys(self) -> None:
        """Non-overridden keys should be preserved from each level."""
        defaults = {"output_dir": "./dist", "default_format": "both"}
        user = {"output_dir": "./user"}
        project = {"default_template": "ats-safe"}
        result = merge_configs(defaults, user, project, {}, None)
        assert result["output_dir"] == "./user"
        assert result["default_format"] == "both"
        assert result["default_template"] == "ats-safe"


class TestGetConfig:
    """Test get_config function."""

    def test_get_config_returns_resume_config(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """get_config should return a ResumeConfig instance."""
        reset_config()
        monkeypatch.chdir(tmp_path)
        with patch.dict("os.environ", {}, clear=True):
            config = get_config()
            assert isinstance(config, ResumeConfig)

    def test_get_config_applies_defaults(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """get_config should apply default values."""
        reset_config()
        monkeypatch.chdir(tmp_path)
        with patch.dict("os.environ", {}, clear=True):
            config = get_config()
            assert config.output_dir == Path("./dist")
            assert config.default_format == "both"

    def test_get_config_with_cli_overrides(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """get_config should apply CLI overrides."""
        reset_config()
        monkeypatch.chdir(tmp_path)
        with patch.dict("os.environ", {}, clear=True):
            config = get_config(cli_overrides={"output_dir": "./cli-dist"})
            assert config.output_dir == Path("./cli-dist")

    def test_get_config_with_project_config_path(self, tmp_path: Path) -> None:
        """get_config should use explicit project config path."""
        reset_config()
        custom_file = tmp_path / "custom.yaml"
        custom_file.write_text("output_dir: ./custom-dist\n")

        with patch.dict("os.environ", {}, clear=True):
            config = get_config(project_config_path=custom_file)
            assert config.output_dir == Path("./custom-dist")

    def test_get_config_project_path_overrides_cwd(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Explicit project config path should override .resume.yaml in cwd."""
        reset_config()
        # Create default config in cwd
        default_file = tmp_path / ".resume.yaml"
        default_file.write_text("output_dir: ./default-dist\n")

        # Create custom config
        custom_file = tmp_path / "custom.yaml"
        custom_file.write_text("output_dir: ./custom-dist\n")

        monkeypatch.chdir(tmp_path)

        with patch.dict("os.environ", {}, clear=True):
            config = get_config(project_config_path=custom_file)
            assert config.output_dir == Path("./custom-dist")


class TestGetConfigSources:
    """Test get_config_sources function."""

    def test_get_config_sources_returns_dict(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """get_config_sources should return a dict of ConfigSource."""
        reset_config()
        monkeypatch.chdir(tmp_path)
        with patch.dict("os.environ", {}, clear=True):
            get_config()
            sources = get_config_sources()
            assert isinstance(sources, dict)

    def test_sources_track_default_values(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Sources should track which values came from defaults."""
        reset_config()
        monkeypatch.chdir(tmp_path)
        with patch.dict("os.environ", {}, clear=True):
            get_config()
            sources = get_config_sources()
            assert sources["output_dir"].source == "default"

    def test_sources_track_cli_overrides(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Sources should track which values came from CLI."""
        reset_config()
        monkeypatch.chdir(tmp_path)
        with patch.dict("os.environ", {}, clear=True):
            get_config(cli_overrides={"output_dir": "./cli"})
            sources = get_config_sources()
            assert sources["output_dir"].source == "cli"


class TestSerializeValue:
    """Test _serialize_value function."""

    def test_serialize_none(self) -> None:
        """None should serialize to None."""
        assert _serialize_value(None) is None

    def test_serialize_string(self) -> None:
        """String should serialize unchanged."""
        assert _serialize_value("hello") == "hello"

    def test_serialize_int(self) -> None:
        """Int should serialize unchanged."""
        assert _serialize_value(42) == 42

    def test_serialize_float(self) -> None:
        """Float should serialize unchanged."""
        assert _serialize_value(3.14) == 3.14

    def test_serialize_bool(self) -> None:
        """Bool should serialize unchanged."""
        assert _serialize_value(True) is True
        assert _serialize_value(False) is False

    def test_serialize_path(self) -> None:
        """Path should serialize to string."""
        result = _serialize_value(Path("/tmp/test"))
        assert result == "/tmp/test"
        assert isinstance(result, str)

    def test_serialize_dict(self) -> None:
        """Dict should serialize recursively."""
        result = _serialize_value({"key": "value", "nested": {"a": 1}})
        assert result == {"key": "value", "nested": {"a": 1}}

    def test_serialize_dict_with_path(self) -> None:
        """Dict containing Path should serialize Path to string."""
        result = _serialize_value({"path": Path("/tmp/test")})
        assert result == {"path": "/tmp/test"}

    def test_serialize_list(self) -> None:
        """List should serialize recursively."""
        result = _serialize_value([1, "two", 3.0])
        assert result == [1, "two", 3.0]

    def test_serialize_list_with_path(self) -> None:
        """List containing Path should serialize Path to string."""
        result = _serialize_value([Path("/a"), Path("/b")])
        assert result == ["/a", "/b"]

    def test_serialize_pydantic_model(self) -> None:
        """Pydantic model should serialize to dict via model_dump()."""
        weights = ScoringWeights(title_weight=2.0, skills_weight=1.5)
        result = _serialize_value(weights)
        assert isinstance(result, dict)
        assert result["title_weight"] == 2.0
        assert result["skills_weight"] == 1.5
        assert result["experience_weight"] == 1.0

    def test_serialize_unknown_type(self) -> None:
        """Unknown types should serialize to string representation."""

        class CustomClass:
            def __str__(self) -> str:
                return "custom_value"

        result = _serialize_value(CustomClass())
        assert result == "custom_value"
