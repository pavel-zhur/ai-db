"""AI-DB specific data models."""

from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field


class PermissionLevel(str, Enum):
    """Permission levels for AI-DB operations."""

    SELECT = "select"
    DATA_MODIFY = "data_modify"
    SCHEMA_MODIFY = "schema_modify"
    VIEW_MODIFY = "view_modify"


class DataLossIndicator(str, Enum):
    """Indicators for potential data loss."""

    NONE = "none"
    PROBABLE = "probable"
    YES = "yes"


class QueryRequest(BaseModel):
    """Request model for AI-DB queries."""

    query: str = Field(..., description="Natural language query to execute")
    transaction_id: Optional[str] = Field(None, description="Transaction ID if within transaction")


class QueryResponse(BaseModel):
    """Response model for AI-DB queries."""

    status: str = Field(..., description="Success or failure status")
    data: Optional[list[dict[str, Any]]] = Field(
        None, description="Query results for select operations"
    )
    result_schema: Optional[dict[str, Any]] = Field(
        default=None, description="Result schema for data-returning queries"
    )
    data_loss_indicator: DataLossIndicator = Field(
        ..., description="Indicator of potential data loss"
    )
    ai_comment: str = Field(..., description="AI interpretation details")
    compiled_plan: Optional[str] = Field(
        None, description="Serialized query plan for data-returning queries"
    )
    transaction_id: Optional[str] = Field(None, description="Transaction ID if within transaction")
    error: Optional[str] = Field(None, description="Error message if operation failed")


class TransactionRequest(BaseModel):
    """Request model for transaction operations."""

    transaction_id: Optional[str] = Field(None, description="Transaction ID for commit/rollback")
    commit_message: Optional[str] = Field(None, description="Commit message for git layer")


class TransactionResponse(BaseModel):
    """Response model for transaction operations."""

    status: str = Field(..., description="Success or failure status")
    transaction_id: Optional[str] = Field(None, description="Transaction ID for new transactions")
    error: Optional[str] = Field(None, description="Error message if operation failed")


class SchemaRequest(BaseModel):
    """Request model for schema introspection."""

    include_semantic_docs: bool = Field(True, description="Include semantic documentation")


class SchemaResponse(BaseModel):
    """Response model for schema introspection."""

    db_schema: dict[str, Any] = Field(..., description="Current database schema")
    semantic_docs: Optional[dict[str, Any]] = Field(None, description="Semantic documentation")
    error: Optional[str] = Field(None, description="Error message if operation failed")
