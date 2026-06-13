"""Integration tests for the health check routes."""

import sys
import pytest
from unittest.mock import MagicMock, AsyncMock
from fastapi.testclient import TestClient

@pytest.fixture
def health_module():
    """Import health module dynamically to avoid ModuleNotFoundError."""
    # Essaie les 3 chemins possibles
    for path in ["app.api.routes.health", "app.routes.health", "crisalid_taxi.api.routes.health"]:
        try:
            return __import__(path, fromlist=["health"])
        except ModuleNotFoundError:
            continue
    raise ImportError("Impossible de trouver le module health")

@pytest.mark.asyncio
async def test_health_all_healthy(client: TestClient, monkeypatch, health_module):
    mock_os = MagicMock()
    mock_os.ping.return_value = True
    monkeypatch.setattr(health_module, "get_opensearch_client", lambda: mock_os)
    
    mock_emb = MagicMock()
    mock_emb.ping = AsyncMock(return_value=True)
    monkeypatch.setattr(health_module, "EmbeddingService", lambda: mock_emb)

    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

@pytest.mark.asyncio
async def test_health_opensearch_down(client: TestClient, monkeypatch, health_module):
    mock_os = MagicMock()
    mock_os.ping.return_value = False
    monkeypatch.setattr(health_module, "get_opensearch_client", lambda: mock_os)
    
    mock_emb = MagicMock()
    mock_emb.ping = AsyncMock(return_value=True)
    monkeypatch.setattr(health_module, "EmbeddingService", lambda: mock_emb)

    response = client.get("/api/v1/health")
    assert response.status_code == 503

@pytest.mark.asyncio
async def test_health_embedding_down(client: TestClient, monkeypatch, health_module):
    mock_os = MagicMock()
    mock_os.ping.return_value = True
    monkeypatch.setattr(health_module, "get_opensearch_client", lambda: mock_os)
    
    mock_emb = MagicMock()
    mock_emb.ping = AsyncMock(return_value=False)
    monkeypatch.setattr(health_module, "EmbeddingService", lambda: mock_emb)

    response = client.get("/api/v1/health")
    assert response.status_code == 503

@pytest.mark.asyncio
async def test_health_embedding_exception(client: TestClient, monkeypatch, health_module):
    mock_os = MagicMock()
    mock_os.ping.return_value = True
    monkeypatch.setattr(health_module, "get_opensearch_client", lambda: mock_os)
    
    mock_emb = MagicMock()
    mock_emb.ping = AsyncMock(side_effect=RuntimeError("API timeout"))
    monkeypatch.setattr(health_module, "EmbeddingService", lambda: mock_emb)

    response = client.get("/api/v1/health")
    assert response.status_code == 503