# crisalid-taxi

Microservice FastAPI pour la gestion de la taxonomie OpenAlex. API minimale et extensible.

## 📋 Prérequis

- Docker et Docker Compose installés
- Python 3.11+ (pour le développement local)
- [uv](https://docs.astral.sh/uv/) (gestionnaire de packages Python moderne)

### Installation de uv

```bash
# Linux / macOS
curl -LsSf https://astral.sh/uv/install.sh | sh

# Ou via pip
pip install uv
```

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
# Installer les dépendances de production
uv sync

# Installer toutes les dépendances (prod + dev : pytest, black, pylint, etc.)
uv sync --all-extras
```

### Gestion des dépendances

Les dépendances sont déclarées dans `pyproject.toml` et verrouillées dans `uv.lock`.

```bash
# Ajouter une dépendance de production
uv add <package>

# Ajouter une dépendance de développement
uv add --optional dev <package>

# Supprimer une dépendance
uv remove <package>
```

> ⚠️ **Ne pas modifier manuellement `uv.lock`** — ce fichier est généré automatiquement par `uv sync` / `uv add`.

### Variables d'environnement

Créer un fichier `.env` pour le développement local :

```bash
cp .env.sample .env
```

### Démarrer l'API

```bash
uv run uvicorn app.crisalid_taxi:CrisalidTaxi --reload
```

### Tests et qualité de code

```bash
# Lancer les tests
uv run pytest tests/ -v

# Lancer les tests avec couverture
uv run pytest tests/ -v --cov=app --cov-report=html

# Vérifier le formatage
uv run black --check app/ tests/

# Formater le code
uv run black app/ tests/

# Linter
uv run pylint app/

# Vérification de types
uv run mypy app/ tests/
```

## 🔍 OpenSearch

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

## 📦 Dépendances

Gérées via `pyproject.toml` et verrouillées dans `uv.lock`.

### Production

| Package | Rôle |
|---------|------|
| **fastapi** | Framework web API |
| **uvicorn** | Serveur ASGI |
| **pydantic** | Validation des données |
| **pydantic-settings** | Configuration via variables d'environnement |
| **loguru** | Logging structuré |
| **httpx** | Client HTTP asynchrone |
| **aiohttp** | Client HTTP asynchrone (sessions) |
| **opensearch-py** | Client OpenSearch |
| **pyyaml** | Parsing YAML |
| **python-dotenv** | Chargement des fichiers `.env` |

### Développement

| Package | Rôle |
|---------|------|
| **pytest** | Framework de tests |
| **pytest-asyncio** | Support async pour pytest |
| **pytest-cov** | Couverture de code |
| **black** | Formatage du code |
| **isort** | Tri des imports |
| **flake8** | Linter PEP 8 |
| **mypy** | Vérification de types |
| **pylint** | Analyse statique |

## 🔒 Sécurité

- **Secrets** : Tous les secrets sont gérés par variables d'environnement
- **Fichiers d'environnement** : `.env.local` et `.env` sont ignorés dans git
- **Configuration** : Utilisez `.env.sample` comme template, jamais commit de vrais secrets

## 📝 Licence

MIT
