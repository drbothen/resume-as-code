"""Unit tests for SkillRegistry service."""

from __future__ import annotations

from pathlib import Path
from tempfile import NamedTemporaryFile
from unittest.mock import MagicMock

import pytest

from resume_as_code.models.config import ONetConfig
from resume_as_code.models.skill_entry import SkillEntry
from resume_as_code.services.onet_service import ONetOccupation, ONetService, ONetSkill
from resume_as_code.services.skill_registry import SkillRegistry


@pytest.fixture
def registry() -> SkillRegistry:
    """Create test registry with common skills."""
    entries = [
        SkillEntry(canonical="Kubernetes", aliases=["k8s", "kube"]),
        SkillEntry(canonical="TypeScript", aliases=["ts"]),
        SkillEntry(canonical="Python", aliases=["py", "python3"]),
        SkillEntry(
            canonical="Amazon Web Services",
            aliases=["aws", "amazon aws"],
            category="cloud",
            onet_code="2.A.2.b",
        ),
    ]
    return SkillRegistry(entries)


class TestSkillRegistryNormalize:
    """Test normalize() method."""

    def test_normalize_alias_to_canonical(self, registry: SkillRegistry) -> None:
        """Alias normalizes to canonical name."""
        assert registry.normalize("k8s") == "Kubernetes"
        assert registry.normalize("ts") == "TypeScript"
        assert registry.normalize("py") == "Python"

    def test_normalize_canonical_returns_itself(self, registry: SkillRegistry) -> None:
        """Canonical name returns itself."""
        assert registry.normalize("Kubernetes") == "Kubernetes"
        assert registry.normalize("TypeScript") == "TypeScript"

    def test_normalize_case_insensitive(self, registry: SkillRegistry) -> None:
        """Normalization is case insensitive."""
        assert registry.normalize("KUBERNETES") == "Kubernetes"
        assert registry.normalize("kubernetes") == "Kubernetes"
        assert registry.normalize("K8S") == "Kubernetes"

    def test_normalize_unknown_passthrough(self, registry: SkillRegistry) -> None:
        """Unknown skill returns original string unchanged (AC: #4)."""
        assert registry.normalize("UnknownSkill") == "UnknownSkill"
        assert registry.normalize("some-custom-skill") == "some-custom-skill"

    def test_normalize_empty_registry(self) -> None:
        """Empty registry passes through all skills."""
        registry = SkillRegistry([])
        assert registry.normalize("anything") == "anything"


class TestSkillRegistryGetAliases:
    """Test get_aliases() method."""

    def test_get_aliases_includes_canonical(self, registry: SkillRegistry) -> None:
        """Aliases set includes lowercase canonical name."""
        aliases = registry.get_aliases("k8s")
        assert "kubernetes" in aliases

    def test_get_aliases_includes_all_aliases(self, registry: SkillRegistry) -> None:
        """Aliases set includes all registered aliases."""
        aliases = registry.get_aliases("Kubernetes")
        assert "k8s" in aliases
        assert "kube" in aliases

    def test_get_aliases_from_any_alias(self, registry: SkillRegistry) -> None:
        """Can get all aliases from any alias."""
        aliases_from_k8s = registry.get_aliases("k8s")
        aliases_from_kube = registry.get_aliases("kube")
        aliases_from_canonical = registry.get_aliases("Kubernetes")
        assert aliases_from_k8s == aliases_from_kube == aliases_from_canonical

    def test_get_aliases_unknown_returns_singleton(self, registry: SkillRegistry) -> None:
        """Unknown skill returns singleton set with lowercase original."""
        aliases = registry.get_aliases("UnknownSkill")
        assert aliases == {"unknownskill"}


class TestSkillRegistryGetOnetCode:
    """Test get_onet_code() method."""

    def test_get_onet_code_exists(self, registry: SkillRegistry) -> None:
        """Returns O*NET code when available."""
        assert registry.get_onet_code("aws") == "2.A.2.b"
        assert registry.get_onet_code("Amazon Web Services") == "2.A.2.b"

    def test_get_onet_code_not_set(self, registry: SkillRegistry) -> None:
        """Returns None when O*NET code not set."""
        assert registry.get_onet_code("Kubernetes") is None

    def test_get_onet_code_unknown(self, registry: SkillRegistry) -> None:
        """Returns None for unknown skill."""
        assert registry.get_onet_code("unknown") is None


