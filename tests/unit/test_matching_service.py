"""Unit tests for matching services (Matcher, matches_to_payload, MatchingService)."""

from __future__ import annotations

from datetime import datetime

import numpy as np
import pytest

from app.services.matching.match_store import matches_to_payload
from app.services.matching.matcher import Match, Matcher
from app.services.matching.matching_service import MatchingService


class DummyOpenSearchClient:
    """
    Stand-in for OpenSearchClient, returning pre-canned k-NN hits.

    Parameters
    ----------
    hits_by_call : list of list of (str, float, str)
        One entry per expected call to `knn_search_batch`, each a list of
        `(concept_uid, cosine_similarity, level)` tuples per query vector.
    """

    def __init__(self, hits_by_call: list[list[tuple[str, float, str]]]) -> None:
        self._hits_by_call = hits_by_call
        self.calls: list[dict] = []

    async def knn_search_batch(
        self,
        index_name: str,
        query_vectors: list[list[float]],
        k: int,
    ) -> list[list[tuple[str, float, str]]]:
        """Record the call and return the pre-canned hits, one list per query vector."""
        self.calls.append({"index_name": index_name, "query_vectors": query_vectors, "k": k})
        return self._hits_by_call


@pytest.mark.asyncio
async def test_matcher_returns_empty_when_no_doc_ids():
    """No doc_ids means no k-NN search should even be attempted."""
    opensearch = DummyOpenSearchClient(hits_by_call=[])
    matcher = Matcher(opensearch_client=opensearch, index_name="openalex_embeddings", top_k=5)

    matches = await matcher.match([], np.zeros((0, 3), dtype=np.float32))

    assert matches == []
    assert opensearch.calls == []


@pytest.mark.asyncio
async def test_matcher_maps_hits_to_matches_with_rel_type():
    """Hits returned by OpenSearch are converted into Match objects with the right rel_type."""
    opensearch = DummyOpenSearchClient(
        hits_by_call=[
            [("tax-domain", 0.91, "domain")],
            [("tax-field", 0.82, "field")],
        ]
    )
    matcher = Matcher(opensearch_client=opensearch, index_name="openalex_embeddings", top_k=1)

    doc_embs = np.array([[1.0, 0.0], [0.0, 1.0]], dtype=np.float32)
    matches = await matcher.match(["doc-0", "doc-1"], doc_embs)

    assert {(m.concept_uid, m.doc_id, m.rel_type, m.score) for m in matches} == {
        ("tax-domain", "doc-0", "HAS_DOMAIN", 0.91),
        ("tax-field", "doc-1", "HAS_FIELD", 0.82),
    }


@pytest.mark.asyncio
async def test_matcher_rel_type_subfield_topic():
    """Levels 'subfield' and 'topic' map to HAS_SUBFIELD / HAS_TOPIC."""
    opensearch = DummyOpenSearchClient(
        hits_by_call=[
            [("tax-s", 0.9, "subfield")],
            [("tax-t", 0.9, "topic")],
        ]
    )
    matcher = Matcher(opensearch_client=opensearch, index_name="openalex_embeddings", top_k=1)

    doc_embs = np.array([[1.0, 0.0], [0.0, 1.0]], dtype=np.float32)
    matches = await matcher.match(["d0", "d1"], doc_embs)

    rel_types = {m.rel_type for m in matches}
    assert rel_types == {"HAS_SUBFIELD", "HAS_TOPIC"}


@pytest.mark.asyncio
async def test_matcher_unknown_level_falls_back_to_has_domain():
    """An unrecognised level string falls back to HAS_DOMAIN rather than raising."""
    opensearch = DummyOpenSearchClient(hits_by_call=[[("tax-x", 0.7, "unknown_level")]])
    matcher = Matcher(opensearch_client=opensearch, index_name="openalex_embeddings", top_k=1)

    matches = await matcher.match(["doc-0"], np.array([[1.0, 0.0]], dtype=np.float32))

    assert matches[0].rel_type == "HAS_DOMAIN"


