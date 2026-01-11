"""Tests for exception hierarchy and structured errors."""

from __future__ import annotations

from resume_as_code.models.errors import (
    ConfigurationError,
    NotFoundError,
    ResumeError,
    RuntimeSystemError,
    StructuredError,
    UserError,
    ValidationError,
)


class TestExitCodes:
    """Verify correct exit codes for each exception type (AC #1-#6)."""

    def test_resume_error_base_exit_code(self) -> None:
        """Base ResumeError has exit code 1."""
        assert ResumeError("test").exit_code == 1

    def test_user_error_exit_code_1(self) -> None:
        """UserError has exit code 1 (AC #2)."""
        assert UserError("test").exit_code == 1

    def test_configuration_error_exit_code_2(self) -> None:
        """ConfigurationError has exit code 2 (AC #3)."""
        assert ConfigurationError("test").exit_code == 2

    def test_validation_error_exit_code_3(self) -> None:
        """ValidationError has exit code 3 (AC #4)."""
        assert ValidationError("test").exit_code == 3

    def test_not_found_error_exit_code_4(self) -> None:
        """NotFoundError has exit code 4 (AC #5)."""
        assert NotFoundError("test").exit_code == 4

    def test_system_error_exit_code_5(self) -> None:
        """RuntimeSystemError has exit code 5 (AC #6)."""
        assert RuntimeSystemError("test").exit_code == 5


class TestErrorCodes:
    """Verify correct error codes for each exception type."""

    def test_user_error_code(self) -> None:
        assert UserError("test").error_code == "USER_ERROR"

    def test_configuration_error_code(self) -> None:
        assert ConfigurationError("test").error_code == "CONFIG_ERROR"

    def test_validation_error_code(self) -> None:
        assert ValidationError("test").error_code == "VALIDATION_ERROR"

    def test_not_found_error_code(self) -> None:
        assert NotFoundError("test").error_code == "NOT_FOUND_ERROR"

    def test_system_error_code(self) -> None:
        assert RuntimeSystemError("test").error_code == "SYSTEM_ERROR"


class TestExceptionAttributes:
    """Verify exception attributes are properly set."""

    def test_resume_error_message(self) -> None:
        """ResumeError stores message attribute."""
        error = ResumeError("test message")
        assert error.message == "test message"
        assert str(error) == "test message"

    def test_resume_error_path(self) -> None:
        """ResumeError stores path attribute."""
        error = ResumeError("test", path="/some/file.yaml:10")
        assert error.path == "/some/file.yaml:10"

    def test_resume_error_suggestion(self) -> None:
        """ResumeError stores suggestion attribute."""
        error = ResumeError("test", suggestion="Fix the thing")
        assert error.suggestion == "Fix the thing"

    def test_resume_error_all_attributes(self) -> None:
        """ResumeError stores all attributes."""
        error = ResumeError(
            message="test message",
            path="/path.yaml",
            suggestion="Do this",
            recoverable=True,
        )
        assert error.message == "test message"
        assert error.path == "/path.yaml"
        assert error.suggestion == "Do this"
        assert error.recoverable is True


class TestStructuredError:
    """Verify structured error formatting (AC #7)."""

    def test_structured_error_all_fields(self) -> None:
        """StructuredError includes all required fields."""
        error = StructuredError(
            code="TEST_ERROR",
            message="Test message",
            path="test/path.yaml:10",
            suggestion="Fix the thing",
            recoverable=True,
        )
        assert error.code == "TEST_ERROR"
        assert error.message == "Test message"
        assert error.path == "test/path.yaml:10"
        assert error.suggestion == "Fix the thing"
        assert error.recoverable is True

    def test_to_dict_includes_all_fields(self) -> None:
        """to_dict() returns all fields for JSON serialization."""
        error = StructuredError(
            code="TEST_ERROR",
            message="Test message",
            path="test/path.yaml:10",
            suggestion="Fix the thing",
            recoverable=True,
        )
        d = error.to_dict()
        assert d["code"] == "TEST_ERROR"
        assert d["message"] == "Test message"
        assert d["path"] == "test/path.yaml:10"
        assert d["suggestion"] == "Fix the thing"
        assert d["recoverable"] is True

    def test_structured_error_optional_fields(self) -> None:
        """StructuredError handles optional fields."""
        error = StructuredError(
            code="MINIMAL",
            message="Just a message",
        )
        assert error.path is None
        assert error.suggestion is None
        assert error.recoverable is False

    def test_to_dict_includes_none_values(self) -> None:
        """to_dict() includes None values for optional fields."""
        error = StructuredError(
            code="MINIMAL",
            message="Just a message",
        )
        d = error.to_dict()
        assert d["path"] is None
        assert d["suggestion"] is None
        assert d["recoverable"] is False


