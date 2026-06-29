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
    """Embed the provided inputs and return matching taxonomy nodes.

    - **inputs**: list of objects containing id and text

    Query embeddings are computed on the fly and are never stored.
    """

    texts = [item.text for item in request.inputs]
    ids = [item.id for item in request.inputs]

    logger.info("POST /match — %d document(s)", len(texts))

    try:
        service = MatchingService()
        payload = await service.search_as_payload(
            texts, ids, similarity_threshold=request.similarity_threshold
        )
        return MatchPayload(**payload)
    except Exception as exc:
        logger.error("Match failed: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc)) from exc
