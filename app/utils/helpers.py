"""Utility functions."""


def format_response(message: str, data: dict | None = None) -> dict:
    """Format a response."""
    return {
        "message": message,
        "data": data or {},
    }
