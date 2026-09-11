"""Unit tests for the OpenAI-compatible embedding provider URL construction."""

# pylint: disable=protected-access

import pytest

from app.services.embeddings.providers.openai_compatible import OpenAICompatibleProvider
from app.settings.app_settings import AppSettings


@pytest.mark.parametrize(
    "base_url",
    ["https://rag-api.ilaas.fr", "https://rag-api.ilaas.fr/"],
)
def test_url_appends_v1_embeddings_to_base_url(base_url):
    """EMBEDDING_API_URL is a base URL: /v1/embeddings is appended, trailing slash tolerated."""
    settings = AppSettings(embedding_api_url=base_url, embedding_api_model="bge-m3")
    provider = OpenAICompatibleProvider(settings)
    assert provider._url == "https://rag-api.ilaas.fr/v1/embeddings"


def test_missing_url_raises():
    settings = AppSettings(embedding_api_url=None, embedding_api_model="bge-m3")
    with pytest.raises(ValueError, match="EMBEDDING_API_URL"):
        OpenAICompatibleProvider(settings)


def test_missing_model_raises():
    settings = AppSettings(embedding_api_url="https://rag-api.ilaas.fr", embedding_api_model=None)
    with pytest.raises(ValueError, match="EMBEDDING_API_MODEL"):
        OpenAICompatibleProvider(settings)
