"""Unit tests for matching services (Matcher, matches_to_payload, MatchingService)."""

from __future__ import annotations

from datetime import datetime

import numpy as np
import pytest

from app.services.matching.match_store import matches_to_payload
from app.services.matching.matcher import Match, Matcher
from app.services.matching.matching_service import MatchingService

def test_matcher_returns_empty_when_no_inputs():
    matcher = Matcher(threshold=0.5)

    taxonomy_ids: list[str] = []
    taxonomy_embs = np.zeros((0, 3), dtype=np.float32)
    taxonomy_levels: list[str] = []
    doc_ids: list[str] = []
    doc_embs = np.zeros((0, 3), dtype=np.float32)

    assert (
        matcher.match(
            taxonomy_ids,
            taxonomy_embs,
            taxonomy_levels,
            doc_ids,
            doc_embs,
        )
        == []
    )

def test_matcher_threshold_and_rel_type_mapping_domain_field():
    taxonomy_embs = np.array(
        [
            [1.0, 0.0], # perfect cosine with doc0
            [0.0, 1.0], # perfect cosine with doc1
        ],
        dtype=np.float32,
    )
    taxonomy_ids = ["tax-0", "tax-1"]
    taxonomy_levels = ["domain", "field"]

    doc_embs = np.array(
        [
            [1.0, 0.0], # aligns with tax-0
            [0.0, 1.0], # aligns with tax-1
        ],
        dtype=np.float32,
    )
    doc_ids = ["doc-0", "doc-1"]

    matcher = Matcher(threshold=0.8, top_k=None, chunk_size=5000)
    matches = matcher.match(
        taxonomy_ids,
        taxonomy_embs,
        taxonomy_levels,
        doc_ids,
        doc_embs,
    )

    assert len(matches) == 2

    m0 = next(m for m in matches if m.concept_uid == "tax-0")
    assert m0.doc_id == "doc-0"
    assert m0.rel_type == "HAS_DOMAIN"
    assert pytest.approx(m0.score, rel=1e-6) == 1.0

    m1 = next(m for m in matches if m.concept_uid == "tax-1")
    assert m1.doc_id == "doc-1"
    assert m1.rel_type == "HAS_FIELD"
    assert pytest.approx(m1.score, rel=1e-6) == 1.0

def test_matcher_rel_type_subfield_topic():
    """Test mapping HAS_SUBFIELD and HAS_TOPIC rel_types."""
    taxonomy_levels = ["subfield", "topic"]
    taxonomy_ids = ["tax-s", "tax-t"]
    taxonomy_embs = np.array([[1.0, 0.0], [0.0, 1.0]], dtype=np.float32)
    doc_embs = np.array([[1.0, 0.0], [0.0, 1.0]], dtype=np.float32)
    doc_ids = ["d0", "d1"]

    matcher = Matcher(threshold=0.8)
    matches = matcher.match(taxonomy_ids, taxonomy_embs, taxonomy_levels, doc_ids, doc_embs)

    assert len(matches) == 2
    rel_types = {m.rel_type for m in matches}
    assert rel_types == {"HAS_SUBFIELD", "HAS_TOPIC"}

def test_matcher_score_below_threshold_returns_no_match():
    """Test that scores < threshold produce no matches."""
    taxonomy_embs = np.array([[1.0, 0.0]], dtype=np.float32)
    taxonomy_ids = ["tax-0"]
    taxonomy_levels = ["topic"]
    doc_embs = np.array([[0.3, 0.95]], dtype=np.float32) # cosine ~0.3
    doc_embs[0] = doc_embs[0] / np.linalg.norm(doc_embs[0])
    doc_ids = ["doc-0"]

    matcher = Matcher(threshold=0.5)
    matches = matcher.match(taxonomy_ids, taxonomy_embs, taxonomy_levels, doc_ids, doc_embs)
    assert matches == []

