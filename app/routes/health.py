"""Health Check Route."""

from fastapi import APIRouter, HTTPException, status
from loguru import logger
from pydantic import BaseModel

from app.services.embeddings.embedding_service import EmbeddingService
from app.services.opensearch_client import get_opensearch_client

class HealthCheck(BaseModel):
    status: str
    opensearch: str
    embedding_model: str

router = APIRouter()

@router.get(
    "/",
    tags=["healthcheck"],
    summary="Perform a Health Check",
    response_description="Return health status of API and dependencies",
    status_code=status.HTTP_200_OK,
    response_model=HealthCheck,
)
async def get_health() -> HealthCheck:
    logger.info("Health check performed")

    os_client = get_opensearch_client()
    opensearch_status = "connected" if os_client.ping() else "disconnected"

    # Check Embedding service avec try/except
    emb_service = EmbeddingService()
    try:
        embedding_status = "connected" if await emb_service.ping() else "disconnected"
    except Exception as e:
        logger.error("Embedding service health check failed: %s", e)
        embedding_status = "disconnected"

    if opensearch_status == "disconnected" or embedding_status == "disconnected":
        logger.warning("Health check failed: opensearch=%s, embedding=%s", opensearch_status, embedding_status)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "status": "unhealthy",
                "opensearch": opensearch_status,
                "embedding_model": embedding_status,
            }
        )

    return HealthCheck(
        status="healthy",
        opensearch=opensearch_status,
        embedding_model=embedding_status,
    )