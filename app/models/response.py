"""Response models."""

from typing import Optional

from pydantic import BaseModel, Field


class TestResponse(BaseModel):
    """Test response model.

    Modèle de réponse pour les endpoints de test.
    """

    message: str = Field(
        ...,
        description="Message de réponse principal",
        examples=["Test successful"],
    )
    data: Optional[dict] = Field(
        default=None,
        description="Données additionnelles de test",
        examples=[
            {
                "name": "CRISalid Taxi",
                "message": "Hello CRISalid Taxi!",
                "timestamp": "2026-05-27T00:00:00Z",
            }
        ],
    )

    class Config:
        """Pydantic config."""

        json_schema_extra = {
            "example": {
                "message": "Test successful",
                "data": {"test_value": "example"},
            }
        }
