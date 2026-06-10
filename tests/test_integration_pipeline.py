"""Integration tests for the StartupPipeline."""

import os
from unittest.mock import AsyncMock, MagicMock, patch
import pytest

from app.services.loading.loader import OpenAlexLoader
from app.services.pipeline import StartupPipeline
from app.services.embeddings.embedding_service import EmbeddingService
from app.services.opensearch_client import OpenSearchClient
from app.models.embedding import EmbeddingRecord


@pytest.mark.asyncio
async def test_startup_pipeline_integration():
    """Test the complete StartupPipeline execution with mocked external clients."""
    data_path = os.getenv("OPENALEX_DATA_PATH")
    if not data_path or not os.path.exists(data_path):
        pytest.skip("OPENALEX_DATA_PATH not found or directory does not exist")

    # 1. Initialize Loader
    loader = OpenAlexLoader(data_path)

    # 2. Mock state file path so it doesn't overwrite real state
    test_state_file = "/tmp/.taxi_state_test.json"
    if os.path.exists(test_state_file):
        try:
            os.remove(test_state_file)
        except OSError:
            pass

    loader.state._state_file = test_state_file

    # 3. Mock Embedding Service
    mock_embedding_service = MagicMock(spec=EmbeddingService)
    # Return mock EmbeddingRecords
    dummy_records = [
        EmbeddingRecord(
            _id="https://openalex.org/D1",
            display_name="Test Domain",
            embedding=[0.1] * 1024,
            type="domain",
        )
    ]
    mock_embedding_service.embed_openalex_items = AsyncMock(return_value=dummy_records)

    # 4. Mock OpenSearch Client
    mock_opensearch_client = MagicMock(spec=OpenSearchClient)
    mock_opensearch_client.save_embeddings = MagicMock()

    # 5. Build and run pipeline
    pipeline = StartupPipeline(
        loader=loader,
        embedding_service=mock_embedding_service,
        opensearch_client=mock_opensearch_client,
    )

    success = await pipeline.run()

    # 6. Verify assertions
    assert success is True
    assert loader._loaded is True

    # Check that the embedding service was called if there were changes
    if loader.state.changed_levels:
        assert mock_embedding_service.embed_openalex_items.called
        assert mock_opensearch_client.save_embeddings.called

        # Verify call arguments to OpenSearch client
        call_args = mock_opensearch_client.save_embeddings.call_args[1]
        assert call_args["index_name"] == "openalex_embeddings"
        assert len(call_args["docs"]) == len(dummy_records)
        assert call_args["docs"][0]["_id"] == "https://openalex.org/D1"

        # Check that state file was created
        assert os.path.exists(test_state_file)
    else:
        # If no changes were detected, it should skip embedding and return True
        assert not mock_embedding_service.embed_openalex_items.called
        assert not mock_opensearch_client.save_embeddings.called

    # Clean up test state file
    if os.path.exists(test_state_file):
        try:
            os.remove(test_state_file)
        except OSError:
            pass
