"""Unit tests for migration framework.

Tests cover:
- MigrationResult dataclass
- MigrationContext dataclass
- Migration abstract base class
- Migration registry and decorators
- Version detection
- Backup and restore operations
- YAML comment preservation
- V1 to V2 migration
"""

from __future__ import annotations

from pathlib import Path

import pytest

from resume_as_code.migrations import CURRENT_SCHEMA_VERSION, LEGACY_VERSION
from resume_as_code.migrations.base import Migration, MigrationContext, MigrationResult


class TestMigrationResultDataclass:
    """Tests for MigrationResult dataclass."""

    def test_migration_result_success_default(self) -> None:
        """Test that success field is set correctly."""
        result = MigrationResult(success=True)
        assert result.success is True

    def test_migration_result_failure(self) -> None:
        """Test failed migration result."""
        result = MigrationResult(success=False, errors=["Something went wrong"])
        assert result.success is False
        assert "Something went wrong" in result.errors

    def test_migration_result_files_modified_default(self) -> None:
        """Test that files_modified defaults to empty list."""
        result = MigrationResult(success=True)
        assert result.files_modified == []

    def test_migration_result_warnings_default(self) -> None:
        """Test that warnings defaults to empty list."""
        result = MigrationResult(success=True)
        assert result.warnings == []

    def test_migration_result_errors_default(self) -> None:
        """Test that errors defaults to empty list."""
        result = MigrationResult(success=True)
        assert result.errors == []

    def test_migration_result_with_files(self) -> None:
        """Test MigrationResult with modified files."""
        files = [Path(".resume.yaml"), Path("work-units/wu-1.yaml")]
        result = MigrationResult(success=True, files_modified=files)
        assert len(result.files_modified) == 2
        assert Path(".resume.yaml") in result.files_modified


class TestMigrationContextDataclass:
    """Tests for MigrationContext dataclass."""

    def test_migration_context_project_path(self, tmp_path: Path) -> None:
        """Test that project_path is set correctly."""
        ctx = MigrationContext(project_path=tmp_path)
        assert ctx.project_path == tmp_path

    def test_migration_context_backup_path_default(self, tmp_path: Path) -> None:
        """Test that backup_path defaults to None."""
        ctx = MigrationContext(project_path=tmp_path)
        assert ctx.backup_path is None

    def test_migration_context_backup_path_set(self, tmp_path: Path) -> None:
        """Test that backup_path can be set."""
        backup = tmp_path / ".resume-backup"
        ctx = MigrationContext(project_path=tmp_path, backup_path=backup)
        assert ctx.backup_path == backup

    def test_migration_context_dry_run_default(self, tmp_path: Path) -> None:
        """Test that dry_run defaults to False."""
        ctx = MigrationContext(project_path=tmp_path)
        assert ctx.dry_run is False

    def test_migration_context_dry_run_true(self, tmp_path: Path) -> None:
        """Test that dry_run can be set to True."""
        ctx = MigrationContext(project_path=tmp_path, dry_run=True)
        assert ctx.dry_run is True


class TestMigrationAbstractClass:
    """Tests for Migration abstract base class."""

    def test_migration_cannot_be_instantiated(self) -> None:
        """Test that Migration abstract class cannot be instantiated directly."""
        with pytest.raises(TypeError, match="abstract"):
            Migration()  # type: ignore[abstract]

    def test_migration_subclass_must_implement_methods(self) -> None:
        """Test that subclass must implement all abstract methods."""

        class IncompleteMigration(Migration):
            from_version = "1.0.0"
            to_version = "2.0.0"
            description = "Test"

            def check_applicable(self, ctx: MigrationContext) -> bool:
                return True

            # Missing preview and apply methods

        with pytest.raises(TypeError, match="abstract"):
            IncompleteMigration()  # type: ignore[abstract]

    def test_migration_subclass_complete(self, tmp_path: Path) -> None:
        """Test that complete subclass can be instantiated."""

        class CompleteMigration(Migration):
            from_version = "1.0.0"
            to_version = "2.0.0"
            description = "Test migration"

            def check_applicable(self, ctx: MigrationContext) -> bool:
                return True

            def preview(self, ctx: MigrationContext) -> list[str]:
                return ["Would do something"]

            def apply(self, ctx: MigrationContext) -> MigrationResult:
                return MigrationResult(success=True)

        migration = CompleteMigration()
        assert migration.from_version == "1.0.0"
        assert migration.to_version == "2.0.0"
        assert migration.description == "Test migration"

        ctx = MigrationContext(project_path=tmp_path)
        assert migration.check_applicable(ctx) is True
        assert migration.preview(ctx) == ["Would do something"]
        assert migration.apply(ctx).success is True


class TestVersionConstants:
    """Tests for version constants in migrations module."""

    def test_current_schema_version_format(self) -> None:
        """Test that CURRENT_SCHEMA_VERSION is a valid semver string."""
        parts = CURRENT_SCHEMA_VERSION.split(".")
        assert len(parts) == 3
        assert all(p.isdigit() for p in parts)

    def test_legacy_version_format(self) -> None:
        """Test that LEGACY_VERSION is a valid semver string."""
        parts = LEGACY_VERSION.split(".")
        assert len(parts) == 3
        assert all(p.isdigit() for p in parts)

    def test_current_version_is_4_0_0(self) -> None:
        """Test that current version is 4.0.0 (Story 12.1)."""
        assert CURRENT_SCHEMA_VERSION == "4.0.0"

    def test_legacy_version_is_1_0_0(self) -> None:
        """Test that legacy version is 1.0.0."""
        assert LEGACY_VERSION == "1.0.0"


