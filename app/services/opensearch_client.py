import asyncio
from functools import lru_cache

from loguru import logger
from opensearchpy import OpenSearch
from opensearchpy.helpers import bulk

import numpy as np

from app.config import get_app_settings


class OpenSearchClient:
    """OpenSearch client wrapper."""

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
        from typing import Any
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

    def __init__(self):
        """Initialize OpenSearch client."""
        settings = get_app_settings()

        logger.debug(
            f"Connecting to OpenSearch at {settings.opensearch_scheme}://"
            f"{settings.opensearch_host}:{settings.opensearch_port}"
        )
        self.client = OpenSearch(
            hosts=[
                {
                    "host": settings.opensearch_host,
                    "port": settings.opensearch_port,
                    "scheme": settings.opensearch_scheme,
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

    def ensure_embeddings_index(self, index_name: str, dims: int) -> None:
        """Ensure the OpenSearch index exists with a vector-compatible mapping."""
        if self.client.indices.exists(index=index_name):
            return

        mapping = {
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
