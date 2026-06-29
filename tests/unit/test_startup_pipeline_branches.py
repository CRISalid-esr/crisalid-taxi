"""Unit tests for StartupPipeline branch coverage."""

import os
import pytest
from unittest.mock import MagicMock

from app.services.loading.loader import OpenAlexLoader
from app.services.pipeline import StartupPipeline


@pytest.mark.asyncio
async def test_startup_pipeline_returns_false_when_loader_fails(
    mock_embedding_service, mock_opensearch_client, temp_openalex_dir
):
    """If loader.load() fails, pipeline.run() must return False and do nothing else."""

    loader = OpenAlexLoader(temp_openalex_dir)
    # Force loader failure
    loader.load = MagicMock(return_value=False)

    pipeline = StartupPipeline(
        loader=loader,
        embedding_service=mock_embedding_service,
        opensearch_client=mock_opensearch_client,
    )

    success = await pipeline.run()
    assert success is False

    assert not mock_embedding_service.embed_openalex_items.called
    assert not mock_opensearch_client.save_embeddings.called
    assert not mock_opensearch_client.ensure_embeddings_index.called


@pytest.mark.asyncio
async def test_startup_pipeline_returns_true_when_no_items_changed(
    mock_embedding_service, mock_opensearch_client, temp_openalex_dir
):
    """If formatter produces no items, pipeline.run() must return True and skip AI/OpenSearch work."""

    loader = OpenAlexLoader(temp_openalex_dir)

    # Ensure loader loads ok
    loader.load = MagicMock(return_value=True)

    # Make formatter return no items
    loader.formatter.get_all_embedding_items = MagicMock(return_value=[])

    # state.changed_levels is a read-only property; use its backing field
    loader.state._changed_levels = set()

    pipeline = StartupPipeline(
        loader=loader,
        embedding_service=mock_embedding_service,
        opensearch_client=mock_opensearch_client,
    )

    success = await pipeline.run()
    assert success is True

    assert not mock_embedding_service.embed_openalex_items.called
    assert not mock_opensearch_client.save_embeddings.called
    assert not mock_opensearch_client.ensure_embeddings_index.called


@pytest.mark.asyncio
async def test_startup_pipeline_exception_in_embedding_returns_false(
    mock_embedding_service, mock_opensearch_client, temp_openalex_dir
):
    """If embedding_service raises, pipeline.run() must return False."""

    loader = OpenAlexLoader(temp_openalex_dir)
    loader.load = MagicMock(return_value=True)

    loader.formatter.get_all_embedding_items = MagicMock(
        return_value=[{"id": "x1", "display_name": "d1", "text": "t1", "type": "topic"}]
    )
    loader.state._changed_levels = {"topics"}

    mock_embedding_service.embed_openalex_items.side_effect = RuntimeError("boom")

    pipeline = StartupPipeline(
        loader=loader,
        embedding_service=mock_embedding_service,
        opensearch_client=mock_opensearch_client,
    )

    success = await pipeline.run()
    assert success is False

    assert mock_embedding_service.embed_openalex_items.called
    assert not mock_opensearch_client.ensure_embeddings_index.called
    assert not mock_opensearch_client.save_embeddings.called


@pytest.mark.asyncio
async def test_startup_pipeline_records_empty_skips_index_and_saves_empty_docs(
    mock_embedding_service, mock_opensearch_client, temp_openalex_dir
):
    """If embeddings returns empty list, pipeline must not call ensure_embeddings_index and should still save (empty docs)."""

    loader = OpenAlexLoader(temp_openalex_dir)
    loader.load = MagicMock(return_value=True)

    # Return at least one item so embedding is invoked
    loader.formatter.get_all_embedding_items = MagicMock(
        return_value=[{"id": "x1", "display_name": "d1", "text": "t1", "type": "topic"}]
    )
    loader.state._changed_levels = {"topics"}

    # Embedding returns empty -> records == []
    mock_embedding_service.embed_openalex_items = MagicMock(return_value=[])

    # Avoid filesystem writes issues by controlling state file and mtimes
    test_state_file = os.path.join(temp_openalex_dir, "state.json")
    loader.state._state_file = test_state_file
    loader.state._level_mtimes = {"topics": 1.0}
    loader.state.save_state = MagicMock(return_value=None)

    pipeline = StartupPipeline(
        loader=loader,
        embedding_service=mock_embedding_service,
        opensearch_client=mock_opensearch_client,
    )

    success = await pipeline.run()
    assert success is True

    assert mock_embedding_service.embed_openalex_items.called
    assert not mock_opensearch_client.ensure_embeddings_index.called

    mock_opensearch_client.save_embeddings.assert_called_once()
    save_kwargs = mock_opensearch_client.save_embeddings.call_args.kwargs
    assert save_kwargs["index_name"] == "openalex_embeddings"
    assert save_kwargs["docs"] == []
