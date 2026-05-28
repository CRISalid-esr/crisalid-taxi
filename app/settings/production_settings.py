"""Production environment settings."""

from app.settings.app_settings import AppSettings


class ProdAppSettings(AppSettings):
    """Production environment settings."""

    app_env: str = "PROD"
    log_level: str = "WARNING"