@pytest.mark.asyncio
async def test_matcher_forwards_top_k_and_index_name_to_opensearch():
    """top_k and index_name configured on the Matcher are passed through to the client."""
    opensearch = DummyOpenSearchClient(hits_by_call=[[]])
    matcher = Matcher(opensearch_client=opensearch, index_name="my_custom_index", top_k=7)

    await matcher.match(["doc-0"], np.array([[1.0, 0.0]], dtype=np.float32))

    assert len(opensearch.calls) == 1
    assert opensearch.calls[0]["index_name"] == "my_custom_index"
    assert opensearch.calls[0]["k"] == 7


@pytest.mark.asyncio
async def test_matcher_no_hits_returns_empty_list():
    """A document with no nearest neighbours above OpenSearch's own cutoff yields no Match."""
    opensearch = DummyOpenSearchClient(hits_by_call=[[]])
    matcher = Matcher(opensearch_client=opensearch, index_name="openalex_embeddings", top_k=5)

    matches = await matcher.match(["doc-0"], np.array([[1.0, 0.0]], dtype=np.float32))

    assert matches == []


def test_matches_to_payload_groups_by_doc_and_rounds():
    """Matches are grouped by doc_id and scores rounded to 6 decimals."""
    matches = [
        Match(concept_uid="c1", doc_id="doc-1", rel_type="HAS_DOMAIN", score=0.1234567),
        Match(concept_uid="c2", doc_id="doc-1", rel_type="HAS_FIELD", score=0.9),
        Match(concept_uid="c3", doc_id="doc-2", rel_type="HAS_TOPIC", score=0.3333),
    ]

    payload = matches_to_payload(matches, doc_ids=["doc-1", "doc-2"], model="mymodel")

    assert payload["model"] == "mymodel"
    assert payload["query_count"] == 2
    assert payload["total_matches"] == 3
    assert "generated_at" in payload

    results_by_id = {r["id"]: r for r in payload["results"]}
    assert set(results_by_id.keys()) == {"doc-1", "doc-2"}

    doc1_matches = results_by_id["doc-1"]["matches"]
    assert {(m["concept_uid"], m["rel_type"], m["value"]) for m in doc1_matches} == {
        ("c1", "HAS_DOMAIN", round(0.1234567, 6)),
        ("c2", "HAS_FIELD", round(0.9, 6)),
    }


def test_matches_to_payload_includes_docs_without_matches():
    """A doc_id with no retained match still appears, with an empty matches list."""
    matches = [Match(concept_uid="c1", doc_id="doc-1", rel_type="HAS_TOPIC", score=0.8)]

    payload = matches_to_payload(matches, doc_ids=["doc-1", "doc-2", "doc-3"], model="m")

    assert payload["query_count"] == 3
    results_by_id = {r["id"]: r for r in payload["results"]}
    assert results_by_id["doc-2"]["matches"] == []
    assert results_by_id["doc-3"]["matches"] == []


def test_matches_to_payload_orders_results_like_doc_ids():
    """Results follow the order of doc_ids, not the order matches were produced in."""
    matches = [
        Match(concept_uid="c1", doc_id="doc-b", rel_type="HAS_TOPIC", score=0.5),
        Match(concept_uid="c2", doc_id="doc-a", rel_type="HAS_TOPIC", score=0.6),
    ]

    payload = matches_to_payload(matches, doc_ids=["doc-a", "doc-b"], model="m")

    assert [r["id"] for r in payload["results"]] == ["doc-a", "doc-b"]


def test_matches_to_payload_timestamp_format():
    """generated_at follows the YYYYMMDDTHHMMSSZ format."""
    matches = [Match(concept_uid="c1", doc_id="d1", rel_type="HAS_TOPIC", score=0.9)]
    payload = matches_to_payload(matches, doc_ids=["d1"], model="bge-m3")

    assert payload["generated_at"].endswith("Z")
    datetime.strptime(payload["generated_at"], "%Y%m%dT%H%M%SZ")


