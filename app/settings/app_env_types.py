"""Application settings and environment types."""

from enum import Enum


class AppEnvTypes(Enum):
    """Application environment types."""

    PROD = "prod"
    DEV = "dev"
    TEST = "test"
