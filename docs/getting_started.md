# 🚀 Getting Started & Docker

Ce guide explique comment démarrer rapidement et exécuter l'API `crisalid-taxi` en utilisant Docker et Docker Compose.

---

## 📋 Prérequis

Pour exécuter le projet via Docker, assurez-vous d'avoir installé :
*   **Docker** et **Docker Compose**
*   *Facultatif :* Python 3.11+ et `uv` (si vous souhaitez également développer en local)

---

## ⚡ Lancement rapide avec Docker Compose

Le projet s'appuie sur une pile multi-conteneurs incluant l'API FastAPI, OpenSearch (moteur de recherche vectoriel) et OpenSearch Dashboards (interface graphique d'administration).

### 1. Configuration de l'environnement

Copiez le modèle de configuration `.env.sample` vers un fichier `.env` :

```bash
cp .env.sample .env
```

> ⚠️ **Important :** Modifiez les variables par défaut si nécessaire, en particulier les chemins d'accès aux données OpenAlex (`OPENALEX_DATA_HOST_PATH`) et la clé d'API de l'Embedding Provider.

### 2. Démarrage des services

Lancez l'ensemble de la pile en tâche de fond :

```bash
docker-compose up -d
```

Cette commande va :
1.  Construire l'image Docker de l'API FastAPI.
2.  Démarrer le serveur API FastAPI (écoute sur le port **8000**).
3.  Démarrer une instance OpenSearch 2.11.0 (écoute sur le port **9200**).
4.  Démarrer OpenSearch Dashboards (accessible sur le port **5601**).

### 3. Vérifier le bon fonctionnement

Une fois lancés, vous pouvez valider que les services répondent correctement.

#### Vérifier l'état de préparation de l'API (Readiness)
```bash
curl http://localhost:8000/readiness
```

#### Vérifier l'état de santé d'OpenSearch
```bash
curl http://localhost:9200/
```
*Réponse attendue (exemple) :*
```json
{
  "name": "opensearch-node",
  "cluster_name": "opensearch-cluster",
  "version": {
    "number": "2.11.0"
  }
}
```

#### Accéder à la documentation Swagger/OpenAPI
*   **Swagger UI :** http://localhost:8000/docs
*   **ReDoc :** http://localhost:8000/redoc

---

## 🛑 Arrêter les services

Pour stopper et supprimer l'ensemble des conteneurs créés par Docker Compose :

```bash
docker-compose down
```

> 💡 *Note :* Pour supprimer également les volumes créés (si vous souhaitez réinitialiser complètement l'index OpenSearch), vous pouvez ajouter le drapeau `-v` : `docker-compose down -v`.
