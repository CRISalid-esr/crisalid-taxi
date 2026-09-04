from app.services.embeddings.providers.base import EmbeddingProvider


class SentenceTransformerProvider(EmbeddingProvider):
    """Local sentence-transformers embedding provider (not yet implemented)."""

    def __init__(self, settings):
        self.settings = settings

    async def embed_texts(self, texts: list[str]) -> list[list[float]]:
        raise NotImplementedError("SentenceTransformerProvider is not yet implemented")
