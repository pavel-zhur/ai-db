"""Unit tests for AI-DB tools."""

import pytest
from src.tools.ai_db import (
    SchemaModifyTool,
    DataModifyTool,
    SelectTool,
    ViewModifyTool,
    ExecuteCompiledTool,
    BeginTransactionTool,
    CommitTransactionTool,
    RollbackTransactionTool,
    GetSchemaTool,
)
from src.models.ai_db import (
    QueryRequest,
    TransactionRequest,
    SchemaRequest,
    PermissionLevel,
    DataLossIndicator,
)


class TestSchemaModifyTool:
    """Test schema modification tool."""
    
    @pytest.mark.asyncio
    async def test_schema_modify_success(self, mock_ai_db, mock_git_layer, mock_logger):
        """Test successful schema modification."""
        tool = SchemaModifyTool(mock_ai_db, mock_git_layer, mock_logger)
        
        request = QueryRequest(query="CREATE TABLE products (id INT, name TEXT)")
        response = await tool.execute(request)
        
        assert response.status == "success"
        assert response.ai_comment == "Created new table"
        assert response.data_loss_indicator == DataLossIndicator.NONE
    
    @pytest.mark.asyncio
    async def test_schema_modify_with_transaction(self, mock_ai_db, mock_git_layer, mock_logger):
        """Test schema modification within transaction."""
        tool = SchemaModifyTool(mock_ai_db, mock_git_layer, mock_logger)
        tool.store_transaction("test-tx-1", {"id": "test-tx-1"})
        
        request = QueryRequest(
            query="ALTER TABLE users ADD COLUMN age INT",
            transaction_id="test-tx-1"
        )
        response = await tool.execute(request)
        
        assert response.status == "success"
        assert response.transaction_id == "test-tx-1"
    
    def test_tool_properties(self, mock_ai_db, mock_git_layer, mock_logger):
        """Test tool properties."""
        tool = SchemaModifyTool(mock_ai_db, mock_git_layer, mock_logger)
        
        assert tool.name == "schema_modify"
        assert tool.permission_level == PermissionLevel.SCHEMA_MODIFY
        assert tool.destructive_hint is True
        assert tool.read_only_hint is False


class TestDataModifyTool:
    """Test data modification tool."""
    
    @pytest.mark.asyncio
    async def test_data_modify_success(self, mock_ai_db, mock_git_layer, mock_logger):
        """Test successful data modification."""
        tool = DataModifyTool(mock_ai_db, mock_git_layer, mock_logger)
        
        request = QueryRequest(query="INSERT INTO users (name, email) VALUES ('Test', 'test@example.com')")
        response = await tool.execute(request)
        
        assert response.status == "success"
        assert response.ai_comment == "Operation completed"


class TestSelectTool:
    """Test select query tool."""
    
    @pytest.mark.asyncio
    async def test_select_success(self, mock_ai_db, mock_git_layer, mock_logger):
        """Test successful select query."""
        tool = SelectTool(mock_ai_db, mock_git_layer, mock_logger)
        
        request = QueryRequest(query="SELECT * FROM users")
        response = await tool.execute(request)
        
        assert response.status == "success"
        assert response.data is not None
        assert len(response.data) == 2
        assert response.ai_comment == "Selected all users"
    
    def test_tool_properties(self, mock_ai_db, mock_git_layer, mock_logger):
        """Test tool properties."""
        tool = SelectTool(mock_ai_db, mock_git_layer, mock_logger)
        
        assert tool.name == "select"
        assert tool.permission_level == PermissionLevel.SELECT
        assert tool.destructive_hint is False
        assert tool.read_only_hint is True


class TestTransactionTools:
    """Test transaction-related tools."""
    
    @pytest.mark.asyncio
    async def test_begin_transaction(self, mock_ai_db, mock_git_layer, mock_logger):
        """Test beginning a transaction."""
        tool = BeginTransactionTool(mock_ai_db, mock_git_layer, mock_logger)
        
        request = TransactionRequest()
        response = await tool.execute(request)
        
        assert response.status == "success"
        assert response.transaction_id is not None
        assert response.transaction_id.startswith("mock-transaction-")
    
    @pytest.mark.asyncio
    async def test_commit_transaction(self, mock_ai_db, mock_git_layer, mock_logger):
        """Test committing a transaction."""
        begin_tool = BeginTransactionTool(mock_ai_db, mock_git_layer, mock_logger)
        commit_tool = CommitTransactionTool(mock_ai_db, mock_git_layer, mock_logger)
        
        # Share transaction state
        begin_tool._transactions = commit_tool._transactions = {}
        
        # Begin transaction
        begin_response = await begin_tool.execute(TransactionRequest())
        tx_id = begin_response.transaction_id
        
        # Commit transaction
        commit_request = TransactionRequest(
            transaction_id=tx_id,
            commit_message="Test commit"
        )
        commit_response = await commit_tool.execute(commit_request)
        
        assert commit_response.status == "success"
        assert commit_response.transaction_id == tx_id
    
    @pytest.mark.asyncio
    async def test_rollback_transaction(self, mock_ai_db, mock_git_layer, mock_logger):
        """Test rolling back a transaction."""
        begin_tool = BeginTransactionTool(mock_ai_db, mock_git_layer, mock_logger)
        rollback_tool = RollbackTransactionTool(mock_ai_db, mock_git_layer, mock_logger)
        
        # Share transaction state
        begin_tool._transactions = rollback_tool._transactions = {}
        
        # Begin transaction
        begin_response = await begin_tool.execute(TransactionRequest())
        tx_id = begin_response.transaction_id
        
        # Rollback transaction
        rollback_request = TransactionRequest(transaction_id=tx_id)
        rollback_response = await rollback_tool.execute(rollback_request)
        
        assert rollback_response.status == "success"
        assert rollback_response.transaction_id == tx_id


class TestIntrospectionTools:
    """Test introspection tools."""
    
    @pytest.mark.asyncio
    async def test_get_schema(self, mock_ai_db, mock_git_layer, mock_logger):
        """Test getting schema."""
        tool = GetSchemaTool(mock_ai_db, mock_git_layer, mock_logger)
        
        request = SchemaRequest(include_semantic_docs=True)
        response = await tool.execute(request)
        
        assert response.schema is not None
        assert "tables" in response.schema
        assert response.semantic_docs is not None
    
    @pytest.mark.asyncio
    async def test_get_schema_without_docs(self, mock_ai_db, mock_git_layer, mock_logger):
        """Test getting schema without semantic docs."""
        tool = GetSchemaTool(mock_ai_db, mock_git_layer, mock_logger)
        
        request = SchemaRequest(include_semantic_docs=False)
        response = await tool.execute(request)
        
        assert response.schema is not None
        assert response.semantic_docs is None