# 🔄 Pipeline d'intégration & Suivi de l'état (State Management)

Au démarrage du serveur FastAPI (hors environnement de test), un pipeline d'initialisation (`StartupPipeline`) s'exécute automatiquement pour lire, structurer, vectoriser et indexer la taxonomie OpenAlex dans OpenSearch.

---

## 📂 Structure attendue des données OpenAlex

Le chargeur de données (`OpenAlexLoader`) cherche les fichiers dans le dossier pointé par `OPENALEX_DATA_PATH`. Ce dossier doit suivre la structure suivante (générée par le snapshot OpenAlex) :

```
/data/openalex/
├── domains/
│   └── YYYYMMDD/
│       └── part_X.ndjson
├── fields/
│   └── YYYYMMDD/
│       └── part_X.ndjson
├── subfields/
│   └── YYYYMMDD/
│       └── part_X.ndjson
└── topics/
    └── YYYYMMDD/
        └── part_X.ndjson
```

---

## ⚡ Indexation incrémentale & Suivi de l'état

Pour éviter de régénérer inutilement les embeddings vectoriels (opération coûteuse en temps et en requêtes d'API IA) à chaque démarrage de l'application, un gestionnaire d'état (`StateTracker`) est implémenté :

1.  **Calcul du statut** : Au démarrage, le pipeline parcourt récursivement chaque sous-dossier de données (`domains`, `fields`, `subfields`, `topics`) et récupère la date de dernière modification maximale (`max_mtime`) de l'ensemble des fichiers s'y trouvant.
2.  **Fichier d'état** : Ces valeurs temporelles sont comparées aux données précédemment stockées dans le fichier JSON d'état local : `/tmp/.taxi_state.json`.
3.  **Décision d'exécution** :
    *   **Aucun changement détecté** : Si aucun niveau n'a de date de modification supérieure à celle enregistrée, le pipeline affiche un message de succès et **ignore** totalement la phase de génération d'embeddings IA et d'écriture OpenSearch.
    *   **Changements détectés** : Si un ou plusieurs niveaux de la hiérarchie ont été modifiés (ou si le fichier d'état n'existe pas), seuls les niveaux modifiés sont traités. Leurs textes formatés sont renvoyés à l'API d'embeddings.
4.  **Sauvegarde** : Une fois l'indexation OpenSearch complétée, le fichier `/tmp/.taxi_state.json` est mis à jour avec les nouvelles valeurs de `mtimes`.

---

## 🎨 Construction du texte pour Embedding

Le texte final envoyé au modèle IA est généré par `build_embedding_text` à partir de la concaténation propre des valeurs textuelles ordonnées :
*   Pour un **Domaine** : son nom d'affichage (`display_name`) et sa description.
*   Pour un **Champ** (Field) : son nom, sa description, ainsi que le nom du Domaine parent associé.
*   Pour un **Sous-champ** (Subfield) : son nom, sa description, ainsi que les noms du Champ et du Domaine parents associés.
*   Pour un **Sujet** (Topic) : son nom, sa description, ses mots-clés (`keywords`), ainsi que la hiérarchie parente complète.

---

## 🔍 Indexation dans OpenSearch

Les embeddings générés sont L2-normalisés (pour rendre le produit scalaire équivalent à la similarité cosinus) et envoyés en lot (*bulk*) dans OpenSearch.

Si l'index `openalex_embeddings` n'existe pas, le pipeline le crée à la volée avec le mapping KNN suivant :
*   **Moteur** : `nmslib`
*   **Algorithme** : `hnsw` (Hierarchical Navigable Small World)
*   **Métrique** : `cosinesimil` (similarité cosinus)
*   **Champs additionnels** : `type` (niveau de la taxonomie) et `display_name` (nom d'affichage original).