class TestSkillRegistryLoadFromYaml:
    """Test load_from_yaml() class method."""

    def test_load_from_yaml_basic(self) -> None:
        """Load registry from valid YAML file."""
        yaml_content = """
skills:
  - canonical: JavaScript
    aliases: [js, ecmascript]
    category: language
  - canonical: React
    aliases: [reactjs]
"""
        with NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(yaml_content)
            f.flush()
            path = Path(f.name)

        try:
            registry = SkillRegistry.load_from_yaml(path)
            assert registry.normalize("js") == "JavaScript"
            assert registry.normalize("reactjs") == "React"
        finally:
            path.unlink()

    def test_load_from_yaml_empty_skills(self) -> None:
        """Load registry with empty skills list."""
        yaml_content = "skills: []"
        with NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(yaml_content)
            f.flush()
            path = Path(f.name)

        try:
            registry = SkillRegistry.load_from_yaml(path)
            assert registry.normalize("anything") == "anything"
        finally:
            path.unlink()


class TestSkillRegistryLoadDefault:
    """Test load_default() class method."""

    def test_load_default_returns_registry(self) -> None:
        """load_default() returns a SkillRegistry instance."""
        registry = SkillRegistry.load_default()
        assert isinstance(registry, SkillRegistry)

    def test_load_default_has_common_skills(self) -> None:
        """Default registry includes common tech skills."""
        registry = SkillRegistry.load_default()
        # These should be in the bundled skills.yaml
        assert registry.normalize("k8s") == "Kubernetes"
        assert registry.normalize("ts") == "TypeScript"
        assert registry.normalize("aws") == "Amazon Web Services"


