# ⚙️ Configuration & Variables d'environnement

L'application FastAPI utilise `pydantic-settings` pour charger dynamiquement sa configuration à partir des variables d'environnement ou d'un fichier local `.env`.

---

## 📝 Fichier `.env` de référence

Lors du déploiement ou du développement local, copiez `.env.sample` sous le nom `.env`. Voici le détail complet de toutes les options de configuration disponibles.

### 1. Configuration Générale de l'Application

| Variable | Description | Valeur par défaut / Exemple |
| :--- | :--- | :--- |
| `APP_ENV` | Environnement d'exécution de l'application (`DEV`, `PROD` ou `TEST`). | `DEV` |
| `API_HOST` | Adresse d'écoute de l'API. | `0.0.0.0` |
| `API_PORT` | Port d'écoute de l'API. | `8000` |
| `LOG_LEVEL` | Niveau de journalisation de l'application (ex. `DEBUG`, `INFO`, `WARNING`). | `DEBUG` |

---

### 2. Données OpenAlex

| Variable | Description | Valeur par défaut / Exemple |
| :--- | :--- | :--- |
| `OPENALEX_DATA_HOST_PATH` | Chemin physique sur la machine hôte contenant le snapshot OpenAlex. | `/path/to/openalex/data` |
| `OPENALEX_DATA_PATH` | Chemin d'accès interne (dans le conteneur) où sont lues les données. | `/data/openalex` |

---

### 3. Client & Cluster OpenSearch

| Variable | Description | Valeur par défaut / Exemple |
| :--- | :--- | :--- |
| `OPENSEARCH_HOST` | Adresse d'accès à l'instance OpenSearch. | `opensearch` (Docker) ou `localhost` |
| `OPENSEARCH_PORT` | Port d'accès à l'instance OpenSearch. | `9200` |
| `OPENSEARCH_SCHEME` | Protocole de connexion (`http` ou `https`). | `http` |
| `OPENSEARCH_CLUSTER_NAME` | Nom du cluster OpenSearch (démarrage conteneur). | `opensearch-cluster` |
| `OPENSEARCH_NODE_NAME` | Nom du nœud OpenSearch (démarrage conteneur). | `opensearch-node` |
| `OPENSEARCH_DISCOVERY_TYPE` | Type de découverte de nœuds. | `single-node` |
| `OPENSEARCH_JAVA_OPTS` | Allocation mémoire JVM pour OpenSearch. | `-Xms512m -Xmx512m` |
| `OPENSEARCH_INITIAL_ADMIN_PASSWORD` | Mot de passe administrateur par défaut. | `<change-me>` |
| `OPENSEARCH_SECURITY_DISABLED` | Désactive le plugin de sécurité OpenSearch (recommandé en dev local). | `true` |

---

### 4. Service d'Embeddings (IA)

| Variable | Description | Valeur par défaut / Exemple |
| :--- | :--- | :--- |
| `EMBEDDING_PROVIDER` | Moteur utilisé pour générer les embeddings (`openai_compatible` ou `sentence_transformer`). *Note: seul `openai_compatible` est actuellement implémenté.* | `openai_compatible` |
| `EMBEDDING_API_URL` | Point d'entrée de l'API d'embeddings OpenAI-compatible. L'application ajoute automatiquement `/embeddings` à cette URL. | `https://rag-api.ilaas.fr/v1` |
| `EMBEDDING_API_KEY` | Clé d'API (Bearer token) d'authentification pour le service distant. | `<ilaas-api-key>` |
| `EMBEDDING_API_MODEL` | Nom du modèle d'embedding (ex. `bge-m3`). | `bge-m3` |
| `EMBEDDING_TIMEOUT_SECONDS` | Délai maximal d'attente pour la génération d'embeddings (secondes). | `30` |
| `EMBEDDING_BATCH_SIZE` | Nombre maximal de textes envoyés en une seule requête à l'API IA. Évite les surcharges. | `32` |

---

### 5. Algorithme de Matching

| Variable | Description | Valeur par défaut / Exemple |
| :--- | :--- | :--- |
| `SIMILARITY_THRESHOLD` | Seuil minimum de similarité cosinus (compris entre -1.0 et 1.0) pour valider une relation de classification. | `0.52` |
| `TOP_K` | Nombre maximal de concepts retournés par document. Si `null` ou non défini, tous les concepts au-dessus du seuil sont retournés. | `null` |
| `CHUNK_SIZE` | Taille des lots pour le calcul matriciel de similarité cosinus afin de limiter la consommation mémoire. | `5000` |
