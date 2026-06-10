"""Main application module, defining the FastAPI app and its configuration."""

import sys
from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI
from loguru import logger
from pydantic import ValidationError

from app.config import get_app_settings
from app.errors.exceptions import NotFoundError, invalid_entity_error_handler
from app.routes.api import router as api_router
from app.services.loading import get_openalex_loader
from app.settings.app_env_types import AppEnvTypes
from app.services.embeddings.embedding_service import EmbeddingService
from app.services.embeddings.providers.sentence_transformer import SentenceTransformerProvider


@asynccontextmanager
async def _lifespan(app: FastAPI) -> AsyncIterator[None]:  # noqa: ARG001
    """Application lifespan: run the OpenAlex startup pipeline."""
    settings = get_app_settings()

    if settings.app_env == AppEnvTypes.TEST:
        dummy_provider = SentenceTransformerProvider(settings)
        embedding_service = EmbeddingService.__new__(EmbeddingService)
        embedding_service.settings = settings
        embedding_service.provider = dummy_provider
    else:
        embedding_service = EmbeddingService()

    if settings.app_env != AppEnvTypes.TEST:
        from app.services.pipeline import StartupPipeline
        from app.services.opensearch_client import get_opensearch_client

        pipeline = StartupPipeline(
            loader=get_openalex_loader(),
            embedding_service=embedding_service,
            opensearch_client=get_opensearch_client(),
        )
        await pipeline.run()

    yield  # ← application runs here

    logger.info("CrisalidTaxi shutdown complete")


class CrisalidTaxi(FastAPI):
    """Main application, routing logic, middlewares and startup/shutdown events"""

    def __init__(self):
        super().__init__(lifespan=_lifespan)
        settings = get_app_settings()

        self.include_router(api_router, prefix=f"{settings.api_prefix}/{settings.api_version}")

        if settings.app_env != AppEnvTypes.TEST:
            logger.remove()
            logger.add(
                settings.logger_sink,
                level=settings.loguru_level,
                **({"rotation": "100 MB"} if settings.logger_sink != sys.stderr else {}),
            )

        self.add_exception_handler(NotFoundError, invalid_entity_error_handler)
        self.add_exception_handler(ValidationError, invalid_entity_error_handler)
