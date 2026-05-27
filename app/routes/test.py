"""Test routes."""

from fastapi import APIRouter

from app.models.response import TestResponse
from app.services.test_service import TestService

router = APIRouter(tags=["test"])


@router.get("/", response_model=TestResponse)
async def test_endpoint():
    """Test endpoint."""
    data = TestService.get_test_data("CRISalid Taxi")
    return TestResponse(message="Test successful", data=data)


@router.get("/{name}", response_model=TestResponse)
async def test_with_name(name: str):
    """Test endpoint with name parameter."""
    data = TestService.get_test_data(name)
    return TestResponse(message=f"Hello {name}!", data=data)