class TestMigrationRegistry:
    """Tests for migration registry and path resolution."""

    def test_register_migration_decorator(self) -> None:
        """Test that @register_migration decorator registers migration."""
        from resume_as_code.migrations.registry import (
            _migrations,
            register_migration,
        )

        initial_count = len(_migrations)

        @register_migration
        class TestMigration(Migration):
            from_version = "99.0.0"
            to_version = "99.1.0"
            description = "Test migration"

            def check_applicable(self, ctx: MigrationContext) -> bool:
                return True

            def preview(self, ctx: MigrationContext) -> list[str]:
                return []

            def apply(self, ctx: MigrationContext) -> MigrationResult:
                return MigrationResult(success=True)

        assert len(_migrations) == initial_count + 1
        # Clean up
        _migrations.remove(TestMigration)

    def test_get_migration_path_single_step(self) -> None:
        """Test migration path with single migration."""
        from resume_as_code.migrations.registry import (
            _migrations,
            get_migration_path,
            register_migration,
        )

        @register_migration
        class TestMigration(Migration):
            from_version = "98.0.0"
            to_version = "98.1.0"
            description = "Test"

            def check_applicable(self, ctx: MigrationContext) -> bool:
                return True

            def preview(self, ctx: MigrationContext) -> list[str]:
                return []

            def apply(self, ctx: MigrationContext) -> MigrationResult:
                return MigrationResult(success=True)

        path = get_migration_path("98.0.0", "98.1.0")
        assert len(path) == 1
        assert path[0] is TestMigration

        # Clean up
        _migrations.remove(TestMigration)

    def test_get_migration_path_multi_step(self) -> None:
        """Test migration path with multiple migrations."""
        from resume_as_code.migrations.registry import (
            _migrations,
            get_migration_path,
            register_migration,
        )

        @register_migration
        class TestMigrationA(Migration):
            from_version = "97.0.0"
            to_version = "97.1.0"
            description = "Test A"

            def check_applicable(self, ctx: MigrationContext) -> bool:
                return True

            def preview(self, ctx: MigrationContext) -> list[str]:
                return []

            def apply(self, ctx: MigrationContext) -> MigrationResult:
                return MigrationResult(success=True)

        @register_migration
        class TestMigrationB(Migration):
            from_version = "97.1.0"
            to_version = "97.2.0"
            description = "Test B"

            def check_applicable(self, ctx: MigrationContext) -> bool:
                return True

            def preview(self, ctx: MigrationContext) -> list[str]:
                return []

            def apply(self, ctx: MigrationContext) -> MigrationResult:
                return MigrationResult(success=True)

        path = get_migration_path("97.0.0", "97.2.0")
        assert len(path) == 2
        assert path[0] is TestMigrationA
        assert path[1] is TestMigrationB

        # Clean up
        _migrations.remove(TestMigrationA)
        _migrations.remove(TestMigrationB)

    def test_get_migration_path_not_found(self) -> None:
        """Test that missing migration path raises ValueError."""
        from resume_as_code.migrations.registry import get_migration_path

        with pytest.raises(ValueError, match="No migration path"):
            get_migration_path("0.0.1", "0.0.2")


class TestSchemaVersionDetection:
    """Tests for schema version detection."""

    def test_detect_schema_version_legacy_no_file(self, tmp_path: Path) -> None:
        """Test that missing config returns LEGACY_VERSION."""
        from resume_as_code.migrations.registry import detect_schema_version

        version = detect_schema_version(tmp_path)
        assert version == LEGACY_VERSION

    def test_detect_schema_version_legacy_no_field(self, tmp_path: Path) -> None:
        """Test that config without schema_version returns LEGACY_VERSION."""
        from resume_as_code.migrations.registry import detect_schema_version

        config_path = tmp_path / ".resume.yaml"
        config_path.write_text("output_dir: ./dist\n")

        version = detect_schema_version(tmp_path)
        assert version == LEGACY_VERSION

    def test_detect_schema_version_explicit(self, tmp_path: Path) -> None:
        """Test that config with schema_version returns that version."""
        from resume_as_code.migrations.registry import detect_schema_version

        config_path = tmp_path / ".resume.yaml"
        config_path.write_text("schema_version: 2.0.0\noutput_dir: ./dist\n")

        version = detect_schema_version(tmp_path)
        assert version == "2.0.0"


