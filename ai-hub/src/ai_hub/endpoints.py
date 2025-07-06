"""API endpoints for AI-Hub."""

import logging

from fastapi import APIRouter, Depends, HTTPException

from .exceptions import AIHubError, create_user_friendly_error
from .models import (
    DataModificationRequest,
    ErrorResponse,
    QueryRequest,
    QueryResponse,
    ViewQueryRequest,
)
from .service import AIHubService

logger = logging.getLogger(__name__)


def get_service() -> AIHubService:
    """Dependency to get AI-Hub service instance."""
    from .main import get_service_instance

    return get_service_instance()


router = APIRouter()


@router.post("/db/query", response_model=QueryResponse)
async def execute_query(
    request: QueryRequest, service: AIHubService = Depends(get_service)
) -> QueryResponse:
    """Execute a compiled query or natural language query."""
    try:
        logger.info(
            f"Executing query with permissions {request.permissions}: {request.query[:100]}..."
        )

        result = await service.execute_query(query=request.query, permissions=request.permissions)

        logger.info(f"Query execution completed successfully: {result.success}")
        return result

    except AIHubError:
        # AIHubError instances are handled by global exception handler
        raise
    except Exception as e:
        logger.exception(f"Unexpected error in execute_query: {e}")

        # Convert to user-friendly error
        user_friendly_message, technical_details, error_type = create_user_friendly_error(e)

        raise HTTPException(
            status_code=500,
            detail=ErrorResponse(
                error=user_friendly_message, error_details=technical_details, error_type=error_type
            ).model_dump(),
        )


@router.post("/db/query/view", response_model=QueryResponse)
async def execute_view(
    request: ViewQueryRequest, service: AIHubService = Depends(get_service)
) -> QueryResponse:
    """Execute a named view query."""
    try:
        logger.info(f"Executing view: {request.view_name}")

        # Convert parameters from Any to object if present
        params: dict[str, object] | None = None
        if request.parameters:
            params = {k: v for k, v in request.parameters.items()}

        result = await service.execute_view(view_name=request.view_name, parameters=params)

        logger.info(f"View execution completed successfully: {result.success}")
        return result

    except AIHubError:
        # AIHubError instances are handled by global exception handler
        raise
    except Exception as e:
        logger.exception(f"Unexpected error in execute_view: {e}")

        # Convert to user-friendly error
        user_friendly_message, technical_details, error_type = create_user_friendly_error(e)

        raise HTTPException(
            status_code=500,
            detail=ErrorResponse(
                error=user_friendly_message, error_details=technical_details, error_type=error_type
            ).model_dump(),
        )


@router.post("/db/data", response_model=QueryResponse)
async def execute_data_modification(
    request: DataModificationRequest, service: AIHubService = Depends(get_service)
) -> QueryResponse:
    """Execute a data modification operation (INSERT/UPDATE/DELETE)."""
    try:
        logger.info(
            f"Executing data modification with permissions {request.permissions}: "
            f"{request.operation[:100]}..."
        )

        result = await service.execute_data_modification(
            operation=request.operation, permissions=request.permissions
        )

        logger.info(f"Data modification completed successfully: {result.success}")
        return result

    except AIHubError:
        # AIHubError instances are handled by global exception handler
        raise
    except Exception as e:
        logger.exception(f"Unexpected error in execute_data_modification: {e}")

        # Convert to user-friendly error
        user_friendly_message, technical_details, error_type = create_user_friendly_error(e)

        raise HTTPException(
            status_code=500,
            detail=ErrorResponse(
                error=user_friendly_message, error_details=technical_details, error_type=error_type
            ).model_dump(),
        )
