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
    max_topics : int, default 10
        Maximum number of concepts kept per document, among those above the
        threshold.
    similarity_threshold : float, default 0.0
        Minimum cosine similarity a concept must reach to be kept. 0.0 keeps
        everything the k-NN returned.
    """

    def __init__(
        self,
        opensearch_client: "OpenSearchClient",
        index_name: str,
        max_topics: int = 10,
        similarity_threshold: float = 0.0,
    ) -> None:
        self._opensearch = opensearch_client
        self._index_name = index_name
        self.max_topics = max_topics
        self.similarity_threshold = similarity_threshold

    async def match(
        self,
        doc_ids: list[str],
        doc_embeddings: np.ndarray,
    ) -> list[Match]:
        """
        Retrieve the closest taxonomy concepts for each document.

        Parameters
        ----------
        doc_ids : list of str
            Opaque document identifiers.
        doc_embeddings : numpy.ndarray
            L2-normalised query embeddings, shape ``(n_docs, dim)``.

        Returns
        -------
        list of Match
            Matches found across all documents: at most `max_topics` per document,
            none below `similarity_threshold`.
        """
        if not doc_ids:
            return []

        doc_embeddings = np.asarray(doc_embeddings, dtype=np.float32)

        per_doc_hits = await self._opensearch.knn_search_batch(
            index_name=self._index_name,
            query_vectors=doc_embeddings.tolist(),
            k=self.max_topics,
        )

        results: list[Match] = []
        dropped = 0
        for doc_id, hits in zip(doc_ids, per_doc_hits):
            # Phase 1: drop everything below the threshold.
            above = [hit for hit in hits if hit[1] >= self.similarity_threshold]
            dropped += len(hits) - len(above)
            # Phase 2: keep at most max_topics of what survived.
            for concept_uid, cosine_similarity, level in above[: self.max_topics]:
                results.append(
                    Match(
                        concept_uid=concept_uid,
                        doc_id=doc_id,
                        rel_type=_level_to_rel(level),
                        score=cosine_similarity,
                    )
                )

        logger.debug(
            "Matcher: {} kept across {} docs ({} dropped below threshold {}, max_topics={})",
            len(results),
            len(doc_ids),
            dropped,
            self.similarity_threshold,
            self.max_topics,
        )
        return results
