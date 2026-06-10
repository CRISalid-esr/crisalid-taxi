"""Integration tests for the StartupPipeline."""

import os
import pytest
from unittest.mock import MagicMock

from app.services.loading.loader import OpenAlexLoader
from app.services.pipeline import StartupPipeline


@pytest.mark.asyncio
async def test_startup_pipeline_full_flow(temp_openalex_dir, mock_embedding_service, mock_opensearch_client):
    """Test the complete StartupPipeline execution flow with mocked external services."""
    
    # Initialize loader pointing to temporary mock dataset
    loader = OpenAlexLoader(temp_openalex_dir)

    # Use a temporary state file
    test_state_file = os.path.join(temp_openalex_dir, "state.json")
    loader.state._state_file = test_state_file

    # Build pipeline
    pipeline = StartupPipeline(
        loader=loader,
        embedding_service=mock_embedding_service,
        opensearch_client=mock_opensearch_client,
    )

    # First run: should execute loader, then embedding, then opensearch write
    success = await pipeline.run()

    assert success is True
    assert loader._loaded is True
    assert mock_embedding_service.embed_openalex_items.called
    assert mock_opensearch_client.save_embeddings.called

    # Get arguments sent to save_embeddings
    call_args = mock_opensearch_client.save_embeddings.call_args[1]
    assert call_args["index_name"] == "openalex_embeddings"
    assert len(call_args["docs"]) == 4  # 1 domain, 1 field, 1 subfield, 1 topic

    # Check state file got created
    assert os.path.exists(test_state_file)

    # Reset mocks to see if subsequent run (with a new loader/session) skips AI generation
    mock_embedding_service.embed_openalex_items.reset_mock()
    mock_opensearch_client.save_embeddings.reset_mock()

    # Create a new loader instance mimicking a new application session
    new_loader = OpenAlexLoader(temp_openalex_dir)
    new_loader.state._state_file = test_state_file

    new_pipeline = StartupPipeline(
        loader=new_loader,
        embedding_service=mock_embedding_service,
        opensearch_client=mock_opensearch_client,
    )

    # Re-run pipeline
    second_run_success = await new_pipeline.run()
    assert second_run_success is True
    assert not mock_embedding_service.embed_openalex_items.called
    assert not mock_opensearch_client.save_embeddings.called
