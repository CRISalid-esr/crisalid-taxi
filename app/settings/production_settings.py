"""Production environment settings."""

import logging

from app.settings.app_env_types import AppEnvTypes
from app.settings.app_settings import AppSettings


class ProdAppSettings(AppSettings):
    """Production environment settings."""

    app_env: AppEnvTypes = AppEnvTypes.PROD
    debug: bool = False
    logging_level: int = logging.WARNING
    loguru_level: str = "WARNING"
