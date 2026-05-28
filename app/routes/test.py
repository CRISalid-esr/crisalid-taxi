"""Test routes for development purposes."""
from fastapi import APIRouter, status
from loguru import logger
from pydantic import BaseModel


class TestResponse(BaseModel):
    """Response model for test endpoint."""

    message: str
    data: dict


router = APIRouter()


@router.get(
    "/",
    tags=["test"],
    summary="Test endpoint",
    status_code=status.HTTP_200_OK,
    response_model=TestResponse,
)
async def test_endpoint() -> TestResponse:
    """Test endpoint without name parameter.

    Returns:
        TestResponse: Returns a test response with greeting
    """
    logger.info("Test endpoint called without name")
    return TestResponse(
        message="Test successful",
        data={
            "name": "CRISalid Taxi",
            "message": "Hello CRISalid Taxi!",
        },
    )


@router.get(
    "/{name}",
    tags=["test"],
    summary="Test endpoint with name",
    status_code=status.HTTP_200_OK,
    response_model=TestResponse,
)
async def test_endpoint_with_name(name: str) -> TestResponse:
    """Test endpoint with name parameter.

    Args:
        name: Name parameter for greeting

    Returns:
        TestResponse: Returns a test response with personalized greeting
    """
    logger.info(f"Test endpoint called with name: {name}")
    return TestResponse(
        message=f"Hello {name}!",
        data={
            "name": name,
            "message": f"Hello {name}!",
        },
    )
