"""Application settings."""

from pydantic_settings import BaseSettings


class AppSettings(BaseSettings):
    """Application settings."""

    app_name: str = "CRISalid Taxi API"
    app_version: str = "0.1.0"
    debug: bool = False
    api_prefix: str = "/api/v1"

    class Config:
        """Pydantic config."""

        env_file = ".env"
        case_sensitive = True


app_settings = AppSettings()