def test_matcher_top_k_limits_matches_per_taxonomy_node():
    taxonomy_embs = np.array([[1.0, 0.0]], dtype=np.float32)
    taxonomy_ids = ["tax-0"]
    taxonomy_levels = ["topic"] # HAS_TOPIC

    doc_embs = np.array(
        [
            [1.0, 0.0],
            [0.9, 0.4358899],
        ],
        dtype=np.float32,
    )
    doc_embs[1] = doc_embs[1] / np.linalg.norm(doc_embs[1])

    doc_ids = ["doc-0", "doc-1"]

    matcher = Matcher(threshold=0.5, top_k=1, chunk_size=5000)
    matches = matcher.match(
        taxonomy_ids,
        taxonomy_embs,
        taxonomy_levels,
        doc_ids,
        doc_embs,
    )

    assert len(matches) == 1
    assert matches[0].concept_uid == "tax-0"
    assert matches[0].rel_type == "HAS_TOPIC"
    assert matches[0].doc_id == "doc-0"

def test_matcher_top_k_zero_returns_empty():
    """Test top_k=0 returns no matches regardless of scores."""
    taxonomy_embs = np.array([[1.0, 0.0]], dtype=np.float32)
    taxonomy_ids = ["t0"]
    taxonomy_levels = ["topic"]
    doc_embs = np.array([[1.0, 0.0]], dtype=np.float32)
    doc_ids = ["d0"]

    matcher = Matcher(threshold=0.5, top_k=0)
    matches = matcher.match(taxonomy_ids, taxonomy_embs, taxonomy_levels, doc_ids, doc_embs)
    assert matches == []

def test_matcher_chunking_produces_same_results_as_single_chunk():
    taxonomy_embs = np.array(
        [
            [1.0, 0.0],
            [0.0, 1.0],
            [1.0, 0.0],
        ],
        dtype=np.float32,
    )
    taxonomy_ids = ["t0", "t1", "t2"]
    taxonomy_levels = ["domain", "domain", "field"]

    doc_embs = np.array([[1.0, 0.0], [0.0, 1.0]], dtype=np.float32)
    doc_ids = ["d0", "d1"]

    m1 = Matcher(threshold=0.8, top_k=None, chunk_size=10)
    r1 = m1.match(taxonomy_ids, taxonomy_embs, taxonomy_levels, doc_ids, doc_embs)

    m2 = Matcher(threshold=0.8, top_k=None, chunk_size=1)
    r2 = m2.match(taxonomy_ids, taxonomy_embs, taxonomy_levels, doc_ids, doc_embs)

    assert {(m.concept_uid, m.doc_id, m.rel_type, round(m.score, 6)) for m in r1} == {
        (m.concept_uid, m.doc_id, m.rel_type, round(m.score, 6)) for m in r2
    }

def test_matches_to_payload_groups_by_doc_and_rounds():
    matches = [
        Match(concept_uid="c1", doc_id="doc-1", rel_type="HAS_DOMAIN", score=0.1234567),
        Match(concept_uid="c2", doc_id="doc-1", rel_type="HAS_FIELD", score=0.9),
        Match(concept_uid="c3", doc_id="doc-2", rel_type="HAS_TOPIC", score=0.3333),
    ]

    payload = matches_to_payload(matches, model="mymodel", similarity_threshold=0.52)

    assert payload["model"] == "mymodel"
    assert payload["query_count"] == 2
    assert payload["total_matches"] == 3
    assert payload["similarity_threshold"] == 0.52
    assert "generated_at" in payload

    results_by_id = {r["id"]: r for r in payload["results"]}
    assert set(results_by_id.keys()) == {"doc-1", "doc-2"}

    doc1_matches = results_by_id["doc-1"]["matches"]
    assert {(m["concept_uid"], m["rel_type"], m["value"]) for m in doc1_matches} == {
        ("c1", "HAS_DOMAIN", round(0.1234567, 6)),
        ("c2", "HAS_FIELD", round(0.9, 6)),
    }

