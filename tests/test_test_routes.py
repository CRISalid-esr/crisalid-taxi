"""Tests for test routes."""

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


class TestTestRoutes:
    """Test cases for test routes."""

    def test_test_endpoint(self):
        """Test the /api/v1/test/ endpoint."""
        response = client.get("/api/v1/test/")
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Test successful"
        assert data["data"]["name"] == "CRISalid Taxi"
        assert "Hello CRISalid Taxi!" in data["data"]["message"]

    def test_test_endpoint_with_name(self):
        """Test the /api/v1/test/{name} endpoint."""
        response = client.get("/api/v1/test/Alice")
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Hello Alice!"
        assert data["data"]["name"] == "Alice"
        assert "Hello Alice!" in data["data"]["message"]

    def test_test_endpoint_with_special_name(self):
        """Test the /api/v1/test/{name} endpoint with special characters."""
        response = client.get("/api/v1/test/Taxi%20Service")
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Hello Taxi Service!"
        assert data["data"]["name"] == "Taxi Service"
