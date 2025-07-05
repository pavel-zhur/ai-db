"""Test data models."""

from datetime import datetime

import pytest

from console.models import (
    OutputFormat,
    CommandType,
    ConversationEntry,
    SessionState
)


def test_output_format_enum():
    """Test OutputFormat enum."""
    assert OutputFormat.TABLE.value == "table"
    assert OutputFormat.JSON.value == "json" 
    assert OutputFormat.YAML.value == "yaml"
    
    # Test enum creation from string
    assert OutputFormat("table") == OutputFormat.TABLE
    assert OutputFormat("json") == OutputFormat.JSON
    assert OutputFormat("yaml") == OutputFormat.YAML


def test_command_type_enum():
    """Test CommandType enum."""
    assert CommandType.QUERY.value == "query"
    assert CommandType.SCHEMA_MODIFY.value == "schema_modify"
    assert CommandType.TRANSACTION_BEGIN.value == "transaction_begin"
    assert CommandType.HELP.value == "help"
    assert CommandType.EXIT.value == "exit"


def test_conversation_entry():
    """Test ConversationEntry model."""
    now = datetime.now()
    entry = ConversationEntry(
        timestamp=now,
        user_input="SELECT * FROM users",
        response="3 rows returned",
        command_type=CommandType.QUERY
    )
    
    assert entry.timestamp == now
    assert entry.user_input == "SELECT * FROM users"
    assert entry.response == "3 rows returned"
    assert entry.error is None
    assert entry.command_type == CommandType.QUERY
    
    # Test with error
    error_entry = ConversationEntry(
        timestamp=now,
        user_input="invalid query",
        error="Syntax error"
    )
    
    assert error_entry.response is None
    assert error_entry.error == "Syntax error"
    assert error_entry.command_type is None


def test_session_state():
    """Test SessionState model."""
    state = SessionState(
        conversation_history=[],
        transaction_active=False,
        current_output_format=OutputFormat.TABLE
    )
    
    assert len(state.conversation_history) == 0
    assert state.transaction_active is False
    assert state.transaction_id is None
    assert state.current_output_format == OutputFormat.TABLE
    
    # Test adding entry
    state.add_entry(
        user_input="test query",
        response="test response",
        command_type=CommandType.QUERY
    )
    
    assert len(state.conversation_history) == 1
    entry = state.conversation_history[0]
    assert entry.user_input == "test query"
    assert entry.response == "test response"
    assert entry.command_type == CommandType.QUERY
    assert isinstance(entry.timestamp, datetime)
    
    # Test adding error entry
    state.add_entry(
        user_input="bad query",
        error="Error message"
    )
    
    assert len(state.conversation_history) == 2
    error_entry = state.conversation_history[1]
    assert error_entry.user_input == "bad query"
    assert error_entry.response is None
    assert error_entry.error == "Error message"


def test_session_state_with_transaction():
    """Test SessionState with transaction."""
    state = SessionState(
        conversation_history=[],
        transaction_active=True,
        transaction_id="tx-123"
    )
    
    assert state.transaction_active is True
    assert state.transaction_id == "tx-123"