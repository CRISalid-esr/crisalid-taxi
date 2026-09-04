"""Base settings module.

Application settings main class with parameters definition.
Supports loading configuration from environment variables and YAML files.
"""

import logging
import os
import sys
from typing import ClassVar, TextIO, Any, cast

import yaml
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from app.settings.app_env_types import AppEnvTypes


class AppSettings(BaseSettings):
    """App settings main class with parameters definition."""

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False, extra="ignore")

    @staticmethod
    def settings_file_path(filename: str) -> str:
        """
        Get the path of a settings file.

        :param filename: The name of the settings file
        :return: The path of the settings file
        """
        return os.path.join(os.path.abspath(os.path.dirname(__file__)), "..", "..", filename)

    @staticmethod
    def dct_from_yml(yml_file: str) -> dict[str, Any]:
        """
        Load settings from yml file.

        :param yml_file: Path to the YAML file
        :return: Dictionary loaded from YAML file
        """
        with open(yml_file, encoding="utf8") as file:
            return cast(dict[str, Any], yaml.load(file, Loader=yaml.FullLoader))

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
    logger_sink: ClassVar[str | TextIO] = sys.stderr

    # API Configuration
    api_prefix: str = "/api"
    api_version: str = "v1"

    # OpenSearch Configuration
    opensearch_host: str = "localhost"
    opensearch_port: int = 9200
    opensearch_scheme: str = "http"

    # Embedding Configuration
    embedding_provider: str = "openai_compatible"
    embedding_api_url: str | None = None
    embedding_api_key: str | None = None
    embedding_api_model: str | None = None
    embedding_timeout_seconds: int = 30
    embedding_batch_size: int = 32

    # Retry Configuration
    retry_max_attempts: int = 3
    retry_min_wait: int = 2
    retry_max_wait: int = 10

    # Matching Configuration
    # Default maximum number of taxonomy concepts returned per input text.
    # Overridable per request via MatchRequest.top_k. Must stay a valid int:
    # it is passed straight to OpenSearch as the k-NN `k`.
    top_k: int = 100
    # Chunk size used to split the taxonomy embeddings for similarity computation.
    chunk_size: int = 5000

    # Application metadata
    git_commit: str = "-"
    git_branch: str = "-"
    docker_digest: str = "-"