class TestBackupSystem:
    """Tests for backup creation and restoration."""

    def test_create_backup_creates_directory(self, tmp_path: Path) -> None:
        """Test that create_backup creates a backup directory."""
        from resume_as_code.migrations.backup import create_backup

        # Create a minimal project
        config_path = tmp_path / ".resume.yaml"
        config_path.write_text("output_dir: ./dist\n")

        backup_path = create_backup(tmp_path)

        assert backup_path.exists()
        assert backup_path.is_dir()
        assert backup_path.name.startswith(".resume-backup-")

    def test_create_backup_copies_config_file(self, tmp_path: Path) -> None:
        """Test that create_backup copies .resume.yaml."""
        from resume_as_code.migrations.backup import create_backup

        # Create a config file
        config_path = tmp_path / ".resume.yaml"
        config_path.write_text("output_dir: ./dist\ntest_field: value\n")

        backup_path = create_backup(tmp_path)

        backup_config = backup_path / ".resume.yaml"
        assert backup_config.exists()
        assert "test_field: value" in backup_config.read_text()

    def test_create_backup_copies_positions_file(self, tmp_path: Path) -> None:
        """Test that create_backup copies positions.yaml if it exists."""
        from resume_as_code.migrations.backup import create_backup

        # Create config and positions files
        (tmp_path / ".resume.yaml").write_text("output_dir: ./dist\n")
        (tmp_path / "positions.yaml").write_text("- id: pos-1\n")

        backup_path = create_backup(tmp_path)

        backup_positions = backup_path / "positions.yaml"
        assert backup_positions.exists()
        assert "pos-1" in backup_positions.read_text()

    def test_create_backup_copies_work_units_directory(self, tmp_path: Path) -> None:
        """Test that create_backup copies work-units/ directory."""
        from resume_as_code.migrations.backup import create_backup

        # Create config and work-units directory
        (tmp_path / ".resume.yaml").write_text("output_dir: ./dist\n")
        work_units = tmp_path / "work-units"
        work_units.mkdir()
        (work_units / "wu-1.yaml").write_text("id: wu-1\ntitle: Test\n")

        backup_path = create_backup(tmp_path)

        backup_wu = backup_path / "work-units" / "wu-1.yaml"
        assert backup_wu.exists()
        assert "wu-1" in backup_wu.read_text()

    def test_create_backup_naming_format(self, tmp_path: Path) -> None:
        """Test backup directory naming follows pattern."""
        import re

        from resume_as_code.migrations.backup import create_backup

        (tmp_path / ".resume.yaml").write_text("output_dir: ./dist\n")

        backup_path = create_backup(tmp_path)

        # Pattern: .resume-backup-YYYY-MM-DD-HHMMSS
        pattern = r"\.resume-backup-\d{4}-\d{2}-\d{2}-\d{6}"
        assert re.match(pattern, backup_path.name)

    def test_restore_from_backup(self, tmp_path: Path) -> None:
        """Test that restore_from_backup restores files."""
        from resume_as_code.migrations.backup import create_backup, restore_from_backup

        # Create original files
        config_path = tmp_path / ".resume.yaml"
        config_path.write_text("original: content\n")

        # Create backup
        backup_path = create_backup(tmp_path)

        # Modify original
        config_path.write_text("modified: content\n")
        assert "modified" in config_path.read_text()

        # Restore from backup
        restored = restore_from_backup(backup_path, tmp_path)

        # Original content should be restored
        assert "original" in config_path.read_text()
        assert config_path in restored

    def test_restore_from_backup_restores_directories(self, tmp_path: Path) -> None:
        """Test that restore_from_backup restores directories."""
        from resume_as_code.migrations.backup import create_backup, restore_from_backup

        # Create original files
        (tmp_path / ".resume.yaml").write_text("output_dir: ./dist\n")
        work_units = tmp_path / "work-units"
        work_units.mkdir()
        (work_units / "wu-1.yaml").write_text("id: wu-1\ntitle: Original\n")

        # Create backup
        backup_path = create_backup(tmp_path)

        # Modify work unit
        (work_units / "wu-1.yaml").write_text("id: wu-1\ntitle: Modified\n")

        # Restore from backup
        restore_from_backup(backup_path, tmp_path)

        # Original content should be restored
        assert "Original" in (work_units / "wu-1.yaml").read_text()


class TestYamlCommentPreservation:
    """Tests for YAML comment preservation."""

    def test_load_yaml_preserve_returns_commented_map(self, tmp_path: Path) -> None:
        """Test that load_yaml_preserve returns a CommentedMap."""
        from ruamel.yaml.comments import CommentedMap

        from resume_as_code.migrations.yaml_handler import load_yaml_preserve

        config = tmp_path / "test.yaml"
        config.write_text("key: value\n")

        data = load_yaml_preserve(config)

        assert isinstance(data, CommentedMap)
        assert data["key"] == "value"

    def test_load_yaml_preserve_empty_file(self, tmp_path: Path) -> None:
        """Test that load_yaml_preserve handles empty files."""
        from ruamel.yaml.comments import CommentedMap

        from resume_as_code.migrations.yaml_handler import load_yaml_preserve

        config = tmp_path / "empty.yaml"
        config.write_text("")

        data = load_yaml_preserve(config)

        assert isinstance(data, CommentedMap)
        assert len(data) == 0

    def test_save_yaml_preserve_writes_file(self, tmp_path: Path) -> None:
        """Test that save_yaml_preserve writes a file."""
        from ruamel.yaml.comments import CommentedMap

        from resume_as_code.migrations.yaml_handler import save_yaml_preserve

        data = CommentedMap()
        data["key"] = "value"

        output_path = tmp_path / "output.yaml"
        save_yaml_preserve(output_path, data)

        assert output_path.exists()
        assert "key: value" in output_path.read_text()

    def test_yaml_comment_preservation_roundtrip(self, tmp_path: Path) -> None:
        """Test that comments are preserved in load/save roundtrip."""
        from resume_as_code.migrations.yaml_handler import (
            load_yaml_preserve,
            save_yaml_preserve,
        )

        # Create a file with comments
        original = tmp_path / "original.yaml"
        original.write_text(
            """# This is a header comment
key1: value1  # inline comment
# Section comment
key2: value2
"""
        )

        # Load and save
        data = load_yaml_preserve(original)
        output = tmp_path / "output.yaml"
        save_yaml_preserve(output, data)

        content = output.read_text()

        # Comments should be preserved
        assert "# This is a header comment" in content
        assert "# inline comment" in content
        assert "# Section comment" in content

    def test_yaml_modification_preserves_comments(self, tmp_path: Path) -> None:
        """Test that modifying data preserves existing comments."""
        from resume_as_code.migrations.yaml_handler import (
            load_yaml_preserve,
            save_yaml_preserve,
        )

        # Create a file with comments
        original = tmp_path / "original.yaml"
        original.write_text(
            """# Header comment
existing: old_value
"""
        )

        # Load, modify, save
        data = load_yaml_preserve(original)
        data["new_key"] = "new_value"
        output = tmp_path / "output.yaml"
        save_yaml_preserve(output, data)

        content = output.read_text()

        # Original comment should still be there
        assert "# Header comment" in content
        assert "existing: old_value" in content
        assert "new_key: new_value" in content


