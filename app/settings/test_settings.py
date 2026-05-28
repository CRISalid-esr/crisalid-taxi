"""Test environment settings."""

from app.settings.app_settings import AppSettings


class TestAppSettings(AppSettings):
    """Test environment settings."""

    app_env: str = "TEST"
    log_level: str = "INFO"
