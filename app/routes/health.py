"""Health Check and Probes Routes."""

from fastapi import APIRouter, HTTPException, status
from loguru import logger
from pydantic import BaseModel

from app.services.embeddings.embedding_service import EmbeddingService
from app.services.opensearch_client import get_opensearch_client


class HealthCheck(BaseModel):
    status: str
    opensearch: str
    embedding_model: str


class LivenessCheck(BaseModel):
    status: str


probes_router = APIRouter()


async def _perform_full_check(probe_name: str) -> HealthCheck:
    """Helper to check all service dependencies."""
    os_client = get_opensearch_client()
    opensearch_status = "connected" if os_client.ping() else "disconnected"

    # Check Embedding service avec try/except
    emb_service = EmbeddingService()
    try:
        embedding_status = "connected" if await emb_service.ping() else "disconnected"
    except Exception as e:  # pylint: disable=broad-exception-caught
        logger.error("Embedding service health check failed: %s", e)
        embedding_status = "disconnected"

    if opensearch_status == "disconnected" or embedding_status == "disconnected":
        logger.warning(
            "%s check failed: opensearch=%s, embedding=%s",
            probe_name,
            opensearch_status,
            embedding_status,
        )
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "status": "unhealthy",
                "opensearch": opensearch_status,
                "embedding_model": embedding_status,
            },
        )

    return HealthCheck(
        status="healthy",
        opensearch=opensearch_status,
        embedding_model=embedding_status,
    )


@probes_router.get(
    "/liveness",
    tags=["healthcheck"],
    summary="Liveness check for Kubernetes",
    response_description="Return liveness status of the API",
    status_code=status.HTTP_200_OK,
    response_model=LivenessCheck,
)
async def get_liveness() -> LivenessCheck:
    logger.info("Liveness check performed")
    return LivenessCheck(status="healthy")


@probes_router.get(
    "/readiness",
    tags=["healthcheck"],
    summary="Readiness check for Kubernetes",
    response_description="Return readiness status of API and dependencies",
    status_code=status.HTTP_200_OK,
    response_model=HealthCheck,
)
async def get_readiness() -> HealthCheck:
    logger.info("Readiness check performed")
    return await _perform_full_check("Readiness")
