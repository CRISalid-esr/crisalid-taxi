import asyncio
from functools import lru_cache
from typing import Any

from loguru import logger
from tenacity import retry, stop_after_attempt, wait_exponential
from opensearchpy import OpenSearch
from opensearchpy.helpers import bulk

import numpy as np

from app.config import get_app_settings, settings


def _nmslib_score_to_cosine(score: float) -> float:
    """
    Convert an OpenSearch nmslib `cosinesimil` score back to cosine similarity.

    With `space_type: cosinesimil`, OpenSearch/nmslib returns
    ``score = 1 / (1 + distance)`` where ``distance = 1 - cosine``. This
    inverts that relationship so the rest of the pipeline keeps working
    with plain cosine similarity values, exactly as before.

    Parameters
    ----------
    score : float
        Raw `_score` returned by OpenSearch for a `knn` query on a
        `cosinesimil` index.

    Returns
    -------
    float
        The corresponding cosine similarity, in ``[-1, 1]``. Returns
        ``-1.0`` for a non-positive score, which should not occur in
        practice but is guarded against to avoid a division by zero.
    """
    if score <= 0:
        return -1.0
    return 2.0 - 1.0 / score


class OpenSearchClient:
    """OpenSearch client wrapper."""

    @retry(
        stop=stop_after_attempt(settings.retry_max_attempts),
        wait=wait_exponential(
            multiplier=1,
            min=settings.retry_min_wait,
            max=settings.retry_max_wait,
        ),
        reraise=True,
    )
    async def get_all_embeddings(
        self, index_name: str
    ) -> tuple[list[str], "np.ndarray", list[str]]:
        """Load all embeddings from an OpenSearch index.

        Returns
        -------
        (ids, embeddings, levels)
            - ids: concept_uid per record
            - embeddings: float32 numpy matrix (n, dims)
            - levels: hierarchy level per record
        """

        # Query all docs (use scroll). This implementation favors correctness.
        query: dict[str, Any] = {"query": {"match_all": {}}}
        response = await asyncio.to_thread(
            self.client.search, index=index_name, body=query, scroll="1m", size=1000
        )

        ids: list[str] = []
        embeddings: list[list[float]] = []
        levels: list[str] = []

        while True:
            hits = response.get("hits", {}).get("hits", [])
            for hit in hits:
                src = hit.get("_source", {})
                ids.append(str(hit.get("_id", src.get("_id", ""))))
                emb = src.get("embedding", [])
                embeddings.append(list(emb))
                levels.append(str(src.get("type", "domain")))

            scroll_id = response.get("_scroll_id")
            if not scroll_id:
                break

            response = await asyncio.to_thread(self.client.scroll, scroll_id=scroll_id, scroll="1m")
            if not response.get("hits", {}).get("hits"):
                break

        if not embeddings:
            return [], np.zeros((0, 0), dtype=np.float32), []

        emb_matrix = np.asarray(embeddings, dtype=np.float32)
        # Some stored data might already be L2-normalised, which is fine.
        return ids, emb_matrix, levels

    @retry(
        stop=stop_after_attempt(settings.retry_max_attempts),
        wait=wait_exponential(
            multiplier=1,
            min=settings.retry_min_wait,
            max=settings.retry_max_wait,
        ),
        reraise=True,
    )
    async def knn_search_batch(
        self,
        index_name: str,
        query_vectors: list[list[float]],
        k: int,
    ) -> list[list[tuple[str, float, str]]]:
        """
        Run a batched approximate k-NN search via the OpenSearch `_msearch` API.

        Delegates the nearest-neighbour computation to the HNSW index
        configured in :meth:`ensure_embeddings_index`, instead of loading
        the full taxonomy matrix and computing similarity in Python.

        Parameters
        ----------
        index_name : str
            Name of the OpenSearch index to search.
        query_vectors : list of list of float
            One L2-normalised query embedding per document.
        k : int
            Number of nearest concepts to retrieve per query vector.

        Returns
        -------
        list of list of (str, float, str)
            One list of hits per input query vector, in the same order,
            each hit given as ``(concept_uid, cosine_similarity, level)``,
            sorted by decreasing similarity.
        """
        if not query_vectors:
            return []

        body: list[dict] = []
        for vector in query_vectors:
            body.append({"index": index_name})
            body.append(
                {
                    "size": k,
                    "_source": ["type"],
                    "query": {"knn": {"embedding": {"vector": vector, "k": k}}},
                }
            )

        response = await asyncio.to_thread(self.client.msearch, body=body)

        results: list[list[tuple[str, float, str]]] = []
        for i, single_response in enumerate(response.get("responses", [])):
            if "error" in single_response:
                logger.error(
                    f"knn_search_batch: query {i} failed on index {index_name!r}: "
                    f"{single_response['error']}"
                )
                results.append([])
                continue

            hits = single_response.get("hits", {}).get("hits", [])
            parsed: list[tuple[str, float, str]] = []
            for hit in hits:
                cosine = _nmslib_score_to_cosine(float(hit.get("_score", 0.0)))
                level = str(hit.get("_source", {}).get("type", "domain"))
                parsed.append((str(hit.get("_id", "")), cosine, level))
            results.append(parsed)

        return results

    def __init__(self):
        """Initialize OpenSearch client."""
        app_settings = get_app_settings()

        logger.debug(
            f"Connecting to OpenSearch at {app_settings.opensearch_scheme}://"
            f"{app_settings.opensearch_host}:{app_settings.opensearch_port}"
        )
        self.client = OpenSearch(
            hosts=[
                {
                    "host": app_settings.opensearch_host,
                    "port": app_settings.opensearch_port,
                    "scheme": app_settings.opensearch_scheme,
                }
            ],
            verify_certs=False,
            timeout=5,
        )

    def ping(self) -> bool:
        """Test connection to OpenSearch."""
        try:
            result = self.client.ping()
            logger.debug(f"OpenSearch ping result: {result}")
            return bool(result)
        except Exception as e:  # pylint: disable=broad-exception-caught
            logger.error(f"OpenSearch ping failed: {type(e).__name__}: {e}")
            return False

    def get_info(self) -> dict:
        """Get OpenSearch cluster info."""
        try:
            info = self.client.info()
            return dict(info) if isinstance(info, dict) else {}
        except Exception as e:  # pylint: disable=broad-exception-caught
            logger.error(f"Failed to get OpenSearch info: {e}")
            return {}

    @retry(
        stop=stop_after_attempt(settings.retry_max_attempts),
        wait=wait_exponential(
            multiplier=1,
            min=settings.retry_min_wait,
            max=settings.retry_max_wait,
        ),
        reraise=True,
    )
    def ensure_embeddings_index(self, index_name: str, dims: int) -> None:
        """Ensure the OpenSearch index exists with a vector-compatible mapping."""
        if self.client.indices.exists(index=index_name):
            return

        mapping = {
            "settings": {
                "index": {
                    "knn": True,
                }
            },
            "mappings": {
                "properties": {
                    "embedding": {
                        "type": "knn_vector",
                        "dimension": dims,
                        "method": {
                            "name": "hnsw",
                            "space_type": "cosinesimil",
                            "engine": "nmslib",
                            "parameters": {},
                        },
                    },
                    "type": {"type": "keyword"},
                    "display_name": {"type": "text"},
                }
            }
        }

        self.client.indices.create(index=index_name, body=mapping)

    @retry(
        stop=stop_after_attempt(settings.retry_max_attempts),
        wait=wait_exponential(
            multiplier=1,
            min=settings.retry_min_wait,
            max=settings.retry_max_wait,
        ),
    )
    def save_embeddings(self, index_name: str, docs: list[dict]) -> None:
        actions = [
            {
                "_index": index_name,
                "_id": doc["_id"],
                "_source": {
                    "embedding": doc["embedding"],
                    "type": doc["type"],
                    "display_name": doc["display_name"],
                },
            }
            for doc in docs
        ]

        success, failed = bulk(
            self.client,
            actions,
            raise_on_error=False,
            stats_only=True,
        )

        logger.info(f"OpenSearch bulk indexing completed: success={success}, failed={failed}")


@lru_cache(maxsize=1)
def get_opensearch_client() -> OpenSearchClient:
    """Get OpenSearch client (cached singleton)."""
    return OpenSearchClient()
