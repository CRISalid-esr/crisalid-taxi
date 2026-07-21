"""POST /match — semantic taxonomy matching route."""

from fastapi import APIRouter, HTTPException
from loguru import logger
from pydantic import BaseModel, Field, field_validator, model_validator

from app.services.matching.matching_service import MatchingService

router = APIRouter()


class MatchInputItem(BaseModel):
    id: str = Field(description="Opaque document identifier (e.g. an application-specific UUID).")
    text: str = Field(description="Query text to classify (e.g. publication abstract).")

    @field_validator("text")
    @classmethod
    def text_no_empty(cls, v: str) -> str:
        """
        Reject empty or whitespace-only text.

        Parameters
        ----------
        v : str
            Candidate value for `text`.

        Returns
        -------
        str
            The validated value, unchanged.
        """
        if not v or not v.strip():
            raise ValueError("text cannot be empty or whitespace-only")
        return v


class MatchRequest(BaseModel):
    """Request body for POST /match."""

    inputs: list[MatchInputItem] = Field(
        description="List of inputs containing an id and text to classify.",
        min_length=1,
    )

    @model_validator(mode="after")
    def ids_are_unique(self) -> "MatchRequest":
        """
        Ensure all input ids are unique within the request.

        Returns
        -------
        MatchRequest
            The validated request, unchanged.
        """
        ids = [item.id for item in self.inputs]
        if len(ids) != len(set(ids)):
            raise ValueError("inputs must have unique ids")
        return self


class ConceptMatchItem(BaseModel):
    concept_uid: str = Field(description="OpenAlex URI of the matched taxonomy node")
    rel_type: str = Field(
        description="Relationship type: HAS_DOMAIN | HAS_FIELD | HAS_SUBFIELD | HAS_TOPIC"
    )
    value: float = Field(description="Cosine similarity score (L2-normalised dot product)")


class DocumentMatchResult(BaseModel):
    id: str = Field(description="The opaque document identifier supplied in the request")
    matches: list[ConceptMatchItem]


class MatchPayload(BaseModel):
    """IKG-ready response payload returned by POST /match."""

    generated_at: str = Field(description="UTC timestamp of computation (YYYYMMDDTHHMMSSz)")
    model: str = Field(description="Embedding model used")
    query_count: int = Field(description="Number of documents in the response")
    total_matches: int = Field(
        description="Total number of (document, concept) pairs above threshold"
    )
    results: list[DocumentMatchResult]


@router.post(
    "/",
    response_model=MatchPayload,
    summary="Classify documents against the OpenAlex taxonomy",
)
async def match_taxonomy(request: MatchRequest) -> MatchPayload:
    """Embed the provided inputs and return matching taxonomy nodes.

    - **inputs**: list of objects containing id and text

    Query embeddings are computed on the fly and are never stored. Matching
    retrieves the top-k nearest taxonomy concepts per document via
    approximate k-NN search; there is no similarity threshold.
    """
    texts = [item.text for item in request.inputs]
    ids = [item.id for item in request.inputs]

    logger.info("POST /match — %d document(s)", len(texts))

    try:
        service = MatchingService()
        payload = await service.search_as_payload(texts, ids)
        return MatchPayload(**payload)
    except Exception as exc:
        logger.error("Match failed: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc)) from exc