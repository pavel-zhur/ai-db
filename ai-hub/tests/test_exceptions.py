"""Tests for AI-Hub exceptions."""

from fastapi import HTTPException

from ai_hub.exceptions import (
    AIHubError,
    ConfigurationError,
    DatabaseError,
    PermissionError,
    RepositoryError,
    ValidationError,
    create_user_friendly_error,
)


class TestAIHubError:
    """Test AIHubError base class."""

    def test_basic_error(self):
        """Test basic error creation."""
        error = AIHubError("Something went wrong")
        assert str(error) == "Something went wrong"
        assert error.message == "Something went wrong"
        assert error.error_details == {}
        assert error.status_code == 500

    def test_error_with_details(self):
        """Test error with details."""
        details = {"field": "value", "code": 123}
        error = AIHubError("Error with details", error_details=details, status_code=400)
        assert error.message == "Error with details"
        assert error.error_details == details
        assert error.status_code == 400


class TestSpecificErrors:
    """Test specific error types."""

    def test_configuration_error(self):
        """Test ConfigurationError."""
        error = ConfigurationError("Invalid config")
        assert error.status_code == 500
        assert error.message == "Invalid config"

    def test_validation_error(self):
        """Test ValidationError."""
        error = ValidationError("Invalid input")
        assert error.status_code == 400
        assert error.message == "Invalid input"

    def test_repository_error(self):
        """Test RepositoryError."""
        error = RepositoryError("Git error")
        assert error.status_code == 500
        assert error.message == "Git error"

    def test_database_error(self):
        """Test DatabaseError."""
        error = DatabaseError("DB error")
        assert error.status_code == 500
        assert error.message == "DB error"

    def test_permission_error(self):
        """Test PermissionError."""
        error = PermissionError("Access denied")
        assert error.status_code == 403
        assert error.message == "Access denied"


class TestCreateUserFriendlyError:
    """Test create_user_friendly_error function."""

    def test_permission_error_message(self):
        """Test permission error user-friendly message."""
        error = Exception("Permission denied for user")
        message, details, error_type = create_user_friendly_error(error)

        assert "permission" in message.lower()
        assert details["exception_type"] == "Exception"
        assert details["exception_message"] == "Permission denied for user"
        assert error_type == "Exception"

    def test_schema_error_message(self):
        """Test schema error user-friendly message."""
        error = Exception("Schema validation failed")
        message, details, error_type = create_user_friendly_error(error)

        assert "format" in message.lower()
        assert details["exception_type"] == "Exception"

    def test_constraint_error_message(self):
        """Test constraint error user-friendly message."""
        error = Exception("Constraint violation detected")
        message, details, error_type = create_user_friendly_error(error)

        assert "constraint" in message.lower()
        assert "violate" in message.lower()

    def test_compilation_error_message(self):
        """Test compilation error user-friendly message."""
        error = Exception("Query compilation failed")
        message, details, error_type = create_user_friendly_error(error)

        assert "understand" in message.lower() or "syntax" in message.lower()

    def test_repository_error_message(self):
        """Test repository error user-friendly message."""
        error = Exception("Git repository error")
        message, details, error_type = create_user_friendly_error(error)

        assert "repository" in message.lower()

    def test_transaction_error_message(self):
        """Test transaction error user-friendly message."""
        error = Exception("Transaction lock failed")
        message, details, error_type = create_user_friendly_error(error)

        assert "conflict" in message.lower() or "progress" in message.lower()

    def test_timeout_error_message(self):
        """Test timeout error user-friendly message."""
        error = Exception("Operation timeout")
        message, details, error_type = create_user_friendly_error(error)

        assert "timeout" in message.lower() or "long" in message.lower()

    def test_api_error_message(self):
        """Test API error user-friendly message."""
        error = Exception("API key invalid")
        message, details, error_type = create_user_friendly_error(error)

        assert "ai service" in message.lower() or "configuration" in message.lower()

    def test_validation_error_message(self):
        """Test validation error user-friendly message."""
        error = ValueError("Invalid value provided")
        message, details, error_type = create_user_friendly_error(error)

        assert "invalid input" in message.lower()
        assert error_type == "ValueError"

    def test_http_error_message(self):
        """Test HTTP error user-friendly message."""
        error = HTTPException(status_code=404, detail="Not found")
        message, details, error_type = create_user_friendly_error(error)

        assert "network" in message.lower()
        assert error_type == "HTTPException"

    def test_file_error_message(self):
        """Test file error user-friendly message."""
        error = Exception("File not found in directory")
        message, details, error_type = create_user_friendly_error(error)

        assert "files" in message.lower()

    def test_generic_error_message(self):
        """Test generic error user-friendly message."""
        error = Exception("Some unknown error")
        message, details, error_type = create_user_friendly_error(error)

        assert "unexpected error" in message.lower()
        assert "try again" in message.lower()

    def test_error_with_attributes(self):
        """Test error with custom attributes."""
        error = Exception("Test error")
        error.custom_field = "custom_value"
        error.status_code = 404

        message, details, error_type = create_user_friendly_error(error)

        assert details["custom_field"] == "custom_value"
        assert details["status_code"] == 404
        assert "args" not in details  # Should be excluded
