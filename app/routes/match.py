"""POST /match — semantic taxonomy matching route."""

from fastapi import APIRouter, HTTPException
from loguru import logger

from app.models.match import MatchPayload, MatchRequest
from app.services.matching.matching_service import MatchingService

router = APIRouter()


@router.post(
    "/",
    response_model=MatchPayload,
    summary="Classify documents against the OpenAlex taxonomy",
)
async def match_taxonomy(request: MatchRequest) -> MatchPayload:
    """Embed the provided texts and return matching taxonomy nodes.

    - **texts**: list of free-text queries (e.g. publication abstracts)
    - **ids**: one opaque identifier per text (e.g. Neo4j element_id)

    Both lists must have the same length. Query embeddings are computed on the
    fly and are never stored.
    """

    if len(request.texts) != len(request.ids):
        raise HTTPException(
            status_code=422,
            detail=(
                "texts and ids must have the same length "
                f"({len(request.texts)} vs {len(request.ids)})"
            ),
        )

    logger.info("POST /match — %d document(s)", len(request.texts))

    try:
        service = MatchingService()
        payload = await service.search_as_payload(request.texts, request.ids)
        return MatchPayload(**payload)
    except Exception as exc:
        logger.error("Match failed: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc)) from exc

