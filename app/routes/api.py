"""Main API router for /api/v1 endpoints."""

from fastapi import APIRouter

from app.routes.match import router as match_router

# Create main router for /api/v1
router = APIRouter()

# Include sub-routers under /api/v1
router.include_router(match_router, prefix="/match", tags=["match"])
