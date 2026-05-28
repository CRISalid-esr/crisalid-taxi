# crisalid-taxi

Microservice FastAPI pour la gestion de la taxonomie OpenAlex. API minimale et extensible.

## 📋 Prérequis

- Docker et Docker Compose installés
- Python 3.11+ (pour le développement local)
- uv (gestionnaire de packages Python moderne)

## 🚀 Démarrage rapide avec Docker

### 1. Configuration de l'environnement

Copier le fichier template `.env.sample` en `.env.local` :

```bash
cp .env.sample .env.local
```

Le fichier `.env.local` contient :

```env
APP_ENV=DEV
API_HOST=0.0.0.0
API_PORT=8000
API_TITLE=CRISalid Taxi API
API_VERSION=0.1.0
LOG_LEVEL=DEBUG
```

### 2. Démarrer l'API avec Docker Compose

```bash
docker-compose up -d
```

Cela va :
- Construire l'image Docker de l'API FastAPI
- Démarrer l'API sur le port 8000
- Démarrer OpenSearch 2.11.0 sur le port 9200

### 3. Vérifier que tout fonctionne

**Vérifier la santé de l'API** :
```bash
curl http://localhost:8000/
```

Réponse attendue :
```json
{
  "version": "1.0.0",
  "title": "CRISalid Taxi API"
}
```

**Vérifier la santé d'OpenSearch** :
```bash
curl http://localhost:9200/
```

Réponse attendue :
```json
{
  "name": "opensearch-node",
  "cluster_name": "opensearch-cluster",
  "version": {
    "number": "2.11.0",
    ...
  }
}
```

**Accéder à la documentation Swagger** :
- Ouvrir http://localhost:8000/docs dans le navigateur
- Voir aussi ReDoc à http://localhost:8000/redoc

### 4. Arrêter les services

```bash
docker-compose down
```

## 📚 Documentation API

La documentation Swagger interactive est disponible à :
- **Swagger UI** : http://localhost:8000/docs
- **ReDoc** : http://localhost:8000/redoc
- **OpenAPI JSON** : http://localhost:8000/openapi.json

## 🛠️ Développement local (sans Docker)

### Installation des dépendances

```bash
uv sync
```

### Variables d'environnement

Créer un fichier `.env` pour le développement local :

```bash
cp .env.sample .env
```

### Démarrer l'API

```bash
uv run uvicorn app.crisalid_taxi:CrisalidTaxi --reload
```

## � OpenSearch

OpenSearch 2.11.0 est inclus dans le docker-compose pour la recherche et indexation de la taxonomie.

### Endpoints OpenSearch

- **REST API** : http://localhost:9200
- **Performance Analyzer** : http://localhost:9600

### Commandes utiles

```bash
# Vérifier l'état du cluster
curl http://localhost:9200/_cluster/health

# Lister les indices
curl http://localhost:9200/_cat/indices

# Créer un test index
curl -X PUT http://localhost:9200/test-index

# Ajouter un document
curl -X POST http://localhost:9200/test-index/_doc \
  -H 'Content-Type: application/json' \
  -d '{"name": "Test", "value": 123}'

# Rechercher les documents
curl http://localhost:9200/test-index/_search
```

## �📦 Dépendances

- **fastapi** : Framework web API
- **uvicorn** : Serveur ASGI
- **pydantic** : Validation des données
- **loguru** : Logging structuré
- **httpx** : Client HTTP

## � Sécurité

- **Secrets** : Tous les secrets sont gérés par variables d'environnement
- **Fichiers d'environnement** : `.env.local` et `.env` sont ignorés dans git
- **Configuration** : Utilisez `.env.sample` comme template, jamais commit de vrais secrets

## 📝 Licence

MIT
