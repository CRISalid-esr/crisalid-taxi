"""Response models."""

from typing import Optional

from pydantic import BaseModel


class TestResponse(BaseModel):
    """Test response model."""

    message: str
    data: Optional[dict] = None

    class Config:
        """Pydantic config."""

        json_schema_extra = {
            "example": {
                "message": "Test successful",
                "data": {"test_value": "example"},
            }
        }
