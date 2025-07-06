"""AI-Frontend specific data models."""

from typing import Optional

from pydantic import BaseModel, Field


class FrontendRequest(BaseModel):
    """Request model for AI-Frontend operations."""

    request: str = Field(
        ..., description="Natural language request for frontend generation/modification"
    )
    transaction_id: Optional[str] = Field(None, description="Transaction ID if within transaction")


class FrontendResponse(BaseModel):
    """Response model for AI-Frontend operations."""

    status: str = Field(..., description="Success or failure status")
    generated_files: Optional[list[str]] = Field(
        None, description="List of generated/modified files"
    )
    ai_comment: str = Field(..., description="AI interpretation and actions taken")
    transaction_id: Optional[str] = Field(None, description="Transaction ID if within transaction")
    error: Optional[str] = Field(None, description="Error message if operation failed")


class FrontendInfoResponse(BaseModel):
    """Response model for frontend introspection."""

    components: list[dict[str, str]] = Field(..., description="List of frontend components")
    semantic_docs: dict[str, str] = Field(..., description="Semantic documentation for components")
    error: Optional[str] = Field(None, description="Error message if operation failed")
