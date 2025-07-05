"""Data models for the console."""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union


class OutputFormat(Enum):
    """Output format for query results."""
    TABLE = "table"
    JSON = "json"
    YAML = "yaml"


class CommandType(Enum):
    """Type of console command."""
    QUERY = "query"
    SCHEMA_MODIFY = "schema_modify"
    DATA_MODIFY = "data_modify"
    VIEW_MODIFY = "view_modify"
    FRONTEND_GENERATE = "frontend_generate"
    TRANSACTION_BEGIN = "transaction_begin"
    TRANSACTION_COMMIT = "transaction_commit"
    TRANSACTION_ROLLBACK = "transaction_rollback"
    HELP = "help"
    EXIT = "exit"
    OUTPUT_FORMAT = "output_format"
    EXPORT = "export"


@dataclass
class ConversationEntry:
    """Entry in conversation history."""
    timestamp: datetime
    user_input: str
    response: Optional[str] = None
    error: Optional[str] = None
    command_type: Optional[CommandType] = None


@dataclass
class SessionState:
    """Current session state."""
    conversation_history: List[ConversationEntry]
    transaction_active: bool = False
    transaction_id: Optional[str] = None
    current_output_format: OutputFormat = OutputFormat.TABLE
    
    def add_entry(
        self,
        user_input: str,
        response: Optional[str] = None,
        error: Optional[str] = None,
        command_type: Optional[CommandType] = None
    ) -> None:
        """Add entry to conversation history."""
        entry = ConversationEntry(
            timestamp=datetime.now(),
            user_input=user_input,
            response=response,
            error=error,
            command_type=command_type
        )
        self.conversation_history.append(entry)