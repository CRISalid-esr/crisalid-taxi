"""Test service."""


class TestService:
    """Service for testing."""

    @staticmethod
    def get_test_data(name: str) -> dict:
        """Get test data."""
        return {
            "name": name,
            "message": f"Hello {name}!",
            "timestamp": "2026-05-27T00:00:00Z",
        }
