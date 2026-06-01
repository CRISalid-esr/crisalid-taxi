"""Main API router for /api/v1 endpoints."""
from fastapi import APIRouter

from app.routes.health import router as health_router
from app.routes.test import router as test_router

# Create main router for /api/v1
router = APIRouter()

# Include sub-routers under /api/v1
router.include_router(health_router, prefix="/health", tags=["health"])
router.include_router(test_router, prefix="/test", tags=["test"])
