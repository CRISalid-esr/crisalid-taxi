"""Pydantic models for embedding results."""

from typing import Literal
from pydantic import BaseModel, Field


class EmbeddingRecord(BaseModel):
    """Structured result returned by the embedding service for an OpenAlex entity."""

    id: str = Field(alias="_id", description="OpenAlex entity id")
    display_name: str = Field(description="Human-readable name of the entity")
    embedding: list[float] = Field(description="L2-normalised float32 embedding vector")
    type: Literal["domain", "field", "subfield", "topic"] = Field(
        description="OpenAlex hierarchy level"
    )

    model_config = {"populate_by_name": True}
