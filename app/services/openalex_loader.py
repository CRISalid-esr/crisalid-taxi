"""OpenAlex hierarchy loader service.

Reads OpenAlex snapshot data (domains/fields/subfields/topics) from local filesystem.
Fully autonomous - zero external dependencies beyond standard library.
"""

import os
from functools import lru_cache
from loguru import logger

from app.utils.helpers import (
    build_embedding_text,
    build_id_lookup,
    build_name_lookup,
    build_parent_lookup,
    read_ndjson_entity_dir,
    resolve_env_path,
)


class OpenAlexLoader:
    """Autonomous loader for OpenAlex classification hierarchy."""

    def __init__(self, base_path: str | None = None):
        """Initialize loader with path to OpenAlex data directory.
        
        Args:
            base_path: Path to OpenAlex data directory. If None, uses OPENALEX_DATA_PATH env var.
        """
        resolved_base_path = resolve_env_path(base_path, "OPENALEX_DATA_PATH")
        self.base_path = os.path.abspath(resolved_base_path) if resolved_base_path else ""
        logger.debug(f"OpenAlexLoader initialized with path: {self.base_path}")

        # In-memory caches
        self._domains_raw = None
        self._fields_raw = None
        self._subfields_raw = None
        self._topics_raw = None

        # Lookup tables for names (uri → display_name)
        self.domain_names: dict[str, str] = {}
        self.field_names: dict[str, str] = {}
        self.subfield_names: dict[str, str] = {}
        
        # Lookup tables for hierarchy (uri → parent_uri)
        self.field_to_domain: dict[str, str] = {}
        self.subfield_to_field: dict[str, str] = {}
        
        # Lookup tables for fast O(1) entity access (uri → record)
        self._domains_by_id: dict[str, dict] = {}
        self._fields_by_id: dict[str, dict] = {}
        self._subfields_by_id: dict[str, dict] = {}
        self._topics_by_id: dict[str, dict] = {}

        self._loaded = False

    @staticmethod
    def _build_named_entity(entity_id: str, entity_name: str) -> dict[str, str]:
        """Build a standard id/name payload for a hierarchy node."""
        return {
            "id": entity_id,
            "name": entity_name,
        }

    @staticmethod
    def _build_embedding_payload(values: list[str], keywords: list[str] | None = None) -> str:
        """Build a flat text payload ready for embedding."""
        return build_embedding_text(values, keywords=keywords)

    def _load_raw_records(self) -> None:
        """Load raw entity records from the OpenAlex snapshot."""
        self._domains_raw = read_ndjson_entity_dir(self.base_path, "domains")
        self._fields_raw = read_ndjson_entity_dir(self.base_path, "fields")
        self._subfields_raw = read_ndjson_entity_dir(self.base_path, "subfields")
        self._topics_raw = read_ndjson_entity_dir(self.base_path, "topics")

    def _build_lookups(self) -> None:
        """Build entity lookup tables after raw records are loaded."""
        self.domain_names = build_name_lookup(self.domains)
        self.field_names = build_name_lookup(self.fields)
        self.subfield_names = build_name_lookup(self.subfields)

        self._domains_by_id = build_id_lookup(self.domains)
        self._fields_by_id = build_id_lookup(self.fields)
        self._subfields_by_id = build_id_lookup(self.subfields)
        self._topics_by_id = build_id_lookup(self.topics)

        self.field_to_domain = build_parent_lookup(self.fields, "domain")
        self.subfield_to_field = build_parent_lookup(self.subfields, "field")

    def load(self) -> bool:
        """Load all OpenAlex data into memory and build lookups."""
        if self._loaded:
            logger.debug("OpenAlex data already loaded, skipping reload")
            return True

        if not os.path.exists(self.base_path):
            logger.error(f"OpenAlex path does not exist: {self.base_path}")
            return False

        try:
            logger.info(f"Loading OpenAlex hierarchy from {self.base_path}")

            self._load_raw_records()
            self._build_lookups()

            self._loaded = True
            total = sum(len(x) for x in [self.domains, self.fields, self.subfields, self.topics])
            logger.info(f"OpenAlex hierarchy loaded: {total} total records")
            return True
        except Exception as e:
            logger.error(f"Failed to load OpenAlex hierarchy: {e}")
            return False

    @property
    def domains(self) -> list[dict]:
        """Get all domains."""
        return self._domains_raw or []

    @property
    def fields(self) -> list[dict]:
        """Get all fields."""
        return self._fields_raw or []

    @property
    def subfields(self) -> list[dict]:
        """Get all subfields."""
        return self._subfields_raw or []

    @property
    def topics(self) -> list[dict]:
        """Get all topics."""
        return self._topics_raw or []

    def get_domain_by_uri(self, uri: str) -> dict | None:
        """Get domain record by URI. O(1) lookup."""
        return self._domains_by_id.get(uri)

    def get_field_by_uri(self, uri: str) -> dict | None:
        """Get field record by URI. O(1) lookup."""
        return self._fields_by_id.get(uri)

    def get_subfield_by_uri(self, uri: str) -> dict | None:
        """Get subfield record by URI. O(1) lookup."""
        return self._subfields_by_id.get(uri)

    def get_topic_by_uri(self, uri: str) -> dict | None:
        """Get topic record by URI. O(1) lookup."""
        return self._topics_by_id.get(uri)

    def get_domain_of_field(self, field_uri: str) -> str:
        """Resolve domain name for a field URI."""
        parent_uri = self.field_to_domain.get(field_uri, "")
        return self.domain_names.get(parent_uri, "?")

    def get_field_of_subfield(self, subfield_uri: str) -> str:
        """Resolve field name for a subfield URI."""
        parent_uri = self.subfield_to_field.get(subfield_uri, "")
        return self.field_names.get(parent_uri, "?")

    def get_domain_of_subfield(self, subfield_uri: str) -> str:
        """Resolve domain name for a subfield URI."""
        field_uri = self.subfield_to_field.get(subfield_uri, "")
        return self.get_domain_of_field(field_uri)

    def _resolve_topic_hierarchy(self, topic: dict) -> dict:
        """Extract and resolve hierarchy for a topic (used by formatters).
        
        Returns dict with domain_name, field_name, subfield_name resolved.
        """
        sf_uri = (topic.get("subfield") or {}).get("id", "")
        field_uri = self.subfield_to_field.get(sf_uri, "")
        subfield_name = self.subfield_names.get(sf_uri, "?")
        field_name = self.field_names.get(field_uri, "?")
        domain_name = self.get_domain_of_field(field_uri)
        return {
            "domain_name": domain_name,
            "field_name": field_name,
            "subfield_name": subfield_name,
        }

    def _resolve_subfield_hierarchy(self, subfield: dict) -> dict:
        """Extract and resolve hierarchy for a subfield."""
        field_uri = (subfield.get("field") or {}).get("id", "")
        return {
            "domain_id": self.field_to_domain.get(field_uri, ""),
            "domain_name": self.get_domain_of_field(field_uri),
            "field_id": field_uri,
            "field_name": self.field_names.get(field_uri, "?"),
        }

    def get_keywords(self, record: dict) -> list[str]:
        """Extract keywords from record."""
        kws = record.get("keywords", [])
        if not kws:
            return []
        if isinstance(kws[0], dict):
            return [kw.get("display_name", str(kw)) for kw in kws]
        return [str(k) for k in kws]

    def get_summary(self) -> dict:
        """Get summary statistics."""
        return {
            "domains": len(self.domains),
            "fields": len(self.fields),
            "subfields": len(self.subfields),
            "topics": len(self.topics),
            "total": len(self.domains) + len(self.fields) + len(self.subfields) + len(self.topics),
        }

    # ========================================================================
    # FORMATTED OUTPUT METHODS - Returns hierarchical dict payloads
    # ========================================================================

    def get_domains_formatted(self) -> list[dict]:
        """Get domains formatted as dict payloads."""
        return [
            {
                "domain": self._build_named_entity(
                    domain.get("id", ""),
                    domain.get("display_name", "?"),
                ),
                "description": domain.get("description", ""),
            }
            for domain in self.domains
        ]

    def get_fields_formatted(self) -> list[dict]:
        """Get fields formatted as dict payloads."""
        result = []
        for field in self.fields:
            domain_uri = (field.get("domain") or {}).get("id", "")
            domain_name = self.domain_names.get(domain_uri, "?")
            result.append({
                "domain": self._build_named_entity(domain_uri, domain_name),
                "field": self._build_named_entity(
                    field.get("id", ""),
                    field.get("display_name", "?"),
                ),
                "description": field.get("description", ""),
            })
        return result

    def get_subfields_formatted(self) -> list[dict]:
        """Get subfields formatted as dict payloads."""
        result = []
        for subfield in self.subfields:
            hierarchy = self._resolve_subfield_hierarchy(subfield)
            result.append({
                "domain": self._build_named_entity(hierarchy["domain_id"], hierarchy["domain_name"]),
                "field": self._build_named_entity(hierarchy["field_id"], hierarchy["field_name"]),
                "subfield": self._build_named_entity(
                    subfield.get("id", ""),
                    subfield.get("display_name", "?"),
                ),
                "description": subfield.get("description", ""),
            })
        return result

    def get_topics_formatted(self) -> list[dict]:
        """Get topics formatted as dict payloads."""
        result = []
        for topic in self.topics:
            hierarchy = self._resolve_topic_hierarchy(topic)
            subfield_uri = (topic.get("subfield") or {}).get("id", "")
            field_uri = self.subfield_to_field.get(subfield_uri, "")
            domain_uri = self.field_to_domain.get(field_uri, "")
            result.append({
                "domain": self._build_named_entity(domain_uri, hierarchy["domain_name"]),
                "field": self._build_named_entity(field_uri, hierarchy["field_name"]),
                "subfield": self._build_named_entity(subfield_uri, hierarchy["subfield_name"]),
                "topic": self._build_named_entity(
                    topic.get("id", ""),
                    topic.get("display_name", "?"),
                ),
                "description": topic.get("description", ""),
                "keywords": self.get_keywords(topic),
            })
        return result

    # ========================================================================
    # EMBEDDING OUTPUT METHODS - Returns flat payloads for embedding input
    # ========================================================================

    def get_domains_embedding(self) -> list[str]:
        """Get domains as concatenated text payloads for embedding."""
        return [
            self._build_embedding_payload([
                domain.get("display_name", "?"),
                domain.get("description", ""),
            ])
            for domain in self.domains
        ]

    def get_fields_embedding(self) -> list[str]:
        """Get fields as concatenated text payloads for embedding."""
        result = []
        for field in self.fields:
            domain_uri = (field.get("domain") or {}).get("id", "")
            result.append(self._build_embedding_payload([
                self.domain_names.get(domain_uri, "?"),
                field.get("display_name", "?"),
                field.get("description", ""),
            ]))
        return result

    def get_subfields_embedding(self) -> list[str]:
        """Get subfields as concatenated text payloads for embedding."""
        result = []
        for subfield in self.subfields:
            hierarchy = self._resolve_subfield_hierarchy(subfield)
            result.append(self._build_embedding_payload([
                hierarchy["domain_name"],
                hierarchy["field_name"],
                subfield.get("display_name", "?"),
                subfield.get("description", ""),
            ]))
        return result

    def get_topics_embedding(self) -> list[str]:
        """Get topics as concatenated text payloads for embedding."""
        result = []
        for topic in self.topics:
            hierarchy = self._resolve_topic_hierarchy(topic)
            result.append(self._build_embedding_payload(
                [
                    hierarchy["domain_name"],
                    hierarchy["field_name"],
                    hierarchy["subfield_name"],
                    topic.get("display_name", "?"),
                    topic.get("description", ""),
                ],
                keywords=self.get_keywords(topic),
            ))
        return result


@lru_cache(maxsize=1)
def get_openalex_loader(base_path: str | None = None) -> OpenAlexLoader:
    """Factory function to get OpenAlex loader instance (cached).
    
    Args:
        base_path: Path to OpenAlex data directory. If None, uses OPENALEX_DATA_PATH env var.
    
    Prevents redundant loads when called multiple times with same path.
    """
    loader = OpenAlexLoader(resolve_env_path(base_path, "OPENALEX_DATA_PATH"))
    if not loader.load():
        logger.warning(f"Failed to load OpenAlex data from {loader.base_path or 'OPENALEX_DATA_PATH'}")
    return loader
