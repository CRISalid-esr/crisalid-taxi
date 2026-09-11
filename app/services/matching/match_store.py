from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.services.matching.matcher import Match


@dataclass
class ConceptMatchItem:
    """
    A single (concept, score) pair attached to a document.

    Parameters
    ----------
    concept_uid : str
        OpenAlex URI of the matched taxonomy node.
    rel_type : str
        Relationship type (``HAS_DOMAIN`` | ``HAS_FIELD`` | ``HAS_SUBFIELD`` |
        ``HAS_TOPIC``).
    value : float
        Cosine similarity score, rounded for display.
    """

    concept_uid: str
    rel_type: str
    value: float


@dataclass
class InputResultItem:
    """
    Matches grouped for a single input document.

    Parameters
    ----------
    id : str
        Opaque document identifier supplied in the request.
    matches : list of ConceptMatchItem
        Concepts retained for this document, possibly empty.
    """

    id: str
    matches: list[ConceptMatchItem] = field(default_factory=list)


def matches_to_payload(
    matches: list["Match"],
    doc_ids: list[str],
    model: str = "",
    similarity_threshold: float = 0.53,
) -> dict:
    """
    Group a flat Match list into the IKG-ready JSON payload.

    Parameters
    ----------
    matches : list of Match
        Flat list of retained (concept, document) matches, at most
        `max_topics` per document.
    doc_ids : list of str
        All document ids submitted in the request, in the order in which
        they should appear in the payload.
    model : str, default ""
        Embedding model name to report in the payload.
    similarity_threshold : float, default 0.53
        Threshold applied to this request, echoed in the payload so the caller
        knows what filtering ran.

    Returns
    -------
    dict
        JSON-serialisable payload with keys `generated_at`, `model`,
        `query_count`, `total_matches` and `results`.
    """
    results: dict[str, InputResultItem] = {doc_id: InputResultItem(id=doc_id) for doc_id in doc_ids}
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

    ordered_ids = list(doc_ids) + [d for d in results if d not in doc_ids]
    result_list = [results[doc_id] for doc_id in ordered_ids]

    return {
        "generated_at": datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ"),
        "model": model,
        "query_count": len(doc_ids),
        "total_matches": len(matches),
        "similarity_threshold": similarity_threshold,
        "results": [asdict(r) for r in result_list],
    }
