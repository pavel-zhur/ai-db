"""Tests for AI-Hub models."""

import pytest
from pydantic import ValidationError

from ai_hub.models import (
    DataLossIndicator,
    DataModificationRequest,
    ErrorResponse,
    PermissionLevel,
    QueryRequest,
    QueryResponse,
    ViewQueryRequest,
)


class TestPermissionLevel:
    """Test PermissionLevel enum."""

    def test_permission_levels(self):
        """Test all permission level values."""
        assert PermissionLevel.SELECT.value == "select"
        assert PermissionLevel.DATA_MODIFY.value == "data_modify"
        assert PermissionLevel.SCHEMA_MODIFY.value == "schema_modify"
        assert PermissionLevel.VIEW_MODIFY.value == "view_modify"


class TestDataLossIndicator:
    """Test DataLossIndicator enum."""

    def test_data_loss_indicators(self):
        """Test all data loss indicator values."""
        assert DataLossIndicator.NONE.value == "none"
        assert DataLossIndicator.PROBABLE.value == "probable"
        assert DataLossIndicator.YES.value == "yes"


class TestQueryRequest:
    """Test QueryRequest model."""

    def test_valid_query_request(self):
        """Test valid query request creation."""
        request = QueryRequest(query="SELECT * FROM users", permissions=PermissionLevel.SELECT)
        assert request.query == "SELECT * FROM users"
        assert request.permissions == PermissionLevel.SELECT

    def test_query_request_validation(self):
        """Test query request validation."""
        with pytest.raises(ValidationError):
            QueryRequest(permissions=PermissionLevel.SELECT)  # Missing query

        with pytest.raises(ValidationError):
            QueryRequest(query="SELECT * FROM users")  # Missing permissions


class TestViewQueryRequest:
    """Test ViewQueryRequest model."""

    def test_valid_view_request(self):
        """Test valid view request creation."""
        request = ViewQueryRequest(view_name="user_summary")
        assert request.view_name == "user_summary"
        assert request.parameters is None

    def test_view_request_with_parameters(self):
        """Test view request with parameters."""
        params = {"user_id": 123, "status": "active"}
        request = ViewQueryRequest(view_name="user_details", parameters=params)
        assert request.view_name == "user_details"
        assert request.parameters == params

    def test_view_request_validation(self):
        """Test view request validation."""
        with pytest.raises(ValidationError):
            ViewQueryRequest()  # Missing view_name


class TestDataModificationRequest:
    """Test DataModificationRequest model."""

    def test_valid_data_modification_request(self):
        """Test valid data modification request creation."""
        request = DataModificationRequest(operation="INSERT INTO users (name) VALUES ('John')")
        assert request.operation == "INSERT INTO users (name) VALUES ('John')"
        assert request.permissions == PermissionLevel.DATA_MODIFY  # Default

    def test_data_modification_with_custom_permissions(self):
        """Test data modification with custom permissions."""
        request = DataModificationRequest(
            operation="DROP TABLE users", permissions=PermissionLevel.SCHEMA_MODIFY
        )
        assert request.operation == "DROP TABLE users"
        assert request.permissions == PermissionLevel.SCHEMA_MODIFY

    def test_data_modification_validation(self):
        """Test data modification request validation."""
        with pytest.raises(ValidationError):
            DataModificationRequest()  # Missing operation


class TestQueryResponse:
    """Test QueryResponse model."""

    def test_successful_query_response(self):
        """Test successful query response creation."""
        response = QueryResponse(
            success=True,
            data=[{"id": 1, "name": "John"}],
            result_schema={"users": {"id": "integer", "name": "string"}},
        )
        assert response.success is True
        assert response.data == [{"id": 1, "name": "John"}]
        assert response.result_schema == {"users": {"id": "integer", "name": "string"}}
        assert response.data_loss_indicator == DataLossIndicator.NONE
        assert response.error is None

    def test_error_query_response(self):
        """Test error query response creation."""
        response = QueryResponse(
            success=False, error="Table not found", error_details={"table": "non_existent"}
        )
        assert response.success is False
        assert response.error == "Table not found"
        assert response.error_details == {"table": "non_existent"}
        assert response.data is None

    def test_query_response_with_data_loss(self):
        """Test query response with data loss indicator."""
        response = QueryResponse(
            success=True,
            data_loss_indicator=DataLossIndicator.PROBABLE,
            ai_comment="Some data might be lost during schema migration",
        )
        assert response.success is True
        assert response.data_loss_indicator == DataLossIndicator.PROBABLE
        assert response.ai_comment == "Some data might be lost during schema migration"


class TestErrorResponse:
    """Test ErrorResponse model."""

    def test_simple_error_response(self):
        """Test simple error response creation."""
        response = ErrorResponse(error="Something went wrong")
        assert response.success is False
        assert response.error == "Something went wrong"
        assert response.error_details is None
        assert response.error_type is None

    def test_detailed_error_response(self):
        """Test detailed error response creation."""
        response = ErrorResponse(
            error="Database connection failed",
            error_details={"host": "localhost", "port": 5432},
            error_type="ConnectionError",
        )
        assert response.success is False
        assert response.error == "Database connection failed"
        assert response.error_details == {"host": "localhost", "port": 5432}
        assert response.error_type == "ConnectionError"

    def test_error_response_validation(self):
        """Test error response validation."""
        with pytest.raises(ValidationError):
            ErrorResponse()  # Missing error message
