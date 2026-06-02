"""Utility functions."""

import os

from dotenv import load_dotenv


def format_response(message: str, data: dict | None = None) -> dict:
    """Format a response."""
    return {
        "message": message,
        "data": data or {},
    }


def resolve_env_path(path: str | None, env_var: str) -> str | None:
    """Resolve a path from an explicit value or environment variable."""
    if path:
        return path

    load_dotenv()
    return os.getenv(env_var)
