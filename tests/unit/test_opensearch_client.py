"""Unit tests for OpenSearchClient's k-NN batch search and score conversion."""

from __future__ import annotations

import pytest

from app.services.opensearch_client import OpenSearchClient, _nmslib_score_to_cosine


class DummyLowLevelClient:
    """Stand-in for the underlying `opensearchpy.OpenSearch` client used by msearch."""

    def __init__(self, responses: dict) -> None:
        self._responses = responses

    def msearch(self, body: list[dict]) -> dict:
        """Return the pre-canned `responses` dict, ignoring the actual request body."""
        return self._responses


@pytest.mark.asyncio
async def test_knn_search_batch_returns_empty_for_no_query_vectors():
    """No query vectors means no request should be sent to OpenSearch at all."""
    client = OpenSearchClient.__new__(OpenSearchClient)
    client.client = DummyLowLevelClient(responses={"responses": []})

    hits = await client.knn_search_batch(index_name="idx", query_vectors=[], k=5)

    assert hits == []


@pytest.mark.asyncio
async def test_knn_search_batch_parses_hits_and_converts_score():
    """Hits are parsed into (concept_uid, cosine_similarity, level) tuples per query."""
    client = OpenSearchClient.__new__(OpenSearchClient)
    client.client = DummyLowLevelClient(
        responses={
            "responses": [
                {
                    "hits": {
                        "hits": [
                            {
                                "_id": "concept-1",
                                "_score": 1.0,
                                "_source": {"type": "topic"},
                            }
                        ]
                    }
                }
            ]
        }
    )

    hits = await client.knn_search_batch(
        index_name="openalex_embeddings", query_vectors=[[1.0, 0.0]], k=1
    )

    assert len(hits) == 1
    assert len(hits[0]) == 1
    concept_uid, cosine_similarity, level = hits[0][0]
    assert concept_uid == "concept-1"
    assert cosine_similarity == pytest.approx(1.0)
    assert level == "topic"


@pytest.mark.asyncio
async def test_knn_search_batch_handles_per_query_error_gracefully():
    """A query-level error in the _msearch response yields an empty list, not a crash."""
    client = OpenSearchClient.__new__(OpenSearchClient)
    client.client = DummyLowLevelClient(
        responses={
            "responses": [
                {"error": {"type": "index_not_found_exception", "reason": "no such index"}},
                {
                    "hits": {
                        "hits": [
                            {"_id": "concept-2", "_score": 0.75, "_source": {"type": "domain"}}
                        ]
                    }
                },
            ]
        }
    )

    hits = await client.knn_search_batch(
        index_name="openalex_embeddings",
        query_vectors=[[1.0, 0.0], [0.0, 1.0]],
        k=1,
    )

    assert hits[0] == []
    assert hits[1][0][0] == "concept-2"


@pytest.mark.asyncio
async def test_knn_search_batch_defaults_missing_type_to_domain():
    """A hit without a 'type' source field defaults its level to 'domain'."""
    client = OpenSearchClient.__new__(OpenSearchClient)
    client.client = DummyLowLevelClient(
        responses={
            "responses": [
                {"hits": {"hits": [{"_id": "concept-3", "_score": 0.9, "_source": {}}]}}
            ]
        }
    )

    hits = await client.knn_search_batch(
        index_name="openalex_embeddings", query_vectors=[[1.0, 0.0]], k=1
    )

    assert hits[0][0][2] == "domain"