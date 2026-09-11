"""Shared conftest containing fixtures for the unit and integration tests."""

import json
import os
import shutil
import tempfile
from typing import Generator
import pytest
from fastapi.testclient import TestClient

from unittest.mock import MagicMock, AsyncMock
from app.main import app
from app.services.embeddings.embedding_service import EmbeddingService
from app.services.opensearch_client import OpenSearchClient


@pytest.fixture(scope="session")
def client() -> Generator[TestClient, None, None]:
    """Provide a FastAPI TestClient."""
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def temp_openalex_dir() -> Generator[str, None, None]:
    """Create a temporary directory structure mimicking the OpenAlex snapshot format.

    Hierarchy layout:
    temp_dir/
    ├── domains/
    │   └── 20260101/
    │       └── part_0.ndjson
    ├── fields/
    │   └── 20260101/
    │       └── part_0.ndjson
    ├── subfields/
    │   └── 20260101/
    │       └── part_0.ndjson
    └── topics/
        └── 20260101/
            └── part_0.ndjson
    """
    temp_dir = tempfile.mkdtemp()

    # Structure definition
    structure: dict[str, list[dict]] = {
        "domains": [
            {
                "id": "https://openalex.org/domains/1",
                "display_name": "Domain 1",
                "description": "Desc Domain 1",
            }
        ],
        "fields": [
            {
                "id": "https://openalex.org/fields/11",
                "display_name": "Field 1.1",
                "description": "Desc Field 1.1",
                "domain": {"id": "https://openalex.org/domains/1"},
            }
        ],
        "subfields": [
            {
                "id": "https://openalex.org/subfields/111",
                "display_name": "Subfield 1.1.1",
                "description": "Desc Subfield 1.1.1",
                "field": {"id": "https://openalex.org/fields/11"},
            }
        ],
        "topics": [
            {
                "id": "https://openalex.org/topics/1111",
                "display_name": "Topic 1.1.1.1",
                "description": "Desc Topic 1.1.1.1",
                "subfield": {"id": "https://openalex.org/subfields/111"},
                "keywords": ["keyword1", "keyword2"],
            }
        ],
    }

    # Write NDJSON structure
    for level, records in structure.items():
        level_dir = os.path.join(temp_dir, level, "20260101")
        os.makedirs(level_dir, exist_ok=True)
        file_path = os.path.join(level_dir, "part_0.ndjson")
        with open(file_path, "w", encoding="utf-8") as f:
            for rec in records:
                f.write(json.dumps(rec) + "\n")

    yield temp_dir

    # Cleanup temp directory
    shutil.rmtree(temp_dir)


@pytest.fixture
def mock_embedding_service() -> MagicMock:
    """Provide a mock EmbeddingService."""
    from app.models.embedding import EmbeddingRecord

    mock_service = MagicMock(spec=EmbeddingService)

    # Simple async mock for embed_openalex_items
    async def dummy_embed(items: list) -> list[EmbeddingRecord]:
        return [
            EmbeddingRecord(
                _id=item["id"],
                display_name=item["display_name"],
                embedding=[0.1] * 1024,
                type=item["type"],
            )
            for item in items
        ]

    mock_service.embed_openalex_items = AsyncMock(side_effect=dummy_embed)
    return mock_service


@pytest.fixture
def mock_opensearch_client() -> MagicMock:
    """Provide a mock OpenSearchClient."""
    mock_client = MagicMock(spec=OpenSearchClient)
    mock_client.ping.return_value = True
    mock_client.get_info.return_value = {"version": {"number": "2.11.0"}}
    mock_client.save_embeddings = MagicMock()
    return mock_client
