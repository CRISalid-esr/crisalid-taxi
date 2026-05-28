"""Main API router."""
from fastapi import APIRouter

from app.routes.health import router as health_router

# Create main router
router = APIRouter()

# Include sub-routers
router.include_router(health_router, prefix="", tags=["health"])
