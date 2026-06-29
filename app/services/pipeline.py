"""Startup pipeline orchestrator for OpenAlex data flow."""

import json
from loguru import logger

from app.services.loading.loader import OpenAlexLoader
from app.services.embeddings.embedding_service import EmbeddingService
from app.services.opensearch_client import OpenSearchClient


class StartupPipeline:
    """Orchestrates the startup data loading, embedding generation, and indexing."""

    def __init__(
        self,
        loader: OpenAlexLoader,
        embedding_service: EmbeddingService,
        opensearch_client: OpenSearchClient,
    ):
        self._loader = loader
        self._embedding = embedding_service
        self._opensearch = opensearch_client

    async def run(self) -> bool:
        """Execute the full data pipeline.

        1. Load NDJSON files and build hierarchy
        2. Detect changed levels
        3. Format changed items for embedding
        4. Generate embeddings via IA service
        5. Persist to OpenSearch
        6. Save sync state
        """
        logger.info("🚀 Démarrage du pipeline de chargement et d'indexation OpenAlex...")

        # 1. Load data
        if not self._loader.load():
            logger.error("❌ Échec du chargement des données OpenAlex")
            return False

        # 2. Get changed items
        items = self._loader.formatter.get_all_embedding_items(
            domains=self._loader.domains,
            fields=self._loader.fields,
            subfields=self._loader.subfields,
            topics=self._loader.topics,
            changed_levels=self._loader.state.changed_levels,
        )

        if not items:
            logger.info(
                "✅ Aucun concept n'a été modifié depuis la dernière fois – Étape IA ignorée !"
            )
            return True

        logger.info(f"Envoi de {len(items)} concepts au service d'Intelligence Artificielle...")
        try:
            # 3. Generate embeddings
            embedded = self._embedding.embed_openalex_items(items)
            records = await embedded if hasattr(embedded, "__await__") else embedded



            # 3b. Ensure OpenSearch index mapping for vectors
            if records:
                dims = len(records[0].embedding)
                self._opensearch.ensure_embeddings_index(
                    index_name="openalex_embeddings",
                    dims=dims,
                )

            # 4. Save to OpenSearch
            docs = [
                {
                    "_id": rec.id,
                    "embedding": rec.embedding,
                    "type": rec.type,
                    "display_name": rec.display_name,
                }
                for rec in records
            ]

            self._opensearch.save_embeddings(
                index_name="openalex_embeddings",
                docs=docs,
            )


            # Log a preview of the generated embeddings in JSON format
            logger.info(f"── Résultats OpenAlex au format JSON ({len(records)} générés) ──")
            for rec in records:
                rec_dict = rec.model_dump()
                rec_dict["embedding"] = rec_dict["embedding"][:3] + [
                    f"... ({len(rec_dict['embedding'])} dimensions)"
                ]
                logger.info(json.dumps(rec_dict, ensure_ascii=False))
            logger.info("── End of embeddings ──────────────────────────────")

            # 5. Persist state
            self._loader.state.save_state()
            logger.info("🎉 Pipeline exécuté avec succès et état sauvegardé !")
            return True

        except Exception as exc:  # pylint: disable=broad-exception-caught
            logger.exception(f"❌ Échec de la génération ou indexation des embeddings: {exc}")

            return False
