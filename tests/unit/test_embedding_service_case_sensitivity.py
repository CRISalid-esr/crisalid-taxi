"""Unit tests for embedding service case sensitivity fixes."""

import asyncio
from unittest.mock import AsyncMock

import pytest
from app.services.embeddings.embedding_service import EmbeddingService


@pytest.fixture
def mock_provider():
    """Create a mock embedding provider."""
    mock = AsyncMock()
    mock.embed_texts = AsyncMock(return_value=[[0.1, 0.2, 0.3]])
    return mock


@pytest.fixture
def embedding_service(mock_provider):
    """Create an embedding service instance with mocked provider."""
    service = EmbeddingService()
    service.provider = mock_provider
    return service


def test_embed_texts_lowercase_input(embedding_service, mock_provider):
    """Test that embed_texts applies lowercase to input texts."""
    # Given
    texts = ["Hello World", "TEST TEXT", "MiXeD cAsE"]
    
    # When
    result = asyncio.run(embedding_service.embed_texts(texts))
    
    # Then
    mock_provider.embed_texts.assert_called_once_with(["hello world", "test text", "mixed case"])
    assert result == [[0.1, 0.2, 0.3]]


def test_embed_one_lowercase_input(embedding_service, mock_provider):
    """Test that embed_one applies lowercase to input text."""
    # Given
    text = "Hello World"
    
    # When
    result = asyncio.run(embedding_service.embed_one(text))
    
    # Then
    mock_provider.embed_texts.assert_called_once_with(["hello world"])
    assert result == [0.1, 0.2, 0.3]


def test_embed_with_dedup_lowercase_input(embedding_service, mock_provider):
    """Test that embed_with_dedup applies lowercase to input texts."""
    # Given
    texts = ["Hello World", "TEST TEXT", "MiXeD cAsE"]
    
    # When
    result = asyncio.run(embedding_service.embed_with_dedup(texts))
    
    # Then
    mock_provider.embed_texts.assert_called_once_with(["hello world", "test text", "mixed case"])


def test_embed_openalex_items_lowercase_input(embedding_service, mock_provider):
    """Test that embed_openalex_items applies lowercase to item texts."""
    # Given
    items = [
        {"id": "item1", "text": "Hello World", "type": "domain"},
        {"id": "item2", "text": "TEST TEXT", "type": "field"}
    ]
    
    # When
    result = asyncio.run(embedding_service.embed_openalex_items(items))
    
    # Then
    mock_provider.embed_texts.assert_called_once_with(["hello world", "test text"])

