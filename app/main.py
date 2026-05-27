"""Main FastAPI application module."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi

from app.config import settings
from app.routes import health, test


def custom_openapi():
    """Generate custom OpenAPI schema."""
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title=settings.API_TITLE,
        version=settings.API_VERSION,
        description="""
# CRISalid Taxi API

API microservice pour le système CRISalid Taxi.

## Fonctionnalités

- 🏥 Health check et monitoring
- 🧪 Routes de test pour validation
- 📡 API RESTful complètement documentée
- ✅ Validation automatique des données avec Pydantic
- 🔒 Support CORS configuré

## Documentation

Tous les endpoints sont documentés et testables via Swagger UI.

### Tags
- **health**: Endpoints de santé et monitoring
- **test**: Routes de test
- **default**: Endpoints généraux
        """,
        routes=app.routes,
    )

    openapi_schema["info"]["x-logo"] = {
        "url": "https://crisalid-esr.fr/images/logo.png",
        "alt_text": "CRISalid Logo",
    }

    app.openapi_schema = openapi_schema
    return app.openapi_schema


# Create FastAPI app instance
app = FastAPI(
    title=settings.API_TITLE,
    version=settings.API_VERSION,
    description="""
API microservice CRISalid Taxi - Gestion complète des appels de taxi.

## Démarrage Rapide

Les endpoints sont accessibles via:
- Swagger UI: `/docs`
- ReDoc: `/redoc`
- OpenAPI JSON: `/openapi.json`
    """,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    openapi_tags=[
        {
            "name": "health",
            "description": "Endpoints de santé et monitoring de l'application",
        },
        {
            "name": "test",
            "description": "Routes de test pour validation de l'infrastructure",
        },
        {
            "name": "default",
            "description": "Endpoints généraux de l'API",
        },
    ],
)

app.openapi = custom_openapi

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router)
app.include_router(test.router, prefix="/api/v1/test")


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "CRISalid Taxi API",
        "version": settings.API_VERSION,
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.APP_ENV == "DEV",
    )
