"""Main OpenAlex hierarchy loader service using composition."""

import os
from functools import lru_cache
from loguru import logger

from app.utils.helpers import resolve_env_path
from app.utils.openalex.loading import read_ndjson_entity_dir

from .state import StateTracker
from .hierarchy import HierarchyResolver
from .formatter import PayloadFormatter


class OpenAlexLoader:
    """Autonomous loader for OpenAlex classification hierarchy."""

    def __init__(self, base_path: str | None = None):
        """Initialize loader with path to OpenAlex data directory."""
        resolved_base_path = resolve_env_path(base_path, "OPENALEX_DATA_PATH")
        self.base_path = os.path.abspath(resolved_base_path) if resolved_base_path else ""
        logger.debug(f"OpenAlexLoader initialized with path: {self.base_path}")

        # Composition
        self.state = StateTracker(self.base_path)
        self.hierarchy = HierarchyResolver()
        self.formatter = PayloadFormatter(self.hierarchy)

        # In-memory caches for raw NDJSON records
        self._domains_raw: list[dict] | None = None
        self._fields_raw: list[dict] | None = None
        self._subfields_raw: list[dict] | None = None
        self._topics_raw: list[dict] | None = None

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
        return sum(
            len(records) for records in (self.domains, self.fields, self.subfields, self.topics)
        )

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

            # Compute the changes compared to .taxi_state.json
            self.state.compute_changed_levels()

            self._load_raw_records()
            self.hierarchy.build_lookups(
                self.domains,
                self.fields,
                self.subfields,
                self.topics,
            )

            self._finalize_load()
            return True
        except Exception as e:
            logger.error(f"Failed to load OpenAlex hierarchy: {e}")
            return False

    @property
    def domains(self) -> list[dict]:
        """Raw domains list."""
        return self._domains_raw or []

    @property
    def fields(self) -> list[dict]:
        """Raw fields list."""
        return self._fields_raw or []

    @property
    def subfields(self) -> list[dict]:
        """Raw subfields list."""
        return self._subfields_raw or []

    @property
    def topics(self) -> list[dict]:
        """Raw topics list."""
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
        logger.warning(
            f"Failed to load OpenAlex data from {loader.base_path or 'OPENALEX_DATA_PATH'}"
        )
    return loader
