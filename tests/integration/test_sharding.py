"""Integration tests for directory-based sharding (Story 11.2).

Tests cover:
- Three-tier loading fallback (directory > file > embedded)
- Precedence when both directory and file exist
- migrate --shard command functionality
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from click.testing import CliRunner

from resume_as_code.cli import main


class TestThreeTierLoadingFallback:
    """Tests for three-tier loading fallback (AC: 1, 2)."""

    def test_load_from_directory_mode(
        self, tmp_path: Path, cli_runner: CliRunner, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should load certifications from directory when dir exists."""
        monkeypatch.chdir(tmp_path)

        # Create .resume.yaml
        (tmp_path / ".resume.yaml").write_text("schema_version: '1.1.0'\n")

        # Create certifications directory with items
        cert_dir = tmp_path / "certifications"
        cert_dir.mkdir()
        (cert_dir / "cert-2023-06-aws.yaml").write_text(
            'name: "AWS Solutions Architect"\nissuer: "AWS"\ndate: "2023-06"\n'
        )
        (cert_dir / "cert-2022-11-cissp.yaml").write_text(
            'name: "CISSP"\nissuer: "ISC2"\ndate: "2022-11"\n'
        )

        result = cli_runner.invoke(main, ["list", "certifications"])

        assert result.exit_code == 0
        assert "AWS Solutions Architect" in result.output
        assert "CISSP" in result.output
        assert "2 Certification(s)" in result.output

    def test_load_from_file_mode(
        self, tmp_path: Path, cli_runner: CliRunner, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should load certifications from file when no directory exists."""
        monkeypatch.chdir(tmp_path)

        # Create .resume.yaml
        (tmp_path / ".resume.yaml").write_text("schema_version: '1.1.0'\n")

        # Create certifications.yaml (single file mode)
        (tmp_path / "certifications.yaml").write_text(
            '- name: "AWS Cert"\n  issuer: "AWS"\n- name: "Azure Cert"\n  issuer: "Microsoft"\n'
        )

        result = cli_runner.invoke(main, ["list", "certifications"])

        assert result.exit_code == 0
        assert "AWS Cert" in result.output
        assert "Azure Cert" in result.output
        assert "2 Certification(s)" in result.output

    def test_directory_takes_precedence_over_file(
        self, tmp_path: Path, cli_runner: CliRunner, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Directory mode should take precedence when both exist (AC: 2)."""
        monkeypatch.chdir(tmp_path)

        # Create .resume.yaml
        (tmp_path / ".resume.yaml").write_text("schema_version: '1.1.0'\n")

        # Create both directory and file
        cert_dir = tmp_path / "certifications"
        cert_dir.mkdir()
        (cert_dir / "cert-dir-item.yaml").write_text(
            'name: "Directory Cert"\nissuer: "Dir Issuer"\n'
        )

        (tmp_path / "certifications.yaml").write_text(
            '- name: "File Cert"\n  issuer: "File Issuer"\n'
        )

        result = cli_runner.invoke(main, ["list", "certifications"])

        assert result.exit_code == 0
        # Directory cert should be loaded, not file cert
        assert "Directory Cert" in result.output
        assert "File Cert" not in result.output
        assert "1 Certification(s)" in result.output

    def test_empty_directory_returns_empty_list(
        self, tmp_path: Path, cli_runner: CliRunner, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Empty directory should return empty list."""
        monkeypatch.chdir(tmp_path)

        # Create .resume.yaml
        (tmp_path / ".resume.yaml").write_text("schema_version: '1.1.0'\n")

        # Create empty certifications directory
        (tmp_path / "certifications").mkdir()

        result = cli_runner.invoke(main, ["list", "certifications"])

        assert result.exit_code == 0
        assert "No certifications found" in result.output


class TestVerboseSourceDisplay:
    """Tests for verbose source file display (AC: 5)."""

    def test_verbose_shows_source_file_directory_mode(
        self, tmp_path: Path, cli_runner: CliRunner, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Verbose flag should show source file path in directory mode."""
        monkeypatch.chdir(tmp_path)

        # Create .resume.yaml
        (tmp_path / ".resume.yaml").write_text("schema_version: '1.1.0'\n")

        # Create certifications directory
        cert_dir = tmp_path / "certifications"
        cert_dir.mkdir()
        (cert_dir / "cert-2023-06-aws.yaml").write_text(
            'name: "AWS Cert"\nissuer: "AWS"\ndate: "2023-06"\n'
        )

        result = cli_runner.invoke(main, ["list", "certifications", "--verbose"])

        assert result.exit_code == 0
        assert "Source" in result.output  # Column header
        assert "cert-2023-06-aws.yaml" in result.output

    def test_verbose_json_includes_source_file(
        self, tmp_path: Path, cli_runner: CliRunner, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """JSON output with verbose should include source_file field."""
        monkeypatch.chdir(tmp_path)

        # Create .resume.yaml
        (tmp_path / ".resume.yaml").write_text("schema_version: '1.1.0'\n")

        # Create certifications directory
        cert_dir = tmp_path / "certifications"
        cert_dir.mkdir()
        (cert_dir / "cert-2023-06-aws.yaml").write_text('name: "AWS Cert"\nissuer: "AWS"\n')

        result = cli_runner.invoke(main, ["--json", "list", "certifications", "--verbose"])

        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["status"] == "success"
        cert = data["data"]["certifications"][0]
        assert "source_file" in cert
        assert "cert-2023-06-aws.yaml" in cert["source_file"]


class TestMigrateShardCommand:
    """Tests for migrate --shard command (AC: 4)."""

    def test_shard_certifications_dry_run(
        self, tmp_path: Path, cli_runner: CliRunner, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Dry run should preview sharding without making changes."""
        monkeypatch.chdir(tmp_path)

        # Create .resume.yaml
        (tmp_path / ".resume.yaml").write_text("schema_version: '1.1.0'\n")

        # Create certifications.yaml
        (tmp_path / "certifications.yaml").write_text(
            '- name: "AWS Cert"\n  issuer: "AWS"\n  date: "2023-06"\n'
            '- name: "CISSP"\n  issuer: "ISC2"\n  date: "2022-11"\n'
        )

        result = cli_runner.invoke(main, ["migrate", "--shard", "certifications", "--dry-run"])

        assert result.exit_code == 0
        assert "Would migrate" in result.output
        assert "certifications" in result.output
        assert "Files to create" in result.output
        # Verify no changes were made
        assert (tmp_path / "certifications.yaml").exists()
        assert not (tmp_path / "certifications").exists()

    def test_shard_certifications_creates_directory(
        self, tmp_path: Path, cli_runner: CliRunner, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Sharding should create directory with individual files."""
        monkeypatch.chdir(tmp_path)

        # Create .resume.yaml
        (tmp_path / ".resume.yaml").write_text("schema_version: '1.1.0'\n")

        # Create certifications.yaml
        (tmp_path / "certifications.yaml").write_text(
            '- name: "AWS Cert"\n  issuer: "AWS"\n  date: "2023-06"\n'
            '- name: "CISSP"\n  issuer: "ISC2"\n  date: "2022-11"\n'
        )

        result = cli_runner.invoke(main, ["migrate", "--shard", "certifications", "--yes"])

        assert result.exit_code == 0
        assert "Sharding complete" in result.output
        assert "Migrated 2 certifications" in result.output

        # Verify directory was created
        cert_dir = tmp_path / "certifications"
        assert cert_dir.exists()
        assert cert_dir.is_dir()

        # Verify individual files were created
        cert_files = list(cert_dir.glob("*.yaml"))
        assert len(cert_files) == 2

    def test_shard_creates_backup(
        self, tmp_path: Path, cli_runner: CliRunner, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Sharding should create backup of original file."""
        monkeypatch.chdir(tmp_path)

        # Create .resume.yaml
        (tmp_path / ".resume.yaml").write_text("schema_version: '1.1.0'\n")

        # Create certifications.yaml
        original_content = '- name: "AWS Cert"\n  issuer: "AWS"\n'
        (tmp_path / "certifications.yaml").write_text(original_content)

        result = cli_runner.invoke(main, ["migrate", "--shard", "certifications", "--yes"])

        assert result.exit_code == 0

        # Verify backup was created
        backup_file = tmp_path / "certifications.yaml.bak"
        assert backup_file.exists()
        assert "AWS Cert" in backup_file.read_text()

        # Original file should be removed
        assert not (tmp_path / "certifications.yaml").exists()

    def test_shard_updates_config(
        self, tmp_path: Path, cli_runner: CliRunner, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Sharding should update .resume.yaml with directory config."""
        monkeypatch.chdir(tmp_path)

        # Create .resume.yaml
        (tmp_path / ".resume.yaml").write_text("schema_version: '1.1.0'\n")

        # Create certifications.yaml
        (tmp_path / "certifications.yaml").write_text('- name: "Test Cert"\n')

        cli_runner.invoke(main, ["migrate", "--shard", "certifications", "--yes"])

        # Verify config was updated
        config_content = (tmp_path / ".resume.yaml").read_text()
        assert "certifications_dir" in config_content
        assert "./certifications/" in config_content

    def test_shard_already_directory_mode_fails(
        self, tmp_path: Path, cli_runner: CliRunner, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should fail if already in directory mode."""
        monkeypatch.chdir(tmp_path)

        # Create .resume.yaml
        (tmp_path / ".resume.yaml").write_text("schema_version: '1.1.0'\n")

        # Create existing directory
        (tmp_path / "certifications").mkdir()
        (tmp_path / "certifications" / "cert-test.yaml").write_text('name: "Test"\n')

        result = cli_runner.invoke(main, ["migrate", "--shard", "certifications"])

        assert result.exit_code == 1
        assert "already exists" in result.output

    def test_shard_no_source_file_fails(
        self, tmp_path: Path, cli_runner: CliRunner, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should fail if source file doesn't exist."""
        monkeypatch.chdir(tmp_path)

        # Create .resume.yaml only
        (tmp_path / ".resume.yaml").write_text("schema_version: '1.1.0'\n")

        result = cli_runner.invoke(main, ["migrate", "--shard", "certifications"])

        assert result.exit_code == 1
        assert "not found" in result.output

    def test_shard_highlights(
        self, tmp_path: Path, cli_runner: CliRunner, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should shard highlights (strings) correctly."""
        monkeypatch.chdir(tmp_path)

        # Create .resume.yaml
        (tmp_path / ".resume.yaml").write_text("schema_version: '1.1.0'\n")

        # Create highlights.yaml (list of strings)
        (tmp_path / "highlights.yaml").write_text(
            '- "Led digital transformation"\n- "Managed $50M budget"\n'
        )

        result = cli_runner.invoke(main, ["migrate", "--shard", "highlights", "--yes"])

        assert result.exit_code == 0
        assert "Migrated 2 highlights" in result.output

        # Verify directory structure
        hl_dir = tmp_path / "highlights"
        assert hl_dir.exists()
        hl_files = list(hl_dir.glob("hl-*.yaml"))
        assert len(hl_files) == 2

        # Verify file content has 'text' field
        first_file = sorted(hl_files)[0]
        content = first_file.read_text()
        assert "text:" in content

    def test_shard_publications(
        self, tmp_path: Path, cli_runner: CliRunner, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should shard publications correctly with proper ID pattern."""
        monkeypatch.chdir(tmp_path)

        # Create .resume.yaml
        (tmp_path / ".resume.yaml").write_text("schema_version: '1.1.0'\n")

        # Create publications.yaml
        (tmp_path / "publications.yaml").write_text(
            '- title: "Zero Trust Architecture"\n'
            "  type: conference\n"
            '  venue: "RSA Conference"\n'
            '  date: "2023-06"\n'
        )

        result = cli_runner.invoke(main, ["migrate", "--shard", "publications", "--yes"])

        assert result.exit_code == 0

        # Verify directory structure
        pub_dir = tmp_path / "publications"
        assert pub_dir.exists()
        pub_files = list(pub_dir.glob("pub-*.yaml"))
        assert len(pub_files) == 1
        assert "2023-06" in pub_files[0].name


class TestShardingJsonOutput:
    """Tests for sharding with JSON output."""

    def test_shard_dry_run_json(
        self, tmp_path: Path, cli_runner: CliRunner, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Dry run should output JSON when --json flag is used."""
        monkeypatch.chdir(tmp_path)

        # Create .resume.yaml
        (tmp_path / ".resume.yaml").write_text("schema_version: '1.1.0'\n")

        # Create certifications.yaml
        (tmp_path / "certifications.yaml").write_text('- name: "Test Cert"\n')

        result = cli_runner.invoke(
            main, ["--json", "migrate", "--shard", "certifications", "--dry-run"]
        )

        assert result.exit_code == 0
        # Check for key JSON fields in output (avoid full JSON parsing due to
        # console wrapping issues with long paths in test environments)
        assert '"status": "success"' in result.output
        assert '"dry_run": true' in result.output
        assert '"shard": true' in result.output
        assert '"files_to_create"' in result.output

    def test_shard_success_json(
        self, tmp_path: Path, cli_runner: CliRunner, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Successful sharding should output JSON with details."""
        monkeypatch.chdir(tmp_path)

        # Create .resume.yaml
        (tmp_path / ".resume.yaml").write_text("schema_version: '1.1.0'\n")

        # Create certifications.yaml
        (tmp_path / "certifications.yaml").write_text('- name: "Test Cert"\n  issuer: "Test"\n')

        result = cli_runner.invoke(
            main, ["--json", "migrate", "--shard", "certifications", "--yes"]
        )

        assert result.exit_code == 0
        # Check for key JSON fields in output
        assert '"status": "success"' in result.output
        assert '"shard": true' in result.output
        assert '"items_migrated": 1' in result.output
        assert '"files_created"' in result.output
        assert '"backup_file"' in result.output
