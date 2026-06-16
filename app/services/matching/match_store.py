from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.services.matching.matcher import Match


@dataclass
class ConceptMatchItem:
    concept_uid: str
    rel_type: str
    value: float


@dataclass
class InputResultItem:
    id: str
    matches: list[ConceptMatchItem] = field(default_factory=list)


def matches_to_payload(matches: list["Match"], model: str = "", similarity_threshold: float = 0.0) -> dict:
    """Group a flat Match list into the IKG-ready JSON payload.

    Returned structure:
    {
      "generated_at": "20240101T120000Z",
      "model": "...",
      "query_count": N,
      "total_matches": M,
      "similarity_threshold": 0.52,
      "results": [
        {
          "id": "doc-id-1",
          "matches": [
            {"concept_uid": "...", "rel_type": "HAS_DOMAIN", "value": 0.85}
          ]
        }
      ]
    }
    """

    results: dict[str, InputResultItem] = {}
    for m in matches:
        if m.doc_id not in results:
            results[m.doc_id] = InputResultItem(id=m.doc_id)
        results[m.doc_id].matches.append(
            ConceptMatchItem(
                concept_uid=m.concept_uid,
                rel_type=m.rel_type,
                value=round(m.score, 6),
            )
        )

    result_list = list(results.values())
    return {
        "generated_at": datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ"),
        "model": model,
        "query_count": len(result_list),
        "total_matches": len(matches),
        "similarity_threshold": similarity_threshold,
        "results": [asdict(r) for r in result_list],
    }

