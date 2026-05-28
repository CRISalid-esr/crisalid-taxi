"""Base settings module.

Application settings main class with parameters definition.
Supports loading configuration from environment variables and YAML files.
"""
import logging
import os
from typing import ClassVar, TextIO

import yaml
from pydantic import field_validator
from pydantic_settings import BaseSettings

from app.settings.app_env_types import AppEnvTypes


class AppSettings(BaseSettings):
    """App settings main class with parameters definition."""

    @staticmethod
    def settings_file_path(filename: str) -> str:
        """
        Get the path of a settings file.

        :param filename: The name of the settings file
        :return: The path of the settings file
        """
        return os.path.join(
            os.path.abspath(os.path.dirname(__file__)), "..", "..", filename
        )

    @staticmethod
    def dct_from_yml(yml_file: str) -> dict:
        """
        Load settings from yml file.

        :param yml_file: Path to the YAML file
        :return: Dictionary loaded from YAML file
        """
        if not os.path.exists(yml_file):
            return {}
        with open(yml_file, encoding="utf8") as file:
            return yaml.load(file, Loader=yaml.FullLoader) or {}

    @field_validator("app_env", mode="before")
    @classmethod
    def convert_app_env(cls, v):
        """Convert app_env to lowercase if it's a string."""
        if isinstance(v, str):
            return v.lower()
        return v

    # Environment and logging
    app_env: AppEnvTypes = AppEnvTypes.DEV
    debug: bool = False
    logging_level: int = logging.INFO
    loguru_level: str = "INFO"
    logger_sink: ClassVar[str | TextIO] = "logs/app.log"

    # API Configuration
    api_prefix: str = "/api"
    api_version: str = "v1"
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_title: str = "CRISalid Taxi API"

    # Application metadata
    git_commit: str = "-"
    git_branch: str = "-"
    docker_digest: str = "-"

    class Config:
        """Pydantic configuration."""

        env_file = ".env"
        case_sensitive = False

