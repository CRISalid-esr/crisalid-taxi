"""Main OpenAlex hierarchy loader service."""

import os
from functools import lru_cache
from loguru import logger

from app.utils.helpers import resolve_env_path
from app.utils.openalex.loading import read_ndjson_entity_dir

from .state import StateTrackerMixin
from .hierarchy import HierarchyResolverMixin
from .formatter import PayloadFormatterMixin
from app.services.opensearch_client import get_opensearch_client


class OpenAlexLoader(StateTrackerMixin, HierarchyResolverMixin, PayloadFormatterMixin):
    """Autonomous loader for OpenAlex classification hierarchy."""

    def __init__(self, base_path: str | None = None):
        """Initialize loader with path to OpenAlex data directory."""
        resolved_base_path = resolve_env_path(base_path, "OPENALEX_DATA_PATH")
        self.base_path = os.path.abspath(resolved_base_path) if resolved_base_path else ""
        logger.debug(f"OpenAlexLoader initialized with path: {self.base_path}")

        # State management configuration
        self._state_file = "/tmp/.taxi_state.json"
        self._level_mtimes: dict[str, float] = {}
        self._changed_levels: set[str] = set()

        # In-memory caches
        self._domains_raw = None
        self._fields_raw = None
        self._subfields_raw = None
        self._topics_raw = None

        # Lookup tables
        self.domain_names: dict[str, str] = {}
        self.field_names: dict[str, str] = {}
        self.subfield_names: dict[str, str] = {}
        self.field_to_domain: dict[str, str] = {}
        self.subfield_to_field: dict[str, str] = {}
        self._domains_by_id: dict[str, dict] = {}
        self._fields_by_id: dict[str, dict] = {}
        self._subfields_by_id: dict[str, dict] = {}
        self._topics_by_id: dict[str, dict] = {}

        # Embedding results
        self._embeddings: list = []
        self._loaded = False

    def _load_raw_records(self) -> None:
        """Load raw entity records from the OpenAlex snapshot."""
        self._domains_raw = read_ndjson_entity_dir(self.base_path, "domains")
        self._fields_raw = read_ndjson_entity_dir(self.base_path, "fields")
        self._subfields_raw = read_ndjson_entity_dir(self.base_path, "subfields")
        self._topics_raw = read_ndjson_entity_dir(self.base_path, "topics")

    def _should_skip_load(self) -> bool:
        """Return True when the loader is already hydrated in memory."""
        if not self._loaded:
            return False

        logger.debug("OpenAlex data already loaded, skipping reload")
        return True

    def _has_valid_base_path(self) -> bool:
        """Validate that the configured OpenAlex directory exists."""
        if os.path.exists(self.base_path):
            return True

        logger.error(f"OpenAlex path does not exist: {self.base_path}")
        return False

    def _get_total_records(self) -> int:
        """Return the total number of loaded OpenAlex records."""
        return sum(len(records) for records in (self.domains, self.fields, self.subfields, self.topics))

    def _finalize_load(self) -> None:
        """Mark the loader as ready and emit the final load summary."""
        self._loaded = True
        logger.info(f"Total chargé : {self._get_total_records()} concepts OpenAlex.")

    def load(self) -> bool:
        """Load all OpenAlex data into memory and build lookups."""
        if self._should_skip_load():
            return True

        if not self._has_valid_base_path():
            return False

        try:
            logger.info(f"Loading OpenAlex hierarchy from {self.base_path}")

            # Mixin method to compute the changes compared to .taxi_state.json
            self._compute_changed_levels()

            self._load_raw_records()
            self._build_lookups()

            self._finalize_load()
            return True
        except Exception as e:
            logger.error(f"Failed to load OpenAlex hierarchy: {e}")
            return False

    async def load_embeddings(self, embedding_service) -> bool:
        """Call the embedding service for all OpenAlex entities and cache results."""
        if not self._loaded:
            logger.warning("Cannot load embeddings: OpenAlex data not yet loaded")
            return False

        items = self.get_all_embedding_items()
        if not items:
            logger.info("Aucun concept n'a été modifié depuis la dernière fois – on passe l'étape IA pour gagner du temps !")
            return True

        logger.info(f"Envoi de {len(items)} concepts au service d'Intelligence Artificielle...")
        try:
            records = await embedding_service.embed_openalex_items(items)

            docs = [
                {
                    "_id": rec.id,
                    "embedding": rec.embedding,
                    "type": rec.type,
                    "display_name": rec.display_name,
                }
                for rec in records
            ]

            opensearch = get_opensearch_client()
            opensearch.save_embeddings(
                index_name="openalex_embeddings",
                docs=docs,
            )

            logger.info(f"── Résultats OpenAlex au format JSON ({len(records)} générés) ──")
            import json
            for rec in records:
                rec_dict = rec.model_dump()
                rec_dict["embedding"] = rec_dict["embedding"][:3] + ["... (1024 dimensions)"]
                logger.info(json.dumps(rec_dict, ensure_ascii=False))
            logger.info("── End of embeddings ──────────────────────────────")
            
            # Mixin method to save the updated state
            self._save_state()

            return True
        except Exception as exc:
            logger.error(f"Failed to load OpenAlex embeddings: {exc}")
            return False

    @property
    def domains(self) -> list[dict]:
        return self._domains_raw or []

    @property
    def fields(self) -> list[dict]:
        return self._fields_raw or []

    @property
    def subfields(self) -> list[dict]:
        return self._subfields_raw or []

    @property
    def topics(self) -> list[dict]:
        return self._topics_raw or []

    def get_summary(self) -> dict:
        """Get summary statistics."""
        return {
            "domains": len(self.domains),
            "fields": len(self.fields),
            "subfields": len(self.subfields),
            "topics": len(self.topics),
            "total": len(self.domains) + len(self.fields) + len(self.subfields) + len(self.topics),
        }

@lru_cache(maxsize=1)
def get_openalex_loader(base_path: str | None = None) -> OpenAlexLoader:
    """Factory function to get OpenAlex loader instance (cached)."""
    loader = OpenAlexLoader(resolve_env_path(base_path, "OPENALEX_DATA_PATH"))
    if not loader.load():
        logger.warning(f"Failed to load OpenAlex data from {loader.base_path or 'OPENALEX_DATA_PATH'}")
    return loader
