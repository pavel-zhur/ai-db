"""API models for AI-Hub."""

from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field


class PermissionLevel(str, Enum):
    """Permission levels for database operations."""

    SELECT = "select"
    DATA_MODIFY = "data_modify"
    SCHEMA_MODIFY = "schema_modify"
    VIEW_MODIFY = "view_modify"


class DataLossIndicator(str, Enum):
    """Indicator for potential data loss during operations."""

    NONE = "none"
    PROBABLE = "probable"
    YES = "yes"


class QueryRequest(BaseModel):
    """Request model for executing queries."""

    query: str = Field(..., description="The query to execute in natural language or SQL")
    permissions: PermissionLevel = Field(..., description="Permission level for the operation")


class ViewQueryRequest(BaseModel):
    """Request model for executing view queries."""

    view_name: str = Field(..., description="Name of the view to execute")
    # Any is appropriate here - parameters come from external JSON and can be any type
    parameters: Optional[dict[str, Any]] = Field(None, description="Parameters to pass to the view")


class DataModificationRequest(BaseModel):
    """Request model for data modification operations."""

    operation: str = Field(
        ..., description="The data modification operation in natural language or SQL"
    )
    permissions: PermissionLevel = Field(
        default=PermissionLevel.DATA_MODIFY, description="Permission level for the operation"
    )


class QueryResponse(BaseModel):
    """Response model for query operations."""

    success: bool = Field(..., description="Whether the operation succeeded")
    # Any is appropriate - database query results can contain any JSON-serializable type
    data: Optional[list[dict[str, Any]]] = Field(None, description="Query result data")
    # Any is appropriate - schema information from database can be complex nested structures
    result_schema: Optional[dict[str, Any]] = Field(None, description="Schema information")
    data_loss_indicator: DataLossIndicator = Field(
        default=DataLossIndicator.NONE, description="Indicator for potential data loss"
    )
    ai_comment: Optional[str] = Field(None, description="AI-generated comment about the operation")
    compiled_plan: Optional[str] = Field(None, description="Compiled query plan")
    transaction_id: Optional[str] = Field(None, description="Transaction identifier")
    error: Optional[str] = Field(None, description="Error message if operation failed")
    # Any is appropriate - error details can contain arbitrary debugging information
    error_details: Optional[dict[str, Any]] = Field(None, description="Technical error details")
    execution_time: Optional[float] = Field(None, description="Execution time in seconds")


class ErrorResponse(BaseModel):
    """Response model for errors."""

    success: bool = Field(default=False, description="Always false for error responses")
    error: str = Field(..., description="User-friendly error message")
    # Any is appropriate - error details can contain arbitrary debugging information
    error_details: Optional[dict[str, Any]] = Field(
        None, description="Technical error details for debugging"
    )
    error_type: Optional[str] = Field(None, description="Error type classification")
