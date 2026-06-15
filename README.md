# 🚖 crisalid-taxi

FastAPI microservice for managing the OpenAlex taxonomy. A minimal and extensible API that performs fast in-memory semantic classification using vector embeddings and OpenSearch.

---

## 🗺️ Documentation Modulaire (Arbre de Navigation)

Pour plus d'informations sur l'installation, le développement, l'utilisation ou le fonctionnement interne, consultez les sections de la documentation ci-dessous :

*   📁 **[docs/](docs/)**
    *   🚀 **[getting_started.md](docs/getting_started.md)** : Démarrage rapide & Docker (Docker Compose, tests de validation initial).
    *   ⚙️ **[configuration.md](docs/configuration.md)** : Variables d'environnement, secrets et options de configuration du fichier `.env`.
    *   🔄 **[pipeline.md](docs/pipeline.md)** : Chargement de la taxonomie OpenAlex, cache et détection incrémentale de changements (`StateTracker`).
    *   🔌 **[api.md](docs/api.md)** : Référence des points d'accès de l'API (`/liveness`, `/readiness`, `POST /match`) et exemples de payloads JSON réels.
    *   🛠️ **[development.md](docs/development.md)** : Guide de développement local (environnement virtuel `uv`, tests `pytest` et outils de qualité).

*Cliquez sur l'un des fichiers ci-dessus pour accéder directement à sa documentation.*

---

## 📋 Prérequis en bref

*   **Docker & Docker Compose** (pour exécuter l'ensemble de la pile de services)
*   **Python 3.11+** & **uv** (uniquement pour le développement local hors conteneurs)

---

## ⚡ Démarrage Rapide (Docker)

1.  **Configurer l'environnement :**
    ```bash
    cp .env.sample .env
    ```
2.  **Démarrer la pile complète (FastAPI, OpenSearch, Dashboards) :**
    ```bash
    docker-compose up -d
    ```
3.  **Tester si l'API est prête :**
    ```bash
    curl http://localhost:8000/readiness
    ```

Pour des instructions de déploiement complètes, consultez le guide [Démarrage rapide & Docker](docs/getting_started.md).

---

## 🔒 Sécurité

*   **Secrets** : Tous les secrets sont gérés exclusivement par des variables d'environnement.
*   **Fichiers d'environnement** : `.env.local` et `.env` sont ignorés par Git.
*   **Configuration** : Utilisez `.env.sample` comme modèle et ne committez jamais de secrets réels.