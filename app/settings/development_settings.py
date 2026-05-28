"""Development environment settings."""

from app.settings.app_settings import AppSettings


class DevAppSettings(AppSettings):
    """Development environment settings."""

    app_env: str = "DEV"
    log_level: str = "DEBUG"
