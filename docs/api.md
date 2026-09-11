# 🔌 API Reference & Endpoints

The API exposes standard endpoints under `/api/v1` for classification and testing, as well as root-level probes for orchestration (e.g., Kubernetes).

---

## 📚 Documentation Endpoints

When the application is running, the interactive documentation is available at the following URLs:
*   **Swagger UI (Interactive):** http://localhost:8000/docs
*   **ReDoc (Static):** http://localhost:8000/redoc
*   **Raw OpenAPI JSON schema:** http://localhost:8000/openapi.json

---

## 🏥 Probes & Supervision (Orchestration)

These routes are useful for ensuring the service is alive and ready to receive traffic in a Kubernetes cluster or any other supervision system.

### 1. Liveness Probe (`GET /liveness`)
Returns a simple status to confirm that the FastAPI server is running and responding.
*   **Request:** `GET http://localhost:8000/liveness`
*   **Expected Response (Code 200):**
    ```json
    {
      "status": "healthy"
    }
    ```

### 2. Readiness Probe (`GET /readiness`)
Performs an in-depth check of all vital service dependencies (OpenSearch and the AI provider). If any of the services is unreachable, a `503 Service Unavailable` error code is returned.
*   **Request:** `GET http://localhost:8000/readiness`
*   **Healthy Response (Code 200):**
    ```json
    {
      "status": "healthy",
      "opensearch": "connected",
      "embedding_model": "connected"
    }
    ```
*   **Degraded Response (Code 503):**
    ```json
    {
      "detail": {
        "status": "unhealthy",
        "opensearch": "disconnected",
        "embedding_model": "connected"
      }
    }
    ```

---

## 🧠 Semantic Matching Service

### Semantic Classification (`POST /api/v1/match/`)
This is the core of the application. It allows sending one or multiple free texts (e.g., scientific abstracts) to semantically associate them with one or multiple concepts from the OpenAlex taxonomy.

#### Internal Workflow:
1.  Inputs are screened: a text shorter than `MIN_INPUT_LENGTH` is dropped here and never embedded, and comes back with no matches.
1.  The remaining texts are encoded into vectors (embeddings) via the AI service.
2.  An approximate k-NN search is delegated to the HNSW index of OpenSearch (no in-memory matrix is loaded).
3.  The nearest concepts are returned per input, sorted by decreasing cosine similarity.
4.  Filtering runs in two phases: concepts scoring below `similarity_threshold` are dropped, then at most `max_topics` of the remainder are kept. Both are request parameters — see below.

#### Request Format
*   **Endpoint:** `POST http://localhost:8000/api/v1/match/`
*   **Headers:** `Content-Type: application/json`
*   **Request Body (JSON):**
    *   `inputs` (list[object]): List of input objects to classify. Each object contains:
        *   `id` (str): Unique identifier corresponding to the text (e.g., an application-specific UUID).
        *   `text` (str): Text to classify. Must not be empty, and must be at least `MIN_INPUT_LENGTH` characters once stripped.
    *   `similarity_threshold` (float, optional): Minimum cosine similarity a concept must reach to be returned, between `-1.0` and `1.0`. Applied **before** `max_topics`. Omit to use the server default (`SIMILARITY_THRESHOLD`), or pass `0.0` to disable filtering.
    *   `max_topics` (int, optional): Maximum number of concepts returned per input, between `1` and `1000`, kept among those above the threshold. Omit to use the server default (`MAX_TOPICS`).

```bash
curl -X POST http://localhost:8000/api/v1/match/ \
  -H 'Content-Type: application/json' \
  -d '{
    "inputs": [
      {"id": "doc-uuid-1", "text": "Machine learning algorithms for quantum computing physics simulations"},
      {"id": "doc-uuid-2", "text": "Taxonomy of soccer training methods"}
    ],
    "similarity_threshold": 0.5,
    "max_topics": 20
  }'
```

#### Response Format (Return Payload)
The response is formatted as a dictionary ready to be inserted into a Knowledge Graph (IKG):
*   `generated_at` (str): UTC Date/time in ISO format (`YYYYMMDDTHHMMSSZ`).
*   `model` (str): Embedding model used.
*   `query_count` (int): Number of input documents.
*   `total_matches` (int): Total number of (input, concept) pairs returned.
*   `similarity_threshold` (float): The threshold actually applied to this request, whether it came from the body or the server default.
*   `results` (list): List of results grouped by input document. Each item contains:
    *   `id` (str): The provided opaque identifier.
        *   `matches` (list): List of matched concepts, sorted by relevance, possibly empty — either nothing cleared the threshold, or the text was too short to be matched. It contains:
        *   `concept_uid` (str): OpenAlex URI of the concept (e.g., `https://openalex.org/topics/1111`).
        *   `rel_type` (str): The taxonomy relationship type (`HAS_DOMAIN`, `HAS_FIELD`, `HAS_SUBFIELD`, `HAS_TOPIC`).
        *   `value` (float): The cosine similarity score rounded to 6 decimal places, always `>= similarity_threshold`.

*Example Returned Response:*
```json
{
  "generated_at": "20260615T113123Z",
  "model": "bge-m3",
  "query_count": 2,
  "total_matches": 2,
  "similarity_threshold": 0.5,
  "results": [
    {
      "id": "doc-uuid-1",
      "matches": [
        {
          "concept_uid": "https://openalex.org/topics/1111",
          "rel_type": "HAS_TOPIC",
          "value": 0.765432
        },
        {
          "concept_uid": "https://openalex.org/subfields/111",
          "rel_type": "HAS_SUBFIELD",
          "value": 0.612345
        }
      ]
    },
    {
      "id": "doc-uuid-2",
      "matches": []
    }
  ]
}
```


