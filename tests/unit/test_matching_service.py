"""Unit tests for matching services (Matcher, matches_to_payload, MatchingService)."""

from __future__ import annotations

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
            [1.0, 0.0],  # perfect cosine with doc0
            [0.0, 1.0],  # perfect cosine with doc1
        ],
        dtype=np.float32,
    )
    taxonomy_ids = ["tax-0", "tax-1"]
    taxonomy_levels = ["domain", "field"]

    doc_embs = np.array(
        [
            [1.0, 0.0],  # aligns with tax-0
            [0.0, 1.0],  # aligns with tax-1
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


def test_matcher_top_k_limits_matches_per_taxonomy_node():
    taxonomy_embs = np.array([[1.0, 0.0]], dtype=np.float32)
    taxonomy_ids = ["tax-0"]
    taxonomy_levels = ["topic"]  # HAS_TOPIC

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
        Match(concept_uid="c3", doc_id="doc-2", rel_type="HAS_TOPIC", score=0.3333333),
    ]

    payload = matches_to_payload(matches, model="mymodel")

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


@pytest.mark.asyncio
async def test_matching_service_search_happy_path(monkeypatch):
    # MatchingService reads several attributes from app settings during __init__.
    # This repo version doesn't define them; so we patch them via the module-level
    # get_app_settings used by MatchingService.
    import app.services.matching.matching_service as ms

    class DummySettings:
        similarity_threshold = 0.8
        top_k = None
        chunk_size = 5000
        embedding_api_model = ""  # used by search_as_payload

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

    # MatchingService reads several attributes from app settings during __init__.
    # This repo version doesn't define them; so we patch them via the module-level
    # get_app_settings used by MatchingService.
    from app.services import matching as _matching_pkg  # noqa: F401

    import app.services.matching.matching_service as ms

    class DummySettings:
        similarity_threshold = 0.8
        top_k = None
        chunk_size = 5000
        embedding_api_model = ""  # used by search_as_payload

    monkeypatch.setattr(ms, "get_app_settings", lambda: DummySettings())

    service = MatchingService()

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


