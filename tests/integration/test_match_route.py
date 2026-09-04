"""Integration tests for POST /api/v1/match endpoint."""

import pytest


@pytest.mark.asyncio
async def test_post_match_validation_error(client):
    """Should return 422 when an item is missing id or text."""
    resp = client.post("/api/v1/match/", json={"inputs": [{"text": "t1"}]})
    assert resp.status_code == 422
    detail = resp.json()["detail"]
    assert any("id" in str(err["loc"]) for err in detail)


@pytest.mark.asyncio
async def test_post_match_empty_string_validation(client):
    """Should return 422 when texts contains empty or whitespace-only string."""
    resp = client.post(
        "/api/v1/match/",
        json={"inputs": [{"id": "doc-1", "text": " "}, {"id": "doc-2", "text": "ok"}]},
    )
    assert resp.status_code == 422
    detail = resp.json()["detail"][0]
    assert "whitespace-only" in detail["msg"]


@pytest.mark.asyncio
async def test_post_match_empty_texts_list(client):
    """Should return 422 when inputs list is empty due to min_length=1 in MatchRequest."""
    resp = client.post("/api/v1/match/", json={"inputs": []})
    assert resp.status_code == 422
    # Pydantic List min_length=1 validation
    assert any(err["loc"] == ["body", "inputs"] for err in resp.json()["detail"])


@pytest.mark.asyncio
async def test_post_match_returns_payload(client, monkeypatch):
    """Should return MatchPayload shape when MatchingService succeeds."""
    from app.services.matching import matching_service as ms

    payload = {
        "generated_at": "20260101T000Z",
        "model": "dummy-model",
        "query_count": 1,
        "total_matches": 1,
        "results": [
            {
                "id": "doc-1",
                "matches": [
                    {
                        "concept_uid": "https://openalex.org/domains/1",
                        "rel_type": "HAS_DOMAIN",
                        "value": 0.9,
                    }
                ],
            }
        ],
    }

    async def fake_search_as_payload(self, texts, ids):
        assert texts == ["t1"]
        assert ids == ["doc-1"]
        return payload

    monkeypatch.setattr(ms.MatchingService, "search_as_payload", fake_search_as_payload)

    resp = client.post("/api/v1/match/", json={"inputs": [{"id": "doc-1", "text": "t1"}]})
    assert resp.status_code == 200
    body = resp.json()
    assert body["model"] == "dummy-model"
    assert body["query_count"] == 1
    assert body["total_matches"] == 1
    assert body["generated_at"] == "20260101T000Z"
    assert body["results"][0]["id"] == "doc-1"
    assert body["results"][0]["matches"][0]["concept_uid"] == "https://openalex.org/domains/1"
    assert body["results"][0]["matches"][0]["rel_type"] == "HAS_DOMAIN"
    assert body["results"][0]["matches"][0]["value"] == 0.9


@pytest.mark.asyncio
async def test_post_match_multiple_docs(client, monkeypatch):
    """Should handle multiple documents correctly."""
    from app.services.matching import matching_service as ms

    payload = {
        "generated_at": "20260101T000Z",
        "model": "dummy-model",
        "query_count": 2,
        "total_matches": 3,
        "results": [
            {
                "id": "doc-1",
                "matches": [{"concept_uid": "c1", "rel_type": "HAS_DOMAIN", "value": 0.9}],
            },
            {
                "id": "doc-2",
                "matches": [
                    {"concept_uid": "c2", "rel_type": "HAS_FIELD", "value": 0.8},
                    {"concept_uid": "c3", "rel_type": "HAS_TOPIC", "value": 0.7},
                ],
            },
        ],
    }

    async def fake_search_as_payload(self, texts, ids):
        assert len(texts) == 2
        assert len(ids) == 2
        return payload

    monkeypatch.setattr(ms.MatchingService, "search_as_payload", fake_search_as_payload)

    resp = client.post(
        "/api/v1/match/",
        json={"inputs": [{"id": "doc-1", "text": "text1"}, {"id": "doc-2", "text": "text2"}]},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["query_count"] == 2
    assert body["total_matches"] == 3
    assert len(body["results"]) == 2


@pytest.mark.asyncio
async def test_post_match_service_error_returns_500(client, monkeypatch):
    """Should return 500 when MatchingService raises exception."""
    from app.services.matching import matching_service as ms

    async def fake_search_as_payload(self, texts, ids):
        raise RuntimeError("OpenSearch connection failed")

    monkeypatch.setattr(ms.MatchingService, "search_as_payload", fake_search_as_payload)

    resp = client.post("/api/v1/match/", json={"inputs": [{"id": "doc-1", "text": "t1"}]})
    assert resp.status_code == 500
    assert "detail" in resp.json()
    assert "OpenSearch connection failed" in resp.json()["detail"]
