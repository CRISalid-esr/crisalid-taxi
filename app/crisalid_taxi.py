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
from app.services.embeddings.embedding_service import EmbeddingService
from app.services.loading import get_openalex_loader
from app.settings.app_env_types import AppEnvTypes


@asynccontextmanager
async def _lifespan(app: FastAPI) -> AsyncIterator[None]:  # noqa: ARG001
    """Application lifespan: load OpenAlex data then compute embeddings at startup."""
    settings = get_app_settings()

    if settings.app_env != AppEnvTypes.TEST:
        loader = get_openalex_loader()

        if loader._loaded:
            # Data already in memory (e.g. hot reload) – jump straight to embeddings
            embedding_service = EmbeddingService()
            await loader.load_embeddings(embedding_service)
        else:
            ok = loader.load()
            if ok:
                embedding_service = EmbeddingService()
                await loader.load_embeddings(embedding_service)
            else:
                logger.warning(
                    "OpenAlex data could not be loaded – embeddings skipped at startup"
                )

    yield  # ← application runs here

    # Shutdown: loader is cached, provider is stateless – nothing to clean up
    logger.info("CrisalidTaxi shutdown complete")


class CrisalidTaxi(FastAPI):
    """Main application, routing logic, middlewares and startup/shutdown events"""

    def __init__(self):
        super().__init__(lifespan=_lifespan)
        settings = get_app_settings()

        self.include_router(
            api_router, prefix=f"{settings.api_prefix}/{settings.api_version}"
        )

        if settings.app_env != AppEnvTypes.TEST:
            logger.remove()
            logger.add(
                settings.logger_sink,
                level=settings.loguru_level,
                **({
                    "rotation": "100 MB"
                } if settings.logger_sink != sys.stderr else {}),
            )

        self.add_exception_handler(NotFoundError, invalid_entity_error_handler)
        self.add_exception_handler(ValidationError, invalid_entity_error_handler)