class TestSkillRegistryLoadWithOnet:
    """Test load_with_onet() factory method (Story 7.17)."""

    def test_load_with_onet_returns_registry(self) -> None:
        """load_with_onet() returns a SkillRegistry instance."""
        registry = SkillRegistry.load_with_onet(None)
        assert isinstance(registry, SkillRegistry)

    def test_load_with_onet_no_config_has_no_onet_service(self) -> None:
        """Registry without O*NET config has no onet_service (AC #3)."""
        registry = SkillRegistry.load_with_onet(None)
        assert registry._onet_service is None
        assert registry._user_skills_path is None

    def test_load_with_onet_unconfigured_has_no_onet_service(self) -> None:
        """Registry with unconfigured O*NET has no onet_service (AC #3)."""
        # enabled=True but no api_key
        config = ONetConfig(enabled=True, api_key=None)
        registry = SkillRegistry.load_with_onet(config)
        assert registry._onet_service is None

    def test_load_with_onet_disabled_has_no_onet_service(self) -> None:
        """Registry with disabled O*NET has no onet_service (AC #3)."""
        config = ONetConfig(enabled=False, api_key="test-key")
        registry = SkillRegistry.load_with_onet(config)
        assert registry._onet_service is None

    def test_load_with_onet_configured_has_onet_service(self) -> None:
        """Registry with configured O*NET has onet_service (AC #2)."""
        config = ONetConfig(enabled=True, api_key="test-key")
        registry = SkillRegistry.load_with_onet(config)
        assert registry._onet_service is not None
        assert registry._user_skills_path is not None

    def test_load_with_onet_has_common_skills(self) -> None:
        """load_with_onet() includes bundled skills."""
        registry = SkillRegistry.load_with_onet(None)
        # Same skills as load_default
        assert registry.normalize("k8s") == "Kubernetes"
        assert registry.normalize("ts") == "TypeScript"

    def test_load_with_onet_picks_up_env_var(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """load_with_onet(None) enables O*NET when ONET_API_KEY env var is set."""
        monkeypatch.setenv("ONET_API_KEY", "test-env-key")
        registry = SkillRegistry.load_with_onet(None)
        assert registry._onet_service is not None
        assert registry._user_skills_path is not None

    def test_load_with_onet_user_skills_path_set(self) -> None:
        """Configured registry has user skills path for persistence (AC #5)."""
        config = ONetConfig(enabled=True, api_key="test-key")
        registry = SkillRegistry.load_with_onet(config)
        assert registry._user_skills_path is not None
        assert "user-skills.yaml" in str(registry._user_skills_path)


class TestSkillRegistryErrorHandling:
    """Test error handling in load_from_yaml()."""

    def test_load_from_yaml_malformed_raises_value_error(self) -> None:
        """Malformed YAML raises ValueError with clear message."""
        yaml_content = "not: [valid: yaml structure"
        with NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(yaml_content)
            f.flush()
            path = Path(f.name)

        try:
            with pytest.raises(ValueError, match="Invalid YAML"):
                SkillRegistry.load_from_yaml(path)
        finally:
            path.unlink()

    def test_load_from_yaml_empty_file_returns_empty_registry(self) -> None:
        """Empty YAML file returns registry with no entries."""
        with NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write("")  # Empty file
            f.flush()
            path = Path(f.name)

        try:
            registry = SkillRegistry.load_from_yaml(path)
            assert len(registry._entries) == 0
            assert registry.normalize("anything") == "anything"
        finally:
            path.unlink()


class TestSkillRegistryAliasCollision:
    """Test alias collision detection and warnings."""

    def test_alias_collision_emits_warning(self) -> None:
        """Colliding aliases emit UserWarning."""
        entries = [
            SkillEntry(canonical="TensorFlow", aliases=["tf"]),
            SkillEntry(canonical="Terraform", aliases=["tf"]),  # Collision!
        ]

        with pytest.warns(UserWarning, match="Skill alias collision.*tf"):
            SkillRegistry(entries)

    def test_alias_collision_last_wins(self) -> None:
        """When aliases collide, last entry wins."""
        entries = [
            SkillEntry(canonical="TensorFlow", aliases=["tf"]),
            SkillEntry(canonical="Terraform", aliases=["tf"]),
        ]

        with pytest.warns(UserWarning):
            registry = SkillRegistry(entries)

        # Last one (Terraform) should win
        assert registry.normalize("tf") == "Terraform"

    def test_no_warning_when_no_collision(self, registry: SkillRegistry) -> None:
        """No warning emitted when aliases are unique."""
        # The fixture registry has no collisions, should not warn
        import warnings

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            SkillRegistry(registry._entries)
            collision_warnings = [x for x in w if "collision" in str(x.message)]
            assert len(collision_warnings) == 0


class TestSkillRegistryONetIntegration:
    """Test O*NET service integration with SkillRegistry."""

    @pytest.fixture
    def mock_onet_service(self, tmp_path: Path) -> ONetService:
        """Create mock O*NET service."""
        config = ONetConfig(enabled=True, api_key="test-key")
        service = ONetService(config)
        service._cache_dir = tmp_path / "onet_cache"
        service._cache_dir.mkdir(parents=True, exist_ok=True)
        return service

    def test_init_with_onet_service(self, mock_onet_service: ONetService) -> None:
        """Registry accepts optional onet_service parameter."""
        registry = SkillRegistry([], onet_service=mock_onet_service)
        assert registry._onet_service is mock_onet_service

    def test_init_without_onet_service(self) -> None:
        """Registry works without onet_service (default behavior)."""
        registry = SkillRegistry([])
        assert registry._onet_service is None

    def test_lookup_and_cache_returns_none_without_onet(self) -> None:
        """lookup_and_cache returns None when no onet_service configured."""
        registry = SkillRegistry([])
        result = registry.lookup_and_cache("python")
        assert result is None

    def test_lookup_and_cache_skips_known_skills(self, mock_onet_service: ONetService) -> None:
        """lookup_and_cache doesn't call API for skills already in registry."""
        entries = [SkillEntry(canonical="Python", aliases=["py"])]
        registry = SkillRegistry(entries, onet_service=mock_onet_service)

        # Mock the search to track if called
        mock_onet_service.search_occupations = MagicMock(return_value=[])

        result = registry.lookup_and_cache("python")

        # Should return existing entry, not call API
        assert result is not None
        assert result.canonical == "Python"
        mock_onet_service.search_occupations.assert_not_called()

    def test_lookup_and_cache_queries_onet_for_unknown_skill(
        self, mock_onet_service: ONetService
    ) -> None:
        """lookup_and_cache queries O*NET for unknown skills."""
        registry = SkillRegistry([], onet_service=mock_onet_service)

        # Mock successful O*NET response
        mock_onet_service.search_occupations = MagicMock(
            return_value=[ONetOccupation(code="15-1252.00", title="Software Developers")]
        )
        mock_onet_service.get_occupation_skills = MagicMock(
            return_value=[
                ONetSkill(
                    id="2.A.2.b",
                    name="Programming",
                    description="Writing programs",
                    importance=4.75,
                )
            ]
        )

        result = registry.lookup_and_cache("programming")

        assert result is not None
        assert result.canonical == "Programming"
        assert result.onet_code == "2.A.2.b"
        mock_onet_service.search_occupations.assert_called_once_with("programming")

    def test_lookup_and_cache_returns_none_when_no_match(
        self, mock_onet_service: ONetService
    ) -> None:
        """lookup_and_cache returns None when O*NET finds no match."""
        registry = SkillRegistry([], onet_service=mock_onet_service)

        mock_onet_service.search_occupations = MagicMock(return_value=[])

        result = registry.lookup_and_cache("obscure-skill-xyz")

        assert result is None

    def test_lookup_and_cache_adds_entry_to_registry(self, mock_onet_service: ONetService) -> None:
        """lookup_and_cache adds discovered skill to registry."""
        registry = SkillRegistry([], onet_service=mock_onet_service)

        mock_onet_service.search_occupations = MagicMock(
            return_value=[ONetOccupation(code="15-1252.00", title="Software Developers")]
        )
        mock_onet_service.get_occupation_skills = MagicMock(
            return_value=[ONetSkill(id="2.A.2.b", name="Programming")]
        )

        registry.lookup_and_cache("programming")

        # Skill should now be in registry
        assert registry.normalize("programming") == "Programming"
        assert registry.get_onet_code("programming") == "2.A.2.b"

    def test_lookup_and_cache_creates_alias_for_original_query(
        self, mock_onet_service: ONetService
    ) -> None:
        """lookup_and_cache adds original query as alias if different from canonical."""
        registry = SkillRegistry([], onet_service=mock_onet_service)

        mock_onet_service.search_occupations = MagicMock(
            return_value=[ONetOccupation(code="15-1252.00", title="Software Developers")]
        )
        mock_onet_service.get_occupation_skills = MagicMock(
            return_value=[ONetSkill(id="2.A.2.b", name="Computer Programming")]
        )

        result = registry.lookup_and_cache("programming")

        # Original query should be an alias
        assert result is not None
        assert "programming" in result.aliases


class TestSkillRegistryPersistence:
    """Test skill persistence to user skills file (AC #5)."""

    def test_persist_entry_creates_file(self, tmp_path: Path) -> None:
        """_persist_entry creates user skills file if it doesn't exist."""
        skills_path = tmp_path / "user_skills.yaml"
        registry = SkillRegistry([], user_skills_path=skills_path)

        entry = SkillEntry(canonical="NewSkill", aliases=["ns"], onet_code="2.A.1.a")
        registry._add_entry(entry)

        assert skills_path.exists()
        content = skills_path.read_text()
        assert "NewSkill" in content
        assert "ns" in content
        assert "2.A.1.a" in content

    def test_persist_entry_appends_to_existing(self, tmp_path: Path) -> None:
        """_persist_entry appends to existing skills file."""
        skills_path = tmp_path / "user_skills.yaml"
        # Create existing file with one skill
        skills_path.write_text("skills:\n  - canonical: ExistingSkill\n")

        registry = SkillRegistry([], user_skills_path=skills_path)
        entry = SkillEntry(canonical="NewSkill", onet_code="2.A.1.a")
        registry._add_entry(entry)

        content = skills_path.read_text()
        assert "ExistingSkill" in content
        assert "NewSkill" in content

    def test_persist_entry_skipped_without_path(self) -> None:
        """_persist_entry does nothing when user_skills_path is None."""
        registry = SkillRegistry([])  # No user_skills_path
        entry = SkillEntry(canonical="TestSkill")

        # Should not raise, just skip persistence
        registry._add_entry(entry)
        assert registry.normalize("TestSkill") == "TestSkill"

    def test_lookup_and_cache_persists_discovered_skill(self, tmp_path: Path) -> None:
        """lookup_and_cache persists O*NET-discovered skills (AC #5)."""
        skills_path = tmp_path / "discovered_skills.yaml"
        config = ONetConfig(enabled=True, api_key="test-key")
        onet_service = ONetService(config)
        onet_service._cache_dir = tmp_path / "onet_cache"
        onet_service._cache_dir.mkdir(parents=True, exist_ok=True)

        registry = SkillRegistry([], onet_service=onet_service, user_skills_path=skills_path)

        # Mock O*NET responses
        onet_service.search_occupations = MagicMock(
            return_value=[ONetOccupation(code="15-1252.00", title="Software Developers")]
        )
        onet_service.get_occupation_skills = MagicMock(
            return_value=[ONetSkill(id="2.A.2.b", name="Programming")]
        )

        result = registry.lookup_and_cache("programming")

        assert result is not None
        assert skills_path.exists()
        content = skills_path.read_text()
        assert "Programming" in content
        assert "2.A.2.b" in content

    def test_persist_handles_write_error_gracefully(self, tmp_path: Path) -> None:
        """_persist_entry logs warning on write error but doesn't raise."""
        # Use a directory as path to cause write error
        skills_path = tmp_path / "readonly"
        skills_path.mkdir()

        registry = SkillRegistry([], user_skills_path=skills_path)
        entry = SkillEntry(canonical="TestSkill")

        # Should not raise, just log warning
        registry._add_entry(entry)
        # Entry still added to in-memory registry
        assert registry.normalize("TestSkill") == "TestSkill"

    def test_persisted_skills_loaded_in_new_session(self, tmp_path: Path) -> None:
        """Persisted skills should be available in new registry instance (AC #5)."""
        skills_path = tmp_path / "user_skills.yaml"

        # First session: create registry and persist a skill
        registry1 = SkillRegistry([], user_skills_path=skills_path)
        entry = SkillEntry(
            canonical="CloudFormation",
            aliases=["cfn", "cf"],
            onet_code="2.A.3.c",
        )
        registry1._add_entry(entry)

        # Verify persisted to file
        assert skills_path.exists()

        # Second session: load from persisted file
        registry2 = SkillRegistry.load_from_yaml(skills_path)

        # Verify skill is available in new registry
        assert registry2.normalize("cfn") == "CloudFormation"
        assert registry2.normalize("cf") == "CloudFormation"
        assert registry2.get_onet_code("CloudFormation") == "2.A.3.c"


class TestSkillRegistryHasOnetService:
    """Test has_onet_service property (Story 7.17 Issue #3 fix)."""

    def test_has_onet_service_false_when_none(self) -> None:
        """has_onet_service returns False when no service configured."""
        registry = SkillRegistry([])
        assert registry.has_onet_service is False

    def test_has_onet_service_true_when_configured(self, tmp_path: Path) -> None:
        """has_onet_service returns True when service is configured."""
        config = ONetConfig(enabled=True, api_key="test-key")
        onet_service = ONetService(config)
        onet_service._cache_dir = tmp_path / "onet_cache"
        onet_service._cache_dir.mkdir(parents=True, exist_ok=True)

        registry = SkillRegistry([], onet_service=onet_service)
        assert registry.has_onet_service is True
