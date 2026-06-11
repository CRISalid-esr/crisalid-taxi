from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import numpy as np
from loguru import logger

_LEVEL_TO_REL: dict[str, str] = {
    "domain": "HAS_DOMAIN",
    "field": "HAS_FIELD",
    "subfield": "HAS_SUBFIELD",
    "topic": "HAS_TOPIC",
}


def _level_to_rel(level: str) -> str:
    return _LEVEL_TO_REL.get(level.lower(), "HAS_DOMAIN")


@dataclass
class Match:
    concept_uid: str
    doc_id: str
    rel_type: str
    score: float


class Matcher:
    """Chunked cosine-similarity matcher against the full taxonomy matrix.

    Both the taxonomy embeddings and the query embeddings must be L2-normalised
    before being passed in — the dot product then equals cosine similarity.
    """

    def __init__(
        self,
        threshold: float = 0.52,
        top_k: Optional[int] = None,
        chunk_size: int = 5000,
    ) -> None:
        self.threshold = threshold
        self.top_k = top_k
        self.chunk_size = chunk_size

    def match(
        self,
        taxonomy_ids: list[str],
        taxonomy_embeddings: np.ndarray,
        taxonomy_levels: list[str],
        doc_ids: list[str],
        doc_embeddings: np.ndarray,
    ) -> list[Match]:
        """Compute similarity between each taxonomy node and each query document.

        Processes the taxonomy in chunks to keep peak memory bounded.
        """
        if not taxonomy_ids or not doc_ids:
            return []

        results: list[Match] = []
        n_tax = len(taxonomy_ids)

        for chunk_start in range(0, n_tax, self.chunk_size):
            chunk_end = min(chunk_start + self.chunk_size, n_tax)
            tax_chunk = taxonomy_embeddings[chunk_start:chunk_end]

            sims = tax_chunk @ doc_embeddings.T  # (chunk, n_docs)

            for local_i in range(chunk_end - chunk_start):
                tax_id = taxonomy_ids[chunk_start + local_i]
                level = taxonomy_levels[chunk_start + local_i]
                row = sims[local_i]
                rel_type = _level_to_rel(level)

                above = np.where(row >= self.threshold)[0]
                if self.top_k is not None and len(above) > self.top_k:
                    above = above[np.argsort(row[above])[::-1][: self.top_k]]

                for j in above:
                    results.append(
                        Match(
                            concept_uid=tax_id,
                            doc_id=doc_ids[j],
                            rel_type=rel_type,
                            score=float(row[j]),
                        )
                    )

        logger.debug(
            "Matcher: %d matches from %d taxa × %d docs",
            len(results),
            n_tax,
            len(doc_ids),
        )
        return results

