import aiohttp
from loguru import logger
from tenacity import retry, stop_after_attempt, wait_exponential

from app.config import settings
from app.services.embeddings.providers.base import EmbeddingProvider


class OpenAICompatibleProvider(EmbeddingProvider):
    """
    Embedding provider that calls a remote service exposing an OpenAI-compatible
    embeddings API (e.g. vLLM, Hugging Face Text Embeddings Inference via /v1/embeddings).
    """

    def __init__(self, settings):
        if not settings.embedding_api_url:
            raise ValueError("EMBEDDING_API_URL is required for the openai_compatible provider")
        if not settings.embedding_api_model:
            raise ValueError("EMBEDDING_API_MODEL is required for the openai_compatible provider")
        self._url = settings.embedding_api_url.rstrip("/") + "/embeddings"
        self._api_key = settings.embedding_api_key
        self._model = settings.embedding_api_model
        self._timeout = aiohttp.ClientTimeout(total=settings.embedding_timeout_seconds)

        logger.info(f"   > Connexion au serveur d'IA distant établie (Modèle : '{self._model}')")

    @retry(
        stop=stop_after_attempt(settings.retry_max_attempts),
        wait=wait_exponential(
            multiplier=1, min=settings.retry_min_wait, max=settings.retry_max_wait
        ),
    )
    async def embed_texts(self, texts: list[str]) -> list[list[float]]:
        headers = {"Content-Type": "application/json"}
        if self._api_key:
            headers["Authorization"] = f"Bearer {self._api_key}"

        payload = {"model": self._model, "input": texts}

        logger.info(f"   > Envoi de {len(texts)} textes au serveur IA distant...")
        async with aiohttp.ClientSession(timeout=self._timeout) as session:
            async with session.post(self._url, json=payload, headers=headers) as response:
                response.raise_for_status()
                data = await response.json()

        embeddings = data.get("data", [])
        if len(embeddings) != len(texts):
            raise ValueError(
                f"Provider returned {len(embeddings)} embeddings for {len(texts)} texts"
            )

        sorted_embeddings = sorted(embeddings, key=lambda e: e["index"])
        logger.info(
            f"   > Réception réussie des {len(sorted_embeddings)} vecteurs depuis le serveur IA."
        )
        return [e["embedding"] for e in sorted_embeddings]
