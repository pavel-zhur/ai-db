"""Unit tests for data models."""

import pytest
from pydantic import ValidationError
from src.models.ai_db import (
    PermissionLevel,
    DataLossIndicator,
    QueryRequest,
    QueryResponse,
    TransactionRequest,
    TransactionResponse,
    SchemaRequest,
    SchemaResponse,
)
from src.models.ai_frontend import (
    FrontendRequest,
    FrontendResponse,
    FrontendInfoResponse,
)


class TestAIDBModels:
    """Test AI-DB models."""
    
    def test_permission_level_enum(self):
        """Test permission level enum."""
        assert PermissionLevel.SELECT.value == "select"
        assert PermissionLevel.DATA_MODIFY.value == "data_modify"
        assert PermissionLevel.SCHEMA_MODIFY.value == "schema_modify"
        assert PermissionLevel.VIEW_MODIFY.value == "view_modify"
    
    def test_data_loss_indicator_enum(self):
        """Test data loss indicator enum."""
        assert DataLossIndicator.NONE.value == "none"
        assert DataLossIndicator.PROBABLE.value == "probable"
        assert DataLossIndicator.YES.value == "yes"
    
    def test_query_request_validation(self):
        """Test query request validation."""
        # Valid request
        request = QueryRequest(query="SELECT * FROM users")
        assert request.query == "SELECT * FROM users"
        assert request.transaction_id is None
        
        # With transaction ID
        request = QueryRequest(query="INSERT INTO users", transaction_id="tx-123")
        assert request.transaction_id == "tx-123"
        
        # Invalid - missing query
        with pytest.raises(ValidationError):
            QueryRequest()
    
    def test_query_response_validation(self):
        """Test query response validation."""
        # Minimal valid response
        response = QueryResponse(
            status="success",
            data_loss_indicator=DataLossIndicator.NONE,
            ai_comment="Query executed"
        )
        assert response.status == "success"
        assert response.data is None
        assert response.error is None
        
        # Full response
        response = QueryResponse(
            status="success",
            data=[{"id": 1, "name": "Test"}],
            schema={"columns": ["id", "name"]},
            data_loss_indicator=DataLossIndicator.NONE,
            ai_comment="Selected data",
            compiled_plan="compiled_123",
            transaction_id="tx-456"
        )
        assert response.data == [{"id": 1, "name": "Test"}]
        assert response.compiled_plan == "compiled_123"
    
    def test_transaction_request_validation(self):
        """Test transaction request validation."""
        # Empty request (for begin)
        request = TransactionRequest()
        assert request.transaction_id is None
        assert request.commit_message is None
        
        # With transaction ID
        request = TransactionRequest(
            transaction_id="tx-123",
            commit_message="Test commit"
        )
        assert request.transaction_id == "tx-123"
        assert request.commit_message == "Test commit"
    
    def test_schema_request_validation(self):
        """Test schema request validation."""
        # Default
        request = SchemaRequest()
        assert request.include_semantic_docs is True
        
        # Explicit false
        request = SchemaRequest(include_semantic_docs=False)
        assert request.include_semantic_docs is False


class TestAIFrontendModels:
    """Test AI-Frontend models."""
    
    def test_frontend_request_validation(self):
        """Test frontend request validation."""
        # Valid request
        request = FrontendRequest(request="Create a dashboard")
        assert request.request == "Create a dashboard"
        assert request.transaction_id is None
        
        # With transaction
        request = FrontendRequest(
            request="Update form",
            transaction_id="tx-789"
        )
        assert request.transaction_id == "tx-789"
        
        # Invalid - missing request
        with pytest.raises(ValidationError):
            FrontendRequest()
    
    def test_frontend_response_validation(self):
        """Test frontend response validation."""
        # Success response
        response = FrontendResponse(
            status="success",
            generated_files=["/components/Dashboard.tsx"],
            ai_comment="Generated dashboard"
        )
        assert response.status == "success"
        assert len(response.generated_files) == 1
        assert response.error is None
        
        # Error response
        response = FrontendResponse(
            status="error",
            ai_comment="Generation failed",
            error="Invalid request"
        )
        assert response.status == "error"
        assert response.error == "Invalid request"
        assert response.generated_files is None
    
    def test_frontend_info_response_validation(self):
        """Test frontend info response validation."""
        response = FrontendInfoResponse(
            components=[
                {"name": "UserList", "path": "/components/UserList.tsx"}
            ],
            semantic_docs={
                "UserList": "Displays list of users"
            }
        )
        assert len(response.components) == 1
        assert response.components[0]["name"] == "UserList"
        assert response.semantic_docs["UserList"] == "Displays list of users"