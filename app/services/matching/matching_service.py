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
    """
    L2-normalise a list of float vectors into a float32 numpy array.

    Parameters
    ----------
    vectors : list of list of float
        Raw embedding vectors.

    Returns
    -------
    numpy.ndarray
        Array of shape ``(n_vectors, dim)``, L2-normalised row-wise. Rows
        with a zero norm are left as all-zeros rather than divided by zero.
    """
    arr = np.array(vectors, dtype=np.float32)
    norms = np.linalg.norm(arr, axis=1, keepdims=True)
    n_zero = int(np.sum(norms == 0))
    if n_zero:
        logger.warning(f"{n_zero} embedding(s) had a zero norm and were left unnormalised")
    norms = np.where(norms == 0, 1.0, norms)
    return arr / norms


class MatchingService:
    """Orchestrates query embedding, k-NN search against the taxonomy, and payload building."""

    def __init__(self) -> None:
        settings = get_app_settings()
        self._embedding_service = EmbeddingService()
        self._model_name: str = settings.embedding_api_model or ""
        self._matcher = Matcher(
            opensearch_client=get_opensearch_client(),
            index_name=_TAXONOMY_INDEX,
            top_k=settings.top_k or 10,
        )

    async def search(
        self,
        texts: list[str],
        ids: list[str],
    ) -> list[Match]:
        """
        Embed `texts` on the fly and return matches against the taxonomy.

        Parameters
        ----------
        texts : list of str
            Free-text queries (e.g. publication abstracts). Never stored.
        ids : list of str
            Opaque identifiers paired 1-to-1 with `texts` (e.g. Neo4j
            element_ids).

        Returns
        -------
        list of Match
            Matches found across all query texts.

        Raises
        ------
        ValueError
            If `texts` and `ids` do not have the same length.
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

        logger.info(f"MatchingService: running k-NN search for {len(ids)} doc(s)…")
        return await self._matcher.match(ids, query_embs)

    async def search_as_payload(
        self,
        texts: list[str],
        ids: list[str],
    ) -> dict:
        """
        Run :meth:`search` and return the IKG-ready JSON payload dict.

        Parameters
        ----------
        texts : list of str
            Free-text queries.
        ids : list of str
            Opaque identifiers paired 1-to-1 with `texts`.

        Returns
        -------
        dict
            Payload with one entry per input id, including ids with no
            match (empty `matches` list), ordered as in `ids`.
        """
        matches = await self.search(texts, ids)
        return matches_to_payload(matches, doc_ids=ids, model=self._model_name)
