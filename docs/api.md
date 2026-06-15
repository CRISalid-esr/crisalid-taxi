# 🔌 Référence de l'API & Points d'accès (Endpoints)

L'API exposes standard endpoints under `/api/v1` for classification and testing, as well as root-level probes for orchestration (Kubernetes).

---

## 📚 Points d'accès de Documentation

Lorsque l'application est démarrée, les documentations interactives sont accessibles aux adresses suivantes :
*   **Swagger UI (Interactif) :** http://localhost:8000/docs
*   **ReDoc (Statique) :** http://localhost:8000/redoc
*   **Schéma OpenAPI JSON brut :** http://localhost:8000/openapi.json

---

## 🏥 Probes & Supervision (Orchestration)

Ces routes sont utiles pour s'assurer que le service est vivant et prêt à recevoir du trafic dans un cluster Kubernetes ou tout autre système de supervision.

### 1. Liveness Probe (`GET /liveness`)
Renvoie un statut simple pour confirmer que le serveur FastAPI est actif et répond.
*   **Requête :** `GET http://localhost:8000/liveness`
*   **Réponse attendue (Code 200) :**
    ```json
    {
      "status": "healthy"
    }
    ```

### 2. Readiness Probe (`GET /readiness`)
Vérifie en profondeur l'ensemble des dépendances vitales du service (OpenSearch et le fournisseur d'IA). Si l'un des deux services est inaccessible, un code d'erreur `503 Service Unavailable` est retourné.
*   **Requête :** `GET http://localhost:8000/readiness`
*   **Réponse saine (Code 200) :**
    ```json
    {
      "status": "healthy",
      "opensearch": "connected",
      "embedding_model": "connected"
    }
    ```
*   **Réponse dégradée (Code 503) :**
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

## 🧠 Service de Matching Sémantique

### Classification Sémantique (`POST /api/v1/match/`)
C'est le cœur applicatif de l'application. Elle permet d'envoyer un ou plusieurs textes libres (ex. résumés scientifiques) afin de les associer sémantiquement à un ou plusieurs concepts de la taxonomie OpenAlex.

#### Fonctionnement interne :
1.  Les textes fournis sont encodés en vecteurs (embeddings) via le service IA.
2.  L'application charge l'intégralité de l'index d'embeddings OpenAlex en mémoire depuis OpenSearch (en utilisant des requêtes *scroll* optimisées).
3.  Un calcul matriciel de produit scalaire est effectué en mémoire via **NumPy** pour trouver la similarité cosinus de chaque texte avec tous les concepts.
4.  Les résultats dont la valeur de similarité est supérieure ou égale à `SIMILARITY_THRESHOLD` sont triés et regroupés.

#### Format de la Requête
*   **Point d'accès :** `POST http://localhost:8000/api/v1/match/`
*   **En-têtes :** `Content-Type: application/json`
*   **Corps de requête (JSON) :**
    *   `texts` (list[str]) : Liste des textes à classifier. Ne doit pas contenir de chaîne vide.
    *   `ids` (list[str]) : Identifiants uniques correspondant à chaque texte (ex. identifiants de nœuds Neo4j).
    *   *Note : les listes `texts` et `ids` doivent obligatoirement avoir la même taille.*

```bash
curl -X POST http://localhost:8000/api/v1/match/ \
  -H 'Content-Type: application/json' \
  -d '{
    "texts": ["Machine learning algorithms for quantum computing physics simulations", "Taxonomy of soccer training methods"],
    "ids": ["doc-uuid-1", "doc-uuid-2"]
  }'
```

#### Format de la Réponse (Payload de retour)
La réponse renvoyée est formatée sous forme de dictionnaire prêt à être inséré dans un graphe de connaissances (IKG) :
*   `generated_at` (str) : Date/heure UTC au format ISO (`YYYYMMDDTHHMMSSZ`).
*   `model` (str) : Modèle d'embeddings utilisé.
*   `query_count` (int) : Nombre de documents passés en entrée.
*   `total_matches` (int) : Nombre total de correspondances trouvées au-dessus du seuil.
*   `results` (list) : Liste de résultats regroupés par document d'entrée. Chaque élément contient :
    *   `id` (str) : L'identifiant opaque transmis.
    *   `matches` (list) : Liste de concepts appariés, triés par pertinence, contenant :
        *   `concept_uid` (str) : URI OpenAlex du concept (ex. `https://openalex.org/topics/1111`).
        *   `rel_type` (str) : Le type de relation de la taxonomie (`HAS_DOMAIN`, `HAS_FIELD`, `HAS_SUBFIELD`, `HAS_TOPIC`).
        *   `value` (float) : Le score de similarité cosinus arrondi à 6 décimales.

*Exemple de réponse retournée :*
```json
{
  "generated_at": "20260615T113123Z",
  "model": "bge-m3",
  "query_count": 2,
  "total_matches": 2,
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

---

## 🧪 Points d'accès de Test

### Endpoints de Test (`GET /api/v1/test/`)
Ces routes permettent de s'assurer de la communication simple de bout en bout de l'API REST.
*   `GET /api/v1/test/` : Renvoie un message générique.
*   `GET /api/v1/test/{name}` : Renvoie un salut personnalisé avec le nom fourni.
