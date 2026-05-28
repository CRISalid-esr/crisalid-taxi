"""Main application module, defining the FastAPI app and its configuration."""
import sys

from fastapi import FastAPI
from loguru import logger
from pydantic import BaseModel

from app.config import settings
from app.routes.api import router as api_router
from app.settings.app_env_types import AppEnvTypes


class RootResponse(BaseModel):
    """Response model for root endpoint."""

    version: str
    title: str


class CrisalidTaxi(FastAPI):
    """Main application, routing logic, middlewares and startup/shutdown events"""

    def __init__(self, *args, **kwargs):
        kwargs.setdefault("title", "CRISalid Taxi API")
        kwargs.setdefault("description", "API pour la gestion de la taxonomie OpenAlex")
        kwargs.setdefault("version", "1.0.0")
        super().__init__(*args, **kwargs)
        settings_instance = settings

        # Configure logging avec loguru
        if settings_instance.app_env != AppEnvTypes.TEST:
            logger.remove()
            logger.add(
                sys.stderr,
                level=settings_instance.loguru_level,
                format="<level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
            )

        # Include routers
        self.include_router(api_router, prefix="/api/v1")

        # Root endpoint
        @self.get("/", response_model=RootResponse)
        async def root() -> RootResponse:
            """Root endpoint returning API information."""
            logger.info("Root endpoint called")
            return RootResponse(
                version=self.version,
                title=self.title,
            )

        logger.info("Application CRISalid Taxi initialized")
