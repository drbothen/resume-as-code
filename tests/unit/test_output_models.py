"""Tests for JSON output models."""

from __future__ import annotations

import json
from datetime import datetime

from resume_as_code.models.output import FORMAT_VERSION, JSONResponse


class TestFormatVersion:
    """Test format version constant."""

    def test_format_version_is_string(self) -> None:
        """Format version should be a string."""
        assert isinstance(FORMAT_VERSION, str)

    def test_format_version_is_semantic(self) -> None:
        """Format version should follow semver pattern."""
        parts = FORMAT_VERSION.split(".")
        assert len(parts) == 3
        assert all(part.isdigit() for part in parts)


class TestJSONResponseModel:
    """Test JSONResponse Pydantic model."""

    def test_json_response_has_format_version(self) -> None:
        """Response should include format version."""
        response = JSONResponse(status="success", command="test")
        data = json.loads(response.to_json())
        assert data["format_version"] == FORMAT_VERSION

    def test_json_response_has_timestamp(self) -> None:
        """Response should include ISO timestamp."""
        response = JSONResponse(status="success", command="test")
        data = json.loads(response.to_json())
        assert "timestamp" in data
        # Should be parseable as ISO format
        datetime.fromisoformat(data["timestamp"].replace("Z", "+00:00"))

    def test_json_response_required_fields(self) -> None:
        """Response should require status and command."""
        response = JSONResponse(status="success", command="plan")
        data = json.loads(response.to_json())
        assert data["status"] == "success"
        assert data["command"] == "plan"

    def test_json_response_default_data_is_empty_dict(self) -> None:
        """Data field should default to empty dict."""
        response = JSONResponse(status="success", command="test")
        data = json.loads(response.to_json())
        assert data["data"] == {}

    def test_json_response_default_warnings_is_empty_list(self) -> None:
        """Warnings field should default to empty list."""
        response = JSONResponse(status="success", command="test")
        data = json.loads(response.to_json())
        assert data["warnings"] == []

    def test_json_response_default_errors_is_empty_list(self) -> None:
        """Errors field should default to empty list."""
        response = JSONResponse(status="success", command="test")
        data = json.loads(response.to_json())
        assert data["errors"] == []

    def test_json_response_with_data(self) -> None:
        """Response should serialize custom data."""
        response = JSONResponse(
            status="success",
            command="list",
            data={"count": 5, "items": ["a", "b", "c"]},
        )
        data = json.loads(response.to_json())
        assert data["data"]["count"] == 5
        assert data["data"]["items"] == ["a", "b", "c"]

    def test_json_response_with_warnings(self) -> None:
        """Response should include warning messages."""
        response = JSONResponse(
            status="success",
            command="build",
            warnings=["Missing optional field", "Using default template"],
        )
        data = json.loads(response.to_json())
        assert len(data["warnings"]) == 2
        assert "Missing optional field" in data["warnings"]

    def test_json_response_with_errors(self) -> None:
        """Response should include error details."""
        response = JSONResponse(
            status="error",
            command="validate",
            errors=[{"code": "E001", "message": "Invalid format"}],
        )
        data = json.loads(response.to_json())
        assert len(data["errors"]) == 1
        assert data["errors"][0]["code"] == "E001"

    def test_to_json_returns_string(self) -> None:
        """to_json method should return a string."""
        response = JSONResponse(status="success", command="test")
        result = response.to_json()
        assert isinstance(result, str)

    def test_to_json_is_valid_json(self) -> None:
        """to_json output should be valid JSON."""
        response = JSONResponse(status="success", command="test")
        result = response.to_json()
        # Should not raise
        parsed = json.loads(result)
        assert isinstance(parsed, dict)

    def test_status_values(self) -> None:
        """Status can be success, error, or dry_run."""
        for status in ["success", "error", "dry_run"]:
            response = JSONResponse(status=status, command="test")
            data = json.loads(response.to_json())
            assert data["status"] == status
