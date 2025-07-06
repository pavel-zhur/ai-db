"""Data models for the console."""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum


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
    response: str | None = None
    error: str | None = None
    command_type: CommandType | None = None


@dataclass
class SessionState:
    """Current session state."""

    conversation_history: list[ConversationEntry]
    transaction_active: bool = False
    transaction_id: str | None = None
    current_output_format: OutputFormat = OutputFormat.TABLE

    def add_entry(
        self,
        user_input: str,
        response: str | None = None,
        error: str | None = None,
        command_type: CommandType | None = None,
    ) -> None:
        """Add entry to conversation history."""
        entry = ConversationEntry(
            timestamp=datetime.now(),
            user_input=user_input,
            response=response,
            error=error,
            command_type=command_type,
        )
        self.conversation_history.append(entry)
