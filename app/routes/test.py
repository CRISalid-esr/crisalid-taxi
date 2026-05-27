"""Test routes."""

from fastapi import APIRouter

from app.models.response import TestResponse
from app.services.test_service import TestService

router = APIRouter(tags=["test"])


@router.get(
    "/",
    response_model=TestResponse,
    summary="Test endpoint par défaut",
    description="Retourne des données de test avec un message de bienvenue par défaut.",
    responses={
        200: {
            "description": "Succès - Données de test retournées",
            "content": {
                "application/json": {
                    "example": {
                        "message": "Test successful",
                        "data": {
                            "name": "CRISalid Taxi",
                            "message": "Hello CRISalid Taxi!",
                            "timestamp": "2026-05-27T00:00:00Z",
                        },
                    }
                }
            },
        }
    },
)
async def test_endpoint():
    """Test endpoint par défaut.
    
    Cet endpoint retourne des données de test pour valider le fonctionnement de l'API.
    """
    data = TestService.get_test_data("CRISalid Taxi")
    return TestResponse(message="Test successful", data=data)


@router.get(
    "/{name}",
    response_model=TestResponse,
    summary="Test endpoint avec paramètre personnalisé",
    description="Retourne des données de test personnalisées selon le nom fourni.",
    responses={
        200: {
            "description": "Succès - Données de test avec le nom personnalisé",
            "content": {
                "application/json": {
                    "example": {
                        "message": "Hello Alice!",
                        "data": {
                            "name": "Alice",
                            "message": "Hello Alice!",
                            "timestamp": "2026-05-27T00:00:00Z",
                        },
                    }
                }
            },
        }
    },
)
async def test_with_name(name: str):
    """Test endpoint avec paramètre.
    
    ### Paramètres
    - **name** (str): Le nom à utiliser pour personnaliser la réponse de test.
    
    ### Retour
    Une réponse de test personnalisée avec le nom fourni.
    """
    data = TestService.get_test_data(name)
    return TestResponse(message=f"Hello {name}!", data=data)

