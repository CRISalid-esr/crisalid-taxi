"""Test environment settings."""

import logging

from app.settings.app_env_types import AppEnvTypes
from app.settings.app_settings import AppSettings


class TestAppSettings(AppSettings):
    """Test environment settings."""

    app_env: AppEnvTypes = AppEnvTypes.TEST
    debug: bool = True
    logging_level: int = logging.INFO
    loguru_level: str = "INFO"
