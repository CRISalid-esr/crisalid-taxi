"""Tests for health check routes."""

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client():
    """Create a test client."""
    return TestClient(app)


def test_root(client: TestClient):
    """Test API is accessible via /api/v1/health endpoint."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200


def test_health_check(client: TestClient):
    """Test health check endpoint."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"
