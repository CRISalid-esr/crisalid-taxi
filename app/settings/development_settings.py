"""Development environment settings."""

import logging

from app.settings.app_env_types import AppEnvTypes
from app.settings.app_settings import AppSettings


class DevAppSettings(AppSettings):
    """Development environment settings."""

    app_env: AppEnvTypes = AppEnvTypes.DEV
    debug: bool = True
    logging_level: int = logging.DEBUG
    loguru_level: str = "DEBUG"
