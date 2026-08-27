from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

import numpy as np
from loguru import logger

if TYPE_CHECKING:
    from app.services.opensearch_client import OpenSearchClient

_LEVEL_TO_REL: dict[str, str] = {
    "domain": "HAS_DOMAIN",
    "field": "HAS_FIELD",
    "subfield": "HAS_SUBFIELD",
    "topic": "HAS_TOPIC",
}


def _level_to_rel(level: str) -> str:
    """
    Translate a taxonomy level to its IKG relationship type.

    Parameters
    ----------
    level : str
        Taxonomy level name (e.g. ``"domain"``, ``"field"``, ``"subfield"``,
        ``"topic"``), case-insensitive.

    Returns
    -------
    str
        The corresponding relationship type. Falls back to ``"HAS_DOMAIN"``
        if `level` is not recognised.
    """
    return _LEVEL_TO_REL.get(level.lower(), "HAS_DOMAIN")


@dataclass
class Match:
    """
    A single retained (concept, document) match.

    Parameters
    ----------
    concept_uid : str
        OpenAlex URI of the matched taxonomy node.
    doc_id : str
        Opaque identifier of the matched document.
    rel_type : str
        Relationship type (``HAS_DOMAIN`` | ``HAS_FIELD`` | ``HAS_SUBFIELD`` |
        ``HAS_TOPIC``).
    score : float
        Cosine similarity score between the document and the concept.
    """

    concept_uid: str
    doc_id: str
    rel_type: str
    score: float


class Matcher:
    """
    Top-k concept matcher backed by OpenSearch's approximate k-NN search.

    The nearest-neighbour computation is delegated to the HNSW index
    already configured on the taxonomy index, instead of loading the full
    taxonomy matrix and computing cosine similarity in Python.

    Parameters
    ----------
    opensearch_client : OpenSearchClient
        Client used to run the batched k-NN queries.
    index_name : str
        Name of the OpenSearch index holding the taxonomy embeddings.
    top_k : int, default 10
        Number of nearest concepts retrieved per document.
    """

    def __init__(
        self,
        opensearch_client: "OpenSearchClient",
        index_name: str,
        top_k: int = 10,
    ) -> None:
        self._opensearch = opensearch_client
        self._index_name = index_name
        self.top_k = top_k

    async def match(
        self,
        doc_ids: list[str],
        doc_embeddings: np.ndarray,
    ) -> list[Match]:
        """
        Retrieve the top-k nearest taxonomy concepts for each document.

        Parameters
        ----------
        doc_ids : list of str
            Opaque document identifiers.
        doc_embeddings : numpy.ndarray
            L2-normalised query embeddings, shape ``(n_docs, dim)``.

        Returns
        -------
        list of Match
            Matches found across all documents, at most `top_k` per
            document.
        """
        if not doc_ids:
            return []

        doc_embeddings = np.asarray(doc_embeddings, dtype=np.float32)

        per_doc_hits = await self._opensearch.knn_search_batch(
            index_name=self._index_name,
            query_vectors=doc_embeddings.tolist(),
            k=self.top_k,
        )

        results: list[Match] = []
        for doc_id, hits in zip(doc_ids, per_doc_hits):
            for concept_uid, cosine_similarity, level in hits:
                results.append(
                    Match(
                        concept_uid=concept_uid,
                        doc_id=doc_id,
                        rel_type=_level_to_rel(level),
                        score=cosine_similarity,
                    )
                )

        logger.debug(
            "Matcher: {} matches from top-{} search across {} docs",
            len(results),
            self.top_k,
            len(doc_ids),
        )
        return results
