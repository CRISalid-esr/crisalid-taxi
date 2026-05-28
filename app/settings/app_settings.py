"""Base settings module."""

from pydantic_settings import BaseSettings


class AppSettings(BaseSettings):
    """Base application settings."""

    # Environment
    app_env: str = "DEV"

    # API Configuration
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_title: str = "CRISalid Taxi API"
    api_version: str = "0.1.0"

    # Logging
    log_level: str = "INFO"

    class Config:
        """Pydantic configuration."""

        env_file = ".env"
        case_sensitive = False
