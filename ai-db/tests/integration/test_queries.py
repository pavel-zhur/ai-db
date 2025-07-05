"""Integration tests for query execution."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import os

from ai_db import AIDB, PermissionLevel, QueryResult
from ai_db.core.models import TransactionContext, QueryContext
from ai_db.transaction.context import MockTransactionContext


class TestQueryExecution:
    """Test end-to-end query execution."""
    
    @pytest.fixture
    def mock_ai_responses(self):
        """Mock AI responses for testing."""
        return {
            "create_table": {
                "operation_plan": {
                    "operation_type": "create_table",
                    "permission_level": "schema_modify",
                    "affected_tables": ["users"],
                    "requires_python_generation": False,
                    "data_loss_indicator": "none",
                    "confidence": 0.95,
                    "interpretation": "Create users table with specified columns"
                },
                "execution_plan": {
                    "file_updates": [
                        {
                            "path": "schemas/users.schema.yaml",
                            "content": """name: users
description: User accounts table
columns:
  - name: id
    type: integer
    nullable: false
    description: User ID
  - name: name
    type: string
    nullable: false
    description: User name
  - name: email
    type: string
    nullable: false
    description: Email address
constraints:
  - name: pk_users
    type: primary_key
    columns: [id]
  - name: uk_email
    type: unique
    columns: [email]
""",
                            "operation": "create"
                        },
                        {
                            "path": "tables/users.yaml",
                            "content": "[]",
                            "operation": "create"
                        }
                    ],
                    "python_code": None,
                    "validation_queries": [],
                    "error": None
                }
            },
            "insert_data": {
                "operation_plan": {
                    "operation_type": "insert",
                    "permission_level": "data_modify",
                    "affected_tables": ["users"],
                    "requires_python_generation": False,
                    "data_loss_indicator": "none",
                    "confidence": 0.95,
                    "interpretation": "Insert new user into users table"
                },
                "execution_plan": {
                    "file_updates": [
                        {
                            "path": "tables/users.yaml",
                            "content": """- id: 1
  name: Alice
  email: alice@example.com
""",
                            "operation": "update"
                        }
                    ],
                    "python_code": None,
                    "validation_queries": [],
                    "error": None
                }
            },
            "select_data": {
                "operation_plan": {
                    "operation_type": "select",
                    "permission_level": "select",
                    "affected_tables": ["users"],
                    "requires_python_generation": True,
                    "data_loss_indicator": "none",
                    "confidence": 0.95,
                    "interpretation": "Select all users from users table"
                },
                "execution_plan": {
                    "file_updates": [],
                    "python_code": """
def query_select_all_users(tables):
    users = tables.get("users", [])
    return users
