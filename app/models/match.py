"""Pydantic models for the /match endpoint."""

from pydantic import BaseModel, Field, field_validator, model_validator


class MatchInputItem(BaseModel):
    id: str = Field(description="Opaque document identifier (e.g. an application-specific UUID).")
    text: str = Field(description="Query text to classify (e.g. publication abstract).")

    @field_validator("text")
    @classmethod
    def text_no_empty(cls, v: str) -> str:
        """Reject empty or whitespace-only text."""
        if not v or not v.strip():
            raise ValueError("text cannot be empty or whitespace-only")
        return v


class MatchRequest(BaseModel):
    """Request body for POST /match."""

    inputs: list[MatchInputItem] = Field(
        description="List of inputs containing an id and text to classify.",
        min_length=1,
    )
    similarity_threshold: float | None = Field(
        default=None,
        ge=-1.0,
        le=1.0,
        description=(
            "Minimum cosine similarity a concept must reach to be returned. "
            "Applied before max_topics. Omit to use the server default "
            "(SIMILARITY_THRESHOLD)."
        ),
    )
    max_topics: int | None = Field(
        default=None,
        ge=1,
        le=1000,
        description=(
            "Maximum number of taxonomy concepts returned per input text, "
            "kept among those above the threshold. Omit to use the server "
            "default (MAX_TOPICS)."
        ),
    )

    @model_validator(mode="after")
    def ids_are_unique(self) -> "MatchRequest":
        """Ensure all input ids are unique within the request."""
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
    matches: list[ConceptMatchItem] = Field(
        description=(
            "Concepts retained for this input. Empty when nothing cleared the "
            "threshold, and equally when the text was too short to be matched "
            "at all (see MIN_INPUT_LENGTH)."
        )
    )


class MatchPayload(BaseModel):
    """IKG-ready response payload returned by POST /match."""

    generated_at: str = Field(description="UTC timestamp of computation (YYYYMMDDTHHMMSSz)")
    model: str = Field(description="Embedding model used")
    query_count: int = Field(description="Number of documents in the response")
    total_matches: int = Field(description="Total number of (document, concept) pairs returned")
    similarity_threshold: float = Field(
        description="Minimum cosine similarity applied to this request"
    )
    results: list[DocumentMatchResult]
