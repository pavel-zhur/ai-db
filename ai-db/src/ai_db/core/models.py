"""Core data models for AI-DB."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Any
from datetime import datetime


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
    default: Optional[Any] = None
    description: Optional[str] = None


@dataclass
class Constraint:
    """Represents a table constraint."""
    
    name: str
    type: ConstraintType
    columns: List[str]
    definition: Optional[str] = None  # For CHECK constraints
    referenced_table: Optional[str] = None  # For FOREIGN KEY
    referenced_columns: Optional[List[str]] = None  # For FOREIGN KEY


@dataclass
class Table:
    """Represents a database table."""
    
    name: str
    columns: List[Column]
    constraints: List[Constraint] = field(default_factory=list)
    description: Optional[str] = None


@dataclass
class Schema:
    """Represents the database schema."""
    
    tables: Dict[str, Table] = field(default_factory=dict)
    views: Dict[str, str] = field(default_factory=dict)  # name -> python code
    version: str = "1.0.0"
    semantic_documentation: Dict[str, str] = field(default_factory=dict)


@dataclass
class QueryContext:
    """Context passed to query execution."""
    
    schema: Optional[Schema] = None
    recent_errors: List[str] = field(default_factory=list)
    retry_count: int = 0
    max_retries: int = 3


@dataclass
class QueryResult:
    """Result of a query execution."""
    
    status: bool
    data: Optional[List[Dict[str, Any]]] = None
    schema: Optional[Dict[str, Any]] = None  # JSON Schema of result
    data_loss_indicator: DataLossIndicator = DataLossIndicator.NONE
    ai_comment: Optional[str] = None
    compiled_plan: Optional[str] = None
    transaction_id: Optional[str] = None
    error: Optional[str] = None
    execution_time: Optional[float] = None


@dataclass
class TransactionContext:
    """Context for transaction operations."""
    
    transaction_id: str
    working_directory: str
    is_write_escalated: bool = False
    
    def escalate_write(self) -> str:
        """Escalate to write mode and return new working directory."""
        raise NotImplementedError("Must be implemented by git-layer")


@dataclass
class AIOperation:
    """Represents an operation determined by AI."""
    
    operation_type: str  # select, insert, update, delete, create_table, etc.
    permission_level: PermissionLevel
    affected_tables: List[str]
    requires_python_generation: bool = False
    python_code: Optional[str] = None
    file_updates: Dict[str, str] = field(default_factory=dict)  # path -> content
    validation_required: bool = True