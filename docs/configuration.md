# ⚙️ Configuration & Environment Variables

The FastAPI application uses `pydantic-settings` to dynamically load its configuration from environment variables or a local `.env` file.

---

## 📝 Reference `.env` File

For deployment or local development, copy `.env.sample` as `.env`. Below is the complete description of all available configuration options.

### 1. General Application Configuration

| Variable | Description | Default / Example |
| :--- | :--- | :--- |
| `APP_ENV` | Application execution environment (`DEV`, `PROD`, or `TEST`). | `DEV` |
| `API_HOST` | Host address the API listens on. | `0.0.0.0` |
| `API_PORT` | Port the API listens on. | `8000` |
| `LOG_LEVEL` | Application logging level (e.g. `DEBUG`, `INFO`, `WARNING`). | `DEBUG` |

---

### 2. OpenAlex Data Configuration

| Variable | Description | Default / Example |
| :--- | :--- | :--- |
| `OPENALEX_DATA_HOST_PATH` | Physical path on the host machine containing the OpenAlex data snapshot. | `/path/to/openalex/data` |
| `OPENALEX_DATA_PATH` | Internal directory path (inside the container) where the application reads OpenAlex data. | `/data/openalex` |

---

### 3. OpenSearch Client & Cluster Configuration

| Variable | Description | Default / Example |
| :--- | :--- | :--- |
| `OPENSEARCH_HOST` | Connection address to the OpenSearch instance. | `opensearch` (Docker) or `localhost` |
| `OPENSEARCH_PORT` | Connection port to the OpenSearch instance. | `9200` |
| `OPENSEARCH_SCHEME` | Connection protocol (`http` or `https`). | `http` |
| `OPENSEARCH_CLUSTER_NAME` | Name of the OpenSearch cluster (container startup). | `opensearch-cluster` |
| `OPENSEARCH_NODE_NAME` | Name of the OpenSearch node (container startup). | `opensearch-node` |
| `OPENSEARCH_DISCOVERY_TYPE` | Node discovery configuration type. | `single-node` |
| `OPENSEARCH_JAVA_OPTS` | JVM memory allocation flags for OpenSearch. | `-Xms512m -Xmx512m` |
| `OPENSEARCH_INITIAL_ADMIN_PASSWORD` | Default admin password. | `<change-me>` |
| `OPENSEARCH_SECURITY_DISABLED` | Disables the OpenSearch security plugin (recommended for local development). | `true` |

---

### 4. Embedding Service Configuration (AI)

| Variable | Description | Default / Example |
| :--- | :--- | :--- |
| `EMBEDDING_PROVIDER` | Engine used to generate embeddings (`openai_compatible` or `sentence_transformer`). *Note: only `openai_compatible` is currently implemented.* | `openai_compatible` |
| `EMBEDDING_API_URL` | Endpoint of the OpenAI-compatible embeddings API. The application automatically appends `/embeddings` to this URL. | `https://rag-api.ilaas.fr/v1` |
| `EMBEDDING_API_KEY` | API key (Bearer token) used for authentication with the remote service. | `<ilaas-api-key>` |
| `EMBEDDING_API_MODEL` | Embedding model identifier (e.g. `bge-m3`). | `bge-m3` |
| `EMBEDDING_TIMEOUT_SECONDS` | Maximum timeout duration for embedding generation requests (seconds). | `30` |
| `EMBEDDING_BATCH_SIZE` | Maximum number of texts sent in a single batch request to the embedding service. | `32` |

---

### 5. Matching Algorithm Settings

| Variable | Description | Default / Example |
| :--- | :--- | :--- |
| `SIMILARITY_THRESHOLD` | Minimum cosine similarity a concept must reach to be returned. Applied **before** `MAX_TOPICS`: concepts below it are dropped, then at most `MAX_TOPICS` of the remainder are kept. Overridable per request via the `similarity_threshold` body field. Recalibrate when changing the embedding model or the k-NN engine. | `0.53` |
| `MAX_TOPICS` | Default maximum number of taxonomy concepts returned per input text, among those above the threshold. Overridable per request via the `max_topics` body field. | `100` |
| `MIN_INPUT_LENGTH` | Minimum characters an input text must have to be matched. Shorter inputs are never embedded and come back with an empty match list. | `25` |

The index uses the nmslib engine (`cosinesimil`), and `_nmslib_score_to_cosine` converts its scores back to cosine similarity. nmslib is deprecated in OpenSearch and removed in 3.x: migrating to faiss means changing the mapping and that conversion together, then recalibrating `SIMILARITY_THRESHOLD` — faiss reports similarity on a different scale.
