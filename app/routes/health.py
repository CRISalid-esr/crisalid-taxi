"""Health Check Route."""
from fastapi import status, APIRouter
from loguru import logger
from pydantic import BaseModel

from app.services.opensearch_client import get_opensearch_client


class HealthCheck(BaseModel):
    """Response model to validate and return when performing a health check."""

    status: str = "OK"
    opensearch: str = "disconnected"


router = APIRouter()


@router.get(
    "/",
    tags=["healthcheck"],
    summary="Perform a Health Check",
    response_description="Return HTTP Status Code 200 (OK)",
    status_code=status.HTTP_200_OK,
    response_model=HealthCheck,
)
async def get_health() -> HealthCheck:
    """
    ## Perform a Health Check
    Endpoint to perform a healthcheck on API and dependencies.

    Returns:
        HealthCheck: Returns a JSON response with the health status
    """
    logger.info("Health check performed")
    
    # Check OpenSearch connection
    os_client = get_opensearch_client()
    opensearch_status = "connected" if os_client.ping() else "disconnected"
    
    return HealthCheck(status="healthy", opensearch=opensearch_status)
