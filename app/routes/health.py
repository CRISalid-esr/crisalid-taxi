"""Health check routes."""

from fastapi import APIRouter

router = APIRouter(prefix="/api/v1", tags=["health"])


@router.get(
    "/health",
    summary="Vérification de santé",
    description="Endpoint pour vérifier l'état et la disponibilité du service.",
    responses={
        200: {
            "description": "Service en bonne santé",
            "content": {
                "application/json": {
                    "example": {
                        "status": "healthy",
                        "service": "crisalid-taxi",
                    }
                }
            },
        }
    },
)
async def health_check():
    """Vérification de santé du service.
    
    Cet endpoint retourne l'état du service et confirme que l'API fonctionne correctement.
    
    ### Réponse
    - **status** (str): État du service ("healthy", "degraded", "unhealthy")
    - **service** (str): Nom du service
    """
    return {
        "status": "healthy",
        "service": "crisalid-taxi",
    }