""",
                    "validation_queries": [],
                    "error": None
                }
            }
        }
    
    @pytest.mark.asyncio
    async def test_create_table(self, temp_dir, mock_ai_responses):
        """Test creating a table."""
        # Set up environment
        os.environ["AI_DB_API_KEY"] = "test-key"
        
        with patch('ai_db.core.ai_agent.ChatOpenAI') as mock_llm:
            # Mock AI responses
            mock_chat = MagicMock()
            mock_llm.return_value = mock_chat
            
            # Mock analyze_query response
            analyze_response = MagicMock()
            analyze_response.content = str(mock_ai_responses["create_table"]["operation_plan"])
            
            # Mock generate_execution_plan response
            execution_response = MagicMock()
            execution_response.content = str(mock_ai_responses["create_table"]["execution_plan"])
            
            mock_chat.ainvoke = AsyncMock(side_effect=[analyze_response, execution_response])
            
            # Create AI-DB instance
            db = AIDB()
            transaction = MockTransactionContext("test-txn", str(temp_dir))
            
            # Execute create table
            result = await db.execute(
                "CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT NOT NULL, email TEXT UNIQUE)",
                PermissionLevel.SCHEMA_MODIFY,
                transaction
            )
            
            assert result.status is True
            assert result.error is None
            assert result.data_loss_indicator.value == "none"
    
    @pytest.mark.asyncio
    async def test_permission_denied(self, temp_dir):
        """Test permission denied for schema modification."""
        os.environ["AI_DB_API_KEY"] = "test-key"
        
        with patch('ai_db.core.ai_agent.ChatOpenAI') as mock_llm:
            # Mock AI response requiring schema_modify
            mock_chat = MagicMock()
            mock_llm.return_value = mock_chat
            
            analyze_response = MagicMock()
            analyze_response.content = """{
                "operation_type": "create_table",
                "permission_level": "schema_modify",
                "affected_tables": ["users"],
                "requires_python_generation": false,
                "data_loss_indicator": "none",
                "confidence": 0.95,
                "interpretation": "Create table"
            }"""
            
            mock_chat.ainvoke = AsyncMock(return_value=analyze_response)
            
            db = AIDB()
            transaction = MockTransactionContext("test-txn", str(temp_dir))
            
            # Try with insufficient permissions
            result = await db.execute(
                "CREATE TABLE users (id INT)",
                PermissionLevel.SELECT,  # Wrong permission
                transaction
            )
            
            assert result.status is False
            assert "permission" in result.error.lower()
    
    @pytest.mark.asyncio
    async def test_select_query_compilation(self, temp_dir, mock_ai_responses):
        """Test SELECT query compilation."""
        os.environ["AI_DB_API_KEY"] = "test-key"
        
        with patch('ai_db.core.ai_agent.ChatOpenAI') as mock_llm:
            mock_chat = MagicMock()
            mock_llm.return_value = mock_chat
            
            # Mock responses
            analyze_response = MagicMock()
            analyze_response.content = str(mock_ai_responses["select_data"]["operation_plan"])
            
            execution_response = MagicMock()
            execution_response.content = str(mock_ai_responses["select_data"]["execution_plan"])
            
            mock_chat.ainvoke = AsyncMock(side_effect=[analyze_response, execution_response])
            
            # Set up test data
            (temp_dir / "tables").mkdir(exist_ok=True)
            with open(temp_dir / "tables" / "users.yaml", "w") as f:
                f.write("""- id: 1
  name: Alice
  email: alice@example.com
- id: 2
  name: Bob
  email: bob@example.com
""")
            
            db = AIDB()
            transaction = MockTransactionContext("test-txn", str(temp_dir))
            
            result = await db.execute(
                "SELECT * FROM users",
                PermissionLevel.SELECT,
                transaction
            )
            
            assert result.status is True
            assert result.compiled_plan is not None
            assert len(result.data) == 2
            assert result.data[0]["name"] == "Alice"
    
    @pytest.mark.asyncio
    async def test_execute_compiled_query(self, temp_dir):
        """Test executing a pre-compiled query."""
        os.environ["AI_DB_API_KEY"] = "test-key"
        
        # Create a simple compiled query
        from ai_db.core.query_compiler import QueryCompiler
        compiler = QueryCompiler()
        
        code = '''
def query_active_users(tables):
    users = tables.get("users", [])
    return [u for u in users if u.get("is_active", True)]
'''
        
        compiled_plan = compiler.compile_query(code)
        
        # Set up test data
        (temp_dir / "tables").mkdir(exist_ok=True)
        with open(temp_dir / "tables" / "users.yaml", "w") as f:
            f.write("""- id: 1
  name: Alice
  is_active: true
- id: 2
  name: Bob
  is_active: false
- id: 3
  name: Charlie
  is_active: true
""")
        
        db = AIDB()
        transaction = MockTransactionContext("test-txn", str(temp_dir))
        
        result = db.execute_compiled(compiled_plan, transaction)
        
        assert result.status is True
        assert len(result.data) == 2
        assert result.data[0]["name"] == "Alice"
        assert result.data[1]["name"] == "Charlie"