class TestMigrationV1ToV2:
    """Tests for v1.0.0 to v2.0.0 migration."""

    def test_v1_to_v2_check_applicable_no_file(self, tmp_path: Path) -> None:
        """Test check_applicable returns False when no config file."""
        from resume_as_code.migrations.v1_to_v2 import MigrationV1ToV2

        migration = MigrationV1ToV2()
        ctx = MigrationContext(project_path=tmp_path)

        assert migration.check_applicable(ctx) is False

    def test_v1_to_v2_check_applicable_legacy_config(self, tmp_path: Path) -> None:
        """Test check_applicable returns True for legacy config."""
        from resume_as_code.migrations.v1_to_v2 import MigrationV1ToV2

        # Create legacy config (no schema_version)
        config = tmp_path / ".resume.yaml"
        config.write_text("output_dir: ./dist\n")

        migration = MigrationV1ToV2()
        ctx = MigrationContext(project_path=tmp_path)

        assert migration.check_applicable(ctx) is True

    def test_v1_to_v2_check_applicable_already_migrated(self, tmp_path: Path) -> None:
        """Test check_applicable returns False when already migrated."""
        from resume_as_code.migrations.v1_to_v2 import MigrationV1ToV2

        # Create config with schema_version
        config = tmp_path / ".resume.yaml"
        config.write_text("schema_version: 2.0.0\noutput_dir: ./dist\n")

        migration = MigrationV1ToV2()
        ctx = MigrationContext(project_path=tmp_path)

        assert migration.check_applicable(ctx) is False

    def test_v1_to_v2_preview(self, tmp_path: Path) -> None:
        """Test preview returns expected changes."""
        from resume_as_code.migrations.v1_to_v2 import MigrationV1ToV2

        # Create legacy config
        config = tmp_path / ".resume.yaml"
        config.write_text("output_dir: ./dist\n")

        migration = MigrationV1ToV2()
        ctx = MigrationContext(project_path=tmp_path)

        changes = migration.preview(ctx)

        assert len(changes) == 1
        assert "schema_version: 2.0.0" in changes[0]

    def test_v1_to_v2_preview_no_file(self, tmp_path: Path) -> None:
        """Test preview returns empty list when no config."""
        from resume_as_code.migrations.v1_to_v2 import MigrationV1ToV2

        migration = MigrationV1ToV2()
        ctx = MigrationContext(project_path=tmp_path)

        changes = migration.preview(ctx)

        assert changes == []

    def test_v1_to_v2_apply_adds_schema_version(self, tmp_path: Path) -> None:
        """Test apply adds schema_version to config."""
        from resume_as_code.migrations.v1_to_v2 import MigrationV1ToV2

        # Create legacy config
        config = tmp_path / ".resume.yaml"
        config.write_text("output_dir: ./dist\ndefault_format: pdf\n")

        migration = MigrationV1ToV2()
        ctx = MigrationContext(project_path=tmp_path)

        result = migration.apply(ctx)

        assert result.success is True
        assert config in result.files_modified

        content = config.read_text()
        assert "schema_version: 2.0.0" in content
        assert "output_dir: ./dist" in content

    def test_v1_to_v2_apply_preserves_comments(self, tmp_path: Path) -> None:
        """Test apply preserves YAML comments."""
        from resume_as_code.migrations.v1_to_v2 import MigrationV1ToV2

        # Create legacy config with comments
        config = tmp_path / ".resume.yaml"
        config.write_text(
            """# My resume configuration
output_dir: ./dist  # Output directory
default_format: pdf
"""
        )

        migration = MigrationV1ToV2()
        ctx = MigrationContext(project_path=tmp_path)

        result = migration.apply(ctx)

        assert result.success is True
        content = config.read_text()
        assert "# My resume configuration" in content
        assert "# Output directory" in content

    def test_v1_to_v2_apply_no_file(self, tmp_path: Path) -> None:
        """Test apply returns warning when no config file."""
        from resume_as_code.migrations.v1_to_v2 import MigrationV1ToV2

        migration = MigrationV1ToV2()
        ctx = MigrationContext(project_path=tmp_path)

        result = migration.apply(ctx)

        assert result.success is True
        assert len(result.warnings) == 1
        assert ".resume.yaml not found" in result.warnings[0]

    def test_v1_to_v2_apply_idempotent(self, tmp_path: Path) -> None:
        """Test apply is idempotent (safe to run multiple times)."""
        from resume_as_code.migrations.v1_to_v2 import MigrationV1ToV2

        # Create config already with schema_version
        config = tmp_path / ".resume.yaml"
        config.write_text("schema_version: 2.0.0\noutput_dir: ./dist\n")

        migration = MigrationV1ToV2()
        ctx = MigrationContext(project_path=tmp_path)

        result = migration.apply(ctx)

        assert result.success is True
        assert len(result.warnings) == 1
        assert "already exists" in result.warnings[0]
        assert len(result.files_modified) == 0

    def test_v1_to_v2_dry_run(self, tmp_path: Path) -> None:
        """Test apply in dry_run mode doesn't modify files."""
        from resume_as_code.migrations.v1_to_v2 import MigrationV1ToV2

        # Create legacy config
        config = tmp_path / ".resume.yaml"
        original_content = "output_dir: ./dist\n"
        config.write_text(original_content)

        migration = MigrationV1ToV2()
        ctx = MigrationContext(project_path=tmp_path, dry_run=True)

        result = migration.apply(ctx)

        assert result.success is True
        # File should not be modified in dry_run mode
        assert len(result.files_modified) == 0
        assert config.read_text() == original_content

    def test_v1_to_v2_version_attributes(self) -> None:
        """Test migration has correct version attributes."""
        from resume_as_code.migrations.v1_to_v2 import MigrationV1ToV2

        migration = MigrationV1ToV2()

        assert migration.from_version == "1.0.0"
        assert migration.to_version == "2.0.0"
        assert "schema_version" in migration.description.lower()

    def test_v1_to_v2_registered_in_registry(self) -> None:
        """Test migration is registered in the registry."""
        from resume_as_code.migrations.registry import get_migration_path

        path = get_migration_path("1.0.0", "2.0.0")

        assert len(path) == 1
        assert path[0].from_version == "1.0.0"
        assert path[0].to_version == "2.0.0"


