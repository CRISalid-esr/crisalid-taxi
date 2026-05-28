# crisalid-taxi

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

Puis éditer `.env.local` et remplir les variables :

```env
APP_ENV=DEV
API_HOST=0.0.0.0
API_PORT=8000
LOG_LEVEL=INFO

# Database
DB_USER=crisalid_user
DB_PASSWORD=votre_mot_de_passe_securise
DB_NAME=crisalid_db
```

### 2. Démarrer les services avec Docker Compose

```bash
docker-compose up -d
```

Cela va :
- Créer et démarrer le service PostgreSQL sur le port 5432
- Créer et démarrer l'API FastAPI sur le port 8000
- Créer un volume persistant pour les données PostgreSQL

### 3. Vérifier que tout fonctionne

**Vérifier la santé de l'API** :
```bash
curl http://localhost:8000/api/v1/health
```

Réponse attendue :
```json
{
  "status": "healthy",
  "service": "crisalid-taxi"
}
```

**Accéder à la documentation Swagger** :
- Ouvrir http://localhost:8000/docs dans le navigateur

### 4. Arrêter les services

```bash
docker-compose down
```

Pour arrêter et supprimer les données persistantes :
```bash
docker-compose down -v
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
uv run uvicorn app.main:app --reload
```

L'API sera accessible à http://localhost:8000

## 🔒 Sécurité

- **Secrets** : Tous les secrets (DB_PASSWORD, etc.) sont gérés par variables d'environnement
- **Fichiers d'environnement** : `.env.local` et `.env` sont ignorés dans git
- **Configuration** : Utilisez `.env.sample` comme template, jamais commit de vrais secrets

Voir [SECURITY.md](SECURITY.md) pour plus de détails sur la gestion des secrets.

## 📦 Dépendances principales

- **FastAPI** 0.104.1 - Framework web moderne
- **PostgreSQL** 16 - Base de données
- **SQLAlchemy** 2.0.23 - ORM Python
- **Pydantic** - Validation de données
- **Docker** - Conteneurisation

## 📝 Licence

À définir
