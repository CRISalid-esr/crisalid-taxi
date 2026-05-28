"""Application configuration module."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings."""

    # Environment
    APP_ENV: str = "DEV"

    # API Configuration
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    API_TITLE: str = "CRISalid Taxi API"
    API_VERSION: str = "0.1.0"

    # Logging
    LOG_LEVEL: str = "INFO"

    # Database Configuration - Load from environment variables only
    DATABASE_URL: str = ""
    DB_HOST: str = "localhost"
    DB_PORT: int = 5432
    DB_USER: str = ""
    DB_PASSWORD: str = ""
    DB_NAME: str = ""

    class Config:
        """Pydantic configuration."""

        env_file = ".env"
        case_sensitive = True


settings = Settings()