class TestMigrationV2ToV3:
    """Tests for v2.0.0 to v3.0.0 migration (Story 9.2)."""

    def test_v2_to_v3_check_applicable_no_file(self, tmp_path: Path) -> None:
        """Test check_applicable returns False when no config file."""
        from resume_as_code.migrations.v2_to_v3 import MigrationV2ToV3

        migration = MigrationV2ToV3()
        ctx = MigrationContext(project_path=tmp_path)

        assert migration.check_applicable(ctx) is False

    def test_v2_to_v3_check_applicable_v2_with_embedded_data(self, tmp_path: Path) -> None:
        """Test check_applicable returns True for v2 config with embedded data."""
        from resume_as_code.migrations.v2_to_v3 import MigrationV2ToV3

        config = tmp_path / ".resume.yaml"
        config.write_text(
            """schema_version: 2.0.0
output_dir: ./dist
profile:
  name: Test User
  email: test@example.com
"""
        )

        migration = MigrationV2ToV3()
        ctx = MigrationContext(project_path=tmp_path)

        assert migration.check_applicable(ctx) is True

    def test_v2_to_v3_check_applicable_already_v3(self, tmp_path: Path) -> None:
        """Test check_applicable returns False when already at v3."""
        from resume_as_code.migrations.v2_to_v3 import MigrationV2ToV3

        config = tmp_path / ".resume.yaml"
        config.write_text("schema_version: 3.0.0\noutput_dir: ./dist\n")

        migration = MigrationV2ToV3()
        ctx = MigrationContext(project_path=tmp_path)

        assert migration.check_applicable(ctx) is False

    def test_v2_to_v3_preview_profile(self, tmp_path: Path) -> None:
        """Test preview lists profile extraction."""
        from resume_as_code.migrations.v2_to_v3 import MigrationV2ToV3

        config = tmp_path / ".resume.yaml"
        config.write_text(
            """schema_version: 2.0.0
profile:
  name: Test User
"""
        )

        migration = MigrationV2ToV3()
        ctx = MigrationContext(project_path=tmp_path)

        changes = migration.preview(ctx)

        assert any("profile" in c.lower() for c in changes)
        assert any("profile.yaml" in c for c in changes)

    def test_v2_to_v3_preview_certifications(self, tmp_path: Path) -> None:
        """Test preview lists certifications extraction with count."""
        from resume_as_code.migrations.v2_to_v3 import MigrationV2ToV3

        config = tmp_path / ".resume.yaml"
        config.write_text(
            """schema_version: 2.0.0
certifications:
  - name: AWS SAP
  - name: CISSP
"""
        )

        migration = MigrationV2ToV3()
        ctx = MigrationContext(project_path=tmp_path)

        changes = migration.preview(ctx)

        assert any("certifications" in c.lower() and "2 items" in c for c in changes)

    def test_v2_to_v3_apply_extracts_profile(self, tmp_path: Path) -> None:
        """Test apply extracts profile to profile.yaml."""
        from resume_as_code.migrations.v2_to_v3 import MigrationV2ToV3

        config = tmp_path / ".resume.yaml"
        config.write_text(
            """schema_version: 2.0.0
output_dir: ./dist
profile:
  name: Test User
  email: test@example.com
"""
        )

        migration = MigrationV2ToV3()
        ctx = MigrationContext(project_path=tmp_path)

        result = migration.apply(ctx)

        assert result.success is True
        profile_path = tmp_path / "profile.yaml"
        assert profile_path.exists()
        content = profile_path.read_text()
        assert "Test User" in content
        assert "test@example.com" in content

    def test_v2_to_v3_apply_extracts_certifications(self, tmp_path: Path) -> None:
        """Test apply extracts certifications to certifications.yaml."""
        from resume_as_code.migrations.v2_to_v3 import MigrationV2ToV3

        config = tmp_path / ".resume.yaml"
        config.write_text(
            """schema_version: 2.0.0
certifications:
  - name: AWS SAP
    issuer: Amazon
  - name: CISSP
    issuer: ISC2
"""
        )

        migration = MigrationV2ToV3()
        ctx = MigrationContext(project_path=tmp_path)

        result = migration.apply(ctx)

        assert result.success is True
        certs_path = tmp_path / "certifications.yaml"
        assert certs_path.exists()
        content = certs_path.read_text()
        assert "AWS SAP" in content
        assert "CISSP" in content

    def test_v2_to_v3_apply_extracts_career_highlights_to_highlights(self, tmp_path: Path) -> None:
        """Test apply extracts career_highlights to highlights.yaml."""
        from resume_as_code.migrations.v2_to_v3 import MigrationV2ToV3

        config = tmp_path / ".resume.yaml"
        config.write_text(
            """schema_version: 2.0.0
career_highlights:
  - text: Led major transformation
  - text: Saved $1M annually
"""
        )

        migration = MigrationV2ToV3()
        ctx = MigrationContext(project_path=tmp_path)

        result = migration.apply(ctx)

        assert result.success is True
        highlights_path = tmp_path / "highlights.yaml"
        assert highlights_path.exists()
        content = highlights_path.read_text()
        assert "Led major transformation" in content
        assert "$1M" in content

    def test_v2_to_v3_apply_removes_from_config(self, tmp_path: Path) -> None:
        """Test apply removes extracted data from .resume.yaml."""
        from resume_as_code.migrations.v2_to_v3 import MigrationV2ToV3

        config = tmp_path / ".resume.yaml"
        config.write_text(
            """schema_version: 2.0.0
output_dir: ./dist
profile:
  name: Test User
certifications:
  - name: AWS SAP
"""
        )

        migration = MigrationV2ToV3()
        ctx = MigrationContext(project_path=tmp_path)

        migration.apply(ctx)

        content = config.read_text()
        assert "output_dir: ./dist" in content
        assert "profile:" not in content
        assert "certifications:" not in content

    def test_v2_to_v3_apply_updates_schema_version(self, tmp_path: Path) -> None:
        """Test apply updates schema_version to 3.0.0."""
        from resume_as_code.migrations.v2_to_v3 import MigrationV2ToV3

        config = tmp_path / ".resume.yaml"
        config.write_text(
            """schema_version: 2.0.0
output_dir: ./dist
profile:
  name: Test User
"""
        )

        migration = MigrationV2ToV3()
        ctx = MigrationContext(project_path=tmp_path)

        migration.apply(ctx)

        content = config.read_text()
        assert "schema_version: 3.0.0" in content
        assert "schema_version: 2.0.0" not in content

    def test_v2_to_v3_apply_idempotent(self, tmp_path: Path) -> None:
        """Test apply is idempotent (safe to run multiple times)."""
        from resume_as_code.migrations.v2_to_v3 import MigrationV2ToV3

        config = tmp_path / ".resume.yaml"
        config.write_text("schema_version: 3.0.0\noutput_dir: ./dist\n")

        migration = MigrationV2ToV3()
        ctx = MigrationContext(project_path=tmp_path)

        result = migration.apply(ctx)

        assert result.success is True
        assert len(result.warnings) == 1
        assert "v3.0.0" in result.warnings[0]

    def test_v2_to_v3_dry_run(self, tmp_path: Path) -> None:
        """Test apply in dry_run mode doesn't modify files."""
        from resume_as_code.migrations.v2_to_v3 import MigrationV2ToV3

        config = tmp_path / ".resume.yaml"
        original_content = """schema_version: 2.0.0
output_dir: ./dist
profile:
  name: Test User
"""
        config.write_text(original_content)

        migration = MigrationV2ToV3()
        ctx = MigrationContext(project_path=tmp_path, dry_run=True)

        result = migration.apply(ctx)

        assert result.success is True
        assert len(result.files_modified) == 0
        # Config should not be modified
        assert config.read_text() == original_content
        # profile.yaml should not be created
        assert not (tmp_path / "profile.yaml").exists()

    def test_v2_to_v3_version_attributes(self) -> None:
        """Test migration has correct version attributes."""
        from resume_as_code.migrations.v2_to_v3 import MigrationV2ToV3

        migration = MigrationV2ToV3()

        assert migration.from_version == "2.0.0"
        assert migration.to_version == "3.0.0"
        assert "separate" in migration.description.lower()

    def test_v2_to_v3_registered_in_registry(self) -> None:
        """Test migration is registered in the registry."""
        from resume_as_code.migrations.registry import get_migration_path

        path = get_migration_path("2.0.0", "3.0.0")

        assert len(path) == 1
        assert path[0].from_version == "2.0.0"
        assert path[0].to_version == "3.0.0"

    def test_v2_to_v3_full_path_from_v1(self) -> None:
        """Test migration path from v1 to v3 goes through v2."""
        from resume_as_code.migrations.registry import get_migration_path

        path = get_migration_path("1.0.0", "3.0.0")

        assert len(path) == 2
        assert path[0].from_version == "1.0.0"
        assert path[0].to_version == "2.0.0"
        assert path[1].from_version == "2.0.0"
        assert path[1].to_version == "3.0.0"

    def test_v2_to_v3_apply_preserves_comments(self, tmp_path: Path) -> None:
        """Test apply preserves YAML comments in .resume.yaml."""
        from resume_as_code.migrations.v2_to_v3 import MigrationV2ToV3

        config = tmp_path / ".resume.yaml"
        config.write_text(
            """# My resume configuration
schema_version: 2.0.0
output_dir: ./dist  # Output directory
profile:
  name: Test User
"""
        )

        migration = MigrationV2ToV3()
        ctx = MigrationContext(project_path=tmp_path)

        migration.apply(ctx)

        content = config.read_text()
        assert "# My resume configuration" in content
        assert "# Output directory" in content

    def test_v2_to_v3_merges_with_existing_file(self, tmp_path: Path) -> None:
        """Test apply merges with existing data files."""
        from resume_as_code.migrations.v2_to_v3 import MigrationV2ToV3

        config = tmp_path / ".resume.yaml"
        config.write_text(
            """schema_version: 2.0.0
certifications:
  - name: AWS SAP
"""
        )

        # Pre-existing certifications file
        existing_certs = tmp_path / "certifications.yaml"
        existing_certs.write_text("- name: CISSP\n")

        migration = MigrationV2ToV3()
        ctx = MigrationContext(project_path=tmp_path)

        result = migration.apply(ctx)

        assert result.success is True
        assert any("existed" in w.lower() for w in result.warnings)

        # Both certs should be present (merged)
        content = existing_certs.read_text()
        assert "CISSP" in content
        assert "AWS SAP" in content

    def test_v2_to_v3_all_data_files(self, tmp_path: Path) -> None:
        """Test apply extracts all data types to correct files."""
        from resume_as_code.migrations.v2_to_v3 import MigrationV2ToV3

        config = tmp_path / ".resume.yaml"
        config.write_text(
            """schema_version: 2.0.0
output_dir: ./dist
profile:
  name: Test User
certifications:
  - name: AWS SAP
education:
  - degree: BS Computer Science
career_highlights:
  - text: Major achievement
publications:
  - title: My Paper
board_roles:
  - organization: Tech Board
"""
        )

        migration = MigrationV2ToV3()
        ctx = MigrationContext(project_path=tmp_path)

        result = migration.apply(ctx)

        assert result.success is True

        # Check all files were created
        assert (tmp_path / "profile.yaml").exists()
        assert (tmp_path / "certifications.yaml").exists()
        assert (tmp_path / "education.yaml").exists()
        assert (tmp_path / "highlights.yaml").exists()
        assert (tmp_path / "publications.yaml").exists()
        assert (tmp_path / "board-roles.yaml").exists()

        # Check config was cleaned
        content = config.read_text()
        assert "schema_version: 3.0.0" in content
        assert "output_dir: ./dist" in content
        for field in [
            "profile",
            "certifications",
            "education",
            "career_highlights",
            "publications",
            "board_roles",
        ]:
            assert f"{field}:" not in content


