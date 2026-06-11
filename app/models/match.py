"""Pydantic models for the /match endpoint."""

from pydantic import BaseModel, Field


class MatchRequest(BaseModel):
    """Request body for POST /match."""

    texts: list[str] = Field(
        description="Query texts to classify (e.g. publication abstracts).",
        min_length=1,
    )
    ids: list[str] = Field(
        description="Opaque document identifiers, one per text (e.g. Neo4j element_id).",
        min_length=1,
    )


class ConceptMatchItem(BaseModel):
    concept_uid: str = Field(
        description="OpenAlex URI of the matched taxonomy node"
    )
    rel_type: str = Field(
        description="Relationship type: HAS_DOMAIN | HAS_FIELD | HAS_SUBFIELD | HAS_TOPIC"
    )
    value: float = Field(
        description="Cosine similarity score (L2-normalised dot product)"
    )


class DocumentMatchResult(BaseModel):
    id: str = Field(description="The opaque document identifier supplied in the request")
    matches: list[ConceptMatchItem]


class MatchPayload(BaseModel):
    """IKG-ready response payload returned by POST /match."""

    generated_at: str = Field(
        description="UTC timestamp of computation (YYYYMMDDTHHMMSSz)"
    )
    model: str = Field(description="Embedding model used")
    query_count: int = Field(description="Number of documents in the response")
    total_matches: int = Field(
        description="Total number of (document, concept) pairs above threshold"
    )
    results: list[DocumentMatchResult]

