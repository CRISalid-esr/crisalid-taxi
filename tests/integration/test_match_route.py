import pytest
from unittest.mock import AsyncMock


@pytest.mark.asyncio
async def test_post_match_validation_error(client):
    """Should return 422 when texts and ids lengths differ."""
    resp = client.post("/api/v1/match/", json={"texts": ["t1"], "ids": []})
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_post_match_returns_payload(client, monkeypatch):
    """Should return MatchPayload shape when MatchingService succeeds."""

    from app.services.matching import matching_service as ms

    payload = {
        "generated_at": "20260101T000000Z",
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

    resp = client.post("/api/v1/match/", json={"texts": ["t1"], "ids": ["doc-1"]})
    assert resp.status_code == 200
    body = resp.json()
    assert body["model"] == "dummy-model"
    assert body["total_matches"] == 1
    assert body["results"][0]["id"] == "doc-1"
    assert body["results"][0]["matches"][0]["rel_type"] == "HAS_DOMAIN"

