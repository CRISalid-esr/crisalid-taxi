"""Matching orchestration: embed query texts then score against taxonomy."""

from __future__ import annotations

import numpy as np
from loguru import logger

from app.config import get_app_settings
from app.services.embeddings.embedding_service import EmbeddingService
from app.services.matching.match_store import matches_to_payload
from app.services.matching.matcher import Match, Matcher
from app.services.opensearch_client import get_opensearch_client

_TAXONOMY_INDEX = "openalex_embeddings"


def _l2_normalize_matrix(vectors: list[list[float]]) -> np.ndarray:
    """L2-normalise a list of float vectors into a float32 numpy array."""
    arr = np.array(vectors, dtype=np.float32)
    norms = np.linalg.norm(arr, axis=1, keepdims=True)
    norms = np.where(norms == 0, 1.0, norms)
    return arr / norms


class MatchingService:
    """Orchestrates query embedding → taxonomy matrix load → Matcher → payload."""

    def __init__(self) -> None:
        settings = get_app_settings()
        self._embedding_service = EmbeddingService()
        self._opensearch = get_opensearch_client()
        self._model_name: str = settings.embedding_api_model or ""
        self._matcher = Matcher(
            threshold=settings.similarity_threshold,
            top_k=settings.top_k,
            chunk_size=settings.chunk_size,
        )

    async def search(
        self,
        texts: list[str],
        ids: list[str],
    ) -> list[Match]:
        """Embed *texts* on the fly and return matches against the taxonomy.

        Parameters
        ----------
        texts:
            Free-text queries (e.g. publication abstracts). Never stored.
        ids:
            Opaque identifiers paired 1-to-1 with *texts* (e.g. Neo4j element_ids).
        """
        if not texts:
            return []
        if len(texts) != len(ids):
            raise ValueError(
                f"texts and ids must have the same length ({len(texts)} vs {len(ids)})"
            )

        logger.info(f"MatchingService: embedding {len(texts)} query text(s)…")
        raw_vectors = await self._embedding_service.embed_texts(texts)
        query_embs = _l2_normalize_matrix(raw_vectors)

        logger.info("MatchingService: loading taxonomy matrix from OpenSearch…")
        tax_ids, tax_embs, tax_types = await self._opensearch.get_all_embeddings(
            _TAXONOMY_INDEX
        )
        if not tax_ids:
            logger.warning("Taxonomy index is empty — no matches returned")
            return []

        logger.info(
            f"MatchingService: running Matcher ({len(tax_ids)} nodes × {len(ids)} docs)…"
        )
        return self._matcher.match(tax_ids, tax_embs, tax_types, ids, query_embs)

    async def search_as_payload(
        self,
        texts: list[str],
        ids: list[str],
    ) -> dict:
        """Same as :meth:`search` but returns the IKG-ready JSON payload dict."""
        matches = await self.search(texts, ids)
        return matches_to_payload(matches, model=self._model_name)

