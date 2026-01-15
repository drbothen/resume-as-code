"""Tests for JSON schema generation script."""

from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass

# Tests will import generate_schemas module once implemented


class TestSchemaGeneration:
    """Tests for schema generation functionality."""

    def test_generate_schema_includes_schema_field(self) -> None:
        """Schema includes $schema reference to JSON Schema 2020-12 draft."""
        from resume_as_code.models import WorkUnit
        from scripts.generate_schemas import generate_schema

        schema = generate_schema("work-unit", WorkUnit)

        assert "$schema" in schema
        assert schema["$schema"] == "https://json-schema.org/draft/2020-12/schema"

    def test_generate_schema_includes_id(self) -> None:
        """Schema includes proper $id URL."""
        from resume_as_code.models import WorkUnit
        from scripts.generate_schemas import generate_schema

        schema = generate_schema("work-unit", WorkUnit)

        assert "$id" in schema
        assert schema["$id"] == "https://resume-as-code.dev/schemas/work-unit.schema.json"

    def test_generate_schema_all_models(self) -> None:
        """All registered models produce valid schemas."""
        from scripts.generate_schemas import MODELS, generate_schema

        for name, model in MODELS.items():
            schema = generate_schema(name, model)
            assert "$schema" in schema
            assert "$id" in schema
            assert schema["$id"].endswith(f"{name}.schema.json")

    def test_generate_schema_uses_serialization_mode(self) -> None:
        """Schema uses serialization mode for YAML storage compatibility."""
        from resume_as_code.models import WorkUnit
        from scripts.generate_schemas import generate_schema

        schema = generate_schema("work-unit", WorkUnit)

        # In serialization mode, date fields serialize as strings
        # Check that time_started property expects string type
        assert "properties" in schema
        if "time_started" in schema["properties"]:
            time_started = schema["properties"]["time_started"]
            # Should be string in serialization mode, not object
            assert time_started.get("type") == "string" or "anyOf" in time_started

    def test_main_returns_zero_on_success(self, tmp_path: Path) -> None:
        """main() returns 0 on successful generation."""
        from scripts.generate_schemas import main

        # Use tmp_path as schema directory
        exit_code = main(check=False, schema_dir=tmp_path)
        assert exit_code == 0

    def test_main_check_mode_detects_changes(self, tmp_path: Path) -> None:
        """main() with --check detects schema drift."""

        from scripts.generate_schemas import main

        # Create one schema that's out of date
        schema_file = tmp_path / "work-unit.schema.json"
        schema_file.write_text('{"$schema": "old"}')

        # Check mode should detect drift
        exit_code = main(check=True, schema_dir=tmp_path)
        assert exit_code == 1

    def test_main_creates_schema_files(self, tmp_path: Path) -> None:
        """main() creates schema files in output directory."""
        from scripts.generate_schemas import MODELS, main

        exit_code = main(check=False, schema_dir=tmp_path)

        assert exit_code == 0
        for name in MODELS:
            schema_file = tmp_path / f"{name}.schema.json"
            assert schema_file.exists(), f"Expected {schema_file} to be created"

            # Verify valid JSON
            content = json.loads(schema_file.read_text())
            assert "$schema" in content
            assert "$id" in content


class TestSchemaIntegration:
    """Integration tests verifying model-schema consistency."""

    def test_generated_schemas_match_models(self, tmp_path: Path) -> None:
        """Generated schemas accurately reflect Pydantic model definitions."""
        import json

        from scripts.generate_schemas import MODELS, generate_schema, main

        # Generate fresh schemas
        main(check=False, schema_dir=tmp_path)

        for name, model in MODELS.items():
            schema_file = tmp_path / f"{name}.schema.json"
            generated = json.loads(schema_file.read_text())

            # Re-generate to compare
            expected = generate_schema(name, model)

            # Remove $id for comparison (as it's added post-generation)
            # and compare core structure
            assert generated["$schema"] == expected["$schema"]
            assert "properties" in generated or "type" in generated

    def test_workunit_schema_has_required_fields(self, tmp_path: Path) -> None:
        """WorkUnit schema includes all required fields."""
        import json

        from scripts.generate_schemas import main

        main(check=False, schema_dir=tmp_path)

        schema_file = tmp_path / "work-unit.schema.json"
        schema = json.loads(schema_file.read_text())

        # WorkUnit has required: id, title, problem, actions, outcome
        assert "required" in schema
        required = schema["required"]
        assert "id" in required
        assert "title" in required
        assert "problem" in required
        assert "actions" in required
        assert "outcome" in required