def test_matches_to_payload_timestamp_format():
    """Test generated_at follows YYYYMMDDTHHMMSSZ format."""
    matches = [Match(concept_uid="c1", doc_id="d1", rel_type="HAS_TOPIC", score=0.9)]
    payload = matches_to_payload(matches, model="bge-m3")

    assert payload["generated_at"].endswith("Z")
    # Should parse without error
    datetime.strptime(payload["generated_at"], "%Y%m%dT%H%M%SZ")

@pytest.mark.asyncio
async def test_matching_service_search_happy_path(monkeypatch):
    import app.services.matching.matching_service as ms

    class DummySettings:
        similarity_threshold = 0.8
        top_k = None
        chunk_size = 5000
        embedding_api_model = ""

    monkeypatch.setattr(ms, "get_app_settings", lambda: DummySettings())

    service = MatchingService()

    class DummyEmbeddingService:
        async def embed_texts(self, texts: list[str]) -> list[list[float]]:
            return [[1.0, 0.0], [0.0, 1.0]]

    class DummyOpensearchClient:
        async def get_all_embeddings(self, index_name: str):
            assert index_name == "openalex_embeddings"
            tax_ids = ["tax-0", "tax-1"]
            tax_embs = np.array([[1.0, 0.0], [0.0, 1.0]], dtype=np.float32)
            tax_types = ["domain", "field"]
            return tax_ids, tax_embs, tax_types

    monkeypatch.setattr(service, "_embedding_service", DummyEmbeddingService())
    monkeypatch.setattr(service, "_opensearch", DummyOpensearchClient())

    matches = await service.search(["t1", "t2"], ["docA", "docB"])

    assert {(m.concept_uid, m.doc_id, m.rel_type) for m in matches} == {
        ("tax-0", "docA", "HAS_DOMAIN"),
        ("tax-1", "docB", "HAS_FIELD"),
    }

@pytest.mark.asyncio
async def test_matching_service_search_empty_texts_returns_empty(monkeypatch):
    import app.services.matching.matching_service as ms

    class DummySettings:
        similarity_threshold = 0.8
        top_k = None
        chunk_size = 5000
        embedding_api_model = ""

    monkeypatch.setattr(ms, "get_app_settings", lambda: DummySettings())

    service = MatchingService()
    assert await service.search([], []) == []

@pytest.mark.asyncio
async def test_matching_service_search_length_mismatch_raises(monkeypatch):
    import app.services.matching.matching_service as ms

    class DummySettings:
        similarity_threshold = 0.8
        top_k = None
        chunk_size = 5000
        embedding_api_model = ""

    monkeypatch.setattr(ms, "get_app_settings", lambda: DummySettings())

    service = MatchingService()
    with pytest.raises(ValueError):
        await service.search(["a"], ["id1", "id2"])

@pytest.mark.asyncio
async def test_matching_service_case_insensitive(monkeypatch):
    import app.services.matching.matching_service as ms

    class DummySettings:
        similarity_threshold = 0.5
        top_k = None
        chunk_size = 5000
        embedding_api_model = ""

    monkeypatch.setattr(ms, "get_app_settings", lambda: DummySettings())

    service = MatchingService()

    class DummyEmbeddingService:
        async def embed_texts(self, texts):
            # on simule un embedding stable (peu importe le casing)
            return [[1.0, 0.0]]

    class DummyOpensearchClient:
        async def get_all_embeddings(self, index_name):
            return (
                ["tax-ml"],
                np.array([[1.0, 0.0]], dtype=np.float32),
                ["topic"],
            )

    monkeypatch.setattr(service, "_embedding_service", DummyEmbeddingService())
    monkeypatch.setattr(service, "_opensearch", DummyOpensearchClient())

    res1 = await service.search(["machine learning"], ["doc1"])
    res2 = await service.search(["Machine Learning"], ["doc2"])

    assert len(res1) == len(res2)

def test_embedding_lowercasing_is_applied(monkeypatch):
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