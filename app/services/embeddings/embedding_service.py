import hashlib
import math
from typing import Literal, cast

from loguru import logger

from app.config import get_app_settings
from app.models.embedding import EmbeddingRecord
from app.services.embeddings.providers.factory import get_embedding_provider

# Type alias for the hierarchy level
OpenAlexType = Literal["domain", "field", "subfield", "topic"]


def _l2_normalize(vector: list[float]) -> list[float]:
    """Return the L2-normalised version of *vector* (stdlib only, no numpy)."""
    norm = math.sqrt(sum(x * x for x in vector))
    if norm == 0.0:
        return vector
    inv = 1.0 / norm
    return [x * inv for x in vector]


class EmbeddingService:

    def __init__(self):
        self.settings = get_app_settings()
        self.provider = get_embedding_provider(self.settings)

    async def ping(self) -> bool:
        """Health check: test if embedding provider is reachable."""
        try:
            # Test avec un texte dummy court pour éviter de consommer des tokens
            await self.provider.embed_texts(["ping"])
            return True
        except Exception as e:
            logger.error("Embedding provider ping failed: %s", e)
            return False

    # ------------------------------------------------------------------
    # Low-level helpers
    # ------------------------------------------------------------------

    async def embed_texts(self, texts: list[str]) -> list[list[float]]:
        # bge-m3 is case-sensitive (0.93 cosine between "X" and "x").
        # Lowercasing here ensures queries and taxonomy texts land in the same
        # embedding space regardless of the caller's input casing.
        return cast(list[list[float]], await self.provider.embed_texts([t.lower() for t in texts]))

    async def embed_one(self, text: str) -> list[float]:
        vectors = await self.provider.embed_texts([text.lower()])
        return cast(list[float], vectors[0])

    async def embed_with_dedup(
        self,
        texts: list[str],
        previous_hashes: list[str] | None = None,
    ) -> tuple[list[list[float]], list[str]]:
        """
        Optional helper:
        - compute embeddings
        - compute hashes
        - return embeddings + hashes
        """
        vectors = await self.provider.embed_texts([t.lower() for t in texts])
        hashes = [hashlib.sha256(t.encode("utf-8")).hexdigest() for t in texts]
        return vectors, hashes

    # ------------------------------------------------------------------
    # OpenAlex-specific entry point
    # ------------------------------------------------------------------

    async def embed_openalex_items(
        self,
        items: list[dict],
    ) -> list[EmbeddingRecord]:
        """Embed a batch of OpenAlex entities and return structured records.

        Items are sent to the provider in chunks of ``embedding_batch_size``
        to avoid overloading the remote API (prevents 502 Bad Gateway).

        Parameters
        ----------
        items:
            List of dicts with keys:
              - ``id``   : OpenAlex entity URI (used as ``_id``)
              - ``text`` : concatenated text payload to embed
              - ``type`` : ``"domain" | "field" | "subfield" | "topic"``

        Returns
        -------
        list[EmbeddingRecord]
            One record per input item with:
              - ``_id``       : OpenAlex ``id``
              - ``embedding`` : L2-normalised float32 vector
              - ``type``      : hierarchy level
        """
        if not items:
            return []

        batch_size: int = self.settings.embedding_batch_size
        total = len(items)
        logger.info(
            f"Étape 4/4 : Initialisation de la connexion à l'IA pour traiter {total} concepts (par lots de {batch_size})"
        )

        results: list[EmbeddingRecord] = []

        for start in range(0, total, batch_size):
            chunk_items = items[start : start + batch_size]
            chunk_texts = [item["text"].lower() for item in chunk_items]
            batch_num = start // batch_size + 1
            n_batches = (total + batch_size - 1) // batch_size

            logger.info(
                f"Étape 4/4 : Génération des vecteurs par l'Intelligence Artificielle (Lot {batch_num} sur {n_batches})"
            )

            if chunk_texts:
                preview_text = chunk_texts[0][:100] + ("..." if len(chunk_texts[0]) > 100 else "")
                logger.info(f"   > Exemple de texte lu par l'IA : {repr(preview_text)}")

            raw_vectors = await self.provider.embed_texts(chunk_texts)

            for item, vector in zip(chunk_items, raw_vectors):
                results.append(
                    EmbeddingRecord.model_validate(
                        {
                            "_id": item["id"],
                            "display_name": item.get("display_name", ""),
                            "embedding": _l2_normalize(vector),
                            "type": item["type"],
                        }
                    )
                )

        logger.info(
            f"Étape 4/4 : Terminé ! {len(results)}/{total} vecteurs mathématiques ont été générés avec succès."
        )
        return results
