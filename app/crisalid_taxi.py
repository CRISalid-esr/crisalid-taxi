"""Main application module, defining the FastAPI app and its configuration."""
import sys

from fastapi import FastAPI
from loguru import logger

from app.config import settings
from app.routes.api import router as api_router
from app.routes.health import router as health_router
from app.settings.app_env_types import AppEnvTypes


class CrisalidTaxi(FastAPI):
    """Main application, routing logic, middlewares and startup/shutdown events"""

    def __init__(self):
        super().__init__(
            title="CRISalid Taxi API",
            description="API pour la gestion de la taxonomie OpenAlex",
            version="1.0.0",
        )
        settings_instance = settings

        # Configure logging avec loguru
        if settings_instance.app_env != AppEnvTypes.TEST.value:
            logger.remove()
            logger.add(
                sys.stderr,
                level=settings_instance.log_level,
                format="<level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
            )

        # Include routers
        self.include_router(
            api_router,
            prefix="/api/v1",
        )
        self.include_router(health_router, prefix="/health", tags=["health"])

        logger.info("Application CRISalid Taxi initialized")