class TestMigrationV3ToV4:
    """Tests for v3.0.0 to v4.0.0 migration (Story 12.1).

    This migration adds the required archetype field to all work units
    via inference.
    """

    def test_v3_to_v4_check_applicable_no_file(self, tmp_path: Path) -> None:
        """Test check_applicable returns False when no config file."""
        from resume_as_code.migrations.v3_to_v4 import MigrationV3ToV4

        migration = MigrationV3ToV4()
        ctx = MigrationContext(project_path=tmp_path)

        assert migration.check_applicable(ctx) is False

    def test_v3_to_v4_check_applicable_v3_config(self, tmp_path: Path) -> None:
        """Test check_applicable returns True for v3 config."""
        from resume_as_code.migrations.v3_to_v4 import MigrationV3ToV4

        config = tmp_path / ".resume.yaml"
        config.write_text("schema_version: 3.0.0\noutput_dir: ./dist\n")

        migration = MigrationV3ToV4()
        ctx = MigrationContext(project_path=tmp_path)

        assert migration.check_applicable(ctx) is True

    def test_v3_to_v4_check_applicable_already_v4(self, tmp_path: Path) -> None:
        """Test check_applicable returns False when already at v4."""
        from resume_as_code.migrations.v3_to_v4 import MigrationV3ToV4

        config = tmp_path / ".resume.yaml"
        config.write_text("schema_version: 4.0.0\noutput_dir: ./dist\n")

        migration = MigrationV3ToV4()
        ctx = MigrationContext(project_path=tmp_path)

        assert migration.check_applicable(ctx) is False

    def test_v3_to_v4_check_applicable_work_units_without_archetype(self, tmp_path: Path) -> None:
        """Test check_applicable returns True when work units lack archetype."""
        from resume_as_code.migrations.v3_to_v4 import MigrationV3ToV4

        config = tmp_path / ".resume.yaml"
        config.write_text("schema_version: 3.0.0\noutput_dir: ./dist\n")

        # Create work unit without archetype
        work_units = tmp_path / "work-units"
        work_units.mkdir()
        (work_units / "wu-2024-01-01-test.yaml").write_text(
            """id: wu-2024-01-01-test
title: Test work unit title here
problem:
  statement: This is the problem statement
actions:
  - Did some action here
outcome:
  result: Achieved results
"""
        )

        migration = MigrationV3ToV4()
        ctx = MigrationContext(project_path=tmp_path)

        assert migration.check_applicable(ctx) is True

    def test_v3_to_v4_preview_shows_archetype(self, tmp_path: Path) -> None:
        """Test preview shows inferred archetype for each work unit."""
        from resume_as_code.migrations.v3_to_v4 import MigrationV3ToV4

        config = tmp_path / ".resume.yaml"
        config.write_text("schema_version: 3.0.0\noutput_dir: ./dist\n")

        work_units = tmp_path / "work-units"
        work_units.mkdir()
        (work_units / "wu-2024-01-01-test.yaml").write_text(
            """id: wu-2024-01-01-test
title: Built new authentication platform
problem:
  statement: Needed secure authentication system
actions:
  - Designed architecture from scratch
outcome:
  result: Launched new platform
"""
        )

        migration = MigrationV3ToV4()
        ctx = MigrationContext(project_path=tmp_path)

        changes = migration.preview(ctx)

        # Should show archetype and confidence for work unit
        assert any("archetype=" in c for c in changes)
        assert any("confidence=" in c for c in changes)
        # Should show version update
        assert any("4.0.0" in c for c in changes)

    def test_v3_to_v4_apply_adds_archetype(self, tmp_path: Path) -> None:
        """Test apply adds archetype field to work units."""
        from resume_as_code.migrations.v3_to_v4 import MigrationV3ToV4

        config = tmp_path / ".resume.yaml"
        config.write_text("schema_version: 3.0.0\noutput_dir: ./dist\n")

        work_units = tmp_path / "work-units"
        work_units.mkdir()
        wu_file = work_units / "wu-2024-01-01-test.yaml"
        wu_file.write_text(
            """id: wu-2024-01-01-test
title: Built new authentication platform
problem:
  statement: Needed secure authentication system
actions:
  - Designed architecture from scratch
outcome:
  result: Launched new platform
"""
        )

        migration = MigrationV3ToV4()
        ctx = MigrationContext(project_path=tmp_path)

        result = migration.apply(ctx)

        assert result.success is True
        assert wu_file in result.files_modified

        # Check archetype was added
        content = wu_file.read_text()
        assert "archetype:" in content

    def test_v3_to_v4_apply_updates_schema_version(self, tmp_path: Path) -> None:
        """Test apply updates schema_version to 4.0.0."""
        from resume_as_code.migrations.v3_to_v4 import MigrationV3ToV4

        config = tmp_path / ".resume.yaml"
        config.write_text("schema_version: 3.0.0\noutput_dir: ./dist\n")

        migration = MigrationV3ToV4()
        ctx = MigrationContext(project_path=tmp_path)

        migration.apply(ctx)

        content = config.read_text()
        assert "schema_version: 4.0.0" in content
        assert "schema_version: 3.0.0" not in content

    def test_v3_to_v4_apply_idempotent(self, tmp_path: Path) -> None:
        """Test apply is idempotent (safe to run multiple times)."""
        from resume_as_code.migrations.v3_to_v4 import MigrationV3ToV4

        config = tmp_path / ".resume.yaml"
        config.write_text("schema_version: 4.0.0\noutput_dir: ./dist\n")

        migration = MigrationV3ToV4()
        ctx = MigrationContext(project_path=tmp_path)

        result = migration.apply(ctx)

        assert result.success is True
        assert len(result.warnings) == 1
        assert "v4.0.0" in result.warnings[0]

    def test_v3_to_v4_dry_run(self, tmp_path: Path) -> None:
        """Test apply in dry_run mode doesn't modify files."""
        from resume_as_code.migrations.v3_to_v4 import MigrationV3ToV4

        config = tmp_path / ".resume.yaml"
        original_config_content = "schema_version: 3.0.0\noutput_dir: ./dist\n"
        config.write_text(original_config_content)

        work_units = tmp_path / "work-units"
        work_units.mkdir()
        wu_file = work_units / "wu-2024-01-01-test.yaml"
        original_wu_content = """id: wu-2024-01-01-test
title: Test work unit
problem:
  statement: Problem statement here
actions:
  - Did some action
outcome:
  result: Achieved results
"""
        wu_file.write_text(original_wu_content)

        migration = MigrationV3ToV4()
        ctx = MigrationContext(project_path=tmp_path, dry_run=True)

        result = migration.apply(ctx)

        assert result.success is True
        assert len(result.files_modified) == 0
        # Files should not be modified
        assert config.read_text() == original_config_content
        assert wu_file.read_text() == original_wu_content

    def test_v3_to_v4_version_attributes(self) -> None:
        """Test migration has correct version attributes."""
        from resume_as_code.migrations.v3_to_v4 import MigrationV3ToV4

        migration = MigrationV3ToV4()

        assert migration.from_version == "3.0.0"
        assert migration.to_version == "4.0.0"
        assert "archetype" in migration.description.lower()

    def test_v3_to_v4_registered_in_registry(self) -> None:
        """Test migration is registered in the registry."""
        from resume_as_code.migrations.registry import get_migration_path

        path = get_migration_path("3.0.0", "4.0.0")

        assert len(path) == 1
        assert path[0].from_version == "3.0.0"
        assert path[0].to_version == "4.0.0"

    def test_v3_to_v4_full_path_from_v1(self) -> None:
        """Test migration path from v1 to v4 goes through all versions."""
        from resume_as_code.migrations.registry import get_migration_path

        path = get_migration_path("1.0.0", "4.0.0")

        assert len(path) == 3
        assert path[0].from_version == "1.0.0"
        assert path[0].to_version == "2.0.0"
        assert path[1].from_version == "2.0.0"
        assert path[1].to_version == "3.0.0"
        assert path[2].from_version == "3.0.0"
        assert path[2].to_version == "4.0.0"

    def test_v3_to_v4_apply_preserves_comments(self, tmp_path: Path) -> None:
        """Test apply preserves YAML comments in config file."""
        from resume_as_code.migrations.v3_to_v4 import MigrationV3ToV4

        config = tmp_path / ".resume.yaml"
        config.write_text(
            """# My resume configuration
schema_version: 3.0.0
output_dir: ./dist  # Output directory
"""
        )

        migration = MigrationV3ToV4()
        ctx = MigrationContext(project_path=tmp_path)

        migration.apply(ctx)

        content = config.read_text()
        assert "# My resume configuration" in content
        assert "# Output directory" in content

    def test_v3_to_v4_infers_greenfield_archetype(self, tmp_path: Path) -> None:
        """Test migration infers greenfield archetype from content."""
        from resume_as_code.migrations.v3_to_v4 import MigrationV3ToV4

        config = tmp_path / ".resume.yaml"
        config.write_text("schema_version: 3.0.0\noutput_dir: ./dist\n")

        work_units = tmp_path / "work-units"
        work_units.mkdir()
        wu_file = work_units / "wu-2024-01-01-platform.yaml"
        wu_file.write_text(
            """id: wu-2024-01-01-platform
title: Built new authentication platform from scratch
problem:
  statement: Needed new secure authentication capability
actions:
  - Designed architecture
  - Built the platform
outcome:
  result: Launched new authentication system
tags:
  - greenfield
  - architecture
"""
        )

        migration = MigrationV3ToV4()
        ctx = MigrationContext(project_path=tmp_path)

        migration.apply(ctx)

        content = wu_file.read_text()
        assert "archetype: greenfield" in content

    def test_v3_to_v4_infers_minimal_low_confidence(self, tmp_path: Path) -> None:
        """Test migration falls back to minimal for ambiguous content."""
        from resume_as_code.migrations.v3_to_v4 import MigrationV3ToV4

        config = tmp_path / ".resume.yaml"
        config.write_text("schema_version: 3.0.0\noutput_dir: ./dist\n")

        work_units = tmp_path / "work-units"
        work_units.mkdir()
        wu_file = work_units / "wu-2024-01-01-generic.yaml"
        wu_file.write_text(
            """id: wu-2024-01-01-generic
title: Generic task completed
problem:
  statement: Something needed doing here
actions:
  - Did the thing
outcome:
  result: Thing was done
"""
        )

        migration = MigrationV3ToV4()
        ctx = MigrationContext(project_path=tmp_path)

        migration.apply(ctx)

        content = wu_file.read_text()
        assert "archetype: minimal" in content