class TestRecoverableFlag:
    """Verify recoverable flag defaults and overrides (AC #8)."""

    def test_user_error_recoverable_by_default(self) -> None:
        """UserError is recoverable by default."""
        assert UserError("test").recoverable is True

    def test_configuration_error_recoverable_by_default(self) -> None:
        """ConfigurationError is recoverable by default."""
        assert ConfigurationError("test").recoverable is True

    def test_validation_error_recoverable_by_default(self) -> None:
        """ValidationError is recoverable by default."""
        assert ValidationError("test").recoverable is True

    def test_not_found_error_recoverable_by_default(self) -> None:
        """NotFoundError is recoverable by default."""
        assert NotFoundError("test").recoverable is True

    def test_system_error_not_recoverable_by_default(self) -> None:
        """RuntimeSystemError is NOT recoverable by default."""
        assert RuntimeSystemError("test").recoverable is False

    def test_recoverable_can_be_overridden_to_true(self) -> None:
        """Recoverable flag can be overridden to True."""
        error = RuntimeSystemError("test", recoverable=True)
        assert error.recoverable is True

    def test_recoverable_can_be_overridden_to_false(self) -> None:
        """Recoverable flag can be overridden to False."""
        error = UserError("test", recoverable=False)
        assert error.recoverable is False


class TestToStructured:
    """Verify conversion from exception to StructuredError."""

    def test_to_structured_user_error(self) -> None:
        """UserError converts to StructuredError correctly."""
        error = UserError(
            message="Invalid flag",
            path=None,
            suggestion="Use --valid-flag instead",
        )
        structured = error.to_structured()
        assert isinstance(structured, StructuredError)
        assert structured.code == "USER_ERROR"
        assert structured.message == "Invalid flag"
        assert structured.path is None
        assert structured.suggestion == "Use --valid-flag instead"
        assert structured.recoverable is True

    def test_to_structured_validation_error_with_path(self) -> None:
        """ValidationError with path converts correctly."""
        error = ValidationError(
            message="Missing required field 'problem.statement'",
            path="work-units/wu-2024-03-15-api.yaml:12",
            suggestion="Add a problem statement",
        )
        structured = error.to_structured()
        assert structured.code == "VALIDATION_ERROR"
        assert structured.path == "work-units/wu-2024-03-15-api.yaml:12"

    def test_to_structured_preserves_recoverable_override(self) -> None:
        """to_structured() preserves recoverable override."""
        error = RuntimeSystemError("test", recoverable=True)
        structured = error.to_structured()
        assert structured.recoverable is True


class TestExceptionInheritance:
    """Verify exception class hierarchy."""

    def test_user_error_is_resume_error(self) -> None:
        assert isinstance(UserError("test"), ResumeError)

    def test_configuration_error_is_resume_error(self) -> None:
        assert isinstance(ConfigurationError("test"), ResumeError)

    def test_validation_error_is_resume_error(self) -> None:
        assert isinstance(ValidationError("test"), ResumeError)

    def test_not_found_error_is_resume_error(self) -> None:
        assert isinstance(NotFoundError("test"), ResumeError)

    def test_system_error_is_resume_error(self) -> None:
        assert isinstance(RuntimeSystemError("test"), ResumeError)

    def test_resume_error_is_exception(self) -> None:
        assert isinstance(ResumeError("test"), Exception)
