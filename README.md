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

### 3. Vérifier que tout fonctionne

**Vérifier la santé de l'API** :
```bash
curl http://localhost:8000/health/
```

Réponse attendue :
```json
{
  "status": "OK"
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

## 🏗️ Architecture du projet

```
app/
├── main.py                 # Point d'entrée minimaliste
├── crisalid_taxi.py        # Classe principale FastAPI
├── config.py               # Configuration centralisée
├── routes/
│   ├── api.py              # Routeur maître
│   └── health.py           # Endpoint santé
├── settings/
│   └── app_env_types.py    # Types d'environnement
├── db/                     # (À venir) Couche BD
├── models/                 # (À venir) Modèles ORM
├── services/               # (À venir) Logique métier
└── utils/
    └── helpers.py          # Utilitaires
```

## 📦 Dépendances

- **fastapi** : Framework web API
- **uvicorn** : Serveur ASGI
- **pydantic** : Validation des données
- **loguru** : Logging structuré
- **python-dotenv** : Configuration environnement
- **httpx** : Client HTTP

## 🔄 Prochaines étapes

- [ ] Intégrer une base de données (PostgreSQL/MongoDB/etc.)
- [ ] Implémenter les modèles de données (Domain, Field, Subfield, Topic, Keyword)
- [ ] Créer les endpoints API pour la taxonomie CRUD
- [ ] Ajouter les migrations de BD (Alembic)
- [ ] Écrire les tests (pytest)
- [ ] Ajouter l'authentification/autorisation

## � Sécurité

- **Secrets** : Tous les secrets sont gérés par variables d'environnement
- **Fichiers d'environnement** : `.env.local` et `.env` sont ignorés dans git
- **Configuration** : Utilisez `.env.sample` comme template, jamais commit de vrais secrets

## 📝 License

MIT
- **Pydantic** - Validation de données
- **Docker** - Conteneurisation

## 📝 Licence

À définir