@pytest.mark.asyncio
async def test_matching_service_search_happy_path(monkeypatch):
    """search() embeds, normalises, and delegates to Matcher.match, returning its Matches."""
    import app.services.matching.matching_service as ms

    class DummySettings:
        top_k = 10
        embedding_api_model = ""

    monkeypatch.setattr(ms, "get_app_settings", lambda: DummySettings())
    monkeypatch.setattr(ms, "get_opensearch_client", lambda: object())

    service = MatchingService()

    class DummyEmbeddingService:
        async def embed_texts(self, texts: list[str]) -> list[list[float]]:
            return [[1.0, 0.0], [0.0, 1.0]]

    expected = [
        Match(concept_uid="tax-0", doc_id="docA", rel_type="HAS_DOMAIN", score=1.0),
        Match(concept_uid="tax-1", doc_id="docB", rel_type="HAS_FIELD", score=1.0),
    ]

    class DummyMatcher:
        async def match(self, doc_ids, doc_embeddings):
            assert doc_ids == ["docA", "docB"]
            return expected

    monkeypatch.setattr(service, "_embedding_service", DummyEmbeddingService())
    monkeypatch.setattr(service, "_matcher", DummyMatcher())

    matches = await service.search(["t1", "t2"], ["docA", "docB"])

    assert matches == expected


@pytest.mark.asyncio
async def test_matching_service_search_empty_texts_returns_empty(monkeypatch):
    """search() short-circuits to [] when texts is empty, without calling the matcher."""
    import app.services.matching.matching_service as ms

    class DummySettings:
        top_k = 10
        embedding_api_model = ""

    monkeypatch.setattr(ms, "get_app_settings", lambda: DummySettings())
    monkeypatch.setattr(ms, "get_opensearch_client", lambda: object())

    service = MatchingService()
    assert await service.search([], []) == []


@pytest.mark.asyncio
async def test_matching_service_search_length_mismatch_raises(monkeypatch):
    """search() raises ValueError when texts and ids have different lengths."""
    import app.services.matching.matching_service as ms

    class DummySettings:
        top_k = 10
        embedding_api_model = ""

    monkeypatch.setattr(ms, "get_app_settings", lambda: DummySettings())
    monkeypatch.setattr(ms, "get_opensearch_client", lambda: object())

    service = MatchingService()
    with pytest.raises(ValueError):
        await service.search(["a"], ["id1", "id2"])


@pytest.mark.asyncio
async def test_matching_service_search_as_payload_includes_all_ids(monkeypatch):
    """search_as_payload includes every input id, even those the matcher found nothing for."""
    import app.services.matching.matching_service as ms

    class DummySettings:
        top_k = 10
        embedding_api_model = "bge-m3"

    monkeypatch.setattr(ms, "get_app_settings", lambda: DummySettings())
    monkeypatch.setattr(ms, "get_opensearch_client", lambda: object())

    service = MatchingService()

    class DummyEmbeddingService:
        async def embed_texts(self, texts):
            return [[1.0, 0.0], [0.0, 1.0]]

    class DummyMatcher:
        async def match(self, doc_ids, doc_embeddings):
            return [Match(concept_uid="c1", doc_id="doc1", rel_type="HAS_TOPIC", score=0.9)]

    monkeypatch.setattr(service, "_embedding_service", DummyEmbeddingService())
    monkeypatch.setattr(service, "_matcher", DummyMatcher())

    payload = await service.search_as_payload(["t1", "t2"], ["doc1", "doc2"])

    assert payload["model"] == "bge-m3"
    assert payload["query_count"] == 2
    results_by_id = {r["id"]: r for r in payload["results"]}
    assert results_by_id["doc2"]["matches"] == []


def test_embedding_lowercasing_is_applied(monkeypatch):
    """embed_texts lowercases inputs before sending them to the provider."""
    from app.services.embeddings.embedding_service import EmbeddingService

    calls = {}

    class DummyProvider:
        async def embed_texts(self, texts):
            calls["texts"] = texts
            return [[0.1, 0.2]]

    service = EmbeddingService()
    service.provider = DummyProvider()

    import asyncio

    asyncio.run(service.embed_texts(["Machine Learning"]))

    assert calls["texts"] == ["machine learning"]