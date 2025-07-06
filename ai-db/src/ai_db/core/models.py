"""Core data models for AI-DB."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class PermissionLevel(Enum):
    """Permission levels for database operations."""

    SELECT = "select"
    DATA_MODIFY = "data_modify"
    SCHEMA_MODIFY = "schema_modify"
    VIEW_MODIFY = "view_modify"


class DataLossIndicator(Enum):
    """Indicates potential data loss from an operation."""

    NONE = "none"
    PROBABLE = "probable"
    YES = "yes"


class ConstraintType(Enum):
    """Types of constraints supported."""

    PRIMARY_KEY = "primary_key"
    FOREIGN_KEY = "foreign_key"
    CHECK = "check"
    NOT_NULL = "not_null"
    UNIQUE = "unique"


@dataclass
class Column:
    """Represents a table column."""

    name: str
    type: str  # JSON Schema type
    nullable: bool = True
    default: Any | None = None
    description: str | None = None


@dataclass
class Constraint:
    """Represents a table constraint."""

    name: str
    type: ConstraintType
    columns: list[str]
    definition: str | None = None  # For CHECK constraints
    referenced_table: str | None = None  # For FOREIGN KEY
    referenced_columns: list[str] | None = None  # For FOREIGN KEY


@dataclass
class Table:
    """Represents a database table."""

    name: str
    columns: list[Column]
    constraints: list[Constraint] = field(default_factory=list)
    description: str | None = None


@dataclass
class Schema:
    """Represents the database schema."""

    tables: dict[str, Table] = field(default_factory=dict)
    views: dict[str, str] = field(default_factory=dict)  # name -> python code
    version: str = "1.0.0"
    semantic_documentation: dict[str, str] = field(default_factory=dict)


@dataclass
class QueryContext:
    """Context passed to query execution."""

    schema: Schema | None = None
    recent_errors: list[str] = field(default_factory=list)
    retry_count: int = 0
    max_retries: int = 3


@dataclass
class QueryResult:
    """Result of a query execution."""

    status: bool
    data: list[dict[str, Any]] | None = None
    schema: dict[str, Any] | None = None  # JSON Schema of result
    data_loss_indicator: DataLossIndicator = DataLossIndicator.NONE
    ai_comment: str | None = None
    compiled_plan: str | None = None
    transaction_id: str | None = None
    error: str | None = None
    execution_time: float | None = None


@dataclass
class AIOperation:
    """Represents an operation determined by AI."""

    operation_type: str  # select, insert, update, delete, create_table, etc.
    permission_level: PermissionLevel
    affected_tables: list[str]
    requires_python_generation: bool = False
    python_code: str | None = None
    file_updates: dict[str, str] = field(default_factory=dict)  # path -> content
    validation_required: bool = True
