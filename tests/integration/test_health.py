"""Integration tests for the health check routes."""

from fastapi.testclient import TestClient


def test_health_check_endpoint(client: TestClient):
    """Test the /api/v1/health endpoint."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200

    data = response.json()
    assert data["status"] == "healthy"
    assert "opensearch" in data
